"""Terrain of a field from SRTM (NASADEM): elevation and slope (phase 8)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func, select

from app.api.deps import SessionDep, require_roles
from app.api.fields import job_out
from app.models import (
    DataFetchJob,
    DataSource,
    Field,
    JobStatus,
    RegionalObservation,
    Role,
    User,
)
from app.schemas.fields import JobOut
from app.services.fields import visible_to
from app.services.terrain import SOURCE
from app.tasks.terrain import fetch_field_terrain

router = APIRouter(prefix="/fields/{field_id}/terrain", tags=["terrain"])

StaffUser = Annotated[
    User, Depends(require_roles(Role.ADMIN, Role.AGRONOMIST, Role.COOPERATIVE_USER))
]


class TerrainOut(BaseModel):
    available: bool
    elevation_m: float | None
    elevation_min_m: float | None
    elevation_max_m: float | None
    slope_deg: float | None
    source: str
    latest_job: JobOut | None


def _field(session: SessionDep, user: User, field_id: uuid.UUID) -> Field:
    field = session.scalar(select(Field).where(Field.id == field_id, visible_to(user)))
    if field is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Field not found")
    return field


@router.get("", response_model=TerrainOut)
def read_terrain(field_id: uuid.UUID, session: SessionDep, user: StaffUser) -> TerrainOut:
    field = _field(session, user, field_id)
    values = dict(
        session.execute(
            select(RegionalObservation.variable, RegionalObservation.value).where(
                RegionalObservation.field_id == field.id, RegionalObservation.source == SOURCE
            )
        ).all()
    )
    job = session.execute(
        select(DataFetchJob, DataSource.key)
        .join(DataSource, DataSource.id == DataFetchJob.data_source_id)
        .where(DataFetchJob.field_id == field.id, DataSource.key == SOURCE)
        .order_by(DataFetchJob.created_at.desc())
        .limit(1)
    ).first()
    return TerrainOut(
        available=bool(values),
        elevation_m=values.get("elevation_m"),
        elevation_min_m=values.get("elevation_min_m"),
        elevation_max_m=values.get("elevation_max_m"),
        slope_deg=values.get("slope_deg"),
        source="NASADEM (SRTM)",
        latest_job=job_out(job[0], job[1], field) if job else None,
    )


@router.post("/fetch", response_model=JobOut, status_code=status.HTTP_202_ACCEPTED)
def fetch_terrain(field_id: uuid.UUID, session: SessionDep, user: StaffUser) -> JobOut:
    """Queue a terrain read for the field. The worker does the work."""
    field = _field(session, user, field_id)
    source = session.scalar(select(DataSource).where(DataSource.key == SOURCE))
    if source is None:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Reference data is not loaded; run 'python -m app.cli seed-reference'",
        )
    running = session.scalar(
        select(func.count())
        .select_from(DataFetchJob)
        .where(
            DataFetchJob.field_id == field.id,
            DataFetchJob.data_source_id == source.id,
            DataFetchJob.status.in_([JobStatus.QUEUED, JobStatus.RUNNING]),
        )
    )
    if running:
        raise HTTPException(status.HTTP_409_CONFLICT, detail={"code": "fetch_already_running"})
    job = DataFetchJob(field_id=field.id, data_source_id=source.id, status=JobStatus.QUEUED)
    session.add(job)
    session.commit()
    try:
        fetch_field_terrain.delay(str(job.id))
    except Exception as error:  # the broker is down
        job.status = JobStatus.FAILED
        job.error_message = f"The job queue is not reachable: {error}"[:1000]
        job.finished_at = datetime.now(UTC)
        session.commit()
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, detail="The job queue is not reachable"
        ) from error
    session.refresh(job)
    return job_out(job, SOURCE, field)

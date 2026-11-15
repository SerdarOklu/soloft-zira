"""Field Memory: MODIS NDVI, the cropped or fallow history, and its confirmation (phase 5)."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select

from app.api.deps import SessionDep, require_roles
from app.api.fields import job_out
from app.core.parameters import get_config
from app.models import (
    CropCycle,
    CycleSource,
    CycleState,
    DataFetchJob,
    DataSource,
    Field,
    JobStatus,
    Role,
    SatelliteObservation,
    User,
)
from app.schemas.field_memory import (
    ConfirmIn,
    Coverage,
    FieldMemoryOut,
    NdviPoint,
    SeasonOut,
)
from app.schemas.fields import JobOut
from app.services import field_memory as memory
from app.services.fields import visible_to
from app.services.modis import SOURCE as MODIS_SOURCE
from app.services.modis import default_range
from app.tasks.modis import fetch_field_ndvi

router = APIRouter(prefix="/fields/{field_id}/field-memory", tags=["field-memory"])

StaffUser = Annotated[
    User, Depends(require_roles(Role.ADMIN, Role.AGRONOMIST, Role.COOPERATIVE_USER))
]


def _field(session: SessionDep, user: User, field_id: uuid.UUID) -> Field:
    field = session.scalar(select(Field).where(Field.id == field_id, visible_to(user)))
    if field is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Field not found")
    return field


def _confirmer_role(user: User) -> CycleSource:
    return CycleSource.USER if user.role == Role.COOPERATIVE_USER else CycleSource.AGRONOMIST


def build(session: SessionDep, field: Field) -> FieldMemoryOut:
    config = get_config()
    threshold = config.rotation_demo.ndvi_cropped_threshold.value
    history_years = int(config.parameters.get("core", "history_years"))
    today = datetime.now(UTC).date()

    rows = list(
        session.scalars(
            select(SatelliteObservation)
            .where(
                SatelliteObservation.field_id == field.id,
                SatelliteObservation.source == MODIS_SOURCE,
            )
            .order_by(SatelliteObservation.image_date)
        )
    )
    observations = [
        memory.Obs(row.image_date, row.ndvi_mean, row.valid_pixel_count or 0) for row in rows
    ]
    detected = memory.detect(
        observations, threshold=threshold, history_years=history_years, today=today
    )
    confirmed = {
        cycle.season: cycle
        for cycle in session.scalars(select(CropCycle).where(CropCycle.field_id == field.id))
        if cycle.confirmed_at is not None
    }

    seasons = []
    for item in detected:
        cycle = confirmed.get(item.season)
        seasons.append(
            SeasonOut(
                season=item.season,
                harvest_year=item.harvest_year,
                detected_state=item.state,
                peak_ndvi=item.peak_ndvi,
                peak_date=item.peak_date,
                good_observations=item.good_observations,
                total_observations=item.total_observations,
                confidence=item.confidence,
                confidence_level=memory.confidence_level(item.confidence),
                confirmed_state=cycle.state.value if cycle else None,
                confirmed_by=cycle.source.value if cycle else None,
                confirmed_at=cycle.confirmed_at if cycle else None,
            )
        )

    series_from = date(detected[0].harvest_year - 1, 9, 1) if detected else None
    series = [
        NdviPoint(
            date=row.image_date,
            ndvi=row.ndvi_mean,
            valid_pixels=row.valid_pixel_count or 0,
            flag=row.quality_flag,
        )
        for row in rows
        if series_from is None or row.image_date >= series_from
    ]
    job = session.execute(
        select(DataFetchJob, DataSource.key)
        .join(DataSource, DataSource.id == DataFetchJob.data_source_id)
        .where(DataFetchJob.field_id == field.id, DataSource.key == MODIS_SOURCE)
        .order_by(DataFetchJob.created_at.desc())
        .limit(1)
    ).first()
    return FieldMemoryOut(
        field_id=field.id,
        history_years=history_years,
        threshold=threshold,
        provisional=True,
        coverage=Coverage(
            observations=len(rows),
            good=sum(1 for o in observations if o.ndvi is not None and o.valid_pixels >= 1),
            first_date=rows[0].image_date if rows else None,
            last_date=rows[-1].image_date if rows else None,
        ),
        seasons=seasons,
        series=series,
        latest_job=job_out(job[0], job[1], field) if job else None,
        confirmed_count=sum(1 for s in seasons if s.confirmed_state),
    )


@router.get("", response_model=FieldMemoryOut)
def read_field_memory(field_id: uuid.UUID, session: SessionDep, user: StaffUser) -> FieldMemoryOut:
    return build(session, _field(session, user, field_id))


@router.post("/fetch", response_model=JobOut, status_code=status.HTTP_202_ACCEPTED)
def fetch_ndvi(field_id: uuid.UUID, session: SessionDep, user: StaffUser) -> JobOut:
    """Queue a MODIS NDVI fetch for the last seasons. The worker does the work."""
    field = _field(session, user, field_id)
    config = get_config()
    source = session.scalar(select(DataSource).where(DataSource.key == MODIS_SOURCE))
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
    start, end = default_range(
        datetime.now(UTC).date(), int(config.parameters.get("core", "history_years"))
    )
    job = DataFetchJob(
        field_id=field.id,
        data_source_id=source.id,
        date_from=start,
        date_to=end,
        status=JobStatus.QUEUED,
    )
    session.add(job)
    session.commit()
    try:
        fetch_field_ndvi.delay(str(job.id))
    except Exception as error:  # the broker is down
        job.status = JobStatus.FAILED
        job.error_message = f"The job queue is not reachable: {error}"[:1000]
        job.finished_at = datetime.now(UTC)
        session.commit()
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, detail="The job queue is not reachable"
        ) from error
    session.refresh(job)
    return job_out(job, MODIS_SOURCE, field)


@router.post("/confirm", response_model=FieldMemoryOut)
def confirm(
    field_id: uuid.UUID, body: ConfirmIn, session: SessionDep, user: StaffUser
) -> FieldMemoryOut:
    """Record what a person confirms for each season. This history is strategy A (PDT 4.1)."""
    field = _field(session, user, field_id)
    detected = {s.season: s for s in build(session, field).seasons}
    unknown = [item.season for item in body.seasons if item.season not in detected]
    if unknown:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"code": "unknown_season", "season": unknown[0]},
        )
    now = datetime.now(UTC)
    for item in body.seasons:
        cycle = session.scalar(
            select(CropCycle).where(CropCycle.field_id == field.id, CropCycle.season == item.season)
        )
        if cycle is None:
            cycle = CropCycle(field_id=field.id, season=item.season)
            session.add(cycle)
        seen = detected[item.season]
        cycle.state = CycleState(item.state)
        cycle.source = _confirmer_role(user)
        # Confidence belongs to the detection; a person who changes the call overrides it.
        cycle.confidence = seen.confidence if seen.detected_state == item.state else None
        cycle.confirmed_by = user.id
        cycle.confirmed_at = now
    session.commit()
    return build(session, field)

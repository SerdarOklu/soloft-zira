"""Data Center: whether NASA data really arrives (PDT section 10.3, phase 3)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select

from app.api.deps import SessionDep, require_roles
from app.api.fields import job_out
from app.core.parameters import get_config
from app.models import DataFetchJob, DataSource, Field, Role, User, WeatherObservation
from app.schemas.fields import JobCounts, JobOut, SourceOut

router = APIRouter(prefix="/data-center", tags=["data-center"])

Analyst = Annotated[User, Depends(require_roles(Role.ADMIN, Role.AGRONOMIST))]

MAX_JOBS = 200


@router.get("/sources", response_model=list[SourceOut])
def sources(session: SessionDep, _user: Analyst) -> list[SourceOut]:
    rows = {row.key: row for row in session.scalars(select(DataSource))}
    counts: dict[str, JobCounts] = {}
    for source_id, job_status, total in session.execute(
        select(DataFetchJob.data_source_id, DataFetchJob.status, func.count()).group_by(
            DataFetchJob.data_source_id, DataFetchJob.status
        )
    ):
        counts.setdefault(str(source_id), JobCounts())
        setattr(counts[str(source_id)], job_status.value, total)
    weather_rows = dict(
        session.execute(
            select(WeatherObservation.source, func.count()).group_by(WeatherObservation.source)
        ).all()
    )

    result: list[SourceOut] = []
    for key, source in get_config().data_sources.items():
        row = rows.get(key)
        # Only POWER is connected in phase 3; the Earth Engine sources arrive in phase 5.
        connected = source.access == "power_daily_api"
        if not connected:
            state = "not_connected"
        else:
            state = (row.status if row else None) or "never_fetched"
        result.append(
            SourceOut(
                key=key,
                name=source.name,
                role=source.role,
                access=source.access,
                resolution=source.resolution,
                priority=source.priority,
                scale_warning=source.scale_warning,
                collection_id=source.collection_id,
                connected=connected,
                status=state,
                last_success_at=row.last_success_at if row else None,
                observations=weather_rows.get(key, 0),
                jobs=counts.get(str(row.id), JobCounts()) if row else JobCounts(),
            )
        )
    return result


@router.get("/jobs", response_model=list[JobOut])
def jobs(
    session: SessionDep, _user: Analyst, limit: Annotated[int, Query(ge=1, le=MAX_JOBS)] = 50
) -> list[JobOut]:
    rows = session.execute(
        select(DataFetchJob, Field, DataSource.key)
        .outerjoin(Field, Field.id == DataFetchJob.field_id)
        .join(DataSource, DataSource.id == DataFetchJob.data_source_id)
        .order_by(DataFetchJob.created_at.desc())
        .limit(limit)
    ).all()
    return [job_out(job, source_key, field) for job, field, source_key in rows]

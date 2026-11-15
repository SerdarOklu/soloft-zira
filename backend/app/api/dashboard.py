"""Overview: the state of the system at a glance (PDT section 10.3, phase 3)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select

from app.api.deps import SessionDep, require_roles
from app.models import DataFetchJob, Field, JobStatus, Role, User
from app.schemas.fields import DashboardSummary, JobCounts, Marker, MissingField
from app.services.fields import visible_to, weather_days

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

StaffUser = Annotated[
    User, Depends(require_roles(Role.ADMIN, Role.AGRONOMIST, Role.COOPERATIVE_USER))
]

MISSING_LIST_LIMIT = 5


@router.get("/summary", response_model=DashboardSummary)
def summary(session: SessionDep, user: StaffUser) -> DashboardSummary:
    scope = visible_to(user)
    fields = session.execute(
        select(
            Field.id,
            Field.code,
            Field.name,
            Field.area_ha,
            func.ST_Y(Field.centroid).label("lat"),
            func.ST_X(Field.centroid).label("lon"),
            weather_days().label("weather_days"),
        )
        .where(scope)
        .order_by(Field.created_at.desc())
    ).all()

    jobs = JobCounts()
    for job_status, total in session.execute(
        select(DataFetchJob.status, func.count())
        .join(Field, Field.id == DataFetchJob.field_id)
        .where(scope)
        .group_by(DataFetchJob.status)
    ):
        setattr(jobs, job_status.value, total)

    last_update = session.scalar(
        select(func.max(DataFetchJob.finished_at))
        .join(Field, Field.id == DataFetchJob.field_id)
        .where(scope, DataFetchJob.status == JobStatus.DONE)
    )

    missing = [row for row in fields if row.weather_days == 0]
    return DashboardSummary(
        field_count=len(fields),
        fields_with_weather=len(fields) - len(missing),
        fields_missing_weather=[
            MissingField(id=row.id, code=row.code, name=row.name)
            for row in missing[:MISSING_LIST_LIMIT]
        ],
        jobs=jobs,
        last_weather_update=last_update,
        markers=[
            Marker(
                id=row.id,
                code=row.code,
                name=row.name,
                lat=row.lat,
                lon=row.lon,
                area_ha=row.area_ha,
                has_weather=row.weather_days > 0,
            )
            for row in fields
            if row.lat is not None
        ],
    )

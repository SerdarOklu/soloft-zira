"""Regional cross-checks of a field: SMAP, GPM IMERG and GRACE (phase 8)."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, select

from app.api.deps import SessionDep, require_roles
from app.api.fields import job_out
from app.core.config import get_settings
from app.models import (
    DataFetchJob,
    DataSource,
    Field,
    JobStatus,
    RegionalObservation,
    Role,
    User,
    WeatherObservation,
)
from app.schemas.fields import JobOut
from app.services import regional as service
from app.services.fields import visible_to
from app.services.power import SOURCE as POWER_SOURCE
from app.tasks.regional import fetch_field_regional

router = APIRouter(prefix="/fields/{field_id}/regional", tags=["regional"])

StaffUser = Annotated[
    User, Depends(require_roles(Role.ADMIN, Role.AGRONOMIST, Role.COOPERATIVE_USER))
]
SourceChoice = Literal["smap", "gpm", "grace", "all"]


class SmapPoint(BaseModel):
    date: date
    am: float | None
    pm: float | None


class SmapOut(BaseModel):
    days: int
    mean_am: float | None
    mean_pm: float | None
    last_date: date | None
    series: list[SmapPoint]


class GpmPoint(BaseModel):
    date: date
    imerg_mm: float
    power_mm: float | None


class GpmOut(BaseModel):
    days: int
    imerg_total_mm: float | None
    power_total_mm: float | None
    correlation: float | None
    series: list[GpmPoint]


class GraceOut(BaseModel):
    months: int
    first_date: date | None
    last_date: date | None
    latest_cm: float | None
    trend_cm_per_year: float | None


class RegionalOut(BaseModel):
    configured: bool
    smap: SmapOut
    gpm: GpmOut
    grace: GraceOut
    latest_jobs: list[JobOut]


def _field(session: SessionDep, user: User, field_id: uuid.UUID) -> Field:
    field = session.scalar(select(Field).where(Field.id == field_id, visible_to(user)))
    if field is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Field not found")
    return field


def _values(session: SessionDep, field: Field, source: str, variable: str) -> dict[date, float]:
    return {
        day: value
        for day, value in session.execute(
            select(RegionalObservation.observed_on, RegionalObservation.value)
            .where(
                RegionalObservation.field_id == field.id,
                RegionalObservation.source == source,
                RegionalObservation.variable == variable,
                RegionalObservation.value.is_not(None),
            )
            .order_by(RegionalObservation.observed_on)
        )
    }


def build(session: SessionDep, field: Field) -> RegionalOut:
    am = _values(session, field, "smap", "soil_moisture_am")
    pm = _values(session, field, "smap", "soil_moisture_pm")
    days = sorted(set(am) | set(pm))
    smap = SmapOut(
        days=len(days),
        mean_am=sum(am.values()) / len(am) if am else None,
        mean_pm=sum(pm.values()) / len(pm) if pm else None,
        last_date=days[-1] if days else None,
        series=[SmapPoint(date=d, am=am.get(d), pm=pm.get(d)) for d in days],
    )

    imerg = _values(session, field, "gpm", "precip_mm_day")
    power = {
        day: rain
        for day, rain in session.execute(
            select(WeatherObservation.date, WeatherObservation.precipitation_mm).where(
                WeatherObservation.field_id == field.id,
                WeatherObservation.source == POWER_SOURCE,
                WeatherObservation.date.in_(list(imerg) or [date(1900, 1, 1)]),
            )
        )
        if rain is not None
    }
    both = sorted(set(imerg) & set(power))
    gpm = GpmOut(
        days=len(imerg),
        imerg_total_mm=sum(imerg[d] for d in both) if both else None,
        power_total_mm=sum(power[d] for d in both) if both else None,
        correlation=service.pearson([imerg[d] for d in both], [power[d] for d in both]),
        series=[GpmPoint(date=d, imerg_mm=imerg[d], power_mm=power.get(d)) for d in sorted(imerg)],
    )

    grace_values = _values(session, field, "grace", "lwe_thickness_cm")
    months = sorted(grace_values)
    grace = GraceOut(
        months=len(months),
        first_date=months[0] if months else None,
        last_date=months[-1] if months else None,
        latest_cm=grace_values[months[-1]] if months else None,
        trend_cm_per_year=service.trend_per_year([(d, grace_values[d]) for d in months]),
    )

    latest: dict[str, tuple[DataFetchJob, str]] = {}
    for job, key in session.execute(
        select(DataFetchJob, DataSource.key)
        .join(DataSource, DataSource.id == DataFetchJob.data_source_id)
        .where(DataFetchJob.field_id == field.id, DataSource.key.in_(service.SOURCES))
        .order_by(DataFetchJob.created_at.desc())
    ):
        latest.setdefault(key, (job, key))
    return RegionalOut(
        configured=bool(get_settings().earthdata_token),
        smap=smap,
        gpm=gpm,
        grace=grace,
        latest_jobs=[job_out(job, key, field) for job, key in latest.values()],
    )


@router.get("", response_model=RegionalOut)
def read_regional(field_id: uuid.UUID, session: SessionDep, user: StaffUser) -> RegionalOut:
    return build(session, _field(session, user, field_id))


@router.post("/fetch", response_model=list[JobOut], status_code=status.HTTP_202_ACCEPTED)
def fetch_regional(
    field_id: uuid.UUID,
    session: SessionDep,
    user: StaffUser,
    source: Annotated[SourceChoice, Query()] = "all",
) -> list[JobOut]:
    """Queue reads of SMAP, GPM IMERG and GRACE for the field (one job each). They need the NASA
    Earthdata token on the server; without it nothing is queued."""
    field = _field(session, user, field_id)
    if not get_settings().earthdata_token:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, detail={"code": "earthdata_not_configured"}
        )
    wanted = list(service.SOURCES) if source == "all" else [source]
    sources = {
        row.key: row
        for row in session.scalars(select(DataSource).where(DataSource.key.in_(wanted)))
    }
    if set(sources) != set(wanted):
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Reference data is not loaded; run 'python -m app.cli seed-reference'",
        )
    running = session.scalar(
        select(func.count())
        .select_from(DataFetchJob)
        .where(
            DataFetchJob.field_id == field.id,
            DataFetchJob.data_source_id.in_([row.id for row in sources.values()]),
            DataFetchJob.status.in_([JobStatus.QUEUED, JobStatus.RUNNING]),
        )
    )
    if running:
        raise HTTPException(status.HTTP_409_CONFLICT, detail={"code": "fetch_already_running"})

    start, end = service.window_for(session, field.id)
    jobs = []
    for key in wanted:
        job = DataFetchJob(
            field_id=field.id,
            data_source_id=sources[key].id,
            date_from=start if key != "grace" else None,
            date_to=end if key != "grace" else None,
            status=JobStatus.QUEUED,
        )
        session.add(job)
        jobs.append((key, job))
    session.commit()
    for _, job in jobs:
        try:
            fetch_field_regional.delay(str(job.id))
        except Exception as error:  # the broker is down
            for _, queued in jobs:
                if queued.status == JobStatus.QUEUED:
                    queued.status = JobStatus.FAILED
                    queued.error_message = f"The job queue is not reachable: {error}"[:1000]
                    queued.finished_at = datetime.now(UTC)
            session.commit()
            raise HTTPException(
                status.HTTP_503_SERVICE_UNAVAILABLE, detail="The job queue is not reachable"
            ) from error
    out = []
    for key, job in jobs:
        session.refresh(job)
        out.append(job_out(job, key, field))
    return out

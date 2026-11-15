"""Field Memory: satellite NDVI, the cropped or fallow history, and its confirmation (phases 5, 8).

NDVI comes from Landsat 8 and 9 (30 m) and MODIS (250 m), both read from the public Planetary
Computer catalogue. The history is called from Landsat when it covers enough seasons, otherwise
from MODIS; a person can ask for either.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
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
from app.services.modis import default_range
from app.tasks.landsat import fetch_field_ndvi as fetch_landsat
from app.tasks.modis import fetch_field_ndvi as fetch_modis

router = APIRouter(prefix="/fields/{field_id}/field-memory", tags=["field-memory"])

StaffUser = Annotated[
    User, Depends(require_roles(Role.ADMIN, Role.AGRONOMIST, Role.COOPERATIVE_USER))
]

# The data source keys behind each satellite, and what a clear season needs from each.
SOURCES = {"modis": ["modis"], "landsat": ["landsat8", "landsat9"]}
# (fewest clear images that still allow a call, clear images that give full coverage confidence)
COVERAGE = {"modis": (5, 13), "landsat": (4, 8)}
# Landsat is used automatically when at least this many seasons can be called from it.
AUTO_LANDSAT_SEASONS = 6
SourceChoice = Literal["auto", "modis", "landsat"]


def _field(session: SessionDep, user: User, field_id: uuid.UUID) -> Field:
    field = session.scalar(select(Field).where(Field.id == field_id, visible_to(user)))
    if field is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Field not found")
    return field


def _confirmer_role(user: User) -> CycleSource:
    return CycleSource.USER if user.role == Role.COOPERATIVE_USER else CycleSource.AGRONOMIST


def _rows(session: SessionDep, field: Field, source: str) -> list[SatelliteObservation]:
    return list(
        session.scalars(
            select(SatelliteObservation)
            .where(
                SatelliteObservation.field_id == field.id,
                SatelliteObservation.source.in_(SOURCES[source]),
            )
            .order_by(SatelliteObservation.image_date)
        )
    )


def _detect(rows, source, *, threshold, history_years, today):
    observations = [
        memory.Obs(row.image_date, row.ndvi_mean, row.valid_pixel_count or 0) for row in rows
    ]
    minimum, full = COVERAGE[source]
    detected = memory.detect(
        observations,
        threshold=threshold,
        history_years=history_years,
        today=today,
        min_good=minimum,
        full_coverage=full,
    )
    return observations, detected


def _good(observations) -> int:
    return sum(1 for o in observations if o.ndvi is not None and o.valid_pixels >= 1)


def build(session: SessionDep, field: Field, choice: SourceChoice = "auto") -> FieldMemoryOut:
    config = get_config()
    threshold = config.rotation_demo.ndvi_cropped_threshold.value
    history_years = int(config.parameters.get("core", "history_years"))
    today = datetime.now(UTC).date()

    runs = {}
    for source in SOURCES:
        rows = _rows(session, field, source)
        observations, detected = _detect(
            rows, source, threshold=threshold, history_years=history_years, today=today
        )
        runs[source] = (rows, observations, detected)

    if choice == "auto":
        callable_landsat = sum(1 for s in runs["landsat"][2] if s.state != memory.UNKNOWN)
        if callable_landsat >= AUTO_LANDSAT_SEASONS or not runs["modis"][0]:
            chosen = "landsat" if runs["landsat"][0] else "modis"
        else:
            chosen = "modis"
    else:
        chosen = choice
    rows, observations, detected = runs[chosen]

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

    keys = [key for keys in SOURCES.values() for key in keys]
    latest: dict[str, tuple[DataFetchJob, str]] = {}
    for job, key in session.execute(
        select(DataFetchJob, DataSource.key)
        .join(DataSource, DataSource.id == DataFetchJob.data_source_id)
        .where(DataFetchJob.field_id == field.id, DataSource.key.in_(keys))
        .order_by(DataFetchJob.created_at.desc())
    ):
        latest.setdefault(key, (job, key))
    jobs = sorted(latest.values(), key=lambda pair: pair[0].created_at, reverse=True)
    return FieldMemoryOut(
        field_id=field.id,
        history_years=history_years,
        threshold=threshold,
        provisional=True,
        source=chosen,
        available_sources={name: _good(run[1]) for name, run in runs.items()},
        coverage=Coverage(
            observations=len(rows),
            good=_good(observations),
            first_date=rows[0].image_date if rows else None,
            last_date=rows[-1].image_date if rows else None,
        ),
        seasons=seasons,
        series=series,
        latest_job=job_out(jobs[0][0], jobs[0][1], field) if jobs else None,
        latest_jobs=[job_out(job, key, field) for job, key in jobs],
        confirmed_count=sum(1 for s in seasons if s.confirmed_state),
    )


@router.get("", response_model=FieldMemoryOut)
def read_field_memory(
    field_id: uuid.UUID,
    session: SessionDep,
    user: StaffUser,
    source: Annotated[SourceChoice, Query()] = "auto",
) -> FieldMemoryOut:
    return build(session, _field(session, user, field_id), source)


@router.post("/fetch", response_model=list[JobOut], status_code=status.HTTP_202_ACCEPTED)
def fetch_ndvi(
    field_id: uuid.UUID,
    session: SessionDep,
    user: StaffUser,
    source: Annotated[Literal["modis", "landsat", "all"], Query()] = "all",
) -> list[JobOut]:
    """Queue NDVI fetches for the last seasons (one job per satellite source). The worker does
    the work, one job at a time."""
    field = _field(session, user, field_id)
    config = get_config()
    wanted = [key for name, keys in SOURCES.items() if source in (name, "all") for key in keys]
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

    start, end = default_range(
        datetime.now(UTC).date(), int(config.parameters.get("core", "history_years"))
    )
    jobs = []
    for key in wanted:
        job = DataFetchJob(
            field_id=field.id,
            data_source_id=sources[key].id,
            date_from=start,
            date_to=end,
            status=JobStatus.QUEUED,
        )
        session.add(job)
        jobs.append((key, job))
    session.commit()
    for key, job in jobs:
        task = fetch_modis if key == "modis" else fetch_landsat
        try:
            task.delay(str(job.id))
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
        session.refresh(job)  # an inline run (tests) has already updated it
        out.append(job_out(job, key, field))
    return out


@router.post("/confirm", response_model=FieldMemoryOut)
def confirm(
    field_id: uuid.UUID,
    body: ConfirmIn,
    session: SessionDep,
    user: StaffUser,
    source: Annotated[SourceChoice, Query()] = "auto",
) -> FieldMemoryOut:
    """Record what a person confirms for each season. This history is strategy A (PDT 4.1)."""
    field = _field(session, user, field_id)
    detected = {s.season: s for s in build(session, field, source).seasons}
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
    return build(session, field, source)

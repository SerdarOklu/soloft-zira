"""Fields and their NASA POWER weather (PDT section 10.1, phase 3)."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from geoalchemy2 import Geography
from sqlalchemy import Row, cast, extract, func, select, update
from sqlalchemy.exc import IntegrityError

from app.api.deps import ReaderUser, SessionDep, require_roles
from app.core.parameters import get_config
from app.models import (
    DataFetchJob,
    DataSource,
    Field,
    JobStatus,
    Role,
    SoilProfile,
    User,
    WeatherObservation,
)
from app.models.fields import SRID
from app.schemas.fields import (
    DailyRow,
    FetchRequest,
    FieldCreate,
    FieldOut,
    JobOut,
    Point,
    WeatherSummary,
    YearStat,
)
from app.services.fields import visible_to, weather_days
from app.services.power import SOURCE as POWER_SOURCE
from app.services.power import UNITS, default_range
from app.tasks.power import fetch_field_weather

router = APIRouter(prefix="/fields", tags=["fields"])

StaffUser = Annotated[
    User, Depends(require_roles(Role.ADMIN, Role.AGRONOMIST, Role.COOPERATIVE_USER))
]
AdminUser = Annotated[User, Depends(require_roles(Role.ADMIN))]

RECENT_DAYS = 14
SQUARE_METRES_PER_HECTARE = 10_000.0


def _select_fields():
    texture = (
        select(SoilProfile.texture)
        .where(SoilProfile.field_id == Field.id)
        .order_by(SoilProfile.created_at.desc())
        .limit(1)
        .correlate(Field)
        .scalar_subquery()
    )
    return select(
        Field,
        func.ST_AsGeoJSON(Field.geom).label("geojson"),
        func.ST_Y(Field.centroid).label("lat"),
        func.ST_X(Field.centroid).label("lon"),
        texture.label("texture"),
        weather_days().label("weather_days"),
    )


def _to_out(row: Row) -> FieldOut:
    field = row.Field
    return FieldOut(
        id=field.id,
        code=field.code,
        name=field.name,
        region=field.region,
        water_regime=field.water_regime,
        soil_texture=row.texture,
        area_ha=field.area_ha,
        elevation_m=field.elevation_m,
        centroid=Point(lat=row.lat, lon=row.lon) if row.lat is not None else None,
        geometry=json.loads(row.geojson) if row.geojson else None,
        weather_days=row.weather_days,
        farmer_user_id=field.farmer_user_id,
        created_at=field.created_at,
    )


def _load(session: SessionDep, user: User, field_id: uuid.UUID) -> FieldOut:
    row = session.execute(_select_fields().where(Field.id == field_id, visible_to(user))).first()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Field not found")
    return _to_out(row)


def job_out(job: DataFetchJob, source: str, field: Field | None = None) -> JobOut:
    return JobOut(
        id=job.id,
        field_id=job.field_id,
        field_code=field.code if field else None,
        field_name=field.name if field else None,
        source=source,
        status=job.status.value,
        date_from=job.date_from,
        date_to=job.date_to,
        rows_written=job.rows_written,
        error_message=job.error_message,
        created_at=job.created_at,
        started_at=job.started_at,
        finished_at=job.finished_at,
    )


@router.get("", response_model=list[FieldOut])
def list_fields(session: SessionDep, user: ReaderUser) -> list[FieldOut]:
    rows = session.execute(
        _select_fields().where(visible_to(user)).order_by(Field.created_at.desc())
    ).all()
    return [_to_out(row) for row in rows]


@router.post("", response_model=FieldOut, status_code=status.HTTP_201_CREATED)
def create_field(body: FieldCreate, session: SessionDep, user: StaffUser) -> FieldOut:
    config = get_config()
    soil = config.soils.get(body.soil_texture)
    if soil is None:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Unknown soil texture '{body.soil_texture}'",
        )

    geometry = func.ST_SetSRID(
        func.ST_GeomFromGeoJSON(json.dumps(body.geometry.model_dump())), SRID
    )
    if not session.scalar(select(func.ST_IsValid(geometry))):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="The polygon is not valid; its edges must not cross",
        )

    field = Field(
        code=body.code or f"ZR-{uuid.uuid4().hex[:8].upper()}",
        name=body.name,
        region=body.region,
        water_regime=body.water_regime,
        geom=geometry,
        organization_id=user.organization_id,
        created_by=user.id,
    )
    session.add(field)
    try:
        session.flush()
    except IntegrityError as error:
        session.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT, detail="A field with this code already exists"
        ) from error

    # The centroid and the area are derived from the polygon, never typed in.
    session.execute(
        update(Field)
        .where(Field.id == field.id)
        .values(
            centroid=func.ST_Centroid(Field.geom),
            area_ha=func.ST_Area(cast(Field.geom, Geography)) / SQUARE_METRES_PER_HECTARE,
        )
        .execution_options(synchronize_session=False)
    )
    session.add(
        SoilProfile(
            field_id=field.id,
            texture=body.soil_texture,
            # Default from FAO-56 Table 19 (config/soils.yaml) until a sensor calibrates it.
            taw_mm_per_m=soil.taw_mid,
            source="config_default",
            is_calibrated=False,
        )
    )
    session.commit()
    return _load(session, user, field.id)


@router.get("/{field_id}", response_model=FieldOut)
def get_field(field_id: uuid.UUID, session: SessionDep, user: ReaderUser) -> FieldOut:
    return _load(session, user, field_id)


@router.delete("/{field_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_field(field_id: uuid.UUID, session: SessionDep, user: AdminUser) -> None:
    field = session.get(Field, field_id)
    if field is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Field not found")
    session.delete(field)
    session.commit()


@router.post(
    "/{field_id}/weather/fetch", response_model=JobOut, status_code=status.HTTP_202_ACCEPTED
)
def fetch_weather(
    field_id: uuid.UUID,
    session: SessionDep,
    user: StaffUser,
    body: FetchRequest | None = None,
) -> JobOut:
    """Queue a NASA POWER fetch for the field. The worker does the work, not this request."""
    body = body or FetchRequest()
    _load(session, user, field_id)  # 404 for a field this user may not see

    default_from, default_to = default_range(get_config())
    date_from = body.date_from or default_from
    date_to = body.date_to or default_to
    if date_from > date_to:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, detail="date_from is after date_to"
        )
    if date_to > datetime.now(UTC).date():
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, detail="date_to is in the future"
        )

    source = session.scalar(select(DataSource).where(DataSource.key == POWER_SOURCE))
    if source is None:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Reference data is not loaded; run 'python -m app.cli seed-reference'",
        )

    job = DataFetchJob(
        field_id=field_id,
        data_source_id=source.id,
        date_from=date_from,
        date_to=date_to,
        status=JobStatus.QUEUED,
    )
    session.add(job)
    session.commit()
    try:
        fetch_field_weather.delay(str(job.id), body.force)
    except Exception as error:  # the broker is down
        job.status = JobStatus.FAILED
        job.error_message = f"The job queue is not reachable: {error}"[:1000]
        job.finished_at = datetime.now(UTC)
        session.commit()
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, detail="The job queue is not reachable"
        ) from error
    session.refresh(job)  # an inline run (tests) has already updated it
    return job_out(job, POWER_SOURCE)


@router.get("/{field_id}/weather/summary", response_model=WeatherSummary)
def weather_summary(field_id: uuid.UUID, session: SessionDep, user: StaffUser) -> WeatherSummary:
    _load(session, user, field_id)
    scope = (WeatherObservation.field_id == field_id, WeatherObservation.source == POWER_SOURCE)

    days, first_date, last_date, last_fetched = session.execute(
        select(
            func.count(),
            func.min(WeatherObservation.date),
            func.max(WeatherObservation.date),
            func.max(WeatherObservation.fetched_at),
        ).where(*scope)
    ).one()

    year = extract("year", WeatherObservation.date)
    years = [
        YearStat(
            year=int(row[0]),
            days=row[1],
            precipitation_mm=row[2],
            temperature_avg=row[3],
            temperature_min=row[4],
            temperature_max=row[5],
        )
        for row in session.execute(
            select(
                year,
                func.count(),
                func.sum(WeatherObservation.precipitation_mm),
                func.avg(WeatherObservation.temperature_avg),
                func.min(WeatherObservation.temperature_min),
                func.max(WeatherObservation.temperature_max),
            )
            .where(*scope)
            .group_by(year)
            .order_by(year)
        )
    ]
    recent = session.scalars(
        select(WeatherObservation)
        .where(*scope)
        .order_by(WeatherObservation.date.desc())
        .limit(RECENT_DAYS)
    ).all()
    wind_height = session.scalar(select(WeatherObservation.wind_height_m).where(*scope).limit(1))
    latest = session.scalar(
        select(DataFetchJob)
        .where(DataFetchJob.field_id == field_id)
        .order_by(DataFetchJob.created_at.desc())
        .limit(1)
    )
    return WeatherSummary(
        days=days,
        first_date=first_date,
        last_date=last_date,
        last_fetched_at=last_fetched,
        units=UNITS,
        wind_height_m=wind_height,
        years=years,
        recent=[DailyRow.model_validate(row) for row in recent],
        latest_job=job_out(latest, POWER_SOURCE) if latest else None,
    )

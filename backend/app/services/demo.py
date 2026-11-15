"""Demo accounts and a demo field for a jury, so the screens are not empty.

``seed_demo`` is safe to run again: it only adds what is missing. The demo accounts are the ones
the role picker signs in to (``demo-<role>@demo.zira``). They have no usable password: a random one
is set and thrown away, so the only way in is the role picker, and only while DEMO_ROLE_LOGIN is on.

It never fabricates data. Weather, satellite NDVI and message drafts come from the real jobs and
the real model; where one needs the network or a person it is left to that step and reported.
"""

from __future__ import annotations

import json
import secrets
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta

from geoalchemy2 import Geography
from sqlalchemy import cast, func, select, update
from sqlalchemy.orm import Session

from app.api.auth import DEMO_ROLES, demo_email
from app.core.parameters import Config
from app.core.security import hash_password
from app.models import (
    DataFetchJob,
    DataSource,
    Field,
    JobStatus,
    Organization,
    OrganizationType,
    Role,
    SensorCalibration,
    SoilProfile,
    User,
    WaterRegime,
)
from app.models.fields import SRID
from app.services import power
from app.services.messaging import drafts
from app.services.water.rotation_service import parse_rotation

DEMO_ORG = "Zira Demo Kooperatifi"
DEMO_FIELD_CODE = "ZR-DEMO-KULU"
DEMO_NAMES = {
    Role.ADMIN: "Demo Yönetici",
    Role.AGRONOMIST: "Demo Ziraat Mühendisi",
    Role.COOPERATIVE_USER: "Demo Kooperatif Kullanıcısı",
    Role.FARMER: "Demo Çiftçi",
}
# A small rainfed parcel near Kulu, Konya (about 7 ha). Check its MODIS/Landsat NDVI after the
# fetch: the point of the demo field is a clear cropped-fallow signal.
DEMO_RING = [
    [33.048, 39.098],
    [33.052, 39.098],
    [33.052, 39.1018],
    [33.048, 39.1018],
    [33.048, 39.098],
]
DEMO_SOIL = "loam"
# The sensor calibration of the demo field is a placeholder, not a lab result.
DEMO_THETA_WP, DEMO_THETA_FC = 0.15, 0.31
SQUARE_METRES_PER_HECTARE = 10_000


@dataclass
class SeedReport:
    created_users: list[str] = field(default_factory=list)
    field_created: bool = False
    calibration_set: bool = False
    weather_rows: int | None = None
    drafts_created: int = 0
    notes: list[str] = field(default_factory=list)


def _organization(session: Session) -> Organization:
    org = session.scalar(select(Organization).where(Organization.name == DEMO_ORG))
    if org is None:
        org = Organization(name=DEMO_ORG, type=OrganizationType.COOPERATIVE)
        session.add(org)
        session.flush()
    return org


def _users(session: Session, org: Organization, report: SeedReport) -> dict[Role, User]:
    found: dict[Role, User] = {}
    for role in DEMO_ROLES:
        email = demo_email(role)
        user = session.scalar(select(User).where(func.lower(User.email) == email))
        if user is None:
            user = User(
                email=email,
                name=DEMO_NAMES[role],
                role=role,
                # Nobody knows this password; the role picker is the only way in.
                password_hash=hash_password(secrets.token_urlsafe(32)),
                organization_id=None if role is Role.ADMIN else org.id,
            )
            session.add(user)
            session.flush()
            report.created_users.append(email)
        found[role] = user
    return found


def _demo_field(
    session: Session,
    config: Config,
    org: Organization,
    users: dict[Role, User],
    report: SeedReport,
) -> Field:
    row = session.scalar(select(Field).where(Field.code == DEMO_FIELD_CODE))
    if row is not None:
        return row
    soil = config.soils[DEMO_SOIL]
    geometry = func.ST_SetSRID(
        func.ST_GeomFromGeoJSON(json.dumps({"type": "Polygon", "coordinates": [DEMO_RING]})), SRID
    )
    row = Field(
        code=DEMO_FIELD_CODE,
        name="Demo tarlası (Kulu, Konya)",
        region="Konya",
        water_regime=WaterRegime.RAINFED,
        geom=geometry,
        organization_id=org.id,
        created_by=users[Role.AGRONOMIST].id,
        farmer_user_id=users[Role.FARMER].id,
    )
    session.add(row)
    session.flush()
    session.execute(
        update(Field)
        .where(Field.id == row.id)
        .values(
            centroid=func.ST_Centroid(Field.geom),
            area_ha=func.ST_Area(cast(Field.geom, Geography)) / SQUARE_METRES_PER_HECTARE,
        )
        .execution_options(synchronize_session=False)
    )
    session.add(
        SoilProfile(
            field_id=row.id,
            texture=DEMO_SOIL,
            taw_mm_per_m=soil.taw_mid,
            source="config_default",
            is_calibrated=False,
        )
    )
    session.flush()
    report.field_created = True
    return row


def _calibration(
    session: Session, demo_field: Field, users: dict[Role, User], report: SeedReport
) -> None:
    if session.scalar(select(SensorCalibration).where(SensorCalibration.field_id == demo_field.id)):
        return
    session.add(
        SensorCalibration(
            field_id=demo_field.id,
            slope=1.0,
            intercept=0.0,
            theta_wp=DEMO_THETA_WP,
            theta_fc=DEMO_THETA_FC,
            note="Demo placeholder for the simulator, not a gravimetric calibration.",
            calibrated_by=users[Role.AGRONOMIST].id,
            calibrated_at=datetime.now(UTC),
        )
    )
    report.calibration_set = True


def _fetch_weather(session: Session, config: Config, demo_field: Field) -> int:
    """Run the NASA POWER fetch now (needs the network). Returns the rows written."""
    source = session.scalar(select(DataSource).where(DataSource.key == power.SOURCE))
    if source is None:
        raise ValueError("Reference data is not loaded; run seed-reference first")
    start, end = power.default_range(config)
    job = DataFetchJob(
        field_id=demo_field.id,
        data_source_id=source.id,
        date_from=start,
        date_to=min(end, date.today() - timedelta(days=1)),
        status=JobStatus.QUEUED,
    )
    session.add(job)
    session.commit()
    done = power.run_fetch_job(session, job.id, config)
    if done.status is not JobStatus.DONE:
        raise ValueError(f"NASA POWER fetch failed: {done.error_message}")
    return done.rows_written or 0


def seed_demo(
    session: Session,
    config: Config,
    *,
    fetch_weather: bool = False,
    draft_season: int | None = None,
    rotation: str = "winter_wheat,fallow",
) -> SeedReport:
    report = SeedReport()
    org = _organization(session)
    users = _users(session, org, report)
    demo_field = _demo_field(session, config, org, users, report)
    _calibration(session, demo_field, users, report)
    field_code = demo_field.code
    session.commit()

    if fetch_weather:
        report.weather_rows = _fetch_weather(session, config, demo_field)

    if draft_season is not None:
        created, skipped = drafts.generate_drafts(
            session,
            demo_field,
            rotation=parse_rotation(rotation),
            season_year=draft_season,
            locale="tr",
            recipient_phone=None,  # a person types a number on purpose; nothing is sent by itself
            config=config,
        )
        session.commit()
        report.drafts_created = len(created)
        if skipped:
            report.notes.append(f"{skipped} drafts already existed")

    report.notes.append(
        "Still to do by hand, on purpose: set DEMO_ROLE_LOGIN=true; open Field Memory and press "
        "Fetch for the satellite NDVI, then confirm the seasons; run the sensor simulator "
        f"(simulator/README.md) for field {field_code}; type a phone number on a draft "
        "before approving it."
    )
    return report

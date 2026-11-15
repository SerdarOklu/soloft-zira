"""NASA sources, fetch jobs and the observations they produce (PDT sections 6 and 9)."""

from __future__ import annotations

import enum
import uuid
from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Identity,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.accounts import _values
from app.models.base import Base, CreatedAt, UuidPk


class JobStatus(enum.StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


class DataSource(UuidPk, Base):
    """Reference data, seeded from config/data_sources.yaml."""

    __tablename__ = "data_sources"

    key: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    collection_id: Mapped[str | None] = mapped_column(String(200))
    product_version: Mapped[str | None] = mapped_column(String(64))
    resolution: Mapped[str | None] = mapped_column(String(200))
    coverage_from: Mapped[date | None] = mapped_column(Date)
    coverage_to: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str | None] = mapped_column(String(32))
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class DataFetchJob(UuidPk, CreatedAt, Base):
    __tablename__ = "data_fetch_jobs"

    field_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("fields.id", ondelete="CASCADE"), index=True
    )
    data_source_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("data_sources.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    date_from: Mapped[date | None] = mapped_column(Date)
    date_to: Mapped[date | None] = mapped_column(Date)
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, native_enum=False, length=16, values_callable=_values),
        nullable=False,
        default=JobStatus.QUEUED,
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(Text)
    raw_response_path: Mapped[str | None] = mapped_column(String(500))
    rows_written: Mapped[int | None] = mapped_column(Integer)


class WeatherObservation(Base):
    """Daily climate record. Unique per field, day and source, which makes the cache safe."""

    __tablename__ = "weather_observations"

    field_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("fields.id", ondelete="CASCADE"), primary_key=True
    )
    date: Mapped[date] = mapped_column(Date, primary_key=True)
    source: Mapped[str] = mapped_column(String(32), primary_key=True)
    precipitation_mm: Mapped[float | None] = mapped_column(Float)
    temperature_avg: Mapped[float | None] = mapped_column(Float)
    temperature_max: Mapped[float | None] = mapped_column(Float)
    temperature_min: Mapped[float | None] = mapped_column(Float)
    humidity: Mapped[float | None] = mapped_column(Float)
    wind_speed: Mapped[float | None] = mapped_column(Float)
    # ET0 needs wind at 2 m; the height the value was measured at travels with it.
    wind_height_m: Mapped[float | None] = mapped_column(Float)
    solar_radiation: Mapped[float | None] = mapped_column(Float)
    surface_pressure: Mapped[float | None] = mapped_column(Float)
    quality_flag: Mapped[str | None] = mapped_column(String(32))
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class SatelliteObservation(UuidPk, Base):
    __tablename__ = "satellite_observations"
    __table_args__ = (UniqueConstraint("field_id", "source", "scene_id"),)

    field_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("fields.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    image_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    scene_id: Mapped[str | None] = mapped_column(String(200))
    ndvi_mean: Mapped[float | None] = mapped_column(Float)
    ndvi_median: Mapped[float | None] = mapped_column(Float)
    valid_pixel_count: Mapped[int | None] = mapped_column(Integer)
    cloud_fraction: Mapped[float | None] = mapped_column(Float)
    quality_flag: Mapped[str | None] = mapped_column(String(32))
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class SensorObservation(Base):
    """Field sensor or simulator reading. Added by the PDT to the report's table list."""

    __tablename__ = "sensor_observations"
    __table_args__ = (UniqueConstraint("node_id", "measured_at", "depth_cm"),)

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    field_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("fields.id", ondelete="CASCADE"), nullable=False, index=True
    )
    node_id: Mapped[str] = mapped_column(String(64), nullable=False)
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    depth_cm: Mapped[int] = mapped_column(Integer, nullable=False)
    vwc_raw: Mapped[float] = mapped_column(Float, nullable=False)
    vwc_calibrated: Mapped[float | None] = mapped_column(Float)
    battery: Mapped[float | None] = mapped_column(Float)
    is_simulated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class SensorCalibration(UuidPk, Base):
    """The calibration of a field's soil moisture sensors (PDT 12.3, step 2).

    ``vwc_calibrated = slope * vwc_raw + intercept``, found by weighing soil samples for the
    soil type (gravimetric). ``theta_wp`` and ``theta_fc`` are the volumetric water content at
    the wilting point and at field capacity, which turn a reading into usable water. A sensor
    is not trusted until this record exists.
    """

    __tablename__ = "sensor_calibrations"

    field_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("fields.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    slope: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    intercept: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    theta_wp: Mapped[float] = mapped_column(Float, nullable=False)
    theta_fc: Mapped[float] = mapped_column(Float, nullable=False)
    note: Mapped[str | None] = mapped_column(String(500))
    calibrated_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    calibrated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class RegionalObservation(Base):
    """A value read for a field from a source that is not a daily weather record or an NDVI image:
    terrain from SRTM today, regional soil moisture or water storage later. Unique per field,
    source, variable and day, so fetching again is safe."""

    __tablename__ = "regional_observations"
    __table_args__ = (UniqueConstraint("field_id", "source", "variable", "observed_on"),)

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    field_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("fields.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    variable: Mapped[str] = mapped_column(String(32), nullable=False)
    observed_on: Mapped[date] = mapped_column(Date, nullable=False)
    value: Mapped[float | None] = mapped_column(Float)
    unit: Mapped[str | None] = mapped_column(String(16))
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

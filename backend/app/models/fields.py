"""The Field Profile: geometry, soil, crop history and farmer constraints (PDT section 5)."""

from __future__ import annotations

import enum
import uuid
from datetime import date, datetime

from geoalchemy2 import Geometry, WKBElement
from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.accounts import _values
from app.models.base import Base, CreatedAt, UuidPk

SRID = 4326


class WaterRegime(enum.StrEnum):
    RAINFED = "rainfed"
    IRRIGATED = "irrigated"


class CycleState(enum.StrEnum):
    CROPPED = "cropped"
    FALLOW = "fallow"
    UNKNOWN = "unknown"


class CycleSource(enum.StrEnum):
    LANDSAT = "landsat"
    MODIS = "modis"
    USER = "user"
    AGRONOMIST = "agronomist"


class SeasonType(enum.StrEnum):
    WINTER = "winter"
    SUMMER = "summer"
    PERENNIAL = "perennial"


class Field(UuidPk, CreatedAt, Base):
    __tablename__ = "fields"

    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("organizations.id", ondelete="SET NULL"), index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    # No coordinate lives in code: every analysis reads the geometry from here.
    geom: Mapped[WKBElement | None] = mapped_column(Geometry("POLYGON", srid=SRID))
    centroid: Mapped[WKBElement | None] = mapped_column(Geometry("POINT", srid=SRID))
    area_ha: Mapped[float | None] = mapped_column(Float)
    elevation_m: Mapped[float | None] = mapped_column(Float)
    region: Mapped[str | None] = mapped_column(String(200))
    water_regime: Mapped[WaterRegime | None] = mapped_column(
        Enum(WaterRegime, native_enum=False, length=16, values_callable=_values)
    )
    climate_class: Mapped[str | None] = mapped_column(String(64))
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )


class SoilProfile(UuidPk, CreatedAt, Base):
    __tablename__ = "soil_profiles"

    field_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("fields.id", ondelete="CASCADE"), nullable=False, index=True
    )
    texture: Mapped[str | None] = mapped_column(String(32))
    clay_pct: Mapped[float | None] = mapped_column(Float)
    sand_pct: Mapped[float | None] = mapped_column(Float)
    silt_pct: Mapped[float | None] = mapped_column(Float)
    organic_matter_pct: Mapped[float | None] = mapped_column(Float)
    theta_fc: Mapped[float | None] = mapped_column(Float)
    theta_wp: Mapped[float | None] = mapped_column(Float)
    taw_mm_per_m: Mapped[float | None] = mapped_column(Float)
    effective_depth_m: Mapped[float | None] = mapped_column(Float)
    infiltration: Mapped[str | None] = mapped_column(String(64))
    drainage: Mapped[str | None] = mapped_column(String(64))
    source: Mapped[str | None] = mapped_column(String(32))
    is_calibrated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class CropType(UuidPk, Base):
    """Reference data, seeded from config/crops.yaml."""

    __tablename__ = "crop_types"

    key: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    season_type: Mapped[SeasonType | None] = mapped_column(
        Enum(SeasonType, native_enum=False, length=16, values_callable=_values)
    )
    is_legume: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    kc_ini: Mapped[float] = mapped_column(Float, nullable=False)
    # Winter wheat only: kc_ini where the soil does not freeze.
    kc_ini_non_frozen: Mapped[float | None] = mapped_column(Float)
    kc_mid_min: Mapped[float] = mapped_column(Float, nullable=False)
    kc_mid_max: Mapped[float] = mapped_column(Float, nullable=False)
    kc_end_min: Mapped[float] = mapped_column(Float, nullable=False)
    kc_end_max: Mapped[float] = mapped_column(Float, nullable=False)
    height_m: Mapped[float] = mapped_column(Float, nullable=False)
    zr_min_m: Mapped[float] = mapped_column(Float, nullable=False)
    zr_max_m: Mapped[float] = mapped_column(Float, nullable=False)
    p: Mapped[float] = mapped_column(Float, nullable=False)
    l_ini: Mapped[int | None] = mapped_column(Integer)
    l_dev: Mapped[int | None] = mapped_column(Integer)
    l_mid: Mapped[int | None] = mapped_column(Integer)
    l_late: Mapped[int | None] = mapped_column(Integer)


class CropCycle(UuidPk, CreatedAt, Base):
    __tablename__ = "crop_cycles"
    __table_args__ = (UniqueConstraint("field_id", "season"),)

    field_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("fields.id", ondelete="CASCADE"), nullable=False, index=True
    )
    season: Mapped[str] = mapped_column(String(16), nullable=False)  # e.g. "2024-2025"
    crop_type_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("crop_types.id", ondelete="SET NULL")
    )
    state: Mapped[CycleState] = mapped_column(
        Enum(CycleState, native_enum=False, length=16, values_callable=_values),
        nullable=False,
        default=CycleState.UNKNOWN,
    )
    sowing_date: Mapped[date | None] = mapped_column(Date)
    harvest_date: Mapped[date | None] = mapped_column(Date)
    source: Mapped[CycleSource] = mapped_column(
        Enum(CycleSource, native_enum=False, length=16, values_callable=_values),
        nullable=False,
    )
    confidence: Mapped[float | None] = mapped_column(Float)
    confirmed_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class FarmerConstraint(UuidPk, Base):
    __tablename__ = "farmer_constraints"

    field_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("fields.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    water_constraint: Mapped[str | None] = mapped_column(Text)
    equipment_constraint: Mapped[str | None] = mapped_column(Text)
    market_constraint: Mapped[str | None] = mapped_column(Text)
    priorities: Mapped[list[str] | None] = mapped_column()
    irrigation_method: Mapped[str | None] = mapped_column(String(64))
    irrigation_quota_mm: Mapped[float | None] = mapped_column(Float)
    irrigation_efficiency: Mapped[float | None] = mapped_column(Float)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

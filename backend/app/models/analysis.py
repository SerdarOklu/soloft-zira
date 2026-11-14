"""Analysis runs and their results: water balance, rotation scenarios, cards (PDT section 9)."""

from __future__ import annotations

import enum
import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
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
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.accounts import _values
from app.models.base import Base, CreatedAt, UuidPk
from app.models.data import JobStatus


class Strategy(enum.StrEnum):
    A = "A"  # current rotation
    B = "B"  # water-dependent flexible rotation
    C = "C"  # legume rotation


class Variant(enum.StrEnum):
    LOW = "low"
    MID = "mid"
    HIGH = "high"


class AnalysisRun(UuidPk, CreatedAt, Base):
    """One row per analysis. Stores what it ran with, so a card can be reproduced."""

    __tablename__ = "analysis_runs"

    field_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("fields.id", ondelete="CASCADE"), nullable=False, index=True
    )
    run_type: Mapped[str] = mapped_column(String(32), nullable=False)
    model_version: Mapped[str] = mapped_column(String(32), nullable=False)
    parameters: Mapped[dict[str, Any]] = mapped_column(nullable=False)
    data_versions: Mapped[dict[str, Any]] = mapped_column(nullable=False)
    date_from: Mapped[date | None] = mapped_column(Date)
    date_to: Mapped[date | None] = mapped_column(Date)
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, native_enum=False, length=16, values_callable=_values),
        nullable=False,
        default=JobStatus.QUEUED,
    )
    error_message: Mapped[str | None] = mapped_column(Text)


class RotationScenario(UuidPk, Base):
    __tablename__ = "rotation_scenarios"
    __table_args__ = (UniqueConstraint("analysis_run_id", "strategy"),)

    analysis_run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    field_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("fields.id", ondelete="CASCADE"), nullable=False, index=True
    )
    strategy: Mapped[Strategy] = mapped_column(
        Enum(Strategy, native_enum=False, length=4, values_callable=_values), nullable=False
    )
    definition: Mapped[dict[str, Any]] = mapped_column(nullable=False)
    sufficient_seasons: Mapped[int | None] = mapped_column(Integer)
    valid_seasons: Mapped[int | None] = mapped_column(Integer)
    stress_days_critical: Mapped[float | None] = mapped_column(Float)
    deficit_mm: Mapped[float | None] = mapped_column(Float)
    irrigation_need_mm: Mapped[float | None] = mapped_column(Float)
    range_low: Mapped[int | None] = mapped_column(Integer)
    range_high: Mapped[int | None] = mapped_column(Integer)
    # The five fields every strategy block of the card must carry.
    rationale: Mapped[str | None] = mapped_column(Text)
    evidence: Mapped[str | None] = mapped_column(Text)
    benefit: Mapped[str | None] = mapped_column(Text)
    info_gap: Mapped[str | None] = mapped_column(Text)
    local_review_risk: Mapped[str | None] = mapped_column(Text)


class SoilWaterBalance(Base):
    """Daily water balance, one row per run, scenario, uncertainty variant and day."""

    __tablename__ = "soil_water_balances"
    __table_args__ = (
        UniqueConstraint(
            "analysis_run_id", "scenario_id", "variant", "date", postgresql_nulls_not_distinct=True
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    analysis_run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    scenario_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("rotation_scenarios.id", ondelete="CASCADE"), index=True
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    variant: Mapped[Variant] = mapped_column(
        Enum(Variant, native_enum=False, length=8, values_callable=_values),
        nullable=False,
        default=Variant.MID,
    )
    p_mm: Mapped[float | None] = mapped_column(Float)
    p_eff_mm: Mapped[float | None] = mapped_column(Float)
    irrigation_mm: Mapped[float | None] = mapped_column(Float)
    et0_mm: Mapped[float | None] = mapped_column(Float)
    kc: Mapped[float | None] = mapped_column(Float)
    etc_mm: Mapped[float | None] = mapped_column(Float)
    ks: Mapped[float | None] = mapped_column(Float)
    eta_mm: Mapped[float | None] = mapped_column(Float)
    runoff_mm: Mapped[float | None] = mapped_column(Float)
    deep_perc_mm: Mapped[float | None] = mapped_column(Float)
    storage_mm: Mapped[float | None] = mapped_column(Float)
    taw_mm: Mapped[float | None] = mapped_column(Float)


class ZiraCard(UuidPk, CreatedAt, Base):
    """A card is a draft until an agronomist approves it; only approved cards are shared."""

    __tablename__ = "zira_cards"

    analysis_run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    field_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("fields.id", ondelete="CASCADE"), nullable=False, index=True
    )
    payload: Mapped[dict[str, Any]] = mapped_column(nullable=False)
    export_path: Mapped[str | None] = mapped_column(String(500))
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    shared_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

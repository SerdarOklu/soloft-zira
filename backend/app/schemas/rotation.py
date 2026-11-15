"""The rotation comparison answer (PDT section 4.4)."""

from __future__ import annotations

import uuid
from datetime import date

from pydantic import BaseModel


class SeasonOut(BaseModel):
    year: int  # year of sowing
    planned: str | None
    crop: str | None  # what was sown; null when fallow or held back
    valid: bool
    sufficient: bool
    ratio: float | None
    deficit_mm: float
    stress_days: int
    storage_at_decision_mm: float | None


class MetricsOut(BaseModel):
    sown: int
    valid: int
    sufficient: int
    fallow: int
    share: float | None
    share_low: float | None
    share_high: float | None
    sufficient_low: int
    sufficient_high: int
    stress_days_mean: float | None
    deficit_mean_mm: float | None
    irrigation_need_mean_mm: float | None


class DifferenceOut(BaseModel):
    """Strategy minus the current rotation (A) on the same field."""

    share_points: float | None
    stress_days_mean: float | None
    deficit_mean_mm: float | None
    irrigation_need_mean_mm: float | None
    sufficient: int


class StrategyOut(BaseModel):
    key: str  # "A", "B" or "C"
    crops: list[str]  # crops this strategy sows (for the legend)
    metrics: MetricsOut
    difference: DifferenceOut | None
    seasons: list[SeasonOut]


class ReferenceOut(BaseModel):
    crop: str
    root_depth_m: float
    taw_mm: float
    taw_low_mm: float
    taw_high_mm: float


class RotationOut(BaseModel):
    field_id: uuid.UUID
    model_version: str
    # The stage lengths, sowing dates and irrigation efficiency are provisional demo values.
    provisional: bool
    provisional_sources: list[str]
    rotation: list[str | None]
    first_day: date
    last_day: date
    seasons: int
    reference: ReferenceOut
    flex_threshold_mm: float
    sufficiency_ratio: float
    irrigation_efficiency: float
    needs_signoff: list[str]
    assumptions: list[str]
    strategies: list[StrategyOut]

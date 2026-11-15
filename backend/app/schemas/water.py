"""The Water Vault answer (PDT section 4.3)."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel


class CropInfo(BaseModel):
    key: str
    name_tr: str
    season_type: str | None
    root_depth_m: float
    # The crop season (ETc, actual ET, stress) needs the stage lengths, which the agronomist
    # sets (config/crops.yaml). Until then only the decision-day water is computed.
    season_ready: bool
    season_blocker: str | None


class Decision(BaseModel):
    storage_mm: float
    low_mm: float
    high_mm: float
    taw_mm: float
    taw_low_mm: float
    taw_high_mm: float
    fill_fraction: float


class Window(BaseModel):
    start: date
    end: date
    days: int
    missing_days: int


class Parameters(BaseModel):
    fallow_efficiency: float
    initial_storage_frac: float
    spinup_days: int
    uncertainty_delta: float


class DayRow(BaseModel):
    date: date
    precipitation_mm: float | None
    et0_mm: float | None
    storage_mm: float


class SensorInfo(BaseModel):
    """What a calibrated field sensor says, next to what the model says (PDT 4.3)."""

    model_mm: float
    sensor_mm: float
    difference_mm: float  # sensor minus model
    measured_at: datetime
    nodes: int
    depths_cm: list[int]
    available_fraction: float
    band_mm: float


class WaterVaultOut(BaseModel):
    field_id: uuid.UUID
    crop: CropInfo
    date: date
    date_is_default: bool
    decision: Decision
    window: Window
    parameters: Parameters
    # Parameters used here that still wait for an agronomist's sign-off.
    needs_signoff: list[str]
    # Codes the screen turns into sentences: what this number rests on.
    assumptions: list[str]
    # sensor: a calibrated sensor corrected the day; satellite: the model state stands.
    mode: Literal["sensor", "satellite"] = "satellite"
    sensor: SensorInfo | None = None
    soil_calibrated: bool
    et0_days: int
    et0_blocker: str | None
    daily: list[DayRow]


class CropOption(BaseModel):
    key: str
    name_tr: str
    season_type: str | None
    root_depth_m: float
    season_ready: bool

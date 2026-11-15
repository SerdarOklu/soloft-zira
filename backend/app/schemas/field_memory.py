"""Field Memory: the detected history, the user's confirmation, and the NDVI behind it (phase 5)."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.fields import JobOut

State = Literal["cropped", "fallow", "unknown"]


class SeasonOut(BaseModel):
    season: str  # "2024-2025"
    harvest_year: int
    detected_state: State
    peak_ndvi: float | None
    peak_date: date | None
    good_observations: int
    total_observations: int
    confidence: float | None
    confidence_level: Literal["high", "medium", "low"] | None
    # What a person confirmed; null until someone does.
    confirmed_state: State | None
    confirmed_by: Literal["user", "agronomist"] | None
    confirmed_at: datetime | None


class NdviPoint(BaseModel):
    date: date
    ndvi: float | None
    valid_pixels: int
    flag: str | None


class Coverage(BaseModel):
    observations: int
    good: int
    first_date: date | None
    last_date: date | None


class FieldMemoryOut(BaseModel):
    field_id: uuid.UUID
    history_years: int
    threshold: float
    # The threshold is a starting value that an agronomist has not calibrated.
    provisional: bool
    coverage: Coverage
    seasons: list[SeasonOut]
    series: list[NdviPoint]
    latest_job: JobOut | None
    confirmed_count: int


class ConfirmItem(BaseModel):
    season: str = Field(pattern=r"^\d{4}-\d{4}$")
    state: State


class ConfirmIn(BaseModel):
    seasons: list[ConfirmItem] = Field(min_length=1, max_length=12)

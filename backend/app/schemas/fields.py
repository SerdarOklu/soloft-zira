"""Field Profile, NASA fetch jobs and the screens that read them (PDT sections 5 and 10.1)."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models import WaterRegime

MAX_RING_POINTS = 1000


class PolygonIn(BaseModel):
    """A GeoJSON Polygon: one closed ring of [longitude, latitude] points, no holes."""

    type: Literal["Polygon"]
    coordinates: list[list[list[float]]]

    @field_validator("coordinates")
    @classmethod
    def _one_valid_ring(cls, rings: list[list[list[float]]]) -> list[list[list[float]]]:
        if len(rings) != 1:
            raise ValueError("A field is a single ring; holes are not supported")
        ring = rings[0]
        for point in ring:
            if len(point) != 2:
                raise ValueError("Each point is [longitude, latitude]")
            longitude, latitude = point
            if not (-180 <= longitude <= 180 and -90 <= latitude <= 90):
                raise ValueError("Longitude must be within ±180 and latitude within ±90")
        if ring and ring[0] != ring[-1]:
            ring = [*ring, ring[0]]
        if len(ring) < 4:
            raise ValueError("A polygon needs at least three corners")
        if len(ring) > MAX_RING_POINTS:
            raise ValueError(f"A polygon may have at most {MAX_RING_POINTS} points")
        return [ring]


class FieldCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=200)
    # Generated when left out.
    code: str | None = Field(default=None, min_length=1, max_length=64)
    region: str | None = Field(default=None, max_length=200)
    water_regime: WaterRegime
    # A key of config/soils.yaml.
    soil_texture: str = Field(min_length=1, max_length=32)
    geometry: PolygonIn


class Point(BaseModel):
    lat: float
    lon: float


class FieldOut(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    region: str | None
    water_regime: WaterRegime | None
    soil_texture: str | None
    area_ha: float | None
    elevation_m: float | None
    centroid: Point | None
    geometry: dict[str, Any] | None
    weather_days: int
    created_at: datetime


class FetchRequest(BaseModel):
    # Defaults to the 25 years in the parameter sheet.
    date_from: date | None = None
    date_to: date | None = None
    # Fetch again even when the whole period is already stored.
    force: bool = False


class JobOut(BaseModel):
    id: uuid.UUID
    field_id: uuid.UUID | None
    field_code: str | None = None
    field_name: str | None = None
    source: str
    status: str
    date_from: date | None
    date_to: date | None
    rows_written: int | None
    error_message: str | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None


class YearStat(BaseModel):
    year: int
    days: int
    precipitation_mm: float | None
    temperature_avg: float | None
    temperature_min: float | None
    temperature_max: float | None


class DailyRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    date: date
    precipitation_mm: float | None
    temperature_avg: float | None
    temperature_max: float | None
    temperature_min: float | None
    humidity: float | None
    wind_speed: float | None
    solar_radiation: float | None
    surface_pressure: float | None
    quality_flag: str | None


class WeatherSummary(BaseModel):
    days: int
    first_date: date | None
    last_date: date | None
    last_fetched_at: datetime | None
    units: dict[str, str]
    wind_height_m: float | None
    years: list[YearStat]
    recent: list[DailyRow]
    latest_job: JobOut | None


class JobCounts(BaseModel):
    queued: int = 0
    running: int = 0
    done: int = 0
    failed: int = 0


class SourceOut(BaseModel):
    key: str
    name: str
    role: str
    access: str
    resolution: str
    priority: str
    scale_warning: str
    collection_id: str | None
    # power: connected now. earth_engine sources connect in phase 5.
    connected: bool
    # ok | error | never_fetched | not_connected
    status: str
    last_success_at: datetime | None
    observations: int
    jobs: JobCounts


class MissingField(BaseModel):
    id: uuid.UUID
    code: str
    name: str


class Marker(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    lat: float
    lon: float
    area_ha: float | None
    has_weather: bool


class DashboardSummary(BaseModel):
    field_count: int
    fields_with_weather: int
    fields_missing_weather: list[MissingField]
    jobs: JobCounts
    last_weather_update: datetime | None
    markers: list[Marker]

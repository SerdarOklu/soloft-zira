"""Sensor readings, calibration and status (phase 7)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class ReadingIn(BaseModel):
    depth_cm: int = Field(ge=1, le=300)
    vwc_raw: float = Field(ge=0.0, le=1.0)


class ReadingsIn(BaseModel):
    """The reading schema of PDT 12.2. ``field_id`` is the Zira field's id."""

    field_id: uuid.UUID
    measured_at: datetime
    is_simulated: bool = False
    battery_v: float | None = Field(default=None, ge=0.0, le=20.0)
    readings: list[ReadingIn] = Field(min_length=1, max_length=8)

    @model_validator(mode="after")
    def _distinct_depths(self) -> ReadingsIn:
        depths = [reading.depth_cm for reading in self.readings]
        if len(set(depths)) != len(depths):
            raise ValueError("Each depth may appear once")
        if self.measured_at.tzinfo is None:
            raise ValueError("measured_at needs a time zone")
        return self


class IngestOut(BaseModel):
    stored: int
    calibrated: bool


class CalibrationIn(BaseModel):
    slope: float = Field(gt=0.0, le=5.0)
    intercept: float = Field(ge=-0.5, le=0.5)
    theta_wp: float = Field(gt=0.0, lt=0.6)
    theta_fc: float = Field(gt=0.0, lt=0.7)
    note: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def _ordered(self) -> CalibrationIn:
        if self.theta_wp >= self.theta_fc:
            raise ValueError("The wilting point must be below field capacity")
        return self


class CalibrationOut(CalibrationIn):
    calibrated_at: datetime


class NodeReading(BaseModel):
    depth_cm: int
    vwc_raw: float
    vwc_calibrated: float | None


class NodeStatus(BaseModel):
    node_id: str
    last_seen: datetime
    status: Literal["active", "silent"]
    battery_v: float | None
    is_simulated: bool
    readings: list[NodeReading]


class SensorStatusOut(BaseModel):
    field_id: uuid.UUID
    mode: Literal["sensor", "satellite"]
    silence_h: float
    calibration: CalibrationOut | None
    nodes: list[NodeStatus]

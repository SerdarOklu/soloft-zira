"""Users of an organization and the farmer view (phase 7)."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

RoleName = Literal["admin", "agronomist", "cooperative_user", "farmer"]


class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    name: str
    role: RoleName
    organization_id: uuid.UUID | None
    is_active: bool
    phone: str | None = None
    field_count: int
    created_at: datetime


class UserCreate(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    name: str = Field(min_length=1, max_length=200)
    # Optional for a farmer, who then signs in with a link or a WhatsApp code only.
    password: str | None = Field(default=None, min_length=10, max_length=200)
    phone: str | None = Field(default=None, max_length=32)
    role: RoleName = "farmer"
    # Admin only; a cooperative user always creates farmers in their own organization.
    organization_id: uuid.UUID | None = None


class UserPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    is_active: bool | None = None
    # An empty string removes the number.
    phone: str | None = Field(default=None, max_length=32)


class LoginLink(BaseModel):
    token: str
    expires_at: datetime


class LinkFarmer(BaseModel):
    farmer_user_id: uuid.UUID | None


class FarmerWater(BaseModel):
    date: date
    storage_mm: float
    low_mm: float
    high_mm: float
    taw_mm: float
    fill_fraction: float


class FarmerField(BaseModel):
    id: uuid.UUID
    name: str
    region: str | None
    area_ha: float | None
    mode: Literal["sensor", "satellite"]
    water: FarmerWater | None
    # Why the water cannot be shown (for example no NASA data yet), as a code.
    water_problem: str | None
    last_weather_date: date | None


class FarmerMessage(BaseModel):
    id: uuid.UUID
    field_name: str
    event_type: str
    event_date: date
    body: str
    sent_at: datetime | None


class FarmerSummary(BaseModel):
    name: str
    fields: list[FarmerField]
    messages: list[FarmerMessage]

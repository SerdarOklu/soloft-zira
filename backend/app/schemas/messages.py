"""Message drafts and the gateway status (phase 6)."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field


class DraftOut(BaseModel):
    id: uuid.UUID
    field_id: uuid.UUID
    field_name: str
    event_type: str
    event_date: date
    locale: str
    body: str
    payload: dict[str, Any]
    status: str
    # Only the last digits, so the list does not hold a full phone number.
    recipient_hint: str | None
    has_recipient: bool
    error: str | None
    created_at: datetime
    decided_at: datetime | None
    sent_at: datetime | None


class GenerateIn(BaseModel):
    season_year: int = Field(ge=1990, le=2100)  # the year of the autumn decision day
    rotation: str | None = Field(default=None, max_length=200)
    locale: str = Field(default="tr", pattern="^(tr|en)$")
    recipient_phone: str | None = Field(default=None, max_length=30)


class GenerateOut(BaseModel):
    created: int
    skipped: int
    drafts: list[DraftOut]


class EditIn(BaseModel):
    body: str | None = Field(default=None, max_length=1600)
    # An empty string clears the number.
    recipient_phone: str | None = Field(default=None, max_length=30)


class ApproveIn(BaseModel):
    recipient_phone: str | None = Field(default=None, max_length=30)


class GatewayOut(BaseModel):
    configured: bool
    provider: str

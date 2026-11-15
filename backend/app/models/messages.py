"""Message drafts: Zira writes them, an agronomist approves them, then they go to the farmer.

Nothing is sent without an approval. The draft keeps the numbers it was written from, so the
agronomist sees what the sentence rests on.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import Date, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAt, UuidPk


class MessageDraft(UuidPk, CreatedAt, Base):
    __tablename__ = "message_drafts"
    __table_args__ = (UniqueConstraint("field_id", "event_type", "event_date"),)

    field_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("fields.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(String(32), nullable=False)
    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    locale: Mapped[str] = mapped_column(String(2), nullable=False, default="tr")
    body: Mapped[str] = mapped_column(Text, nullable=False)
    # The numbers the sentence was written from.
    payload: Mapped[dict[str, Any]] = mapped_column(nullable=False, default=dict)
    # pending, approved, sent, rejected or failed
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending", index=True)
    recipient_phone: Mapped[str | None] = mapped_column(String(20))
    decided_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    provider_message_id: Mapped[str | None] = mapped_column(String(64))
    error: Mapped[str | None] = mapped_column(Text)

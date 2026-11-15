"""Users and organizations (PDT section 9; roles in section 10.3)."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, CreatedAt, UuidPk


class Role(enum.StrEnum):
    ADMIN = "admin"
    AGRONOMIST = "agronomist"
    COOPERATIVE_USER = "cooperative_user"
    # The farmer account arrives with the cooperative system (phase 7); the value is
    # defined now so the column does not need a migration then.
    FARMER = "farmer"


class OrganizationType(enum.StrEnum):
    COOPERATIVE = "cooperative"
    INSTITUTION = "institution"


def _values(enum_cls: type[enum.Enum]) -> list[str]:
    return [member.value for member in enum_cls]


class Organization(UuidPk, CreatedAt, Base):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    type: Mapped[OrganizationType] = mapped_column(
        Enum(OrganizationType, native_enum=False, length=32, values_callable=_values),
        nullable=False,
    )

    users: Mapped[list[User]] = relationship(back_populates="organization")


class User(UuidPk, CreatedAt, Base):
    __tablename__ = "users"

    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("organizations.id", ondelete="SET NULL"), index=True
    )
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[Role] = mapped_column(
        Enum(Role, native_enum=False, length=32, values_callable=_values), nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    # Digits with the country code (905321234567). Where a farmer's sign-in code is sent.
    phone: Mapped[str | None] = mapped_column(String(20), index=True)

    organization: Mapped[Organization | None] = relationship(back_populates="users")


class LoginToken(UuidPk, CreatedAt, Base):
    """A one-time way to sign in without a password: a link a cooperative hands over, or a
    short code sent to the farmer's WhatsApp. Only a keyed hash of the secret is stored."""

    __tablename__ = "login_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # "link" or "code"
    kind: Mapped[str] = mapped_column(String(8), nullable=False)
    secret_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Wrong guesses so far; a code is dead after a few.
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )

"""Password hashing and access tokens."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.core.config import get_settings

ALGORITHM = "HS256"

_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False


def create_access_token(
    user_id: uuid.UUID, role: str, now: datetime | None = None, ttl: timedelta | None = None
) -> str:
    settings = get_settings()
    issued = now or datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "role": role,
        "iat": issued,
        "exp": issued + (ttl or timedelta(minutes=settings.access_token_ttl_minutes)),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> uuid.UUID | None:
    """The user id the token was issued for, or None if it is invalid or expired."""
    try:
        payload = jwt.decode(token, get_settings().secret_key, algorithms=[ALGORITHM])
        return uuid.UUID(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        return None

"""Passwordless sign-in for farmers: a one-time link and a one-time WhatsApp code.

Both work for farmer accounts only. Staff (admin, agronomist, cooperative user) keep their
password, so a stolen phone number or a forwarded link never opens a staff account.

Only a keyed hash (HMAC-SHA256 with the server secret) of a link secret or a code is stored.
A link is used once; a code lives a few minutes, allows a few wrong guesses and is requested
at most a few times an hour per account.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import LoginToken, Role, User
from app.services.messaging.greenapi import normalise_phone

LINK = "link"
CODE = "code"
CODE_DIGITS = 6
MAX_WRONG_CODES = 5
MAX_CODES_PER_HOUR = 3


def _now() -> datetime:
    return datetime.now(UTC)


def _hash(secret: str, user_id: uuid.UUID | None = None) -> str:
    message = f"{user_id}:{secret}" if user_id else secret
    return hmac.new(
        get_settings().secret_key.encode(), message.encode(), hashlib.sha256
    ).hexdigest()


def clean_phone(raw: str | None) -> str | None:
    """The phone as stored (digits with the country code), or None if it is not a number."""
    if not raw or not raw.strip():
        return None
    try:
        return normalise_phone(raw)
    except ValueError:
        return None


def _farmer_by_phone(session: Session, phone: str) -> User | None:
    """The one active farmer with this number. Two accounts on one number is ambiguous, so
    neither gets a code."""
    users = session.scalars(
        select(User).where(User.phone == phone, User.is_active.is_(True), User.role == Role.FARMER)
    ).all()
    return users[0] if len(users) == 1 else None


# --- link ----------------------------------------------------------------------------------


def issue_link(session: Session, user: User, created_by: User) -> tuple[str, datetime]:
    """A new single-use link secret for a farmer; earlier unused links stop working."""
    now = _now()
    session.execute(
        update(LoginToken)
        .where(LoginToken.user_id == user.id, LoginToken.kind == LINK, LoginToken.used_at.is_(None))
        .values(used_at=now)
    )
    secret = secrets.token_urlsafe(32)
    expires = now + timedelta(hours=get_settings().login_link_ttl_hours)
    session.add(
        LoginToken(
            user_id=user.id,
            kind=LINK,
            secret_hash=_hash(secret),
            expires_at=expires,
            created_by=created_by.id,
        )
    )
    session.commit()
    return secret, expires


def redeem_link(session: Session, secret: str) -> User | None:
    now = _now()
    token = session.scalar(
        select(LoginToken)
        .where(
            LoginToken.secret_hash == _hash(secret),
            LoginToken.kind == LINK,
            LoginToken.used_at.is_(None),
            LoginToken.expires_at > now,
        )
        .with_for_update()
    )
    if token is None:
        return None
    user = session.get(User, token.user_id)
    if user is None or not user.is_active or user.role != Role.FARMER:
        return None
    token.used_at = now
    session.commit()
    return user


# --- code ----------------------------------------------------------------------------------


def request_code(session: Session, raw_phone: str) -> tuple[User, str] | None:
    """A new code for the farmer with this number, or None (unknown number, ambiguous number
    or too many requests). The caller answers the same way in every case."""
    phone = clean_phone(raw_phone)
    user = _farmer_by_phone(session, phone) if phone else None
    if user is None:
        return None
    now = _now()
    recent = session.scalar(
        select(func.count())
        .select_from(LoginToken)
        .where(
            LoginToken.user_id == user.id,
            LoginToken.kind == CODE,
            LoginToken.created_at > now - timedelta(hours=1),
        )
    )
    if (recent or 0) >= MAX_CODES_PER_HOUR:
        return None
    session.execute(
        update(LoginToken)
        .where(LoginToken.user_id == user.id, LoginToken.kind == CODE, LoginToken.used_at.is_(None))
        .values(used_at=now)
    )
    code = f"{secrets.randbelow(10**CODE_DIGITS):0{CODE_DIGITS}d}"
    session.add(
        LoginToken(
            user_id=user.id,
            kind=CODE,
            secret_hash=_hash(code, user.id),
            expires_at=now + timedelta(minutes=get_settings().login_code_ttl_minutes),
        )
    )
    session.commit()
    return user, code


def verify_code(session: Session, raw_phone: str, code: str) -> User | None:
    phone = clean_phone(raw_phone)
    user = _farmer_by_phone(session, phone) if phone else None
    if user is None:
        return None
    now = _now()
    token = session.scalar(
        select(LoginToken)
        .where(
            LoginToken.user_id == user.id,
            LoginToken.kind == CODE,
            LoginToken.used_at.is_(None),
            LoginToken.expires_at > now,
        )
        .order_by(LoginToken.created_at.desc())
        .limit(1)
        .with_for_update()
    )
    if token is None or token.attempts >= MAX_WRONG_CODES:
        return None
    if not hmac.compare_digest(token.secret_hash, _hash(code, user.id)):
        token.attempts += 1
        session.commit()
        return None
    token.used_at = now
    session.commit()
    return user

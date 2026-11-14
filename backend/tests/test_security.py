import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.core.config import Settings, get_settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hash_roundtrip():
    hashed = hash_password("correct horse battery")
    assert hashed != "correct horse battery"
    assert verify_password("correct horse battery", hashed)
    assert not verify_password("wrong", hashed)


def test_verify_rejects_garbage_hash():
    assert not verify_password("anything", "not-a-hash")


def test_token_roundtrip():
    user_id = uuid.uuid4()
    assert decode_access_token(create_access_token(user_id, "admin")) == user_id


def test_expired_token_is_rejected():
    ttl = get_settings().access_token_ttl_minutes
    long_ago = datetime.now(UTC) - timedelta(minutes=ttl + 5)
    assert decode_access_token(create_access_token(uuid.uuid4(), "admin", now=long_ago)) is None


def test_tampered_token_is_rejected():
    token = create_access_token(uuid.uuid4(), "admin")
    assert decode_access_token(token[:-2] + ("aa" if token[-2:] != "aa" else "bb")) is None
    assert decode_access_token("garbage") is None


def test_production_refuses_weak_secrets():
    for secret in ("change-me", "too-short"):
        with pytest.raises(RuntimeError, match="SECRET_KEY"):
            Settings(environment="production", secret_key=secret).check()
    Settings(environment="production", secret_key="x" * 32).check()
    Settings(environment="development", secret_key="change-me").check()

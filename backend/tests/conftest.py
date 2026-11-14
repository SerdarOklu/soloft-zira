"""Shared fixtures.

Unit tests run on an in-memory SQLite database that holds only the tables without
geometry columns. Tests marked ``db`` need PostgreSQL with PostGIS and are skipped
when TEST_DATABASE_URL is not reachable.
"""

from __future__ import annotations

import os
from collections.abc import Iterator

# Set before the application settings are first read.
os.environ.setdefault("SECRET_KEY", "test-secret-key-that-is-long-enough-for-hs256")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.db import get_session
from app.main import app
from app.models import Base, CropType, DataSource, Organization, User

SQLITE_TABLES = [
    Base.metadata.tables[model.__tablename__]
    for model in (Organization, User, CropType, DataSource)
]

DEFAULT_TEST_DATABASE_URL = "postgresql+psycopg://zira:zira@localhost:5432/zira_test"


@pytest.fixture
def session() -> Iterator[Session]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine, tables=SQLITE_TABLES)
    with Session(engine, expire_on_commit=False) as db:
        yield db
    engine.dispose()


@pytest.fixture
def client(session: Session) -> Iterator[TestClient]:
    app.dependency_overrides[get_session] = lambda: session
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


@pytest.fixture(scope="session")
def postgres_url() -> str:
    url = os.environ.get("TEST_DATABASE_URL", DEFAULT_TEST_DATABASE_URL)
    engine = create_engine(url)
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except OperationalError:
        pytest.skip("PostgreSQL is not reachable; set TEST_DATABASE_URL to run db tests")
    finally:
        engine.dispose()
    return url

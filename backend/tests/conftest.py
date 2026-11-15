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
from alembic import command
from alembic.config import Config as AlembicConfig
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.cli import create_user, seed_reference
from app.core.config import REPO_ROOT, get_settings
from app.core.db import _session_factory, get_engine, get_session
from app.core.parameters import get_config
from app.main import app
from app.models import Base, CropType, DataSource, Organization, OrganizationType, Role, User
from app.tasks.celery_app import celery_app

PASSWORD = "a-long-enough-password"

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


def _reset_app_caches() -> None:
    get_settings.cache_clear()
    get_engine.cache_clear()
    _session_factory.cache_clear()


@pytest.fixture
def pg(postgres_url: str, monkeypatch: pytest.MonkeyPatch) -> Iterator[Engine]:
    """A freshly migrated and seeded PostgreSQL database, wired into the application."""
    monkeypatch.setenv("DATABASE_URL", postgres_url)
    _reset_app_caches()
    engine = create_engine(postgres_url)
    with engine.begin() as connection:
        connection.execute(text("DROP SCHEMA public CASCADE"))
        connection.execute(text("CREATE SCHEMA public"))
    command.upgrade(AlembicConfig(str(REPO_ROOT / "backend" / "alembic.ini")), "head")
    with Session(engine) as db, db.begin():
        seed_reference(db, get_config())
    yield engine
    engine.dispose()
    _reset_app_caches()


@pytest.fixture
def pg_client(pg: Engine) -> Iterator[TestClient]:
    """The real application on the PostgreSQL database; no dependency is replaced."""
    app.dependency_overrides.clear()
    yield TestClient(app)


@pytest.fixture
def eager() -> Iterator[None]:
    """Run Celery tasks inline, so an API call finishes its job before it answers."""
    previous = celery_app.conf.task_always_eager
    celery_app.conf.task_always_eager = True
    yield
    celery_app.conf.task_always_eager = previous


@pytest.fixture
def make_user(pg: Engine):
    """Create an account; returns its id."""

    def _make(email: str, role: Role, organization: str | None = None) -> str:
        with Session(pg) as db, db.begin():
            organization_id = None
            if organization is not None:
                org = db.query(Organization).filter_by(name=organization).first()
                if org is None:
                    org = Organization(name=organization, type=OrganizationType.COOPERATIVE)
                    db.add(org)
                    db.flush()
                organization_id = org.id
            user = create_user(db, email=email, name=email, role=role, password=PASSWORD)
            user.organization_id = organization_id
            return str(user.id)

    return _make


@pytest.fixture
def bearer(pg_client: TestClient):
    """Sign in and return the Authorization header."""

    def _bearer(email: str) -> dict[str, str]:
        response = pg_client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
        assert response.status_code == 200, response.text
        return {"Authorization": f"Bearer {response.json()['access_token']}"}

    return _bearer

"""The migrations must build the schema the models describe, and undo it again."""

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

from app.core.config import REPO_ROOT, get_settings
from app.models import Base

pytestmark = pytest.mark.db

EXPECTED_TABLES = {
    "users",
    "organizations",
    "fields",
    "soil_profiles",
    "crop_types",
    "crop_cycles",
    "farmer_constraints",
    "data_sources",
    "data_fetch_jobs",
    "weather_observations",
    "satellite_observations",
    "sensor_observations",
    "analysis_runs",
    "soil_water_balances",
    "rotation_scenarios",
    "zira_cards",
}


@pytest.fixture
def alembic_config(postgres_url: str, monkeypatch: pytest.MonkeyPatch) -> Config:
    monkeypatch.setenv("DATABASE_URL", postgres_url)
    get_settings.cache_clear()
    engine = create_engine(postgres_url)
    with engine.begin() as connection:
        connection.execute(text("DROP SCHEMA public CASCADE"))
        connection.execute(text("CREATE SCHEMA public"))
    engine.dispose()
    yield Config(str(REPO_ROOT / "backend" / "alembic.ini"))
    get_settings.cache_clear()


def _tables(url: str) -> set[str]:
    engine = create_engine(url)
    try:
        names = set(inspect(engine).get_table_names())
    finally:
        engine.dispose()
    return names - {"spatial_ref_sys", "alembic_version"}


def test_models_define_exactly_the_pdt_tables():
    assert set(Base.metadata.tables) == EXPECTED_TABLES


def test_upgrade_check_downgrade(alembic_config: Config, postgres_url: str):
    command.upgrade(alembic_config, "head")
    assert _tables(postgres_url) == EXPECTED_TABLES

    engine = create_engine(postgres_url)
    with engine.connect() as connection:
        geometry = connection.execute(
            text(
                "SELECT f_geometry_column, type, srid FROM geometry_columns "
                "WHERE f_table_name = 'fields' ORDER BY f_geometry_column"
            )
        ).all()
    engine.dispose()
    assert geometry == [("centroid", "POINT", 4326), ("geom", "POLYGON", 4326)]

    # Fails if a model has changed without a migration.
    command.check(alembic_config)

    command.downgrade(alembic_config, "base")
    assert _tables(postgres_url) == set()


def test_check_ignores_other_schemas_on_the_search_path(alembic_config: Config, postgres_url: str):
    """The postgis Docker image puts the tiger and topology schemas on the search path."""
    engine = create_engine(postgres_url, isolation_level="AUTOCOMMIT")
    with engine.connect() as connection:
        database = connection.execute(text("SELECT current_database()")).scalar_one()
        connection.execute(text("DROP SCHEMA IF EXISTS tiger CASCADE"))
        connection.execute(text("CREATE SCHEMA tiger"))
        connection.execute(text("CREATE TABLE tiger.tabblock (gid serial PRIMARY KEY)"))
        connection.execute(text(f'ALTER DATABASE "{database}" SET search_path = public, tiger'))
    engine.dispose()
    try:
        command.upgrade(alembic_config, "head")
        command.check(alembic_config)
    finally:
        engine = create_engine(postgres_url, isolation_level="AUTOCOMMIT")
        with engine.connect() as connection:
            connection.execute(text(f'ALTER DATABASE "{database}" RESET search_path'))
            connection.execute(text("DROP SCHEMA IF EXISTS tiger CASCADE"))
        engine.dispose()

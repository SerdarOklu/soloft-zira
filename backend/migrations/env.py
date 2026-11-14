"""Alembic environment.

The database URL comes from the application settings (DATABASE_URL), and the
target metadata from the models, so `alembic check` can detect a model that has
drifted from the migrations.
"""

from logging.config import fileConfig

from alembic import context
from geoalchemy2 import alembic_helpers
from sqlalchemy import create_engine, pool

from app.core.config import get_settings
from app.models import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# PostGIS ships its own tables. They are not ours to migrate.
_POSTGIS_TABLES = {"spatial_ref_sys"}

# The postgis Docker image also installs the tiger geocoder and topology extensions and
# puts their schemas on the database's search_path. Without this, Alembic sees their
# tables as if they were ours and reports every one as "removed".
_CONNECT_ARGS = {"options": "-csearch_path=public"}


def include_object(obj, name, type_, reflected, compare_to):
    if type_ == "table" and name in _POSTGIS_TABLES:
        return False
    return alembic_helpers.include_object(obj, name, type_, reflected, compare_to)


def _configure(**kwargs) -> None:
    context.configure(
        target_metadata=target_metadata,
        include_object=include_object,
        process_revision_directives=alembic_helpers.writer,
        render_item=alembic_helpers.render_item,
        compare_type=True,
        **kwargs,
    )


def run_migrations_offline() -> None:
    _configure(url=get_settings().database_url, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(
        get_settings().database_url, poolclass=pool.NullPool, connect_args=_CONNECT_ARGS
    )
    with engine.connect() as connection:
        _configure(connection=connection)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

"""Alembic environment configuration."""

from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

# GeoAlchemy2 alembic helpers (optional, for autogenerate with geometry)
try:
    from geoalchemy2 import alembic_helpers
    HAS_GEALCHEMY_HELPERS = True
except ImportError:
    HAS_GEALCHEMY_HELPERS = False

# Import all models so Alembic can detect them
from app.core.database import Base
from app.models import User, Role, Dataset, DatasetVersion, Feature, ProcessingJob, AuditLog

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_url():
    """Get database URL from environment or config."""
    import os
    return os.getenv("DATABASE_URL", config.get_main_option("sqlalchemy.url"))


def _configure_context(connection=None, url=None, **kwargs):
    opts = dict(
        target_metadata=target_metadata,
        **kwargs,
    )
    if HAS_GEALCHEMY_HELPERS:
        opts["process_revision_directives"] = alembic_helpers.writer
        opts["render_item"] = alembic_helpers.render_item
    if connection:
        opts["connection"] = connection
    if url:
        opts["url"] = url
    context.configure(**opts)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_url()
    _configure_context(
        url=url,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = get_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        _configure_context(connection=connection)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

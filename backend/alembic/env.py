"""Alembic migration environment.

The database URL is resolved at runtime from the application configuration
(``CHAI_DATABASE_URL`` and per-environment defaults) unless it is explicitly
overridden on the Alembic ``Config`` (used by the migration smoke tests).

The target metadata is the shared SQLModel metadata, populated by importing the
``app.models`` package.
"""

from __future__ import annotations

import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# Make the project root importable regardless of the working directory.
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import app.models  # noqa: E402,F401  (registers every table on Base.metadata)
from app.core.config import get_settings  # noqa: E402
from app.core.db import Base  # noqa: E402

config = context.config

# Alembic's own ini logging is a convenience for the CLI; do not disable
# loggers that already exist (e.g. the application's), which would otherwise
# break logging state when migrations run inside the test process.
if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = Base.metadata


def _database_url() -> str:
    """Return the configured URL, preferring an explicit Alembic override."""
    url = config.get_main_option("sqlalchemy.url")
    if url:
        return url
    return get_settings().effective_database_url


def run_migrations_offline() -> None:
    """Render migrations as SQL without a live database connection."""
    context.configure(
        url=_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Apply migrations against a live database connection."""
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = _database_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

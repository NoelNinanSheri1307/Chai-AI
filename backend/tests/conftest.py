"""Shared test fixtures."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, event
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session

import app.models  # noqa: F401  (register every table on Base.metadata)
from app.clients.storage import LocalStorageAdapter
from app.core.config import Settings, clear_settings_cache
from app.core.db import (
    Base,
    clear_database_cache,
    create_db_engine,
    create_session_factory,
)
from app.main import create_app


@pytest.fixture(autouse=True)
def _reset_settings() -> None:
    """Isolate cached settings and databases between tests."""
    clear_settings_cache()
    clear_database_cache()


@pytest.fixture()
def settings() -> Settings:
    """Test configuration with verbose logging suppressed and quiet level."""
    return Settings(
        environment="testing",
        debug=False,
        json_logging=False,
        log_level="ERROR",
        cors_origins=["*"],
        trusted_hosts=["*"],
    )


@pytest.fixture()
def client(settings: Settings) -> TestClient:
    """ASGI test client backed by a freshly built application."""
    app = create_app(settings=settings)
    return TestClient(app)


# ---------------------------------------------------------------------------
# Persistence fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def db_engine(settings: Settings) -> Iterator[Engine]:
    """A fresh in-memory SQLite engine with every table created.

    Foreign-key enforcement is enabled so ON DELETE/CASCADE rules behave like
    PostgreSQL. Each invocation gets its own isolated in-memory database.
    """
    engine = create_db_engine(settings)

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _connection_record) -> None:  # type: ignore[misc]
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture()
def db_session_factory(db_engine: Engine) -> sessionmaker[Session]:
    """A session factory bound to the test engine."""
    return create_session_factory(db_engine)


@pytest.fixture()
def db_session(db_session_factory: sessionmaker[Session]) -> Iterator[Session]:
    """A session against the isolated test database."""
    with db_session_factory() as session:
        yield session


@pytest.fixture()
def storage_root(tmp_path: Path) -> Path:
    """An isolated filesystem storage root."""
    return tmp_path / "storage"


@pytest.fixture()
def storage(storage_root: Path) -> LocalStorageAdapter:
    """An isolated ``LocalStorageAdapter`` backed by a temp directory."""
    return LocalStorageAdapter(storage_root)

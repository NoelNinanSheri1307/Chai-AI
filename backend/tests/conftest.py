"""Shared test fixtures."""

from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, event
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session

import app.models  # noqa: F401  (register every table on Base.metadata)
from app.api.deps import get_db_session, get_settings_dependency
from app.clients.storage import LocalStorageAdapter
from app.core.config import Settings, clear_settings_cache
from app.core.db import (
    Base,
    clear_database_cache,
    create_db_engine,
    create_session_factory,
)
from app.main import create_app
from app.pipeline.config import (
    PipelineConfig,
    clear_pipeline_config_cache,
    get_pipeline_config,
)
from app.pipeline.detectors.registry import build_detectors
from app.pipeline.explanation.placeholder import (
    PlaceholderEvidenceGenerator,
    PlaceholderExplanationGenerator,
)
from app.pipeline.fusion.engine import DeterministicFusionEngine
from app.pipeline.heatmap.placeholder import PlaceholderHeatmapGenerator
from app.pipeline.runner import ModularAnalysisPipeline


@pytest.fixture(autouse=True)
def _reset_settings() -> None:
    """Isolate cached settings, databases and pipeline config between tests."""
    clear_settings_cache()
    clear_database_cache()
    clear_pipeline_config_cache()


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


@pytest.fixture()
def pipeline_config() -> PipelineConfig:
    """The cached default pipeline configuration."""
    return get_pipeline_config()


@pytest.fixture()
def pipeline(pipeline_config: PipelineConfig) -> ModularAnalysisPipeline:
    """A fully wired modular pipeline using all placeholder components."""
    return ModularAnalysisPipeline(
        detectors=build_detectors(pipeline_config.enabled_detector_names()),
        fusion=DeterministicFusionEngine(pipeline_config),
        heatmap_generator=PlaceholderHeatmapGenerator(pipeline_config),
        evidence_generator=PlaceholderEvidenceGenerator(pipeline_config),
        explanation_generator=PlaceholderExplanationGenerator(pipeline_config),
        pipeline_config=pipeline_config,
    )


@pytest.fixture()
def api_client(settings: Settings, db_engine: Engine, storage_root: Path) -> TestClient:
    """An ASGI client wired to the isolated test database and storage root.

    The application's settings, database session and object-storage providers
    are overridden so every request runs against the same in-memory engine and
    temporary storage used by the rest of the test suite.
    """
    app_settings = settings.model_copy(
        update={"database_url": "sqlite://", "storage_root": storage_root}
    )
    app = create_app(settings=app_settings)
    factory = create_session_factory(db_engine)

    def override_settings() -> Settings:
        return app_settings

    def override_db_session() -> Generator[Session, None, None]:
        with factory() as session:
            try:
                yield session
                session.commit()
            except Exception:
                session.rollback()
                raise

    app.dependency_overrides[get_settings_dependency] = override_settings
    app.dependency_overrides[get_db_session] = override_db_session
    return TestClient(app)

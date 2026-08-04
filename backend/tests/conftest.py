"""Shared test fixtures."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings, clear_settings_cache
from app.main import create_app


@pytest.fixture(autouse=True)
def _reset_settings() -> None:
    """Isolate cached settings between tests."""
    clear_settings_cache()


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

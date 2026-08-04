"""Tests for the configuration system."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_development_defaults() -> None:
    settings = Settings(environment="development")
    assert settings.environment == "development"
    assert not settings.is_testing
    assert settings.is_development
    assert settings.request_id_header == "X-Request-ID"
    assert settings.json_logging is True


def test_environment_is_case_insensitive() -> None:
    settings = Settings(environment="PRODUCTION")
    assert settings.environment == "production"
    assert settings.is_production


def test_comma_separated_lists_are_split() -> None:
    settings = Settings(
        cors_origins="http://a.example,http://b.example",
        trusted_hosts="api.example,*.example.invalid",
    )
    assert settings.cors_origins == ["http://a.example", "http://b.example"]
    assert settings.trusted_hosts == ["api.example", "*.example.invalid"]


def test_invalid_environment_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Settings(environment="staging")


def test_invalid_log_level_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Settings(log_level="LOUD")


def test_derived_environment_helpers_are_mutually_exclusive() -> None:
    settings = Settings(environment="testing")
    assert settings.debug is False
    assert not settings.is_production
    assert settings.is_testing

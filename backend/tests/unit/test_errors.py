"""Tests for the exception hierarchy and error catalog."""

from __future__ import annotations

from app.core.errors import ERROR_INFOS, ErrorCode, error_response_payload
from app.core.exceptions import (
    BusinessError,
    ChaiError,
    ChaiValidationError,
    ConfigurationError,
    InfrastructureError,
)


def test_error_catalog_is_complete() -> None:
    for code in ErrorCode:
        assert code in ERROR_INFOS


def test_error_response_payload_uses_defaults() -> None:
    payload = error_response_payload(ErrorCode.FORBIDDEN, "no access")
    assert payload["error"]["code"] == "forbidden"
    assert payload["error"]["message"] == "no access"
    assert payload["error"]["retryable"] is False
    assert payload["error"]["details"] == {}


def test_base_error_serializes_to_envelope() -> None:
    error = ChaiError(ErrorCode.INTERNAL_ERROR, "boom", retryable=True)
    assert error.status_code == 500
    assert error.to_response()["error"]["code"] == "internal_error"


def test_validation_error_defaults() -> None:
    error = ChaiValidationError("bad payload", details={"fields": []})
    assert error.code == ErrorCode.VALIDATION_ERROR
    assert error.status_code == 422
    assert error.retryable is False


def test_configuration_error_is_never_retryable() -> None:
    error = ConfigurationError("missing setting")
    assert error.status_code == 500
    assert error.retryable is False


def test_infrastructure_error_is_always_retryable() -> None:
    error = InfrastructureError(ErrorCode.STORAGE_UNAVAILABLE, "object store down")
    assert error.status_code == 503
    assert error.retryable is True


def test_business_error_respects_code() -> None:
    error = BusinessError("missing analysis", code=ErrorCode.ANALYSIS_NOT_FOUND)
    assert error.status_code == 404
    assert error.retryable is False

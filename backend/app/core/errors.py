"""Error code catalog and standard error envelope.

Implements the error catalog from the backend API specification (Section 13).
Every error code is registered here together with its default HTTP status and
whether a retry of the same request is safe (``retryable``).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ErrorCode(str, Enum):
    """Canonical machine-readable error codes returned by the API."""

    INVALID_REQUEST = "invalid_request"
    VALIDATION_ERROR = "validation_error"
    INVALID_IMAGE = "invalid_image"
    UNSUPPORTED_MEDIA_TYPE = "unsupported_media_type"
    FILE_TOO_LARGE = "file_too_large"
    UNAUTHORIZED = "unauthorized"
    INVALID_CREDENTIALS = "invalid_credentials"
    EXPIRED_TOKEN = "expired_token"
    INVALID_REFRESH_TOKEN = "invalid_refresh_token"
    FORBIDDEN = "forbidden"
    EMAIL_TAKEN = "email_taken"
    ANALYSIS_NOT_FOUND = "analysis_not_found"
    HISTORY_NOT_FOUND = "history_not_found"
    COMPARISON_NOT_FOUND = "comparison_not_found"
    RATE_LIMITED = "rate_limited"
    PIPELINE_ERROR = "pipeline_error"
    PROVIDER_ERROR = "provider_error"
    STORAGE_UNAVAILABLE = "storage_unavailable"
    DB_UNAVAILABLE = "db_unavailable"
    TIMEOUT = "timeout"
    JOB_NOT_FOUND = "job_not_found"
    INTERNAL_ERROR = "internal_error"


@dataclass(frozen=True)
class ErrorInfo:
    """Default HTTP status and retryability for an error code."""

    status_code: int
    retryable: bool


ERROR_INFOS: dict[ErrorCode, ErrorInfo] = {
    ErrorCode.INVALID_REQUEST: ErrorInfo(status_code=400, retryable=False),
    ErrorCode.VALIDATION_ERROR: ErrorInfo(status_code=422, retryable=False),
    ErrorCode.INVALID_IMAGE: ErrorInfo(status_code=422, retryable=False),
    ErrorCode.UNSUPPORTED_MEDIA_TYPE: ErrorInfo(status_code=415, retryable=False),
    ErrorCode.FILE_TOO_LARGE: ErrorInfo(status_code=413, retryable=False),
    ErrorCode.UNAUTHORIZED: ErrorInfo(status_code=401, retryable=False),
    ErrorCode.INVALID_CREDENTIALS: ErrorInfo(status_code=401, retryable=False),
    ErrorCode.EXPIRED_TOKEN: ErrorInfo(status_code=401, retryable=False),
    ErrorCode.INVALID_REFRESH_TOKEN: ErrorInfo(status_code=401, retryable=False),
    ErrorCode.FORBIDDEN: ErrorInfo(status_code=403, retryable=False),
    ErrorCode.EMAIL_TAKEN: ErrorInfo(status_code=409, retryable=False),
    ErrorCode.ANALYSIS_NOT_FOUND: ErrorInfo(status_code=404, retryable=False),
    ErrorCode.HISTORY_NOT_FOUND: ErrorInfo(status_code=404, retryable=False),
    ErrorCode.COMPARISON_NOT_FOUND: ErrorInfo(status_code=404, retryable=False),
    ErrorCode.RATE_LIMITED: ErrorInfo(status_code=429, retryable=True),
    ErrorCode.PIPELINE_ERROR: ErrorInfo(status_code=500, retryable=False),
    ErrorCode.PROVIDER_ERROR: ErrorInfo(status_code=503, retryable=True),
    ErrorCode.STORAGE_UNAVAILABLE: ErrorInfo(status_code=503, retryable=True),
    ErrorCode.DB_UNAVAILABLE: ErrorInfo(status_code=503, retryable=True),
    ErrorCode.TIMEOUT: ErrorInfo(status_code=504, retryable=True),
    ErrorCode.JOB_NOT_FOUND: ErrorInfo(status_code=404, retryable=False),
    ErrorCode.INTERNAL_ERROR: ErrorInfo(status_code=500, retryable=True),
}


def error_response_payload(
    code: ErrorCode,
    message: str,
    *,
    retryable: bool | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the standard error envelope for the given code.

    Falls back to the catalog default for ``retryable`` when not provided.
    """
    info = ERROR_INFOS[code]
    return {
        "error": {
            "code": code.value,
            "message": message,
            "retryable": retryable if retryable is not None else info.retryable,
            "details": details or {},
        }
    }

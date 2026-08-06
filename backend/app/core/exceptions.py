"""Application exception hierarchy.

A single hierarchy used across the API so that one set of global handlers
(``app.api.errors``) can translate any raised exception into the standard
error envelope defined in the API specification (Section 13).
"""

from __future__ import annotations

from typing import Any

from app.core.errors import ERROR_INFOS, ErrorCode, error_response_payload


class ChaiError(Exception):
    """Base class for every application-level error."""

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        *,
        status_code: int | None = None,
        retryable: bool | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        info = ERROR_INFOS[code]
        self.code: ErrorCode = code
        self.message: str = message
        self.status_code: int = (
            status_code if status_code is not None else info.status_code
        )
        self.retryable: bool = retryable if retryable is not None else info.retryable
        self.details: dict[str, Any] = details or {}

    def to_response(self) -> dict[str, Any]:
        """Serialize this error into the standard error envelope."""
        return error_response_payload(
            self.code,
            self.message,
            retryable=self.retryable,
            details=self.details,
        )


class ChaiValidationError(ChaiError):
    """A request payload failed validation."""

    def __init__(
        self,
        message: str = "Invalid request",
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(ErrorCode.VALIDATION_ERROR, message, details=details)


class FileTooLargeError(ChaiError):
    """An upload exceeded the configured size limit (HTTP 413)."""

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(ErrorCode.FILE_TOO_LARGE, message, details=details)


class UnsupportedMediaTypeError(ChaiError):
    """An upload declared a media type the API does not accept (HTTP 415)."""

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(ErrorCode.UNSUPPORTED_MEDIA_TYPE, message, details=details)


class InvalidImageError(ChaiError):
    """An upload is not a supported image or fails magic-byte validation (HTTP 422)."""

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(ErrorCode.INVALID_IMAGE, message, details=details)


class AnalysisNotFoundError(ChaiError):
    """An analysis with the requested public id does not exist (HTTP 404)."""

    def __init__(self, public_id: str) -> None:
        super().__init__(
            ErrorCode.ANALYSIS_NOT_FOUND,
            f"No analysis found for id {public_id!r}.",
            details={"id": public_id},
        )


class HistoryNotFoundError(ChaiError):
    """A history entry with the requested public id does not exist (HTTP 404)."""

    def __init__(self, public_id: str) -> None:
        super().__init__(
            ErrorCode.HISTORY_NOT_FOUND,
            f"No history entry found for id {public_id!r}.",
            details={"id": public_id},
        )


class ComparisonNotFoundError(ChaiError):
    """A comparison with the requested public id does not exist (HTTP 404)."""

    def __init__(self, public_id: str) -> None:
        super().__init__(
            ErrorCode.COMPARISON_NOT_FOUND,
            f"No comparison found for id {public_id!r}.",
            details={"id": public_id},
        )


class ConfigurationError(ChaiError):
    """Invalid or missing configuration; fatal at startup."""

    def __init__(
        self,
        message: str,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            ErrorCode.INTERNAL_ERROR,
            message,
            retryable=False,
            details=details,
        )


class InfrastructureError(ChaiError):
    """A backing system (database, storage, cache, provider) is unavailable.

    Always retryable: a transient infrastructure failure is safe to resubmit.
    """

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(code, message, retryable=True, details=details)


class BusinessError(ChaiError):
    """A business rule was violated.

    Reserved for the future business layer; concrete violations are raised
    with a specific catalog code (for example ``FORBIDDEN``).
    """

    def __init__(
        self,
        message: str,
        *,
        code: ErrorCode = ErrorCode.INVALID_REQUEST,
        status_code: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            code,
            message,
            status_code=status_code,
            retryable=False,
            details=details,
        )

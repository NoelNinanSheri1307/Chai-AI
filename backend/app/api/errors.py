"""Global exception handlers rendering the standard error envelope."""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse

from app.core.config import Settings
from app.core.errors import ErrorCode, error_response_payload
from app.core.exceptions import ChaiError

logger = logging.getLogger(__name__)

_HTTP_STATUS_TO_ERROR: dict[int, ErrorCode] = {
    400: ErrorCode.INVALID_REQUEST,
    401: ErrorCode.UNAUTHORIZED,
    403: ErrorCode.FORBIDDEN,
    404: ErrorCode.INVALID_REQUEST,
    405: ErrorCode.INVALID_REQUEST,
    413: ErrorCode.FILE_TOO_LARGE,
    415: ErrorCode.UNSUPPORTED_MEDIA_TYPE,
    429: ErrorCode.RATE_LIMITED,
    500: ErrorCode.INTERNAL_ERROR,
    503: ErrorCode.PROVIDER_ERROR,
}


def _validation_details(errors: list[dict]) -> dict[str, list[dict[str, str]]]:
    """Flatten pydantic validation errors into a field-by-field map."""
    fields = []
    for error in errors:
        location = error.get("loc", ())
        fields.append(
            {
                "field": ".".join(str(part) for part in location),
                "message": error.get("msg", "Invalid value"),
            }
        )
    return {"fields": fields}


def register_exception_handlers(app: FastAPI, settings: Settings) -> None:
    """Attach handlers that translate exceptions into the standard envelope."""

    @app.exception_handler(ChaiError)
    async def _chai_error_handler(_request: Request, exc: ChaiError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content=exc.to_response())

    @app.exception_handler(RequestValidationError)
    async def _validation_error_handler(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        payload = error_response_payload(
            ErrorCode.VALIDATION_ERROR,
            "Request validation failed.",
            retryable=False,
            details=_validation_details(exc.errors()),
        )
        return JSONResponse(status_code=422, content=payload)

    @app.exception_handler(StarletteHTTPException)
    async def _http_error_handler(
        _request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        code = _HTTP_STATUS_TO_ERROR.get(exc.status_code, ErrorCode.INTERNAL_ERROR)
        payload = error_response_payload(code, str(exc.detail), retryable=False)
        return JSONResponse(status_code=exc.status_code, content=payload)

    @app.exception_handler(Exception)
    async def _unhandled_error_handler(
        _request: Request, exc: Exception
    ) -> JSONResponse:
        logger.error("Unhandled exception during request", exc_info=exc)
        message = "Internal server error."
        if settings.debug:
            message = f"{message} {type(exc).__name__}: {exc}"
        payload = error_response_payload(
            ErrorCode.INTERNAL_ERROR,
            message,
            retryable=True,
        )
        return JSONResponse(status_code=500, content=payload)

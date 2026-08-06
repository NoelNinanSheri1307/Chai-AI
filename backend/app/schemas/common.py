"""Shared response schemas: error envelope, health payloads, page envelope."""

from __future__ import annotations

from enum import Enum
from typing import Any, Generic, Literal, TypeVar

from pydantic import BaseModel, Field

ItemT = TypeVar("ItemT")


class ErrorBody(BaseModel):
    """A single error within the standard error envelope."""

    code: str
    message: str
    retryable: bool
    details: dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    """Standard API error envelope (specification Section 13)."""

    error: ErrorBody


class HealthStatus(str, Enum):
    """Overall status reported by a health or readiness endpoint."""

    OK = "ok"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


class HealthResponse(BaseModel):
    """Liveness probe payload."""

    status: Literal["ok"] = "ok"


class ReadinessResponse(BaseModel):
    """Readiness probe payload with one check per backing system."""

    status: HealthStatus
    checks: dict[str, str]


class PageEnvelope(BaseModel, Generic[ItemT]):
    """Standard paginated list envelope (API contract conventions)."""

    items: list[ItemT]
    total: int
    page: int
    limit: int
    has_more: bool

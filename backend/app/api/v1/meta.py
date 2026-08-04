"""Meta router: liveness, readiness and operational metadata."""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas.common import (
    HealthResponse,
    HealthStatus,
    ReadinessResponse,
)

router = APIRouter(tags=["meta"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Liveness probe",
    description="Returns ``{status: ok}`` whenever the process is alive.",
)
async def health() -> HealthResponse:
    """Return a trivial payload confirming the service is up."""
    return HealthResponse()


@router.get(
    "/health/ready",
    response_model=ReadinessResponse,
    summary="Readiness probe",
    description=(
        "Reports the availability of every backing system (database, object "
        "storage, cache, models). In the foundation milestone those systems "
        "are not yet implemented and are reported as ``not configured``, so "
        "the overall status is ``degraded``. Later milestones replace these "
        "values with real checks."
    ),
)
async def readiness() -> ReadinessResponse:
    """Report per-system readiness for orchestrators and operators."""
    checks = {
        "database": "not configured",
        "storage": "not configured",
        "cache": "not configured",
        "models": "not configured",
    }
    overall = (
        HealthStatus.OK
        if all(value == "ok" for value in checks.values())
        else HealthStatus.DEGRADED
    )
    return ReadinessResponse(status=overall, checks=checks)

"""Meta router: liveness, readiness and operational metadata."""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter
from sqlalchemy import text

from app.api.deps import SettingsDep
from app.core.config import Settings
from app.core.db import get_database
from app.schemas.common import (
    HealthResponse,
    HealthStatus,
    ReadinessResponse,
)

logger = logging.getLogger(__name__)

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


def _database_status(settings: Settings) -> str:
    """Cheap database connectivity probe via the connection pool."""
    if not settings.database_url:
        return "not configured"
    try:
        # ``get_database`` reuses the shared cached engine/pool, so this probe
        # is one pooled round-trip, not a fresh connection.
        with get_database(settings).engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return "ok"
    except Exception:  # noqa: BLE001 - readiness must never raise
        logger.warning("Database readiness probe failed", exc_info=True)
        return "unavailable"


def _storage_status(settings: Settings) -> str:
    """Cheap storage writability probe (create+remove a temp marker)."""
    try:
        root = settings.storage_root
        root.mkdir(parents=True, exist_ok=True)
        marker = root / f".ready-{uuid.uuid4().hex}"
        marker.write_text("ok", encoding="utf-8")
        marker.unlink()
        return "ok"
    except Exception:  # noqa: BLE001 - readiness must never raise
        logger.warning("Storage readiness probe failed", exc_info=True)
        return "unavailable"


def readiness_response(settings: Settings) -> ReadinessResponse:
    """Assemble readiness for the currently configured systems.

    Cache is not yet deployed and models are in-process, so they report
    ``not configured`` (they are not required dependencies of this milestone).
    The database and object storage are probed live.
    """
    checks = {
        "database": _database_status(settings),
        "storage": _storage_status(settings),
        "cache": "not configured",
        "models": "not configured",
    }
    values = set(checks.values())
    if values == {"ok"}:
        status = HealthStatus.OK
    elif "unavailable" in values:
        status = HealthStatus.UNAVAILABLE
    else:
        status = HealthStatus.DEGRADED
    return ReadinessResponse(status=status, checks=checks)


@router.get(
    "/health/ready",
    response_model=ReadinessResponse,
    summary="Readiness probe",
    description=(
        "Reports per-system readiness for orchestrators and operators. The "
        "database and object storage are probed live; cache and models report "
        "``not configured`` until they are wired."
    ),
)
async def readiness(
    settings: SettingsDep,
) -> ReadinessResponse:
    """Report per-system readiness."""
    return readiness_response(settings)

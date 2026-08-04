"""FastAPI dependencies (dependency injection) and future extension points.

Shared dependencies resolved through ``Depends(...)`` live here. Backing
systems (database, storage, cache) and business services are intentionally not
implemented until their milestones; this module exposes clearly-named
placeholders that will be exchanged for real providers.
"""

from __future__ import annotations

from typing import Any

from app.core.config import Settings, get_settings
from app.core.logging import get_request_id


def get_settings_dependency() -> Settings:
    """Provide the shared application settings instance."""
    return get_settings()


def get_request_id_dependency() -> str:
    """Provide the request id bound to the current request context."""
    return get_request_id()


# ---------------------------------------------------------------------------
# Milestone extension points. These are wired once their backing systems are
# implemented; nothing in the foundation milestone consumes them.
# ---------------------------------------------------------------------------


def get_db_session() -> Any:
    """Provide a database session (database milestone)."""
    raise NotImplementedError(
        "Database sessions are not implemented until the database milestone."
    )


def get_object_storage() -> Any:
    """Provide the object-storage adapter (storage milestone)."""
    raise NotImplementedError(
        "Object storage is not implemented until the storage milestone."
    )


def get_cache() -> Any:
    """Provide the cache adapter (production hardening milestone)."""
    raise NotImplementedError(
        "Caching is not implemented until the hardening milestone."
    )


def get_job_service() -> Any:
    """Provide the background job service (analyses milestone)."""
    raise NotImplementedError(
        "The job service is not implemented until the analyses milestone."
    )


def get_analysis_service() -> Any:
    """Provide the analysis service (analyses milestone)."""
    raise NotImplementedError(
        "The analysis service is not implemented until the analyses milestone."
    )


def get_history_service() -> Any:
    """Provide the history service (history milestone)."""
    raise NotImplementedError(
        "The history service is not implemented until the history milestone."
    )

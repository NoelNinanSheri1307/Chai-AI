"""FastAPI dependencies (dependency injection).

Backing systems (database, object storage) and their repositories are provided
here for routers and services. Repositories are constructed with the plain
session they need; nothing in this module leaks HTTP concerns into the
repository layer.

Business services are intentionally not injected yet: they arrive with their
milestones and remain exposed as clearly-marked extension points.
"""

from __future__ import annotations

from collections.abc import Generator
from typing import Annotated, Any

from fastapi import Depends
from sqlmodel import Session

from app.clients.storage import StorageClient, create_storage_client
from app.core.config import Settings, get_settings
from app.core.db import get_session as _get_db_session
from app.core.logging import get_request_id
from app.repos.analysis_repo import AnalysisRepository
from app.repos.comparison_repo import ComparisonRepository
from app.repos.history_repo import HistoryRepository
from app.repos.job_repo import JobRepository
from app.repos.token_repo import TokenRepository
from app.repos.user_repo import UserRepository


def get_settings_dependency() -> Settings:
    """Provide the shared application settings instance."""
    return get_settings()


def get_request_id_dependency() -> str:
    """Provide the request id bound to the current request context."""
    return get_request_id()


def get_db_session(settings: SettingsDep) -> Generator[Session, None, None]:
    """Provide a transactional database session.

    Commits on success and rolls back on exception; the session is always
    closed when the request finishes.
    """
    yield from _get_db_session(settings)


def get_object_storage(settings: SettingsDep) -> StorageClient:
    """Provide the object-storage adapter for the active environment."""
    return create_storage_client(settings)


def get_user_repository(session: SessionDep) -> UserRepository:
    """Provide a :class:`UserRepository` bound to the request session."""
    return UserRepository(session)


def get_analysis_repository(session: SessionDep) -> AnalysisRepository:
    """Provide an :class:`AnalysisRepository` bound to the request session."""
    return AnalysisRepository(session)


def get_history_repository(session: SessionDep) -> HistoryRepository:
    """Provide a :class:`HistoryRepository` bound to the request session."""
    return HistoryRepository(session)


def get_comparison_repository(session: SessionDep) -> ComparisonRepository:
    """Provide a :class:`ComparisonRepository` bound to the request session."""
    return ComparisonRepository(session)


def get_job_repository(session: SessionDep) -> JobRepository:
    """Provide a :class:`JobRepository` bound to the request session."""
    return JobRepository(session)


def get_token_repository(session: SessionDep) -> TokenRepository:
    """Provide a :class:`TokenRepository` bound to the request session."""
    return TokenRepository(session)


# Common dependency aliases. They are declared after the functions they wrap so
# that ``Depends(...)`` resolves the callables at import time.
SettingsDep = Annotated[Settings, Depends(get_settings_dependency)]
SessionDep = Annotated[Session, Depends(get_db_session)]


# ---------------------------------------------------------------------------
# Future milestone extension points. These remain reserved until their backing
# systems arrive; nothing in the persistence milestone consumes them.
# ---------------------------------------------------------------------------


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

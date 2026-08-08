"""History repository: user-scoped analysis queries.

History reads are always scoped to one user, exclude soft-deleted rows by
default, and support verdict/risk/status filtering plus pagination. Soft
deletion and "clear history" are handled here because they mutate the same
analyses rows.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import update
from sqlmodel import Session

from app.core.enums import AnalysisStatus, RiskLevel, Verdict
from app.models.analysis import Analysis
from app.repos.analysis_repo import _analysis_graph_loads
from app.repos.base import BaseRepository, Page, PageParams


class HistoryRepository(BaseRepository[Analysis]):
    """Query builder for a user's history of :class:`Analysis` records."""

    model = Analysis

    def __init__(self, session: Session) -> None:
        super().__init__(session)

    def list_for_user(
        self,
        user_id: int,
        *,
        page: PageParams | None = None,
        verdict: Verdict | None = None,
        risk_level: RiskLevel | None = None,
        status: AnalysisStatus | None = None,
        include_deleted: bool = False,
    ) -> Page[Analysis]:
        """Return a paginated page of the user's analyses.

        Default ordering is recency (``created_at DESC``) unless ``page.sort``
        is provided. ``verdict``, ``risk_level`` and ``status`` optionally
        narrow the page to matching rows.
        """
        resolved_page = page or PageParams(sort="-created_at")
        filters: dict[str, Any] = {"user_id": user_id}
        if verdict is not None:
            filters["verdict"] = verdict
        if risk_level is not None:
            filters["risk_level"] = risk_level
        if status is not None:
            filters["status"] = status
        return self.list(
            page=resolved_page,
            filters=filters,
            include_deleted=include_deleted,
        )

    def get_for_user(
        self,
        user_id: int,
        public_id: str,
        *,
        include_deleted: bool = False,
        eager_child_graph: bool = False,
    ) -> Analysis | None:
        """Return one of the user's analyses by public id, or ``None``.

        ``eager_child_graph`` loads the analysis child graph in a bounded
        number of queries (avoiding N+1 on detail reads).
        """
        statement = self._base_select(include_deleted=include_deleted).where(
            Analysis.public_id == public_id,
            Analysis.user_id == user_id,
        )
        if eager_child_graph:
            statement = statement.options(*_analysis_graph_loads())
        return self.session.scalars(statement).first()

    def soft_delete_for_user(self, user_id: int, public_id: str) -> bool:
        """Soft-delete one of the user's analyses; returns success."""
        analysis = self.get_for_user(user_id, public_id)
        if analysis is None:
            return False
        return self.soft_delete(analysis)

    def clear_for_user(self, user_id: int) -> int:
        """Soft-delete every active analysis belonging to the user.

        Returns the number of rows stamped.
        """
        statement = (
            update(Analysis)
            .where(Analysis.user_id == user_id, Analysis.deleted_at.is_(None))
            .values(deleted_at=datetime.now(timezone.utc))
        )
        result = self.session.exec(statement)
        self.session.flush()
        return result.rowcount or 0

    def count_for_user(self, user_id: int) -> int:
        """Return the number of active analyses belonging to the user."""
        return self.count(filters={"user_id": user_id})

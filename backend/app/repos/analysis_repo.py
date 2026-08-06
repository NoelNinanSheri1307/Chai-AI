"""Analysis repository: analyses and their child records."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlmodel import Session

from app.models.analysis import Analysis, MetadataItem
from app.repos.base import BaseRepository, Page, PageParams


class AnalysisRepository(BaseRepository[Analysis]):
    """Persistence for :class:`Analysis` records.

    In addition to the generic surface, provides public-id lookups and
    user-scoped listing used by history and compare flows. Child entities are
    cascade-deleted with their parent analysis.
    """

    model = Analysis

    def __init__(self, session: Session) -> None:
        super().__init__(session)

    def get_by_public_id(
        self,
        public_id: str,
        *,
        include_deleted: bool = False,
    ) -> Analysis | None:
        """Return the analysis with the given public id, or ``None``."""
        statement = self._base_select(include_deleted=include_deleted).where(
            Analysis.public_id == public_id
        )
        return self.session.scalars(statement).first()

    def public_id_exists(
        self,
        public_id: str,
        *,
        include_deleted: bool = False,
    ) -> bool:
        """Return whether an analysis with the given public id exists."""
        return (
            self.get_by_public_id(public_id, include_deleted=include_deleted)
            is not None
        )

    def get_for_user(
        self,
        user_id: int | None,
        public_id: str,
        *,
        include_deleted: bool = False,
    ) -> Analysis | None:
        """Return an analysis scoped to a user, or ``None``.

        ``user_id`` of ``None`` addresses anonymous analyses (created without
        an authenticated owner).
        """
        statement = self._base_select(include_deleted=include_deleted).where(
            Analysis.public_id == public_id,
            Analysis.user_id == user_id,
        )
        return self.session.scalars(statement).first()

    def list_for_user(
        self,
        user_id: int,
        *,
        page: PageParams | None = None,
        filters: dict[str, Any] | None = None,
        include_deleted: bool = False,
    ) -> Page[Analysis]:
        """Return a paginated page of a user's analyses.

        ``filters`` are equality filters on analysis columns; the user scope is
        always applied. Default ordering is recency unless ``page.sort`` is set.
        """
        resolved_page = page or PageParams(sort="-created_at")
        return self.list(
            page=resolved_page,
            filters={"user_id": user_id, **(filters or {})},
            include_deleted=include_deleted,
        )

    # ------------------------------------------------------------------
    # MetadataItem helpers
    # ------------------------------------------------------------------
    def metadata_key_exists(self, analysis_id: int, key: str) -> bool:
        """Return whether an analysis already has a metadata item with ``key``.

        Uniqueness of (``analysis_id``, ``key``) is enforced by the
        application rather than the database, per the architecture spec.
        """
        statement = select(MetadataItem).where(
            MetadataItem.analysis_id == analysis_id,
            MetadataItem.key == key,
        )
        return self.session.scalars(statement).first() is not None

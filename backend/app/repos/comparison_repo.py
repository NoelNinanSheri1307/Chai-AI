"""Comparison repository: two-image comparison records."""

from __future__ import annotations

from sqlmodel import Session

from app.models.comparison import Comparison
from app.repos.base import BaseRepository, Page, PageParams


class ComparisonRepository(BaseRepository[Comparison]):
    """Persistence for :class:`Comparison` records.

    Child entities (findings, regions) are cascade-deleted with the parent
    comparison.
    """

    model = Comparison

    def __init__(self, session: Session) -> None:
        super().__init__(session)

    def get_by_public_id(
        self,
        public_id: str,
        *,
        include_deleted: bool = False,
    ) -> Comparison | None:
        """Return the comparison with the given public id, or ``None``."""
        statement = self._base_select(include_deleted=include_deleted).where(
            Comparison.public_id == public_id
        )
        return self.session.scalars(statement).first()

    def public_id_exists(
        self,
        public_id: str,
        *,
        include_deleted: bool = False,
    ) -> bool:
        """Return whether a comparison with the given public id exists."""
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
    ) -> Comparison | None:
        """Return a comparison scoped to a user, or ``None``."""
        statement = self._base_select(include_deleted=include_deleted).where(
            Comparison.public_id == public_id,
            Comparison.user_id == user_id,
        )
        return self.session.scalars(statement).first()

    def list_for_user(
        self,
        user_id: int,
        *,
        page: PageParams | None = None,
        include_deleted: bool = False,
    ) -> Page[Comparison]:
        """Return a paginated page of a user's comparisons."""
        resolved_page = page or PageParams(sort="-created_at")
        return self.list(
            page=resolved_page,
            filters={"user_id": user_id},
            include_deleted=include_deleted,
        )

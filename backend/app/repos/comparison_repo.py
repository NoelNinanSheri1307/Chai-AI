"""Comparison repository: two-image comparison records."""

from __future__ import annotations

from dataclasses import dataclass

from sqlmodel import Session

from app.models.comparison import Comparison, ComparisonFinding, ComparisonRegion
from app.repos.base import BaseRepository, Page, PageParams


@dataclass(frozen=True)
class FindingDraft:
    """A similarity/difference line to persist against a comparison."""

    is_similarity: bool
    text: str


@dataclass(frozen=True)
class RegionDraft:
    """A normalized shared manipulated region to persist against a comparison."""

    x: float
    y: float
    width: float
    height: float
    intensity: float
    label: str


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

    # ------------------------------------------------------------------
    # Comparison child persistence
    # ------------------------------------------------------------------
    def persist_children(
        self,
        comparison_id: int,
        *,
        findings: list[FindingDraft],
        regions: list[RegionDraft],
    ) -> None:
        """Persist the findings and regions belonging to a comparison.

        Findings carry a display ``position`` derived from list order; regions
        are stored as normalized rectangles. The caller owns the surrounding
        transaction; this method flushes but never commits.
        """
        for position, finding in enumerate(findings):
            self.session.add(
                ComparisonFinding(
                    comparison_id=comparison_id,
                    is_similarity=finding.is_similarity,
                    text=finding.text,
                    position=position,
                )
            )
        for region in regions:
            self.session.add(
                ComparisonRegion(
                    comparison_id=comparison_id,
                    x=region.x,
                    y=region.y,
                    width=region.width,
                    height=region.height,
                    intensity=region.intensity,
                    label=region.label,
                )
            )
        self.session.flush()

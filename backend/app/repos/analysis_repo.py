"""Analysis repository: analyses and their child records."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlmodel import Session

from app.core.enums import AnalysisStatus
from app.models.analysis import (
    Analysis,
    DetectedIndicator,
    Evidence,
    ForensicScore,
    Heatmap,
    HeatmapRegion,
    MetadataItem,
)
from app.pipeline.base import PipelineResult
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

    # ------------------------------------------------------------------
    # Pipeline result persistence
    # ------------------------------------------------------------------
    def persist_result(self, analysis: Analysis, result: PipelineResult) -> Analysis:
        """Write a pipeline result onto ``analysis`` and its child graph.

        Sets the verdict/confidence/risk/explanation/duration fields, marks the
        analysis completed, and persists the forensic scores, indicators,
        evidence, metadata items and heatmap (with regions). The caller owns the
        surrounding transaction; this method flushes but never commits.
        """
        analysis.verdict = result.verdict
        analysis.confidence = result.confidence
        analysis.risk_level = result.risk_level
        analysis.explanation = result.explanation
        analysis.duration_ms = result.duration_ms
        analysis.status = AnalysisStatus.COMPLETED

        for score in result.scores:
            self.session.add(
                ForensicScore(
                    analysis_id=analysis.id,
                    category=score.category,
                    value=score.value,
                )
            )
        for indicator in result.indicators:
            self.session.add(
                DetectedIndicator(
                    analysis_id=analysis.id,
                    indicator_type=indicator.type,
                    confidence=indicator.confidence,
                    severity=indicator.severity,
                    description=indicator.description,
                )
            )
        for position, line in enumerate(result.evidence):
            self.session.add(
                Evidence(analysis_id=analysis.id, text=line, position=position)
            )
        for key, value in result.metadata.items():
            self.session.add(
                MetadataItem(analysis_id=analysis.id, key=key, value=value)
            )
        if result.heatmap is not None:
            heatmap = Heatmap(
                analysis_id=analysis.id,
                overall_manipulation=result.heatmap.overall_manipulation,
            )
            self.session.add(heatmap)
            for region in result.heatmap.regions:
                self.session.add(
                    HeatmapRegion(
                        heatmap_id=heatmap.id,
                        x=region.x,
                        y=region.y,
                        width=region.width,
                        height=region.height,
                        intensity=region.intensity,
                        label=region.label,
                    )
                )
        self.session.flush()
        return analysis

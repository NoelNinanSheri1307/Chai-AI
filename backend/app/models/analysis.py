"""Analysis persistence entities.

``Analysis`` is the core forensic record: one analyzed image, its verdict and
lifecycle. The child entities (``ForensicScore``, ``DetectedIndicator``,
``Evidence``, ``MetadataItem``, ``Heatmap``, ``HeatmapRegion``) are cascade
children that are hard-deleted with the parent analysis.
"""

from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, Index, text
from sqlmodel import Field, Relationship

from app.core import constants
from app.core.enums import (
    AnalysisStatus,
    IndicatorSeverity,
    IndicatorType,
    RiskLevel,
    ScoreCategory,
    Verdict,
)
from app.models.base import (
    CreatedAtMixin,
    SoftDeleteMixin,
    TimestampMixin,
    enum_column,
    soft_delete_index,
)

if TYPE_CHECKING:
    from app.models.comparison import Comparison
    from app.models.job import Job
    from app.models.user import User


class Analysis(TimestampMixin, SoftDeleteMixin, table=True):
    """One analyzed image together with its verdict and lifecycle state."""

    __tablename__ = "analyses"
    __table_args__ = (
        # History reads sort a user's analyses by recency.
        Index("ix_analyses_user_id_created_at", "user_id", text("created_at DESC")),
        # Worker scanning for queued/running jobs.
        Index("ix_analyses_status", "status"),
        soft_delete_index("analyses"),
        CheckConstraint(
            "confidence >= 0 AND confidence <= 1",
            name="ck_analyses_confidence",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    public_id: str = Field(
        index=True,
        unique=True,
        nullable=False,
        max_length=constants.PUBLIC_ID_MAX_LENGTH,
    )
    user_id: int | None = Field(
        default=None,
        foreign_key="users.id",
        ondelete="SET NULL",
        index=True,
        nullable=True,
    )
    original_key: str = Field(
        nullable=False,
        max_length=constants.RESOURCE_ID_MAX_LENGTH,
    )
    file_name: str | None = Field(
        default=None,
        nullable=True,
        max_length=constants.IMAGE_FILENAME_MAX_LENGTH,
    )
    mime_type: str | None = Field(
        default=None,
        nullable=True,
        max_length=constants.IMAGE_MIME_MAX_LENGTH,
    )
    verdict: Verdict | None = Field(
        default=None,
        sa_column=enum_column(Verdict, nullable=True),
    )
    confidence: float | None = Field(default=None, nullable=True)
    risk_level: RiskLevel | None = Field(
        default=None,
        sa_column=enum_column(RiskLevel, nullable=True),
    )
    explanation: str | None = Field(default=None, nullable=True)
    duration_ms: int | None = Field(default=None, nullable=True)
    status: AnalysisStatus = Field(
        default=AnalysisStatus.RUNNING,
        sa_column=enum_column(
            AnalysisStatus,
            nullable=False,
            server_default=AnalysisStatus.RUNNING.value,
        ),
    )

    # Forensic report snapshot ------------------------------------------
    # The three-class classification support scores in the fixed order
    # (original, ai_edited, ai_generated), the runner-up verdict and the
    # classification margin. Persisted so reports are reconstructable from the
    # stored analysis without ever re-running fusion.
    hypothesis_original: float | None = Field(default=None, nullable=True)
    hypothesis_edited: float | None = Field(default=None, nullable=True)
    hypothesis_generated: float | None = Field(default=None, nullable=True)
    runner_up_verdict: Verdict | None = Field(
        default=None,
        sa_column=enum_column(Verdict, nullable=True),
    )
    classification_margin: float | None = Field(default=None, nullable=True)

    # Relationships
    user: Optional["User"] = Relationship(back_populates="analyses")
    forensic_scores: list["ForensicScore"] = Relationship(
        back_populates="analysis",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    detected_indicators: list["DetectedIndicator"] = Relationship(
        back_populates="analysis",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    evidence: list["Evidence"] = Relationship(
        back_populates="analysis",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    metadata_items: list["MetadataItem"] = Relationship(
        back_populates="analysis",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    heatmap: Optional["Heatmap"] = Relationship(
        back_populates="analysis",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    analysis_contributions: list["AnalysisContribution"] = Relationship(
        back_populates="analysis",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    jobs: list["Job"] = Relationship(
        back_populates="analysis",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    comparison_a: Optional["Comparison"] = Relationship(
        back_populates="analysis_a",
        sa_relationship_kwargs={"foreign_keys": "Comparison.analysis_a_id"},
    )
    comparison_b: Optional["Comparison"] = Relationship(
        back_populates="analysis_b",
        sa_relationship_kwargs={"foreign_keys": "Comparison.analysis_b_id"},
    )


class ForensicScore(CreatedAtMixin, table=True):
    """Per-category confidence breakdown of an analysis result."""

    __tablename__ = "forensic_scores"
    __table_args__ = (
        CheckConstraint(
            "value >= 0 AND value <= 1",
            name="ck_forensic_scores_value",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    analysis_id: int = Field(
        foreign_key="analyses.id",
        ondelete="CASCADE",
        index=True,
        nullable=False,
    )
    category: ScoreCategory = Field(
        sa_column=enum_column(ScoreCategory, nullable=False),
    )
    value: float = Field(nullable=False)

    analysis: "Analysis" = Relationship(back_populates="forensic_scores")


class DetectedIndicator(CreatedAtMixin, table=True):
    """A discrete manipulation signal found by the pipeline."""

    __tablename__ = "detected_indicators"
    __table_args__ = (
        CheckConstraint(
            "confidence >= 0 AND confidence <= 1",
            name="ck_detected_indicators_confidence",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    analysis_id: int = Field(
        foreign_key="analyses.id",
        ondelete="CASCADE",
        index=True,
        nullable=False,
    )
    indicator_type: IndicatorType = Field(
        sa_column=enum_column(IndicatorType, nullable=False),
    )
    confidence: float = Field(nullable=False)
    severity: IndicatorSeverity = Field(
        sa_column=enum_column(IndicatorSeverity, nullable=False),
    )
    description: str = Field(nullable=False)

    analysis: "Analysis" = Relationship(back_populates="detected_indicators")


class Evidence(CreatedAtMixin, table=True):
    """A free-text forensic evidence line in display order."""

    __tablename__ = "evidence"
    __table_args__ = (
        Index("ix_evidence_analysis_id_position", "analysis_id", "position"),
    )

    id: int | None = Field(default=None, primary_key=True)
    analysis_id: int = Field(
        foreign_key="analyses.id",
        ondelete="CASCADE",
        nullable=False,
    )
    text: str = Field(nullable=False)
    position: int = Field(nullable=False)

    analysis: "Analysis" = Relationship(back_populates="evidence")


class MetadataItem(CreatedAtMixin, table=True):
    """A key/value snapshot of the image metadata.

    The (``analysis_id``, ``key``) pair is unique; uniqueness is enforced in
    the repository layer rather than by the database, per the architecture
    specification.
    """

    __tablename__ = "metadata_items"

    id: int | None = Field(default=None, primary_key=True)
    analysis_id: int = Field(
        foreign_key="analyses.id",
        ondelete="CASCADE",
        index=True,
        nullable=False,
    )
    key: str = Field(nullable=False, max_length=100)
    value: str = Field(nullable=False)

    analysis: "Analysis" = Relationship(back_populates="metadata_items")


class Heatmap(CreatedAtMixin, table=True):
    """Aggregate manipulation heatmap for an analysis (at most one)."""

    __tablename__ = "heatmaps"
    __table_args__ = (
        CheckConstraint(
            "overall_manipulation >= 0 AND overall_manipulation <= 1",
            name="ck_heatmaps_overall_manipulation",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    analysis_id: int = Field(
        foreign_key="analyses.id",
        ondelete="CASCADE",
        unique=True,
        index=True,
        nullable=False,
    )
    overall_manipulation: float = Field(nullable=False)

    analysis: "Analysis" = Relationship(back_populates="heatmap")
    regions: list["HeatmapRegion"] = Relationship(
        back_populates="heatmap",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class HeatmapRegion(CreatedAtMixin, table=True):
    """A normalized manipulation rectangle within a heatmap."""

    __tablename__ = "heatmap_regions"
    __table_args__ = (
        CheckConstraint(
            "x >= 0 AND x <= 1"
            " AND y >= 0 AND y <= 1"
            " AND width >= 0 AND width <= 1"
            " AND height >= 0 AND height <= 1",
            name="ck_heatmap_regions_coordinates",
        ),
        CheckConstraint(
            "intensity >= 0 AND intensity <= 1",
            name="ck_heatmap_regions_intensity",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    heatmap_id: int = Field(
        foreign_key="heatmaps.id",
        ondelete="CASCADE",
        index=True,
        nullable=False,
    )
    x: float = Field(nullable=False)
    y: float = Field(nullable=False)
    width: float = Field(nullable=False)
    height: float = Field(nullable=False)
    intensity: float = Field(nullable=False)
    label: str = Field(
        nullable=False, max_length=constants.HEATMAP_REGION_LABEL_MAX_LENGTH
    )

    heatmap: "Heatmap" = Relationship(back_populates="regions")


class AnalysisContribution(CreatedAtMixin, table=True):
    """A per-detector contribution snapshot recorded for the forensic report.

    One row per active detector, in rank order. It mirrors the fused
    ``DetectorContribution`` so the report layer can reconstruct the full
    breakdown (normalized score, self-confidence, reliability weight, evidence
    share, direction and per-hypothesis support) from the stored analysis.
    """

    __tablename__ = "analysis_contributions"
    __table_args__ = (
        Index("ix_analysis_contributions_analysis_id", "analysis_id"),
        CheckConstraint(
            "normalized_score >= 0 AND normalized_score <= 1",
            name="ck_analysis_contributions_normalized_score",
        ),
        CheckConstraint(
            "detector_confidence >= 0 AND detector_confidence <= 1",
            name="ck_analysis_contributions_detector_confidence",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    analysis_id: int = Field(
        foreign_key="analyses.id",
        ondelete="CASCADE",
        nullable=False,
    )
    position: int = Field(nullable=False)
    detector: str = Field(nullable=False, max_length=100)
    detector_version: str = Field(nullable=False, max_length=50)
    category: str = Field(nullable=False, max_length=50)
    normalized_score: float = Field(nullable=False)
    detector_confidence: float = Field(nullable=False)
    reliability: float = Field(nullable=False)
    weight_share: float = Field(nullable=False)
    contribution: float = Field(nullable=False)
    direction: str = Field(nullable=False, max_length=50)
    hypothesis_original: float = Field(nullable=False)
    hypothesis_edited: float = Field(nullable=False)
    hypothesis_generated: float = Field(nullable=False)
    preferred_hypothesis: str = Field(nullable=False, max_length=50)
    processing_time_ms: int = Field(default=0, nullable=False)

    analysis: "Analysis" = Relationship(back_populates="analysis_contributions")

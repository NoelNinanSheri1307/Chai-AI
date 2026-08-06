"""Comparison persistence entities.

``Comparison`` records a two-image comparison result. The child entities
(``ComparisonFinding``, ``ComparisonRegion``) are cascade children that are
hard-deleted with the parent comparison.
"""

from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, Index, text
from sqlmodel import Field, Relationship

from app.core import constants
from app.models.base import (
    CreatedAtMixin,
    SoftDeleteMixin,
    TimestampMixin,
    soft_delete_index,
)

if TYPE_CHECKING:
    from app.models.analysis import Analysis
    from app.models.user import User


class Comparison(TimestampMixin, SoftDeleteMixin, table=True):
    """A two-image comparison record owned by a user."""

    __tablename__ = "comparisons"
    __table_args__ = (
        # History-style reads sort a user's comparisons by recency.
        Index("ix_comparisons_user_id_created_at", "user_id", text("created_at DESC")),
        soft_delete_index("comparisons"),
        CheckConstraint(
            "similarity >= 0 AND similarity <= 1",
            name="ck_comparisons_similarity",
        ),
        CheckConstraint(
            "ai_probability >= 0 AND ai_probability <= 1",
            name="ck_comparisons_ai_probability",
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
    analysis_a_id: int = Field(
        foreign_key="analyses.id",
        ondelete="RESTRICT",
        index=True,
        nullable=False,
    )
    analysis_b_id: int = Field(
        foreign_key="analyses.id",
        ondelete="RESTRICT",
        index=True,
        nullable=False,
    )
    similarity: float = Field(nullable=False)
    ai_probability: float = Field(nullable=False)
    label_a: str = Field(nullable=False, max_length=50)
    label_b: str = Field(nullable=False, max_length=50)

    # Relationships
    user: Optional["User"] = Relationship(back_populates="comparisons")
    analysis_a: "Analysis" = Relationship(
        back_populates="comparison_a",
        sa_relationship_kwargs={"foreign_keys": "Comparison.analysis_a_id"},
    )
    analysis_b: "Analysis" = Relationship(
        back_populates="comparison_b",
        sa_relationship_kwargs={"foreign_keys": "Comparison.analysis_b_id"},
    )
    findings: list["ComparisonFinding"] = Relationship(
        back_populates="comparison",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    regions: list["ComparisonRegion"] = Relationship(
        back_populates="comparison",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class ComparisonFinding(CreatedAtMixin, table=True):
    """A similarity or difference line in display order."""

    __tablename__ = "comparison_findings"
    __table_args__ = (
        Index(
            "ix_comparison_findings_comparison_id_position",
            "comparison_id",
            "position",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    comparison_id: int = Field(
        foreign_key="comparisons.id",
        ondelete="CASCADE",
        nullable=False,
    )
    is_similarity: bool = Field(nullable=False)
    text: str = Field(nullable=False)
    position: int = Field(nullable=False)

    comparison: "Comparison" = Relationship(back_populates="findings")


class ComparisonRegion(CreatedAtMixin, table=True):
    """A normalized shared manipulated region between two images."""

    __tablename__ = "comparison_regions"
    __table_args__ = (
        CheckConstraint(
            "x >= 0 AND x <= 1"
            " AND y >= 0 AND y <= 1"
            " AND width >= 0 AND width <= 1"
            " AND height >= 0 AND height <= 1",
            name="ck_comparison_regions_coordinates",
        ),
        CheckConstraint(
            "intensity >= 0 AND intensity <= 1",
            name="ck_comparison_regions_intensity",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    comparison_id: int = Field(
        foreign_key="comparisons.id",
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

    comparison: "Comparison" = Relationship(back_populates="regions")

"""initial schema

Creates every table defined by the Chai AI architecture specification (Section
8): users, analyses and their forensic children, heatmaps, comparisons and
their children, jobs, and refresh tokens — together with all enums, foreign
keys, constraints and indexes.

Revision ID: 0001
Revises:
Create Date: 2026-08-05

The migration is dialect-portable: enum columns are VARCHAR + ORM validation
(``native_enum=False``), timestamps use ``sa.func.now()``, and partial indexes
carry both SQLite and PostgreSQL ``WHERE`` clauses.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op
from app.core.enums import (
    AnalysisStatus,
    IndicatorSeverity,
    IndicatorType,
    JobStatus,
    JobType,
    RiskLevel,
    ScoreCategory,
    Verdict,
)
from app.models.base import enum_values

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _enum(enum_cls: type) -> sa.Enum:
    """Portable VARCHAR-backed enum column type storing enum ``.value`` strings."""
    return sa.Enum(
        enum_cls,
        native_enum=False,
        length=100,
        values_callable=enum_values,
        validate_strings=True,
    )


def _active_index(table: str) -> None:
    """Create the partial ``deleted_at`` index over active rows."""
    predicate = sa.text("deleted_at IS NULL")
    op.create_index(
        f"ix_{table}_active",
        table,
        ["deleted_at"],
        unique=False,
        postgresql_where=predicate,
        sqlite_where=predicate,
    )


def upgrade() -> None:
    # --- users ---------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=100), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("length(email) <= 254", name="ck_users_email_length"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    _active_index("users")

    # --- analyses ------------------------------------------------------
    op.create_table(
        "analyses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("public_id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("original_key", sa.String(length=255), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=True),
        sa.Column("mime_type", sa.String(length=50), nullable=True),
        sa.Column("verdict", _enum(Verdict), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("risk_level", _enum(RiskLevel), nullable=True),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column(
            "status",
            _enum(AnalysisStatus),
            nullable=False,
            server_default=sa.text("'running'"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.CheckConstraint(
            "confidence >= 0 AND confidence <= 1", name="ck_analyses_confidence"
        ),
    )
    op.create_index("ix_analyses_public_id", "analyses", ["public_id"], unique=True)
    op.create_index("ix_analyses_user_id", "analyses", ["user_id"], unique=False)
    op.create_index(
        "ix_analyses_user_id_created_at",
        "analyses",
        ["user_id", sa.text("created_at DESC")],
        unique=False,
    )
    op.create_index("ix_analyses_status", "analyses", ["status"], unique=False)
    _active_index("analyses")

    # --- forensic_scores ------------------------------------------------
    op.create_table(
        "forensic_scores",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("analysis_id", sa.Integer(), nullable=False),
        sa.Column("category", _enum(ScoreCategory), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["analysis_id"], ["analyses.id"], ondelete="CASCADE"),
        sa.CheckConstraint(
            "value >= 0 AND value <= 1", name="ck_forensic_scores_value"
        ),
    )
    op.create_index(
        "ix_forensic_scores_analysis_id",
        "forensic_scores",
        ["analysis_id"],
        unique=False,
    )

    # --- detected_indicators --------------------------------------------
    op.create_table(
        "detected_indicators",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("analysis_id", sa.Integer(), nullable=False),
        sa.Column("indicator_type", _enum(IndicatorType), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("severity", _enum(IndicatorSeverity), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["analysis_id"], ["analyses.id"], ondelete="CASCADE"),
        sa.CheckConstraint(
            "confidence >= 0 AND confidence <= 1",
            name="ck_detected_indicators_confidence",
        ),
    )
    op.create_index(
        "ix_detected_indicators_analysis_id",
        "detected_indicators",
        ["analysis_id"],
        unique=False,
    )

    # --- evidence -------------------------------------------------------
    op.create_table(
        "evidence",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("analysis_id", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["analysis_id"], ["analyses.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_evidence_analysis_id_position",
        "evidence",
        ["analysis_id", "position"],
        unique=False,
    )

    # --- metadata_items -------------------------------------------------
    op.create_table(
        "metadata_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("analysis_id", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(length=100), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["analysis_id"], ["analyses.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_metadata_items_analysis_id", "metadata_items", ["analysis_id"], unique=False
    )

    # --- heatmaps -------------------------------------------------------
    op.create_table(
        "heatmaps",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("analysis_id", sa.Integer(), nullable=False),
        sa.Column("overall_manipulation", sa.Float(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["analysis_id"], ["analyses.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("analysis_id", name="uq_heatmaps_analysis_id"),
        sa.CheckConstraint(
            "overall_manipulation >= 0 AND overall_manipulation <= 1",
            name="ck_heatmaps_overall_manipulation",
        ),
    )
    op.create_index("ix_heatmaps_analysis_id", "heatmaps", ["analysis_id"], unique=True)

    # --- heatmap_regions -------------------------------------------------
    op.create_table(
        "heatmap_regions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("heatmap_id", sa.Integer(), nullable=False),
        sa.Column("x", sa.Float(), nullable=False),
        sa.Column("y", sa.Float(), nullable=False),
        sa.Column("width", sa.Float(), nullable=False),
        sa.Column("height", sa.Float(), nullable=False),
        sa.Column("intensity", sa.Float(), nullable=False),
        sa.Column("label", sa.String(length=100), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["heatmap_id"], ["heatmaps.id"], ondelete="CASCADE"),
        sa.CheckConstraint(
            "x >= 0 AND x <= 1 AND y >= 0 AND y <= 1"
            " AND width >= 0 AND width <= 1 AND height >= 0 AND height <= 1",
            name="ck_heatmap_regions_coordinates",
        ),
        sa.CheckConstraint(
            "intensity >= 0 AND intensity <= 1", name="ck_heatmap_regions_intensity"
        ),
    )
    op.create_index(
        "ix_heatmap_regions_heatmap_id", "heatmap_regions", ["heatmap_id"], unique=False
    )

    # --- jobs -----------------------------------------------------------
    op.create_table(
        "jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("analysis_id", sa.Integer(), nullable=False),
        sa.Column("job_type", _enum(JobType), nullable=False),
        sa.Column(
            "status",
            _enum(JobStatus),
            nullable=False,
            server_default=sa.text("'queued'"),
        ),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("max_attempts", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["analysis_id"], ["analyses.id"], ondelete="CASCADE"),
        sa.CheckConstraint(
            "attempts >= 0 AND attempts <= max_attempts", name="ck_jobs_attempts"
        ),
    )
    op.create_index("ix_jobs_analysis_id", "jobs", ["analysis_id"], unique=False)
    op.create_index(
        "ix_jobs_status_created_at", "jobs", ["status", "created_at"], unique=False
    )

    # --- refresh_tokens -------------------------------------------------
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("replaced_by_hash", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"], unique=True
    )
    op.create_index(
        "ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"], unique=False
    )
    op.create_index(
        "ix_refresh_tokens_user_id_revoked_at",
        "refresh_tokens",
        ["user_id", "revoked_at"],
        unique=False,
    )

    # --- comparisons ----------------------------------------------------
    op.create_table(
        "comparisons",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("public_id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("analysis_a_id", sa.Integer(), nullable=False),
        sa.Column("analysis_b_id", sa.Integer(), nullable=False),
        sa.Column("similarity", sa.Float(), nullable=False),
        sa.Column("ai_probability", sa.Float(), nullable=False),
        sa.Column("label_a", sa.String(length=50), nullable=False),
        sa.Column("label_b", sa.String(length=50), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["analysis_a_id"], ["analyses.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["analysis_b_id"], ["analyses.id"], ondelete="RESTRICT"
        ),
        sa.CheckConstraint(
            "similarity >= 0 AND similarity <= 1", name="ck_comparisons_similarity"
        ),
        sa.CheckConstraint(
            "ai_probability >= 0 AND ai_probability <= 1",
            name="ck_comparisons_ai_probability",
        ),
    )
    op.create_index(
        "ix_comparisons_public_id", "comparisons", ["public_id"], unique=True
    )
    op.create_index("ix_comparisons_user_id", "comparisons", ["user_id"], unique=False)
    op.create_index(
        "ix_comparisons_analysis_a_id", "comparisons", ["analysis_a_id"], unique=False
    )
    op.create_index(
        "ix_comparisons_analysis_b_id", "comparisons", ["analysis_b_id"], unique=False
    )
    op.create_index(
        "ix_comparisons_user_id_created_at",
        "comparisons",
        ["user_id", sa.text("created_at DESC")],
        unique=False,
    )
    _active_index("comparisons")

    # --- comparison_findings ---------------------------------------------
    op.create_table(
        "comparison_findings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("comparison_id", sa.Integer(), nullable=False),
        sa.Column("is_similarity", sa.Boolean(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["comparison_id"], ["comparisons.id"], ondelete="CASCADE"
        ),
    )
    op.create_index(
        "ix_comparison_findings_comparison_id_position",
        "comparison_findings",
        ["comparison_id", "position"],
        unique=False,
    )

    # --- comparison_regions ----------------------------------------------
    op.create_table(
        "comparison_regions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("comparison_id", sa.Integer(), nullable=False),
        sa.Column("x", sa.Float(), nullable=False),
        sa.Column("y", sa.Float(), nullable=False),
        sa.Column("width", sa.Float(), nullable=False),
        sa.Column("height", sa.Float(), nullable=False),
        sa.Column("intensity", sa.Float(), nullable=False),
        sa.Column("label", sa.String(length=100), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["comparison_id"], ["comparisons.id"], ondelete="CASCADE"
        ),
        sa.CheckConstraint(
            "x >= 0 AND x <= 1 AND y >= 0 AND y <= 1"
            " AND width >= 0 AND width <= 1 AND height >= 0 AND height <= 1",
            name="ck_comparison_regions_coordinates",
        ),
        sa.CheckConstraint(
            "intensity >= 0 AND intensity <= 1", name="ck_comparison_regions_intensity"
        ),
    )
    op.create_index(
        "ix_comparison_regions_comparison_id",
        "comparison_regions",
        ["comparison_id"],
        unique=False,
    )


def downgrade() -> None:
    """Drop every table in reverse dependency order."""
    op.drop_table("comparison_regions")
    op.drop_table("comparison_findings")
    op.drop_table("comparisons")
    op.drop_table("refresh_tokens")
    op.drop_table("jobs")
    op.drop_table("heatmap_regions")
    op.drop_table("heatmaps")
    op.drop_table("metadata_items")
    op.drop_table("evidence")
    op.drop_table("detected_indicators")
    op.drop_table("forensic_scores")
    op.drop_table("analyses")
    op.drop_table("users")

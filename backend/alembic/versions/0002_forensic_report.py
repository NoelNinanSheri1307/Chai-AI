"""forensic report snapshot schema

Adds the fields the report layer needs to reconstruct a full forensic report
from a stored analysis without ever re-running fusion:

* ``analyses`` — the three-class hypothesis support scores, the runner-up
  verdict and the classification margin (all nullable; older rows remain
  valid and reports degrade gracefully).
* ``analysis_contributions`` — one row per active detector recording its
  normalized score, self-confidence, reliability weight, evidence share,
  direction, per-hypothesis support and processing time.

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-08
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op
from app.core.enums import Verdict
from app.models.base import enum_values

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: str | None = "0001"
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


def upgrade() -> None:
    # --- analyses: report snapshot columns ------------------------------
    with op.batch_alter_table("analyses") as batch_op:
        batch_op.add_column(sa.Column("hypothesis_original", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("hypothesis_edited", sa.Float(), nullable=True))
        batch_op.add_column(
            sa.Column("hypothesis_generated", sa.Float(), nullable=True)
        )
        batch_op.add_column(
            sa.Column("runner_up_verdict", _enum(Verdict), nullable=True)
        )
        batch_op.add_column(
            sa.Column("classification_margin", sa.Float(), nullable=True)
        )

    # --- analysis_contributions -----------------------------------------
    op.create_table(
        "analysis_contributions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("analysis_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("detector", sa.String(length=100), nullable=False),
        sa.Column("detector_version", sa.String(length=50), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("normalized_score", sa.Float(), nullable=False),
        sa.Column("detector_confidence", sa.Float(), nullable=False),
        sa.Column("reliability", sa.Float(), nullable=False),
        sa.Column("weight_share", sa.Float(), nullable=False),
        sa.Column("contribution", sa.Float(), nullable=False),
        sa.Column("direction", sa.String(length=50), nullable=False),
        sa.Column("hypothesis_original", sa.Float(), nullable=False),
        sa.Column("hypothesis_edited", sa.Float(), nullable=False),
        sa.Column("hypothesis_generated", sa.Float(), nullable=False),
        sa.Column("preferred_hypothesis", sa.String(length=50), nullable=False),
        sa.Column("processing_time_ms", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["analysis_id"], ["analyses.id"], ondelete="CASCADE"),
        sa.CheckConstraint(
            "normalized_score >= 0 AND normalized_score <= 1",
            name="ck_analysis_contributions_normalized_score",
        ),
        sa.CheckConstraint(
            "detector_confidence >= 0 AND detector_confidence <= 1",
            name="ck_analysis_contributions_detector_confidence",
        ),
    )
    op.create_index(
        "ix_analysis_contributions_analysis_id",
        "analysis_contributions",
        ["analysis_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_analysis_contributions_analysis_id",
        table_name="analysis_contributions",
    )
    op.drop_table("analysis_contributions")
    with op.batch_alter_table("analyses") as batch_op:
        batch_op.drop_column("classification_margin")
        batch_op.drop_column("runner_up_verdict")
        batch_op.drop_column("hypothesis_generated")
        batch_op.drop_column("hypothesis_edited")
        batch_op.drop_column("hypothesis_original")

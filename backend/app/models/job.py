"""Background job persistence entity.

Records the lifecycle of a background job (queued, running, succeeded,
failed) including its retry budget. Jobs are not soft-deleted.
"""

from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Index
from sqlmodel import Field, Relationship

from app.core.enums import JobStatus, JobType
from app.models.base import TimestampMixin, enum_column

if TYPE_CHECKING:
    from app.models.analysis import Analysis


class Job(TimestampMixin, table=True):
    """A background job lifecycle record tied to an analysis."""

    __tablename__ = "jobs"
    __table_args__ = (
        # Worker scanning for the next job to claim.
        Index("ix_jobs_status_created_at", "status", "created_at"),
        CheckConstraint(
            "attempts >= 0 AND attempts <= max_attempts",
            name="ck_jobs_attempts",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    analysis_id: int = Field(
        foreign_key="analyses.id",
        ondelete="CASCADE",
        index=True,
        nullable=False,
    )
    job_type: JobType = Field(
        sa_column=enum_column(JobType, nullable=False),
    )
    status: JobStatus = Field(
        default=JobStatus.QUEUED,
        sa_column=enum_column(
            JobStatus,
            nullable=False,
            server_default=JobStatus.QUEUED.value,
        ),
    )
    attempts: int = Field(default=0, nullable=False)
    max_attempts: int = Field(default=3, nullable=False)

    analysis: "Analysis" = Relationship(back_populates="jobs")

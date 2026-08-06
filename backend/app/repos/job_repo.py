"""Job repository: queued, running and retried background jobs."""

from __future__ import annotations

from sqlmodel import Session

from app.core import constants
from app.core.enums import JobStatus
from app.models.job import Job
from app.repos.base import BaseRepository


class JobRepository(BaseRepository[Job]):
    """Persistence for :class:`Job` lifecycle records."""

    model = Job

    def __init__(self, session: Session) -> None:
        super().__init__(session)

    def list_for_analysis(self, analysis_id: int) -> list[Job]:
        """Return every job scheduled for an analysis (oldest first)."""
        statement = self._base_select().where(Job.analysis_id == analysis_id)
        return list(self.session.scalars(statement).all())

    def latest_for_analysis(self, analysis_id: int) -> Job | None:
        """Return the most recently created job for an analysis, or ``None``."""
        statement = (
            self._base_select()
            .where(Job.analysis_id == analysis_id)
            .order_by(Job.created_at.desc())
        )
        return self.session.scalars(statement).first()

    def list_queued(self, *, limit: int = constants.DEFAULT_PAGE_SIZE) -> list[Job]:
        """Return the oldest queued jobs for worker claiming."""
        statement = (
            self._base_select()
            .where(Job.status == JobStatus.QUEUED)
            .order_by(Job.created_at.asc())
            .limit(limit)
        )
        return list(self.session.scalars(statement).all())

    def list_by_status(self, status: JobStatus, *, limit: int) -> list[Job]:
        """Return jobs in the given status (oldest first)."""
        statement = (
            self._base_select()
            .where(Job.status == status)
            .order_by(Job.created_at.asc())
            .limit(limit)
        )
        return list(self.session.scalars(statement).all())

    def increment_attempts(self, job: Job) -> Job:
        """Bump the retry counter on a job and return it."""
        job.attempts += 1
        self.session.flush()
        return job

    def set_status(self, job: Job, status: JobStatus) -> Job:
        """Set a job's status and return it."""
        job.status = status
        self.session.flush()
        return job

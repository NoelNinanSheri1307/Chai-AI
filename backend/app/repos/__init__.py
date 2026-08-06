"""Data-access (repository) layer.

Repositories are the only modules that query and write to the database. They
are persistence-only: they accept a SQLModel :class:`Session`, return ORM
entities, and contain no HTTP, FastAPI or business-logic knowledge. Services
and pipelines depend on them.
"""

from app.repos.analysis_repo import AnalysisRepository
from app.repos.base import BaseRepository, Page, PageParams
from app.repos.comparison_repo import ComparisonRepository
from app.repos.history_repo import HistoryRepository
from app.repos.job_repo import JobRepository
from app.repos.token_repo import TokenRepository
from app.repos.user_repo import UserRepository

__all__ = [
    "AnalysisRepository",
    "BaseRepository",
    "ComparisonRepository",
    "HistoryRepository",
    "JobRepository",
    "Page",
    "PageParams",
    "TokenRepository",
    "UserRepository",
]

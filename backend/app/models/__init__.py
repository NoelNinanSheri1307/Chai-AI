"""ORM entity models.

Importing this package registers every table model on the shared SQLModel
metadata so that Alembic migrations and ``create_all`` (tests only) see the
complete schema. Models carry persistence logic only; no business logic.
"""

from app.models.analysis import (
    Analysis,
    DetectedIndicator,
    Evidence,
    ForensicScore,
    Heatmap,
    HeatmapRegion,
    MetadataItem,
)
from app.models.comparison import (
    Comparison,
    ComparisonFinding,
    ComparisonRegion,
)
from app.models.job import Job
from app.models.refresh_token import RefreshToken
from app.models.user import User

__all__ = [
    "Analysis",
    "Comparison",
    "ComparisonFinding",
    "ComparisonRegion",
    "DetectedIndicator",
    "Evidence",
    "ForensicScore",
    "Heatmap",
    "HeatmapRegion",
    "Job",
    "MetadataItem",
    "RefreshToken",
    "User",
]

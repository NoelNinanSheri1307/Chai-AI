"""Business services (use-case) layer.

Services orchestrate repositories, the pipeline and external clients on behalf
of HTTP handlers. They return DTOs only — ORM entities never leave this layer —
and they never touch HTTP or FastAPI objects. The analysis, history, comparison
and report services are delivered by the application-core milestone; the auth
and job services remain reserved extension points for their milestones.
"""

from app.services.analysis_service import AnalysisService
from app.services.compare_service import ComparisonService
from app.services.history_service import HistoryService
from app.services.mappers import (
    analysis_to_history_item,
    analysis_to_result_dto,
    comparison_to_result_dto,
    verdict_label,
)
from app.services.report_service import ReportService

__all__ = [
    "AnalysisService",
    "ComparisonService",
    "HistoryService",
    "ReportService",
    "analysis_to_history_item",
    "analysis_to_result_dto",
    "comparison_to_result_dto",
    "verdict_label",
]

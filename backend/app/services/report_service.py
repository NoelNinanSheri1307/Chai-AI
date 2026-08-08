"""Report service: deterministic forensic report construction.

``ReportService`` is responsible for report construction. It loads a stored
analysis and builds the typed :class:`ForensicReportDTO` plus its renderings
(human-readable Markdown, shareable text and structured JSON). Routers stay
thin: they only resolve the analysis and delegate.

The service consumes already-produced analysis results — it never re-runs
detectors, fusion or heatmaps — so report generation is lightweight and
deterministic.
"""

from __future__ import annotations

from app.core.enums import AnalysisStatus
from app.core.errors import ErrorCode
from app.core.exceptions import AnalysisNotFoundError, ChaiError
from app.models.analysis import Analysis
from app.repos.analysis_repo import AnalysisRepository
from app.schemas.report import ForensicReportDTO, ShareTextResponse
from app.services.reporting.builder import build_forensic_report
from app.services.reporting.renderers import render_markdown, render_share_text


class ReportService:
    """Orchestrate forensic report assembly for a stored analysis."""

    def __init__(self, *, analysis_repo: AnalysisRepository) -> None:
        self._analysis_repo = analysis_repo

    # ------------------------------------------------------------------
    # Report construction (the single place reports are built)
    # ------------------------------------------------------------------
    def build_report(
        self,
        public_id: str,
        *,
        user_id: int | None = None,
    ) -> ForensicReportDTO:
        """Return the complete structured forensic report for ``public_id``."""
        analysis = self.get_analysis_for_report(public_id, user_id=user_id)
        return build_forensic_report(analysis)

    def get_analysis_for_report(
        self,
        public_id: str,
        *,
        user_id: int | None = None,
    ) -> Analysis:
        """Resolve a completed analysis for reporting, raising catalog errors.

        An incomplete analysis has no verdict to report, so it is returned as
        an invalid-request error rather than an internal failure.
        """
        analysis = self._analysis_repo.get_for_user(user_id, public_id)
        if analysis is None:
            raise AnalysisNotFoundError(public_id)
        if analysis.status is not AnalysisStatus.COMPLETED or analysis.verdict is None:
            raise ChaiError(
                ErrorCode.INVALID_REQUEST,
                "This analysis has not finished running yet.",
            )
        return analysis

    # ------------------------------------------------------------------
    # Renderings
    # ------------------------------------------------------------------
    def build_share_text(
        self,
        public_id: str,
        *,
        user_id: int | None = None,
    ) -> ShareTextResponse:
        """Compose the concise, deterministic shareable text for ``public_id``."""
        report = self.build_report(public_id, user_id=user_id)
        return ShareTextResponse(text=render_share_text(report))

    def build_markdown(
        self,
        public_id: str,
        *,
        user_id: int | None = None,
    ) -> str:
        """Return the human-readable Markdown report for ``public_id``."""
        report = self.build_report(public_id, user_id=user_id)
        return render_markdown(report)

    def build_json(
        self,
        public_id: str,
        *,
        user_id: int | None = None,
    ) -> str:
        """Return the structured JSON report for ``public_id``."""
        report = self.build_report(public_id, user_id=user_id)
        return report.model_dump_json(indent=2)

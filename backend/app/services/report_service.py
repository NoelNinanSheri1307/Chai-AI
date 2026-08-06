"""Report service: share-text generation from a stored analysis.

``ReportService`` composes a human-readable, shareable summary from a stored
analysis result. PDF rendering and report object-storage paths are deferred to
the reports milestone; this milestone wires the share-text flow end to end.
"""

from __future__ import annotations

from app.core.exceptions import AnalysisNotFoundError
from app.repos.analysis_repo import AnalysisRepository
from app.schemas.report import ShareTextResponse
from app.services.mappers import verdict_label


class ReportService:
    """Orchestrate report assembly for an analysis result."""

    def __init__(self, *, analysis_repo: AnalysisRepository) -> None:
        self._analysis_repo = analysis_repo

    def build_share_text(
        self,
        public_id: str,
        *,
        user_id: int | None = None,
    ) -> ShareTextResponse:
        """Compose the shareable report text for ``public_id``."""
        analysis = self._analysis_repo.get_for_user(user_id, public_id)
        if analysis is None:
            raise AnalysisNotFoundError(public_id)

        verdict = verdict_label(analysis.verdict)
        confidence = f"{analysis.confidence:.0%}" if analysis.confidence else "n/a"
        risk = analysis.risk_level.value if analysis.risk_level else "unknown"
        text = (
            f"Chai AI — Verdict: {verdict}. "
            f"Confidence: {confidence}. "
            f"Risk level: {risk}. "
            f"{analysis.explanation or 'No explanation was produced.'}"
        )
        return ShareTextResponse(text=text)

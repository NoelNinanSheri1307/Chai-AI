"""Reports router: forensic report output for a stored analysis.

The router stays thin — every route delegates to :class:`ReportService`.
Existing contract paths are preserved; the structured JSON and Markdown paths
are additive (no breaking changes) and serve the same completed analyses.

- ``GET /v1/reports/{analysis_public_id}/share-text``  → shareable text
- ``GET /v1/reports/{analysis_public_id}/json``       → structured JSON
- ``GET /v1/reports/{analysis_public_id}/markdown``   → human-readable report
- ``GET /v1/reports/{analysis_public_id}``            → shortcut to share text
"""

from __future__ import annotations

from fastapi import APIRouter, Response

from app.api.deps import ReportServiceDep
from app.schemas.report import ForensicReportDTO, ShareTextResponse

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get(
    "/{analysis_public_id}/share-text",
    response_model=ShareTextResponse,
    summary="Shareable report text",
    description=(
        "Returns the deterministic, shareable plain-text report of an analysis."
    ),
)
async def share_text(
    analysis_public_id: str,
    service: ReportServiceDep,
) -> ShareTextResponse:
    """Compose the shareable text report for ``analysis_public_id``."""
    return service.build_share_text(analysis_public_id)


@router.get(
    "/{analysis_public_id}/json",
    response_model=ForensicReportDTO,
    summary="Structured JSON forensic report",
    description=(
        "Returns the complete, typed forensic report for an analysis as "
        "structured JSON (classification, evidence, detector contributions, "
        "heatmap summary, metadata and processing information)."
    ),
)
async def json_report(
    analysis_public_id: str,
    service: ReportServiceDep,
) -> ForensicReportDTO:
    """Return the structured (typed) forensic report for an analysis."""
    return service.build_report(analysis_public_id)


@router.get(
    "/{analysis_public_id}/md",
    response_class=Response,
    summary="Human-readable Markdown report",
    description=("Returns the complete human-readable forensic report in Markdown."),
)
async def markdown_report(
    analysis_public_id: str,
    service: ReportServiceDep,
) -> Response:
    """Return the Markdown forensic report for an analysis."""
    body = service.build_markdown(analysis_public_id)
    return Response(
        content=body,
        media_type="text/markdown; charset=utf-8",
    )


@router.get(
    "/{analysis_public_id}",
    response_model=ShareTextResponse,
    summary="Shareable report text (shortcut)",
    description=(
        "Convenience alias for ``/reports/{analysis_public_id}/share-text`` "
        "returning the same shareable summary."
    ),
    include_in_schema=False,
)
async def share_text_shortcut(
    analysis_public_id: str,
    service: ReportServiceDep,
) -> ShareTextResponse:
    """Compose the shareable text report for ``analysis_public_id``."""
    return service.build_share_text(analysis_public_id)

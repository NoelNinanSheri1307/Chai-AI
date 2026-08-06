"""Reports router: share-text generation for a stored analysis.

``GET /v1/reports/{analysis_public_id}/share-text`` returns a human-readable
report summary; the shorter ``GET /v1/reports/{analysis_public_id}`` path serves
the same payload for convenience. PDF generation is deferred to the reports
milestone.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import ReportServiceDep
from app.schemas.report import ShareTextResponse

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get(
    "/{analysis_public_id}/share-text",
    response_model=ShareTextResponse,
    summary="Shareable report text",
    description="Returns the shareable plain-text summary of an analysis result.",
)
async def share_text(
    analysis_public_id: str,
    service: ReportServiceDep,
) -> ShareTextResponse:
    """Compose the shareable text report for ``analysis_public_id``."""
    return service.build_share_text(analysis_public_id)


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

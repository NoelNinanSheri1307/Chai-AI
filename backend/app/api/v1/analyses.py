"""Analyses router: image upload and analysis result retrieval.

``POST /v1/analyses`` accepts a multipart image, validates it synchronously and
returns the completed ``AnalysisResult`` produced by the injected (placeholder)
pipeline. ``GET /v1/analyses/{public_id}`` returns a stored result. The async
``202 + poll`` lifecycle and job orchestration arrive with the jobs milestone.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, File, UploadFile, status

from app.api.deps import AnalysisServiceDep
from app.schemas.analysis import AnalysisResultDTO

router = APIRouter(prefix="/analyses", tags=["analyses"])


@router.post(
    "",
    response_model=AnalysisResultDTO,
    status_code=status.HTTP_200_OK,
    summary="Upload and analyze an image",
    description=(
        "Validates the upload (size, MIME, magic bytes), stores the original, "
        "runs the analysis pipeline and returns the completed result. Errors: "
        "413 file_too_large, 415 unsupported_media_type, 422 invalid_image."
    ),
)
def upload_analysis(
    service: AnalysisServiceDep,
    file: Annotated[UploadFile, File()],
) -> AnalysisResultDTO:
    """Validate, store, analyze and return a newly uploaded image.

    The analysis pipeline is CPU-bound, so the handler is declared synchronously
    (``def``) and Starlette/FastAPI runs it in a worker thread. This keeps the
    event loop responsive to other requests (health checks, polls) while a
    heavy analysis is running, instead of blocking all traffic.
    """
    data = file.file.read()
    return service.analyze_upload(
        data=data,
        content_type=file.content_type,
        file_name=file.filename,
    )


@router.get(
    "/{public_id}",
    response_model=AnalysisResultDTO,
    summary="Full analysis result",
    description="Returns the stored analysis result for the given public id.",
)
async def get_analysis(
    public_id: str,
    service: AnalysisServiceDep,
) -> AnalysisResultDTO:
    """Return the stored analysis result for ``public_id``."""
    return service.get_analysis(public_id)

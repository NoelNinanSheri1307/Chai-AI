"""Compare router: two-image comparison.

``POST /v1/compare`` accepts two multipart images and returns the comparison
result synchronously. Each image is analyzed through the same pipeline as a
single upload, and both analyses plus the comparison are persisted.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, File, UploadFile, status

from app.api.deps import ComparisonServiceDep
from app.schemas.compare import CompareResultDTO

router = APIRouter(prefix="/compare", tags=["compare"])


@router.post(
    "",
    response_model=CompareResultDTO,
    status_code=status.HTTP_200_OK,
    summary="Compare two images",
    description=(
        "Accepts two images, analyzes each through the pipeline, persists the "
        "comparison and returns the result. Errors: 413 file_too_large, 415 "
        "unsupported_media_type, 422 invalid_image."
    ),
)
async def compare_images(
    service: ComparisonServiceDep,
    file_a: Annotated[UploadFile, File()],
    file_b: Annotated[UploadFile, File()],
) -> CompareResultDTO:
    """Analyze and compare two uploaded images."""
    data_a = await file_a.read()
    data_b = await file_b.read()
    return service.compare_images(
        file_a_data=data_a,
        content_type_a=file_a.content_type,
        file_a_name=file_a.filename,
        file_b_data=data_b,
        content_type_b=file_b.content_type,
        file_b_name=file_b.filename,
    )

"""History router: user-scoped analysis history.

``GET /v1/history`` lists paginated summaries, ``GET /v1/history/{public_id}``
returns a stored analysis and ``DELETE /v1/history/{public_id}`` soft-deletes
it. In this pre-authentication milestone every analysis is anonymous and the
history collection is the full set of stored analyses.
"""

from __future__ import annotations

from fastapi import APIRouter, Query, Response, status

from app.api.deps import HistoryServiceDep
from app.core import constants
from app.schemas.analysis import AnalysisResultDTO
from app.schemas.common import PageEnvelope
from app.schemas.history import HistoryItemDTO

router = APIRouter(prefix="/history", tags=["history"])


@router.get(
    "",
    response_model=PageEnvelope[HistoryItemDTO],
    summary="List analysis history",
    description=(
        "Returns a paginated list of history summaries. Supports 1-based "
        "``page``, ``limit``, an optional verdict/risk ``filter`` and a camelCase "
        "``sort`` field (for example ``-createdAt``)."
    ),
)
def list_history(
    service: HistoryServiceDep,
    page: int = Query(1, ge=1),
    limit: int = Query(constants.DEFAULT_PAGE_SIZE, ge=1, le=constants.MAX_PAGE_SIZE),
    image_filter: str | None = Query(default=None, alias="filter"),
    sort: str | None = Query(default=None),
) -> PageEnvelope[HistoryItemDTO]:
    """Return a paginated page of history summaries.

    History handlers are declared synchronously so the repositories' sync DB
    calls run in the worker thread pool rather than blocking the event loop.
    """
    return service.list_history(
        page=page,
        limit=limit,
        image_filter=image_filter,
        sort=sort,
    )


@router.get(
    "/{public_id}",
    response_model=AnalysisResultDTO,
    summary="Full stored analysis",
    description="Returns the full analysis result for a history entry.",
)
def get_history_item(
    public_id: str,
    service: HistoryServiceDep,
) -> AnalysisResultDTO:
    """Return the full analysis result for ``public_id``."""
    return service.get_history_item(public_id)


@router.delete(
    "/{public_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a history entry",
    description="Soft-deletes the history entry for the given public id.",
)
def delete_history_item(
    public_id: str,
    service: HistoryServiceDep,
) -> Response:
    """Soft-delete the history entry for ``public_id``."""
    service.delete_history_item(public_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

"""History service: user-scoped listing, detail and deletion of analyses.

Reads are scoped to one user (or all anonymous analyses when no user context is
available, as in this pre-authentication milestone) and exclude soft-deleted
rows. Soft deletion and "clear history" mutate the same analysis rows, so they
also live here.
"""

from __future__ import annotations

from app.core.enums import AnalysisStatus, RiskLevel, Verdict
from app.core.exceptions import HistoryNotFoundError
from app.repos.history_repo import HistoryRepository
from app.schemas.analysis import AnalysisResultDTO
from app.schemas.history import HistoryItemDTO
from app.services.mappers import analysis_to_history_item, analysis_to_result_dto
from app.utils.pagination import build_page_envelope, resolve_page_params


class HistoryService:
    """Orchestrate history queries and mutations for an analysis collection."""

    def __init__(self, *, history_repo: HistoryRepository) -> None:
        self._history_repo = history_repo

    def list_history(
        self,
        *,
        user_id: int | None = None,
        page: int = 1,
        limit: int = 20,
        image_filter: str | None = None,
        sort: str | None = None,
    ) -> dict[str, object]:
        """Return a paginated page of history summaries matching filters.

        ``image_filter`` optionally narrows to a verdict, risk level or status.
        Unknown filter strings are tolerated and ignored.
        """
        params = resolve_page_params(page=page, limit=limit, sort=sort)
        verdict, risk_level, status = _parse_filter(image_filter)
        page_result = self._history_repo.list_for_user(
            user_id,
            page=params,
            verdict=verdict,
            risk_level=risk_level,
            status=status,
        )
        items: list[HistoryItemDTO] = [
            analysis_to_history_item(analysis) for analysis in page_result.items
        ]
        return build_page_envelope(
            items,
            total=page_result.total,
            page=max(int(page), 1),
            limit=params.limit,
        )

    def get_history_item(
        self,
        public_id: str,
        *,
        user_id: int | None = None,
    ) -> AnalysisResultDTO:
        """Return the stored analysis for ``public_id`` as its result DTO."""
        analysis = self._history_repo.get_for_user(user_id, public_id)
        if analysis is None:
            raise HistoryNotFoundError(public_id)
        return analysis_to_result_dto(analysis)

    def delete_history_item(
        self,
        public_id: str,
        *,
        user_id: int | None = None,
    ) -> None:
        """Soft-delete the analysis for ``public_id``.

        Raises :class:`HistoryNotFoundError` (HTTP 404) when the entry is
        missing or already deleted.
        """
        deleted = self._history_repo.soft_delete_for_user(user_id, public_id)
        if not deleted:
            raise HistoryNotFoundError(public_id)


def _parse_filter(
    image_filter: str | None,
) -> tuple[Verdict | None, RiskLevel | None, AnalysisStatus | None]:
    """Coerce a filter string into verdict/risk/status enums, ignoring unknown."""
    if not image_filter:
        return None, None, None
    for member in Verdict:
        if member.value == image_filter:
            return member, None, None
    for member in RiskLevel:
        if member.value == image_filter:
            return None, member, None
    for member in AnalysisStatus:
        if member.value == image_filter:
            return None, None, member
    return None, None, None

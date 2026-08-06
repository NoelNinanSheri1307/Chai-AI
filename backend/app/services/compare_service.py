"""Comparison service: two-image comparison orchestration.

``ComparisonService`` runs the synchronous placeholder comparison workflow: it
analyzes both uploaded images through the analysis service, links them in a
``Comparison`` record with a deterministic placeholder result, persists the
findings/regions and returns the ``CompareResultDTO``.

The matching and signal extraction themselves arrive with a later milestone;
this milestone only wires the comparison lifecycle end to end.
"""

from __future__ import annotations

from app.core.constants import COMPARISON_PUBLIC_ID_PREFIX
from app.models.comparison import Comparison
from app.repos.comparison_repo import ComparisonRepository, FindingDraft, RegionDraft
from app.schemas.compare import CompareResultDTO
from app.services.analysis_service import AnalysisService
from app.services.mappers import comparison_to_result_dto
from app.utils import keys

_LABEL_MAX_LENGTH = 50

# Deterministic placeholder values that validate the comparison flow without
# performing any image matching (deferred to a later milestone).
_PLACEHOLDER_SIMILARITY = 0.21
_PLACEHOLDER_AI_PROBABILITY = 0.86
_PLACEHOLDER_DIFFERENCES = [
    "Metadata timestamp differs from the time implied by the content."
]
_PLACEHOLDER_REGIONS = [
    RegionDraft(
        x=0.1, y=0.2, width=0.5, height=0.3, intensity=0.7, label="Edited region"
    )
]


class ComparisonService:
    """Orchestrate a two-image comparison and its persistence."""

    def __init__(
        self,
        *,
        analysis_service: AnalysisService,
        comparison_repo: ComparisonRepository,
    ) -> None:
        self._analysis_service = analysis_service
        self._comparison_repo = comparison_repo

    def compare_images(
        self,
        *,
        file_a_data: bytes,
        content_type_a: str | None,
        file_a_name: str | None,
        file_b_data: bytes,
        content_type_b: str | None,
        file_b_name: str | None,
        user_id: int | None = None,
    ) -> CompareResultDTO:
        """Analyze both images, persist a comparison and return its result.

        Each image is processed through the analysis service (so its own result
        is retrievable), then linked into a ``Comparison``. Raises the catalog
        upload errors when either file is invalid.
        """
        result_a = self._analysis_service.analyze_upload(
            data=file_a_data,
            content_type=content_type_a,
            file_name=file_a_name,
            user_id=user_id,
        )
        result_b = self._analysis_service.analyze_upload(
            data=file_b_data,
            content_type=content_type_b,
            file_name=file_b_name,
            user_id=user_id,
        )

        analysis_a = self._analysis_service.get_analysis_entity(
            result_a.id, user_id=user_id
        )
        analysis_b = self._analysis_service.get_analysis_entity(
            result_b.id, user_id=user_id
        )

        comparison = self._comparison_repo.create(
            Comparison(
                public_id=keys.new_public_id(COMPARISON_PUBLIC_ID_PREFIX),
                user_id=user_id,
                analysis_a_id=analysis_a.id,
                analysis_b_id=analysis_b.id,
                similarity=_PLACEHOLDER_SIMILARITY,
                ai_probability=_PLACEHOLDER_AI_PROBABILITY,
                label_a=_truncated_label(file_a_name),
                label_b=_truncated_label(file_b_name),
            )
        )
        self._comparison_repo.persist_children(
            comparison.id,
            findings=[
                FindingDraft(is_similarity=False, text=text)
                for text in _PLACEHOLDER_DIFFERENCES
            ],
            regions=_PLACEHOLDER_REGIONS,
        )
        return comparison_to_result_dto(comparison)


def _truncated_label(file_name: str | None) -> str:
    """Return a comparison label derived from the file name (≤50 chars)."""
    label = (file_name or "image").strip() or "image"
    return label[:_LABEL_MAX_LENGTH]

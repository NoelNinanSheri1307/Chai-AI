"""Tests for the comparison service: two-image orchestration."""

from __future__ import annotations

import pytest

from app.core.config import Settings
from app.pipeline.placeholder import PlaceholderAnalysisPipeline
from app.repos.analysis_repo import AnalysisRepository
from app.repos.comparison_repo import ComparisonRepository
from app.schemas.compare import CompareResultDTO
from app.services.analysis_service import AnalysisService
from app.services.compare_service import ComparisonService


@pytest.fixture()
def comparison_service(db_session, storage, settings: Settings) -> ComparisonService:
    """A comparison service wired to the isolated test database and storage."""
    analysis_service = AnalysisService(
        analysis_repo=AnalysisRepository(db_session),
        storage=storage,
        pipeline=PlaceholderAnalysisPipeline(),
        settings=settings,
    )
    return ComparisonService(
        analysis_service=analysis_service,
        comparison_repo=ComparisonRepository(db_session),
    )


def test_compare_images_returns_result_dto(
    comparison_service: ComparisonService,
) -> None:
    result = comparison_service.compare_images(
        file_a_data=b"\xff\xd8\xff\xe0" + b"a" * 10,
        content_type_a="image/jpeg",
        file_a_name="photo_a.png",
        file_b_data=b"\xff\xd8\xff\xe0" + b"b" * 10,
        content_type_b="image/jpeg",
        file_b_name="photo_b.png",
    )
    assert isinstance(result, CompareResultDTO)
    assert result.labelA == "photo_a.png"
    assert result.labelB == "photo_b.png"
    assert result.similarity == pytest.approx(0.21)
    assert result.aiProbability == pytest.approx(0.86)
    assert result.differences
    assert result.manipulatedRegions


def test_compare_images_persists_analyses_and_comparison(
    comparison_service: ComparisonService, db_session
) -> None:
    comparison_service.compare_images(
        file_a_data=b"\xff\xd8\xff\xe0" + b"a" * 10,
        content_type_a="image/jpeg",
        file_a_name="a.jpg",
        file_b_data=b"\xff\xd8\xff\xe0" + b"b" * 10,
        content_type_b="image/jpeg",
        file_b_name="b.jpg",
    )
    assert AnalysisRepository(db_session).count() == 2
    comparisons = ComparisonRepository(db_session).list()
    assert comparisons.total == 1
    comparison = comparisons.items[0]
    assert comparison.findings
    assert comparison.regions


def test_compare_images_invalid_file_does_not_persist(
    comparison_service: ComparisonService, db_session
) -> None:
    from app.core.exceptions import InvalidImageError

    with pytest.raises(InvalidImageError):
        comparison_service.compare_images(
            file_a_data=b"not an image",
            content_type_a="image/jpeg",
            file_a_name="a.jpg",
            file_b_data=b"\xff\xd8\xff\xe0" + b"b" * 10,
            content_type_b="image/jpeg",
            file_b_name="b.jpg",
        )
    assert AnalysisRepository(db_session).count() == 0
    assert ComparisonRepository(db_session).count() == 0

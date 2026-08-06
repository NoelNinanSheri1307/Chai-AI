"""Tests for the analysis service: upload orchestration and result mapping."""

from __future__ import annotations

import pytest

from app.core.config import Settings
from app.core.exceptions import AnalysisNotFoundError, InvalidImageError
from app.pipeline.placeholder import PlaceholderAnalysisPipeline
from app.repos.analysis_repo import AnalysisRepository
from app.schemas.analysis import AnalysisResultDTO
from app.services.analysis_service import AnalysisService
from tests.sample_images import GARBAGE_BYTES, JPEG_BYTES


@pytest.fixture()
def analysis_service(db_session, storage, settings: Settings) -> AnalysisService:
    """An analysis service wired to the isolated test database and storage."""
    return AnalysisService(
        analysis_repo=AnalysisRepository(db_session),
        storage=storage,
        pipeline=PlaceholderAnalysisPipeline(),
        settings=settings,
    )


def test_analyze_upload_returns_completed_result_dto(
    analysis_service: AnalysisService,
) -> None:
    result = analysis_service.analyze_upload(
        data=JPEG_BYTES,
        content_type="image/jpeg",
        file_name="sample.jpg",
    )
    assert isinstance(result, AnalysisResultDTO)
    assert result.id.startswith("ana_")
    assert result.verdict.value == "aiGenerated"
    assert result.confidence == pytest.approx(0.91)
    assert result.fileName == "sample.jpg"
    assert result.scores
    assert result.indicators
    assert result.evidence
    assert result.metadata
    assert result.heatmap is not None
    assert result.imagePath == f"/v1/analyses/{result.id}/original"
    assert result.analysisDuration.startswith("PT")
    assert result.timestamp.endswith("Z")


def test_analyze_upload_persists_full_graph(
    analysis_service: AnalysisService, db_session
) -> None:
    result = analysis_service.analyze_upload(
        data=JPEG_BYTES, content_type="image/jpeg", file_name="sample.jpg"
    )
    stored = AnalysisRepository(db_session).get_by_public_id(result.id)
    assert stored is not None
    assert stored.status.value == "completed"
    assert stored.verdict.value == "aiGenerated"
    assert stored.original_key.startswith("testing/orig/")
    assert stored.forensic_scores
    assert stored.detected_indicators
    assert stored.evidence
    assert stored.metadata_items
    assert stored.heatmap is not None


def test_analyze_upload_stores_original_bytes(
    analysis_service: AnalysisService, storage
) -> None:
    analysis_service.analyze_upload(
        data=JPEG_BYTES, content_type="image/jpeg", file_name="sample.jpg"
    )
    original_files = list((storage.root / "testing" / "orig").iterdir())
    assert len(original_files) == 1
    assert original_files[0].read_bytes() == JPEG_BYTES


def test_analyze_upload_invalid_image_does_not_persist(
    analysis_service: AnalysisService, db_session
) -> None:
    with pytest.raises(InvalidImageError):
        analysis_service.analyze_upload(
            data=GARBAGE_BYTES, content_type="image/jpeg", file_name="bad.jpg"
        )
    assert AnalysisRepository(db_session).count() == 0


def test_get_analysis_returns_stored_result(
    analysis_service: AnalysisService,
) -> None:
    created = analysis_service.analyze_upload(
        data=JPEG_BYTES, content_type="image/jpeg", file_name="sample.jpg"
    )
    fetched = analysis_service.get_analysis(created.id)
    assert fetched.id == created.id
    assert fetched.verdict == created.verdict


def test_get_analysis_missing_raises_not_found(
    analysis_service: AnalysisService,
) -> None:
    with pytest.raises(AnalysisNotFoundError):
        analysis_service.get_analysis("ana_missing")


def test_get_analysis_entity_supports_service_composition(
    analysis_service: AnalysisService,
) -> None:
    created = analysis_service.analyze_upload(
        data=JPEG_BYTES, content_type="image/jpeg", file_name="sample.jpg"
    )
    entity = analysis_service.get_analysis_entity(created.id)
    assert entity.id is not None
    assert entity.public_id == created.id

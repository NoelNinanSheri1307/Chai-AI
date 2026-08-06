"""Tests for the report service: share-text generation."""

from __future__ import annotations

import pytest

from app.core.config import Settings
from app.core.exceptions import AnalysisNotFoundError
from app.pipeline.placeholder import PlaceholderAnalysisPipeline
from app.repos.analysis_repo import AnalysisRepository
from app.schemas.report import ShareTextResponse
from app.services.analysis_service import AnalysisService
from app.services.report_service import ReportService


@pytest.fixture()
def report_service(db_session) -> ReportService:
    """A report service bound to the isolated test database."""
    return ReportService(analysis_repo=AnalysisRepository(db_session))


def _upload(db_session, storage, settings: Settings) -> str:
    service = AnalysisService(
        analysis_repo=AnalysisRepository(db_session),
        storage=storage,
        pipeline=PlaceholderAnalysisPipeline(),
        settings=settings,
    )
    return service.analyze_upload(
        data=b"\xff\xd8\xff\xe0" + b"payload",
        content_type="image/jpeg",
        file_name="sample.jpg",
    ).id


def test_build_share_text_includes_verdict(
    db_session, storage, settings: Settings, report_service: ReportService
) -> None:
    public_id = _upload(db_session, storage, settings)
    response = report_service.build_share_text(public_id)
    assert isinstance(response, ShareTextResponse)
    assert "Chai AI" in response.text
    assert "AI Generated" in response.text
    assert "Confidence" in response.text


def test_build_share_text_missing_raises_not_found(
    report_service: ReportService,
) -> None:
    with pytest.raises(AnalysisNotFoundError):
        report_service.build_share_text("ana_missing")

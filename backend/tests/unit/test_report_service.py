"""Tests for the report service: report, markdown, JSON and share-text flows."""

from __future__ import annotations

import json

import pytest

from app.core.config import Settings
from app.core.enums import AnalysisStatus, Verdict
from app.core.exceptions import AnalysisNotFoundError, ChaiError
from app.models.analysis import Analysis
from app.pipeline.placeholder import PlaceholderAnalysisPipeline
from app.repos.analysis_repo import AnalysisRepository
from app.schemas.report import ForensicReportDTO, ShareTextResponse
from app.services.analysis_service import AnalysisService
from app.services.report_service import ReportService

from .report_helpers import commit_analysis, vt_analysis


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


def test_build_report_returns_typed_dto(
    db_session, storage, settings: Settings, report_service: ReportService
) -> None:
    public_id = _upload(db_session, storage, settings)
    report = report_service.build_report(public_id)
    assert isinstance(report, ForensicReportDTO)
    assert report.analysis_id == public_id
    assert report.classification.verdict == Verdict.AI_GENERATED
    assert report.classification.confidence_percent == 91


def test_build_markdown_and_json_renders(
    db_session, storage, settings: Settings, report_service: ReportService
) -> None:
    public_id = _upload(db_session, storage, settings)
    markdown = report_service.build_markdown(public_id)
    assert markdown.startswith("# Chai AI Forensic Analysis")

    structured = json.loads(report_service.build_json(public_id))
    assert structured["analysis_id"] == public_id
    assert structured["classification"]["verdict"] == Verdict.AI_GENERATED.value


def test_build_markdown_missing_raises_not_found(
    report_service: ReportService,
) -> None:
    with pytest.raises(AnalysisNotFoundError):
        report_service.build_markdown("ana_missing")


def test_build_json_missing_raises_not_found(report_service: ReportService) -> None:
    with pytest.raises(AnalysisNotFoundError):
        report_service.build_json("ana_missing")


def test_build_share_text_missing_raises_not_found(
    report_service: ReportService,
) -> None:
    with pytest.raises(AnalysisNotFoundError):
        report_service.build_share_text("ana_missing")


def test_incomplete_analysis_is_invalid_request(db_session, report_service) -> None:
    analysis = Analysis(
        public_id="ana_running",
        original_key="k",
        status=AnalysisStatus.RUNNING,
    )
    db_session.add(analysis)
    db_session.commit()
    with pytest.raises(ChaiError) as excinfo:
        report_service.build_report("ana_running")
    assert excinfo.value.code == "invalid_request"


def test_report_from_seeded_completed_analysis(db_session, report_service) -> None:
    analysis = vt_analysis(public_id="ana_completed")
    analysis.status = AnalysisStatus.COMPLETED
    commit_analysis(db_session, analysis)
    report = report_service.build_report("ana_completed")
    assert report.analysis_id == "ana_completed"


def test_share_text_is_deterministic(
    db_session, storage, settings: Settings, report_service: ReportService
) -> None:
    public_id = _upload(db_session, storage, settings)
    first = report_service.build_share_text(public_id).text
    second = report_service.build_share_text(public_id).text
    assert first == second

"""Tests for the history service: listing, detail and deletion."""

from __future__ import annotations

import pytest

from app.core.config import Settings
from app.core.exceptions import HistoryNotFoundError
from app.pipeline.placeholder import PlaceholderAnalysisPipeline
from app.repos.analysis_repo import AnalysisRepository
from app.repos.history_repo import HistoryRepository
from app.services.analysis_service import AnalysisService
from app.services.history_service import HistoryService


@pytest.fixture()
def history_service(db_session) -> HistoryService:
    """A history service bound to the isolated test database."""
    return HistoryService(history_repo=HistoryRepository(db_session))


def _upload(analysis_service: AnalysisService, file_name: str) -> str:
    return analysis_service.analyze_upload(
        data=b"\xff\xd8\xff\xe0" + b"payload",
        content_type="image/jpeg",
        file_name=file_name,
    ).id


def test_list_history_returns_page_envelope(
    db_session, storage, settings: Settings, history_service: HistoryService
) -> None:
    analysis_service = AnalysisService(
        analysis_repo=AnalysisRepository(db_session),
        storage=storage,
        pipeline=PlaceholderAnalysisPipeline(),
        settings=settings,
    )
    _upload(analysis_service, "a.jpg")
    _upload(analysis_service, "b.jpg")

    page = history_service.list_history(page=1, limit=10)
    assert page["total"] == 2
    assert page["page"] == 1
    assert page["limit"] == 10
    assert page["has_more"] is False
    items = page["items"]
    assert len(items) == 2
    assert {item.fileName for item in items} == {"a.jpg", "b.jpg"}
    assert all(item.id.startswith("ana_") for item in items)


def test_list_history_filters_by_verdict(
    db_session, storage, settings: Settings, history_service: HistoryService
) -> None:
    analysis_service = AnalysisService(
        analysis_repo=AnalysisRepository(db_session),
        storage=storage,
        pipeline=PlaceholderAnalysisPipeline(),
        settings=settings,
    )
    _upload(analysis_service, "a.jpg")
    _upload(analysis_service, "b.jpg")

    page = history_service.list_history(page=1, limit=10, image_filter="aiGenerated")
    assert page["total"] == 2

    page = history_service.list_history(page=1, limit=10, image_filter="original")
    assert page["total"] == 0


def test_list_history_sorts_by_recency(
    db_session, storage, settings: Settings, history_service: HistoryService
) -> None:
    analysis_service = AnalysisService(
        analysis_repo=AnalysisRepository(db_session),
        storage=storage,
        pipeline=PlaceholderAnalysisPipeline(),
        settings=settings,
    )
    _upload(analysis_service, "first.jpg")
    _upload(analysis_service, "second.jpg")

    page = history_service.list_history(page=1, limit=10, sort="-createdAt")
    assert len(page["items"]) == 2
    timestamps = [item.timestamp for item in page["items"]]
    assert timestamps == sorted(timestamps, reverse=True)


def test_get_history_item_returns_full_result(
    db_session, storage, settings: Settings, history_service: HistoryService
) -> None:
    analysis_service = AnalysisService(
        analysis_repo=AnalysisRepository(db_session),
        storage=storage,
        pipeline=PlaceholderAnalysisPipeline(),
        settings=settings,
    )
    public_id = _upload(analysis_service, "a.jpg")
    result = history_service.get_history_item(public_id)
    assert result.id == public_id
    assert result.verdict.value == "aiGenerated"


def test_get_history_item_missing_raises_not_found(
    history_service: HistoryService,
) -> None:
    with pytest.raises(HistoryNotFoundError):
        history_service.get_history_item("ana_missing")


def test_delete_history_item_soft_deletes(
    db_session, storage, settings: Settings, history_service: HistoryService
) -> None:
    analysis_service = AnalysisService(
        analysis_repo=AnalysisRepository(db_session),
        storage=storage,
        pipeline=PlaceholderAnalysisPipeline(),
        settings=settings,
    )
    public_id = _upload(analysis_service, "a.jpg")

    history_service.delete_history_item(public_id)
    assert history_service.list_history(page=1, limit=10)["total"] == 0

    with pytest.raises(HistoryNotFoundError):
        history_service.get_history_item(public_id)

    with pytest.raises(HistoryNotFoundError):
        history_service.delete_history_item(public_id)

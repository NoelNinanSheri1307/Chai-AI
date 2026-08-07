"""Integration tests for dependency injection of persistence providers."""

from __future__ import annotations

from collections.abc import Generator
from typing import Annotated

from fastapi import APIRouter, Depends, FastAPI
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.api.deps import (
    get_analysis_repository,
    get_analysis_service,
    get_comparison_repository,
    get_comparison_service,
    get_db_session,
    get_detectors,
    get_evidence_generator,
    get_explanation_generator,
    get_fusion_engine,
    get_heatmap_generator,
    get_history_repository,
    get_history_service,
    get_job_repository,
    get_object_storage,
    get_pipeline,
    get_pipeline_config,
    get_report_service,
    get_token_repository,
    get_user_repository,
)
from app.clients.storage import LocalStorageAdapter
from app.core.config import Settings
from app.core.db import Database, create_session_factory
from app.pipeline.base import AnalysisPipeline
from app.pipeline.runner import ModularAnalysisPipeline
from app.repos import (
    AnalysisRepository,
    ComparisonRepository,
    HistoryRepository,
    JobRepository,
    TokenRepository,
    UserRepository,
)
from app.services import (
    AnalysisService,
    ComparisonService,
    HistoryService,
    ReportService,
)


def test_get_db_session_yields_a_session() -> None:
    settings = Settings(environment="testing", database_url="sqlite://")
    Database(settings).create_all()
    generator = get_db_session(settings=settings)
    session = next(generator)
    try:
        assert isinstance(session, Session)
    finally:
        generator.close()


def test_get_object_storage_returns_local_adapter(settings: Settings) -> None:
    adapter = get_object_storage(settings)
    assert isinstance(adapter, LocalStorageAdapter)
    assert adapter.root == settings.storage_root


def test_repository_dependencies_wire_sessions(settings: Settings) -> None:
    settings = Settings(
        environment="testing",
        database_url="sqlite://",
        storage_root=settings.storage_root,
    )
    database = Database(settings)
    database.create_all()
    session = database.session()
    try:
        assert isinstance(get_user_repository(session), UserRepository)
        assert isinstance(get_analysis_repository(session), AnalysisRepository)
        assert isinstance(get_history_repository(session), HistoryRepository)
        assert isinstance(get_comparison_repository(session), ComparisonRepository)
        assert isinstance(get_job_repository(session), JobRepository)
        assert isinstance(get_token_repository(session), TokenRepository)
    finally:
        session.close()


def test_repository_dependency_resolves_through_fastapi(db_engine) -> None:
    """Verify repositories reach routers via FastAPI dependency injection."""
    app = FastAPI()
    factory = create_session_factory(db_engine)

    def override_db_session() -> Generator[Session, None, None]:
        with factory() as session:
            yield session

    app.dependency_overrides[get_db_session] = override_db_session

    router = APIRouter()

    @router.get("/_di/users/{email}")
    def user_exists(
        email: str,
        repo: Annotated[UserRepository, Depends(get_user_repository)],
    ) -> dict[str, bool]:
        return {"exists": repo.email_exists(email)}

    app.include_router(router)

    with factory() as session:
        UserRepository(session).create_user(
            email="di-user@example.com",
            password_hash="h",
            display_name="DI",
        )
        session.commit()

    client = TestClient(app)
    assert client.get("/_di/users/di-user@example.com").json() == {"exists": True}
    assert client.get("/_di/users/unknown@example.com").json() == {"exists": False}


def test_pipeline_dependency_is_injected() -> None:
    """The pipeline framework is composed via DI from injected components."""
    pipeline_config = get_pipeline_config()
    pipeline = get_pipeline(
        detectors=get_detectors(pipeline_config),
        fusion=get_fusion_engine(pipeline_config),
        heatmap_generator=get_heatmap_generator(pipeline_config),
        evidence_generator=get_evidence_generator(pipeline_config),
        explanation_generator=get_explanation_generator(pipeline_config),
        pipeline_config=pipeline_config,
    )
    assert isinstance(pipeline, AnalysisPipeline)
    assert isinstance(pipeline, ModularAnalysisPipeline)

    result = pipeline.analyze(
        b"\xff\xd8\xff\xe0" + b"payload", content_type="image/jpeg"
    )
    assert result.verdict.value in {"original", "aiEdited", "aiGenerated"}
    assert 0.0 <= result.confidence <= 1.0
    assert result.metadata["pipeline_version"] == pipeline_config.pipeline_version


def test_service_dependencies_wire(settings: Settings) -> None:
    """Service providers assemble their repositories, storage and pipeline."""
    settings = Settings(
        environment="testing",
        database_url="sqlite://",
        storage_root=settings.storage_root,
    )
    database = Database(settings)
    database.create_all()
    session = database.session()
    try:
        pipeline_config = get_pipeline_config()
        pipeline = get_pipeline(
            detectors=get_detectors(pipeline_config),
            fusion=get_fusion_engine(pipeline_config),
            heatmap_generator=get_heatmap_generator(pipeline_config),
            evidence_generator=get_evidence_generator(pipeline_config),
            explanation_generator=get_explanation_generator(pipeline_config),
            pipeline_config=pipeline_config,
        )
        storage = get_object_storage(settings)

        analysis_service = get_analysis_service(session, storage, pipeline, settings)
        assert isinstance(analysis_service, AnalysisService)

        history_service = get_history_service(session)
        assert isinstance(history_service, HistoryService)

        comparison_service = get_comparison_service(analysis_service, session)
        assert isinstance(comparison_service, ComparisonService)

        report_service = get_report_service(session)
        assert isinstance(report_service, ReportService)
    finally:
        session.close()

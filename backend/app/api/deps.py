"""FastAPI dependencies (dependency injection).

Backing systems (database, object storage), repositories, services and the
forensic pipeline framework are all provided here for routers. Repositories are
constructed with the plain session they need; services receive their
repositories, the storage client and the injected pipeline.

The pipeline framework is composed at this composition root: detectors, the
fusion engine, heatmap generator and the evidence/explanation generators are all
injected into the modular runner. No service or router ever instantiates an
implementation directly, so a real detector or fusion model can replace a
placeholder without touching callers.
"""

from __future__ import annotations

from collections.abc import Generator
from typing import Annotated, Any

from fastapi import Depends
from sqlmodel import Session

from app.clients.storage import StorageClient, create_storage_client
from app.core.config import Settings, get_settings
from app.core.db import get_session as _get_db_session
from app.core.logging import get_request_id
from app.core.rate_limit import RateLimiter, build_rate_limiter
from app.pipeline.base import AnalysisPipeline
from app.pipeline.config import (
    PipelineConfig,
)
from app.pipeline.config import (
    get_pipeline_config as _resolve_pipeline_config,
)
from app.pipeline.detectors.base import Detector
from app.pipeline.detectors.registry import build_detectors
from app.pipeline.explanation.base import EvidenceGenerator, ExplanationGenerator
from app.pipeline.explanation.classifier import (
    ClassificationEvidenceGenerator,
    ClassificationExplanationGenerator,
)
from app.pipeline.fusion.base import FusionEngine
from app.pipeline.fusion.engine import DeterministicFusionEngine
from app.pipeline.heatmap.base import HeatmapGenerator
from app.pipeline.heatmap.generator import DeterministicHeatmapGenerator
from app.pipeline.runner import ModularAnalysisPipeline
from app.repos.analysis_repo import AnalysisRepository
from app.repos.comparison_repo import ComparisonRepository
from app.repos.history_repo import HistoryRepository
from app.repos.job_repo import JobRepository
from app.repos.token_repo import TokenRepository
from app.repos.user_repo import UserRepository
from app.clients.external_detection.manager import ExternalDetectionManager
from app.services.analysis_service import AnalysisService
from app.services.compare_service import ComparisonService
from app.services.external_benchmark_service import ExternalBenchmarkService
from app.services.history_service import HistoryService
from app.services.report_service import ReportService


def get_settings_dependency() -> Settings:
    """Provide the shared application settings instance."""
    return get_settings()


def get_request_id_dependency() -> str:
    """Provide the request id bound to the current request context."""
    return get_request_id()


def get_db_session(settings: SettingsDep) -> Generator[Session, None, None]:
    """Provide a transactional database session.

    Commits on success and rolls back on exception; the session is always
    closed when the request finishes.
    """
    yield from _get_db_session(settings)


def get_object_storage(settings: SettingsDep) -> StorageClient:
    """Provide the object-storage adapter for the active environment."""
    return create_storage_client(settings)


def get_pipeline_config() -> PipelineConfig:
    """Provide the cached pipeline configuration."""
    return _resolve_pipeline_config()


def get_rate_limiter(settings: SettingsDep) -> RateLimiter:
    """Provide the configured rate limiter abstraction (default: no-op)."""
    return build_rate_limiter(
        settings.rate_limiter,
        limit=settings.rate_limiter_limit,
        window_seconds=settings.rate_limiter_window_seconds,
    )


def get_detectors(pipeline_config: PipelineConfigDep) -> list[Detector]:
    """Provide the detector set selected by the pipeline configuration."""
    return build_detectors(pipeline_config.enabled_detector_names())


def get_fusion_engine(pipeline_config: PipelineConfigDep) -> FusionEngine:
    """Provide the deterministic forensic fusion engine."""
    return DeterministicFusionEngine(pipeline_config)


def get_heatmap_generator(pipeline_config: PipelineConfigDep) -> HeatmapGenerator:
    """Provide the deterministic spatial heatmap generator."""
    return DeterministicHeatmapGenerator(pipeline_config)


def get_evidence_generator(pipeline_config: PipelineConfigDep) -> EvidenceGenerator:
    """Provide the deterministic, classification-driven evidence generator."""
    return ClassificationEvidenceGenerator(pipeline_config)


def get_explanation_generator(
    pipeline_config: PipelineConfigDep,
) -> ExplanationGenerator:
    """Provide the deterministic, classification-driven explanation generator."""
    return ClassificationExplanationGenerator(pipeline_config)


def get_pipeline(
    detectors: DetectorsDep,
    fusion: FusionEngineDep,
    heatmap_generator: HeatmapGeneratorDep,
    evidence_generator: EvidenceGeneratorDep,
    explanation_generator: ExplanationGeneratorDep,
    pipeline_config: PipelineConfigDep,
    settings: Settings | None = None,
) -> AnalysisPipeline:
    """Provide a modular analysis pipeline assembled from injected components."""
    resolved_settings = settings or get_settings()
    return ModularAnalysisPipeline(
        detectors=detectors,
        fusion=fusion,
        heatmap_generator=heatmap_generator,
        evidence_generator=evidence_generator,
        explanation_generator=explanation_generator,
        pipeline_config=pipeline_config,
        max_concurrency=resolved_settings.pipeline_max_concurrency,
    )


def get_user_repository(session: SessionDep) -> UserRepository:
    """Provide a :class:`UserRepository` bound to the request session."""
    return UserRepository(session)


def get_analysis_repository(session: SessionDep) -> AnalysisRepository:
    """Provide an :class:`AnalysisRepository` bound to the request session."""
    return AnalysisRepository(session)


def get_history_repository(session: SessionDep) -> HistoryRepository:
    """Provide a :class:`HistoryRepository` bound to the request session."""
    return HistoryRepository(session)


def get_comparison_repository(session: SessionDep) -> ComparisonRepository:
    """Provide a :class:`ComparisonRepository` bound to the request session."""
    return ComparisonRepository(session)


def get_job_repository(session: SessionDep) -> JobRepository:
    """Provide a :class:`JobRepository` bound to the request session."""
    return JobRepository(session)


def get_token_repository(session: SessionDep) -> TokenRepository:
    """Provide a :class:`TokenRepository` bound to the request session."""
    return TokenRepository(session)


def get_analysis_service(
    session: SessionDep,
    storage: StorageDep,
    pipeline: PipelineDep,
    settings: SettingsDep,
) -> AnalysisService:
    """Provide an :class:`AnalysisService` wired with its dependencies."""
    return AnalysisService(
        analysis_repo=AnalysisRepository(session),
        storage=storage,
        pipeline=pipeline,
        settings=settings,
    )


def get_history_service(session: SessionDep) -> HistoryService:
    """Provide a :class:`HistoryService` bound to the request session."""
    return HistoryService(history_repo=HistoryRepository(session))


def get_comparison_service(
    analysis_service: AnalysisServiceDep,
    session: SessionDep,
) -> ComparisonService:
    """Provide a :class:`ComparisonService` wired with its dependencies."""
    return ComparisonService(
        analysis_service=analysis_service,
        comparison_repo=ComparisonRepository(session),
    )


def get_report_service(session: SessionDep) -> ReportService:
    """Provide a :class:`ReportService` bound to the request session."""
    return ReportService(analysis_repo=AnalysisRepository(session))


def get_external_detection_manager(
    settings: SettingsDep,
) -> ExternalDetectionManager:
    """Provide the :class:`ExternalDetectionManager` with registered providers."""
    return ExternalDetectionManager(settings=settings)


def get_external_benchmark_service(
    session: SessionDep,
    storage: StorageDep,
    manager: Annotated[ExternalDetectionManager, Depends(get_external_detection_manager)],
    settings: SettingsDep,
) -> ExternalBenchmarkService:
    """Provide an :class:`ExternalBenchmarkService` wired with dependencies."""
    return ExternalBenchmarkService(
        analysis_repo=AnalysisRepository(session),
        storage=storage,
        manager=manager,
        settings=settings,
    )


# Common dependency aliases. They are declared after the functions they wrap so
# that ``Depends(...)`` resolves the callables at import time.
SettingsDep = Annotated[Settings, Depends(get_settings_dependency)]
SessionDep = Annotated[Session, Depends(get_db_session)]
StorageDep = Annotated[StorageClient, Depends(get_object_storage)]
PipelineConfigDep = Annotated[PipelineConfig, Depends(get_pipeline_config)]
RateLimiterDep = Annotated[RateLimiter, Depends(get_rate_limiter)]
DetectorsDep = Annotated[list[Detector], Depends(get_detectors)]
FusionEngineDep = Annotated[FusionEngine, Depends(get_fusion_engine)]
HeatmapGeneratorDep = Annotated[HeatmapGenerator, Depends(get_heatmap_generator)]
EvidenceGeneratorDep = Annotated[EvidenceGenerator, Depends(get_evidence_generator)]
ExplanationGeneratorDep = Annotated[
    ExplanationGenerator, Depends(get_explanation_generator)
]
PipelineDep = Annotated[AnalysisPipeline, Depends(get_pipeline)]
AnalysisServiceDep = Annotated[AnalysisService, Depends(get_analysis_service)]
HistoryServiceDep = Annotated[HistoryService, Depends(get_history_service)]
ComparisonServiceDep = Annotated[ComparisonService, Depends(get_comparison_service)]
ReportServiceDep = Annotated[ReportService, Depends(get_report_service)]
ExternalBenchmarkServiceDep = Annotated[
    ExternalBenchmarkService, Depends(get_external_benchmark_service)
]


# ---------------------------------------------------------------------------
# Future milestone extension points. These remain reserved until their backing
# systems arrive; nothing in the application-core milestone consumes them.
# ---------------------------------------------------------------------------


def get_cache() -> Any:
    """Provide the cache adapter (production hardening milestone)."""
    raise NotImplementedError(
        "Caching is not implemented until the hardening milestone."
    )


def get_job_service() -> Any:
    """Provide the background job service (analyses milestone)."""
    raise NotImplementedError(
        "The job service is not implemented until the analyses milestone."
    )

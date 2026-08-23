"""Service layer for external AI detection benchmarking.

Retrieves stored analysis records, fetches original image bytes from storage,
queries active external providers through :class:`ExternalDetectionManager`, and
evaluates comparison metrics against Chai's internal verdict.
"""

from __future__ import annotations

from app.clients.external_detection.base import ExternalDetectionResult
from app.clients.external_detection.benchmark import compute_benchmark_report
from app.clients.external_detection.manager import ExternalDetectionManager
from app.clients.storage import StorageClient
from app.core.config import Settings
from app.core.exceptions import AnalysisNotFoundError
from app.repos.analysis_repo import AnalysisRepository
from app.schemas.external_detection import (
    ExternalBenchmarkItemDTO,
    ExternalBenchmarkResponseDTO,
    ExternalDetectionResultDTO,
)


class ExternalBenchmarkService:
    """Service orchestrating external AI detection benchmarks."""

    def __init__(
        self,
        analysis_repo: AnalysisRepository,
        storage: StorageClient,
        manager: ExternalDetectionManager,
        settings: Settings,
    ) -> None:
        self._analysis_repo = analysis_repo
        self._storage = storage
        self._manager = manager
        self._settings = settings

    def benchmark_analysis(self, public_id: str) -> ExternalBenchmarkResponseDTO:
        """Run external benchmarks for a stored analysis identified by ``public_id``."""
        analysis = self._analysis_repo.get_by_public_id(public_id)
        if analysis is None:
            raise AnalysisNotFoundError(public_id)

        # Retrieve stored image bytes using storage adapter
        try:
            image_bytes = self._storage.fetch(analysis.storage_key)
        except Exception:
            image_bytes = b""

        # Query registered external providers
        external_results: list[ExternalDetectionResult] = self._manager.analyze_all(
            image_bytes=image_bytes,
            filename=analysis.file_name or "image.jpg",
            content_type="image/jpeg",
        )

        # Compute benchmark metrics
        report = compute_benchmark_report(
            analysis_id=analysis.public_id,
            chai_verdict=analysis.verdict,
            chai_confidence=analysis.confidence,
            chai_risk_level=analysis.risk_level,
            external_results=external_results,
        )

        # Map to API response DTO
        return ExternalBenchmarkResponseDTO(
            analysisId=report.analysis_id,
            chaiVerdict=report.chai_verdict,
            chaiConfidence=report.chai_confidence,
            chaiRiskLevel=report.chai_risk_level,
            externalResults=[
                ExternalDetectionResultDTO(
                    provider=res.provider,
                    providerVersion=res.provider_version,
                    isConfigured=res.is_configured,
                    status=res.status,
                    detectedAsAi=res.detected_as_ai,
                    confidence=res.confidence,
                    classificationLabel=res.classification_label,
                    rawCategory=res.raw_category,
                    processingTimeMs=res.processing_time_ms,
                    errorMessage=res.error_message,
                    metadata=res.metadata,
                )
                for res in report.external_results
            ],
            benchmarkItems=[
                ExternalBenchmarkItemDTO(
                    provider=item.provider,
                    providerVersion=item.provider_version,
                    status=item.status,
                    detectedAsAi=item.detected_as_ai,
                    confidence=item.confidence,
                    classificationLabel=item.classification_label,
                    agreement=item.agreement,
                    compatibilityNote=item.compatibility_note,
                    confidenceDelta=item.confidence_delta,
                )
                for item in report.benchmark_items
            ],
            overallAgreementRatio=report.overall_agreement_ratio,
            summary=report.summary,
        )

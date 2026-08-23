"""Modular pipeline runner.

``ModularAnalysisPipeline`` implements the service-facing :class:`AnalysisPipeline`
contract by orchestrating the forensic framework's stages:

    validation (implicit) → detector execution → signal collection → fusion →
    evidence → explanation → heatmap → assembly

It contains orchestration only: detector execution order is supplied externally
(via configuration), fusion/heatmap/evidence/explanation generators are injected,
and no forensic algorithm lives here. Removing a detector, adding one, or
swapping any framework stage requires no change to this runner.

Detector execution supports bounded, deterministic *parallelism*:
:class:`PipelineConfig.max_concurrency` controls how many independent detectors
run concurrently in a thread pool. Detectors are stateless, so concurrent
execution is safe; results are always collected in the configured detector
order so the forensic output (fusion ordering, contributions, report snapshot)
is byte-for-byte identical to the sequential run. A value of ``1`` disables the
pool and keeps the classic sequential execution.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Sequence
from concurrent.futures import Future, ThreadPoolExecutor

from app.clients.external_detection.base import ExternalDetectionResult
from app.clients.external_detection.manager import ExternalDetectionManager
from app.core.logging import get_request_id
from app.pipeline.base import (
    AnalysisPipeline,
    PipelineReportData,
    PipelineResult,
    ReportContribution,
)
from app.pipeline.config import PipelineConfig
from app.pipeline.decision.engine import ProductionDecisionEngine
from app.pipeline.detectors.base import Detector
from app.pipeline.explanation.base import EvidenceGenerator, ExplanationGenerator
from app.pipeline.fusion.base import DetectorContribution, FusionEngine, FusionResult
from app.pipeline.heatmap.base import HeatmapContext, HeatmapGenerator
from app.pipeline.signals import DetectorSignal
from app.pipeline.versioning import ComponentVersion, PipelineRunVersion

logger = logging.getLogger(__name__)


class ModularAnalysisPipeline(AnalysisPipeline):
    """A configurable, modular pipeline orchestrating injected stage components."""

    def __init__(
        self,
        *,
        detectors: Sequence[Detector],
        fusion: FusionEngine,
        heatmap_generator: HeatmapGenerator,
        evidence_generator: EvidenceGenerator,
        explanation_generator: ExplanationGenerator,
        pipeline_config: PipelineConfig,
        decision_engine: ProductionDecisionEngine | None = None,
        external_manager: ExternalDetectionManager | None = None,
        max_concurrency: int | None = None,
    ) -> None:
        self._detectors = tuple(detectors)
        self._fusion = fusion
        self._heatmap_generator = heatmap_generator
        self._evidence_generator = evidence_generator
        self._explanation_generator = explanation_generator
        self._config = pipeline_config
        self._decision_engine = decision_engine or ProductionDecisionEngine(
            pipeline_config
        )
        self._external_manager = external_manager
        if max_concurrency is None:
            max_concurrency = pipeline_config.max_concurrency
        # Bounded: 1..pipeline-config-hard-cap; sequential by default.
        self._max_concurrency = max(
            1, min(int(max_concurrency or 1), pipeline_config.max_concurrency)
        )

    # ------------------------------------------------------------------
    # Component access (used by profiling and observability)
    # ------------------------------------------------------------------
    @property
    def fusion(self) -> FusionEngine:
        """The injected fusion engine."""
        return self._fusion

    @property
    def heatmap_generator(self) -> HeatmapGenerator:
        """The injected heatmap generator."""
        return self._heatmap_generator

    @property
    def evidence_generator(self) -> EvidenceGenerator:
        """The injected evidence generator."""
        return self._evidence_generator

    @property
    def explanation_generator(self) -> ExplanationGenerator:
        """The injected explanation generator."""
        return self._explanation_generator

    @property
    def decision_engine(self) -> ProductionDecisionEngine:
        """The production decision engine."""
        return self._decision_engine

    @property
    def external_manager(self) -> ExternalDetectionManager | None:
        """The external detection manager, if injected."""
        return self._external_manager

    # ------------------------------------------------------------------
    # Versioning
    # ------------------------------------------------------------------
    @property
    def version_info(self) -> PipelineRunVersion:
        """Return the version stamp for a run of this pipeline."""
        return PipelineRunVersion(
            framework_version=self._config.framework_version,
            pipeline_version=self._config.pipeline_version,
            fusion_version=self._config.fusion_version,
            detector_versions=tuple(
                ComponentVersion(name=detector.name, version=detector.version)
                for detector in self._detectors
            ),
        )

    # ------------------------------------------------------------------
    # Orchestration
    # ------------------------------------------------------------------
    def analyze(
        self,
        image_bytes: bytes,
        *,
        content_type: str | None = None,
        file_name: str | None = None,
    ) -> PipelineResult:
        """Run the full stage pipeline and return a :class:`PipelineResult`."""
        started = time.perf_counter()

        signals = self.run_detectors(
            image_bytes, content_type=content_type, file_name=file_name
        )
        fusion_result = self._fusion.fuse(signals)

        heatmap_context = HeatmapContext(
            image_bytes=image_bytes,
            content_type=content_type,
            file_name=file_name,
            signals=tuple(signals),
            fusion=fusion_result,
        )
        heatmap = self._heatmap_generator.generate(heatmap_context)

        evidence = self._evidence_generator.generate(fusion_result, signals)
        explanation = self._explanation_generator.explain(
            fusion_result, evidence, signals
        )

        # External reference check if configured and manager is injected
        external_result: ExternalDetectionResult | None = None
        if self._external_manager is not None:
            try:
                ext_results = self._external_manager.analyze_all(
                    image_bytes=image_bytes,
                    filename=file_name or "image.jpg",
                    content_type=content_type or "image/jpeg",
                )
                if ext_results:
                    external_result = ext_results[0]
            except Exception as exc:
                logger.warning("External detection check failed gracefully: %s", exc)
                external_result = ExternalDetectionResult(
                    provider="sightengine",
                    provider_version="v1.0",
                    is_configured=True,
                    status="error",
                    error_message=str(exc),
                )

        # Multi-source production decision & fusion
        decision = self._decision_engine.decide(
            chai_fusion=fusion_result,
            chai_heatmap=heatmap,
            chai_evidence=evidence,
            chai_scores=fusion_result.scores,
            external_result=external_result,
        )

        duration_ms = max(1, int((time.perf_counter() - started) * 1000))

        # Enrich metadata with decision provenance
        meta = self._build_metadata(signals)
        meta["prov:final_classification"] = (
            decision.provenance.final_classification.value
        )
        meta["prov:final_confidence"] = str(decision.provenance.final_confidence)
        meta["prov:chai_classification"] = decision.provenance.chai_classification.value
        meta["prov:chai_confidence"] = str(decision.provenance.chai_confidence)
        meta["prov:chai_ai_probability"] = str(decision.provenance.chai_ai_probability)
        meta["prov:chai_edit_score"] = str(decision.provenance.chai_edit_score)
        meta["prov:sightengine_status"] = decision.provenance.sightengine_status
        if decision.provenance.sightengine_ai_probability is not None:
            meta["prov:sightengine_ai_probability"] = str(
                decision.provenance.sightengine_ai_probability
            )
        meta["prov:fusion_weight_chai"] = str(decision.provenance.fusion_weight_chai)
        meta["prov:fusion_weight_sightengine"] = str(
            decision.provenance.fusion_weight_sightengine
        )
        meta["prov:final_fused_probability"] = str(
            decision.provenance.final_fused_probability
        )
        meta["prov:decision_reason"] = decision.provenance.decision_reason

        logger.info(
            "pipeline.completed",
            extra={
                "event": "pipeline.completed",
                "request_id": get_request_id(),
                "verdict": decision.verdict.value,
                "confidence": round(decision.confidence, 6),
                "chai_verdict": fusion_result.verdict.value,
                "sightengine_status": decision.provenance.sightengine_status,
                "duration_ms": duration_ms,
                "detector_timings_ms": {
                    signal.detector_name: signal.processing_time_ms
                    for signal in signals
                },
                "active_detector_count": len(signals),
                "concurrency": self._max_concurrency,
            },
        )

        return PipelineResult(
            verdict=decision.verdict,
            confidence=decision.confidence,
            risk_level=decision.risk_level,
            explanation=decision.explanation
            if external_result is not None
            else explanation,
            duration_ms=duration_ms,
            scores=fusion_result.scores,
            indicators=fusion_result.indicators,
            evidence=decision.provenance.evidence,
            metadata=meta,
            heatmap=heatmap,
            report_data=self.build_report_data(signals, fusion_result),
            provenance=decision.provenance,
        )

    # ------------------------------------------------------------------
    # Detector execution (sequential or bounded parallel)
    # ------------------------------------------------------------------
    def run_detectors(
        self,
        image_bytes: bytes,
        *,
        content_type: str | None,
        file_name: str | None,
    ) -> list[DetectorSignal]:
        """Execute each detector, preserving the configured order.

        When :attr:`max_concurrency` is 1 the detectors run sequentially
        (the original behaviour). Otherwise independent detectors run inside a
        bounded thread pool and results are collected in *configured detector
        order*, so the concurrent and sequential runs produce identical output.
        """
        healthy = self._healthy_detectors(image_bytes)
        if self._max_concurrency <= 1 or len(healthy) <= 1:
            return self._run_sequential(
                healthy, image_bytes, content_type=content_type, file_name=file_name
            )
        return self._run_parallel(
            healthy, image_bytes, content_type=content_type, file_name=file_name
        )

    def _healthy_detectors(self, image_bytes: bytes) -> list[Detector]:
        """Return the detectors that are healthy to run for this image."""
        healthy: list[Detector] = []
        for detector in self._detectors:
            if not detector.health().is_healthy:
                logger.warning("Skipping unhealthy detector %s", detector.name)
                continue
            healthy.append(detector)
        return healthy

    def _run_sequential(
        self,
        detectors: Sequence[Detector],
        image_bytes: bytes,
        *,
        content_type: str | None,
        file_name: str | None,
    ) -> list[DetectorSignal]:
        """Execute detectors one after another in the given order."""
        signals: list[DetectorSignal] = []
        for detector in detectors:
            signal = detector.execute(
                image_bytes, content_type=content_type, file_name=file_name
            )
            signals.append(signal)
        return signals

    def _run_parallel(
        self,
        detectors: Sequence[Detector],
        image_bytes: bytes,
        *,
        content_type: str | None,
        file_name: str | None,
    ) -> list[DetectorSignal]:
        """Execute healthy detectors concurrently with bounded workers.

        Results are ordered by the *configured* detector sequence, not by
        completion order, keeping the fused output deterministic.
        """
        workers = min(self._max_concurrency, len(detectors))
        with ThreadPoolExecutor(
            max_workers=workers, thread_name_prefix="chai-detector"
        ) as executor:
            futures: dict[str, Future[DetectorSignal]] = {}
            for detector in detectors:
                futures[detector.name] = executor.submit(
                    detector.execute,
                    image_bytes,
                    content_type=content_type,
                    file_name=file_name,
                )
            signals = [futures[detector.name].result() for detector in detectors]
        return signals

    def _build_metadata(self, signals: Sequence[DetectorSignal]) -> dict[str, str]:
        """Merge the version trail and per-detector metadata into one map."""
        metadata = self.version_info.as_metadata()
        for signal in signals:
            metadata.update(signal.metadata)
        return metadata

    def build_report_data(
        self,
        signals: Sequence[DetectorSignal],
        fusion_result: FusionResult,
    ) -> PipelineReportData:
        """Snapshot the fused decision for the report layer.

        The report layer must never re-run fusion; this snapshot carries the
        three-class hypothesis scores, the runner-up, the classification margin
        and every per-detector contribution (with its processing time).
        """
        times_by_detector = {
            signal.detector_name: signal.processing_time_ms for signal in signals
        }
        contributions = tuple(
            _to_report_contribution(
                contribution, times_by_detector.get(contribution.detector, 0)
            )
            for contribution in fusion_result.contributions
        )
        return PipelineReportData(
            hypothesis_scores=fusion_result.hypothesis_scores,
            runner_up_verdict=fusion_result.runner_up_verdict,
            classification_margin=fusion_result.classification_margin,
            contributions=contributions,
        )


def _to_report_contribution(
    contribution: DetectorContribution,
    processing_time_ms: int,
) -> ReportContribution:
    """Map a fusion contribution onto its report snapshot."""
    return ReportContribution(
        detector=contribution.detector,
        detector_version=contribution.detector_version,
        category=contribution.category,
        normalized_score=contribution.normalized_score,
        detector_confidence=contribution.detector_confidence,
        reliability=contribution.reliability,
        weight_share=contribution.weight_share,
        contribution=contribution.contribution,
        direction=contribution.direction,
        hypothesis_weights=contribution.hypothesis_weights,
        preferred_hypothesis=contribution.preferred_hypothesis,
        processing_time_ms=processing_time_ms,
    )

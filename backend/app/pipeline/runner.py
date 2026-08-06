"""Modular pipeline runner.

``ModularAnalysisPipeline`` implements the service-facing :class:`AnalysisPipeline`
contract by orchestrating the forensic framework's stages:

    validation (implicit) → detector execution → signal collection → fusion →
    evidence → explanation → heatmap → assembly

It contains orchestration only: detector execution order is supplied externally
(via configuration), fusion/heatmap/evidence/explanation generators are injected,
and no forensic algorithm lives here. Removing a detector, adding one, or
swapping any framework stage requires no change to this runner.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Sequence

from app.pipeline.base import AnalysisPipeline, PipelineResult
from app.pipeline.config import PipelineConfig
from app.pipeline.detectors.base import Detector
from app.pipeline.explanation.base import EvidenceGenerator, ExplanationGenerator
from app.pipeline.fusion.base import FusionEngine
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
    ) -> None:
        self._detectors = tuple(detectors)
        self._fusion = fusion
        self._heatmap_generator = heatmap_generator
        self._evidence_generator = evidence_generator
        self._explanation_generator = explanation_generator
        self._config = pipeline_config

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

        signals = self._run_detectors(
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

        duration_ms = max(1, int((time.perf_counter() - started) * 1000))

        return PipelineResult(
            verdict=fusion_result.verdict,
            confidence=fusion_result.confidence,
            risk_level=fusion_result.risk_level,
            explanation=explanation,
            duration_ms=duration_ms,
            scores=fusion_result.scores,
            indicators=fusion_result.indicators,
            evidence=evidence,
            metadata=self._build_metadata(signals),
            heatmap=heatmap,
        )

    # ------------------------------------------------------------------
    # Stage helpers
    # ------------------------------------------------------------------
    def _run_detectors(
        self,
        image_bytes: bytes,
        *,
        content_type: str | None,
        file_name: str | None,
    ) -> list[DetectorSignal]:
        """Execute each detector in configured order, skipping unhealthy ones."""
        signals: list[DetectorSignal] = []
        for detector in self._detectors:
            if not detector.health().is_healthy:
                logger.warning("Skipping unhealthy detector %s", detector.name)
                continue
            signal = detector.execute(
                image_bytes, content_type=content_type, file_name=file_name
            )
            signals.append(signal)
        return signals

    def _build_metadata(self, signals: Sequence[DetectorSignal]) -> dict[str, str]:
        """Merge the version trail and per-detector metadata into one map."""
        metadata = self.version_info.as_metadata()
        for signal in signals:
            metadata.update(signal.metadata)
        return metadata

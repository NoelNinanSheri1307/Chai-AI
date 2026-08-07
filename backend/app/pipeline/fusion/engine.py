"""Deterministic forensic fusion engine.

The :class:`DeterministicFusionEngine` is the single component responsible for
turning detector signals into an explainable forensic verdict. It replaces the
placeholder engine and performs a fixed, fully transparent pipeline:

    1. normalize — map every detector output onto the shared ``[0, 1]`` scale.
    2. metrics   — aggregate the normalized signals (manipulation, agreement,
                   reliability, coverage).
    3. decide    — derive the verdict, confidence and risk from configuration.
    4. explain   — build per-detector contributions and ranked evidence.

Every step is a pure, deterministic function; no randomness, hidden weights or
external models are involved. The behavior is fully governed by
:class:`PipelineConfig`, so the engine can be re-calibrated without code changes
and every result it produces is reproducible from its inputs.
"""

from __future__ import annotations

from collections.abc import Sequence

from app.pipeline.base import ScoreResult
from app.pipeline.config import PipelineConfig
from app.pipeline.fusion.base import FusionEngine, FusionResult
from app.pipeline.signals import DetectorSignal
from app.pipeline.versioning import ComponentVersion

from .decision import make_decision
from .evidence import aggregate_evidence, build_contributions
from .metrics import compute_metrics
from .normalize import normalize_signal


class DeterministicFusionEngine(FusionEngine):
    """Deterministic, configuration-driven forensic fusion."""

    def __init__(self, config: PipelineConfig) -> None:
        self._config = config

    def fuse(self, signals: Sequence[DetectorSignal]) -> FusionResult:
        """Fuse ``signals`` into the final decision, contributions and evidence."""
        normalized = [
            normalize_signal(signal, self._config.reliability_for(signal.detector_name))
            for signal in signals
        ]

        total_capacity = len(self._config.enabled_detector_names())
        metrics = compute_metrics(normalized, total_capacity)
        decision = make_decision(metrics, self._config)

        contributions = build_contributions(
            normalized, self._config.manipulation_support_threshold
        )
        evidence = aggregate_evidence(normalized, contributions)

        scores = [ScoreResult(category=s.category, value=s.score) for s in normalized]
        weights = {s.category.value: s.reliability for s in normalized}
        detector_versions = [
            ComponentVersion(name=c.detector, version=c.detector_version).as_metadata()
            for c in contributions
        ]

        return FusionResult(
            verdict=decision.verdict,
            confidence=decision.confidence,
            risk_level=decision.risk_level,
            scores=scores,
            indicators=[ind for signal in signals for ind in signal.indicators],
            weights=weights,
            contributions=contributions,
            evidence=evidence,
            manipulation=metrics.manipulation,
            agreement=metrics.agreement,
            reliability=metrics.reliability,
            coverage=metrics.coverage,
            decision_reason=decision.reason,
            fusion_version=self._config.fusion_version,
            weight_config_version=self._config.weight_config_version,
            pipeline_version=self._config.pipeline_version,
            detector_versions=detector_versions,
        )

    # Keep the interface explicit: only ``fuse`` is public.
    @property
    def config(self) -> PipelineConfig:
        """Return the configuration driving this engine."""
        return self._config

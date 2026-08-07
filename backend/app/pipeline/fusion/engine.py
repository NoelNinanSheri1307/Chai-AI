"""Deterministic forensic fusion engine.

The :class:`DeterministicFusionEngine` is the single component responsible for
turning detector signals into an explainable forensic verdict. It performs a
fixed, fully transparent pipeline:

    1. normalize — map every detector output onto the shared ``[0, 1]`` scale.
    2. classify  — accumulate per-hypothesis evidence through the contribution
                   matrix and rank Original / AI Edited / AI Generated.
    3. decide    — derive verdict, confidence, margin and risk from the
                   classifier (see :mod:`app.pipeline.fusion.decision`).
    4. explain   — build per-detector contributions, class-aware reasoning and
                   ranked evidence.

Every step is a pure, deterministic function; no randomness, hidden weights or
external models are involved. The behavior is fully governed by
:class:`PipelineConfig`, so the engine can be re-calibrated without code changes
and every result it produces is reproducible from its inputs.
"""

from __future__ import annotations

from collections.abc import Sequence

from app.core.enums import Verdict
from app.pipeline.base import ScoreResult
from app.pipeline.config import PipelineConfig
from app.pipeline.fusion.base import FusionEngine, FusionResult
from app.pipeline.signals import DetectorSignal
from app.pipeline.versioning import ComponentVersion

from .decision import make_decision
from .evidence import aggregate_evidence, build_contributions
from .metrics import compute_metrics
from .normalize import normalize_signal

# Index of each verdict inside the (original, ai_edited, ai_generated) tuple.
_VERDICT_HYPOTHESIS_INDEX = {
    Verdict.ORIGINAL: 0,
    Verdict.AI_EDITED: 1,
    Verdict.AI_GENERATED: 2,
}


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
        decision = make_decision(normalized, self._config, total_capacity)

        contributions = build_contributions(
            normalized,
            self._config.manipulation_support_threshold,
            decision.detector_contributions,
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
            hypothesis_scores=decision.hypothesis_scores,
            runner_up_verdict=decision.runner_up_verdict,
            classification_margin=decision.classification_margin,
            detector_reasoning=_build_detector_reasoning(
                contributions, decision.verdict
            ),
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


def _build_detector_reasoning(
    contributions: list,
    verdict: Verdict,
) -> list[dict[str, object]]:
    """Expose why each detector supported/opposed the winning class.

    Each entry is a deterministic, machine-readable record intended for future
    frontend visualization: the detector name, its normalized score, its
    class-weighted support percentages and whether it supported the winning
    hypothesis.
    """
    winning_index = _VERDICT_HYPOTHESIS_INDEX[verdict]
    reasoning: list[dict[str, object]] = []
    for contribution in contributions:
        weights = contribution.hypothesis_weights
        reasoning.append(
            {
                "detector": contribution.detector,
                "normalized_score": round(contribution.normalized_score, 4),
                "preferred_hypothesis": contribution.preferred_hypothesis,
                "hypothesis_weights": {
                    "original": round(weights[0], 4),
                    "ai_edited": round(weights[1], 4),
                    "ai_generated": round(weights[2], 4),
                },
                "supports_winner": weights[winning_index] == max(weights),
            }
        )
    return reasoning

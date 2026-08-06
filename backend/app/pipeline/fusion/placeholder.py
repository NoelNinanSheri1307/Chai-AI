"""Deterministic placeholder fusion engine.

This engine demonstrates the fusion pipeline without performing real weighting
math: it collects per-category scores and indicators from the signals, applies
the configured category weights for transparency, and emits a fixed placeholder
decision (verdict and confidence from configuration). The risk level is derived
from the confidence using the configured thresholds, so the threshold framework
is exercised end to end.

A later milestone replaces this decision logic with the real fusion model while
keeping the :class:`FusionEngine` interface and this assembly unchanged.
"""

from __future__ import annotations

from collections.abc import Sequence

from app.pipeline.base import ScoreResult
from app.pipeline.config import PipelineConfig
from app.pipeline.fusion.base import FusionEngine, FusionResult
from app.pipeline.signals import DetectorSignal


def _clamp01(value: float) -> float:
    """Clamp a float into the closed unit interval ``[0, 1]``."""
    return max(0.0, min(1.0, value))


class PlaceholderFusionEngine(FusionEngine):
    """Deterministic, configuration-driven placeholder fusion."""

    def __init__(self, config: PipelineConfig) -> None:
        self._config = config

    def fuse(self, signals: Sequence[DetectorSignal]) -> FusionResult:
        """Fuse ``signals`` into a deterministic placeholder decision."""
        scores = [
            ScoreResult(category=signal.category, value=_clamp01(signal.score))
            for signal in signals
        ]
        indicators = [
            indicator for signal in signals for indicator in signal.indicators
        ]
        weights = {
            signal.category.value: self._config.weight_for(signal.category.value)
            for signal in signals
        }

        confidence = _clamp01(self._config.default_confidence)
        verdict = self._config.default_verdict
        risk_level = self._config.risk_level_for(confidence)

        return FusionResult(
            verdict=verdict,
            confidence=confidence,
            risk_level=risk_level,
            scores=scores,
            indicators=indicators,
            weights=weights,
        )

"""Deterministic placeholder evidence and explanation generators."""

from __future__ import annotations

from collections.abc import Sequence

from app.pipeline.config import PipelineConfig
from app.pipeline.explanation.base import EvidenceGenerator, ExplanationGenerator
from app.pipeline.fusion.base import FusionResult
from app.pipeline.signals import DetectorSignal


class PlaceholderEvidenceGenerator(EvidenceGenerator):
    """Configuration-driven placeholder evidence."""

    def __init__(self, config: PipelineConfig) -> None:
        self._config = config

    def generate(
        self,
        fusion: FusionResult,
        signals: Sequence[DetectorSignal],
    ) -> list[str]:
        """Return the configured placeholder evidence lines."""
        return list(self._config.placeholder_evidence)


class PlaceholderExplanationGenerator(ExplanationGenerator):
    """Configuration-driven placeholder explanation."""

    def __init__(self, config: PipelineConfig) -> None:
        self._config = config

    def explain(
        self,
        fusion: FusionResult,
        evidence: Sequence[str],
        signals: Sequence[DetectorSignal],
    ) -> str:
        """Return the configured placeholder explanation text."""
        return self._config.placeholder_explanation

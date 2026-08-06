"""Abstract explainability contracts."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from app.pipeline.fusion.base import FusionResult
from app.pipeline.signals import DetectorSignal


class EvidenceGenerator(ABC):
    """Emit machine-readable forensic evidence lines."""

    @abstractmethod
    def generate(
        self,
        fusion: FusionResult,
        signals: Sequence[DetectorSignal],
    ) -> list[str]:
        """Return the evidence lines recovered from ``fusion`` and ``signals``."""


class ExplanationGenerator(ABC):
    """Compose a human-readable explanation of a result."""

    @abstractmethod
    def explain(
        self,
        fusion: FusionResult,
        evidence: Sequence[str],
        signals: Sequence[DetectorSignal],
    ) -> str:
        """Return the narrative explanation for the given result."""

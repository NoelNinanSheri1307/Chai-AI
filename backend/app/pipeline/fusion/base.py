"""Abstract fusion engine contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass, field

from app.core.enums import RiskLevel, Verdict
from app.pipeline.base import IndicatorResult, ScoreResult
from app.pipeline.signals import DetectorSignal


@dataclass(frozen=True)
class FusionResult:
    """The fused, final decision produced from collected signals."""

    verdict: Verdict
    confidence: float
    risk_level: RiskLevel
    scores: list[ScoreResult] = field(default_factory=list)
    indicators: list[IndicatorResult] = field(default_factory=list)
    weights: dict[str, float] = field(default_factory=dict)


class FusionEngine(ABC):
    """Aggregate detector signals into a verdict, confidence and risk.

    Implementations are deterministic for identical input and never touch HTTP,
    FastAPI, the database or object storage.
    """

    @abstractmethod
    def fuse(self, signals: Sequence[DetectorSignal]) -> FusionResult:
        """Fuse ``signals`` and return the final :class:`FusionResult`."""

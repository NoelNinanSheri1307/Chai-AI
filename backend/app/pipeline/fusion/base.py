"""Abstract fusion engine contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass, field

from app.core.enums import RiskLevel, ScoreCategory, Verdict
from app.pipeline.base import IndicatorResult, ScoreResult
from app.pipeline.signals import DetectorSignal


@dataclass(frozen=True)
class DetectorContribution:
    """A single detector's contribution to the fused decision.

    Used for explainability and UI: it records *which* detector contributed,
    *how much* and *why*.
    """

    detector: str
    detector_version: str
    category: ScoreCategory
    normalized_score: float
    detector_confidence: float
    reliability: float
    weight_share: float  # reliability / total active weight (0..1)
    contribution: float  # this detector's share of fused manipulation (0..1)
    direction: str  # supports:manipulation | supports:original

    def supports_manipulation(self) -> bool:
        """Whether this detector's signal favoured manipulation."""
        return self.direction == "supports:manipulation"


@dataclass(frozen=True)
class FusionResult:
    """The fused, final decision produced from collected signals."""

    verdict: Verdict
    confidence: float
    risk_level: RiskLevel
    scores: list[ScoreResult] = field(default_factory=list)
    indicators: list[IndicatorResult] = field(default_factory=list)
    weights: dict[str, float] = field(default_factory=dict)
    # ------------------------------------------------------------------
    # Explainability / transparency
    # ------------------------------------------------------------------
    contributions: list[DetectorContribution] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    manipulation: float = 0.0  # weighted manipulation mean in [0, 1]
    agreement: float = 0.0  # detector agreement / consistency in [0, 1]
    reliability: float = 0.0  # weighted detector self-confidence in [0, 1]
    coverage: float = 0.0  # fraction of intended detectors active in [0, 1]
    decision_reason: str = ""  # human-readable rationale for the verdict

    # ------------------------------------------------------------------
    # Versioning
    # ------------------------------------------------------------------
    fusion_version: str = ""
    weight_config_version: str = ""
    pipeline_version: str = ""
    detector_versions: list[str] = field(default_factory=list)


class FusionEngine(ABC):
    """Aggregate detector signals into a verdict, confidence and risk.

    Implementations are deterministic for identical input and never touch HTTP,
    FastAPI, the database or object storage.
    """

    @abstractmethod
    def fuse(self, signals: Sequence[DetectorSignal]) -> FusionResult:
        """Fuse ``signals`` and return the final :class:`FusionResult`."""

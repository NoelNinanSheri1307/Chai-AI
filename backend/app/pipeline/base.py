"""Analysis pipeline contract and result value objects.

The pipeline is the only component that produces forensic results. It is kept
isolated from HTTP, the database and object storage so that any implementation
can be unit-tested and swapped independently.

Services depend on the abstract :class:`AnalysisPipeline`; the concrete
implementation is selected through dependency injection. ``PipelineResult`` and
its nested value objects are plain, immutable data carriers that the service
layer maps onto ORM entities and API DTOs.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from app.core.enums import (
    IndicatorSeverity,
    IndicatorType,
    RiskLevel,
    ScoreCategory,
    Verdict,
)


@dataclass(frozen=True)
class ScoreResult:
    """A single per-category confidence measurement."""

    category: ScoreCategory
    value: float


@dataclass(frozen=True)
class IndicatorResult:
    """A discrete manipulation signal detected by the pipeline."""

    type: IndicatorType
    confidence: float
    severity: IndicatorSeverity
    description: str


@dataclass(frozen=True)
class HeatmapRegionResult:
    """A normalized manipulation rectangle within the image."""

    x: float
    y: float
    width: float
    height: float
    intensity: float
    label: str


@dataclass(frozen=True)
class HeatmapResult:
    """Aggregate manipulation heatmap for an analysis (may be empty)."""

    overall_manipulation: float
    regions: list[HeatmapRegionResult] = field(default_factory=list)


@dataclass(frozen=True)
class ReportContribution:
    """A single detector's contribution as recorded for the forensic report.

    This is the persistence/report-facing snapshot of a fusion contribution: it
    carries every field the report needs (including the detector's own
    processing time) without depending on the fusion engine internals.
    """

    detector: str
    detector_version: str
    category: ScoreCategory
    normalized_score: float
    detector_confidence: float
    reliability: float
    weight_share: float
    contribution: float
    direction: str
    hypothesis_weights: tuple[float, float, float]
    preferred_hypothesis: str
    processing_time_ms: int = 0


@dataclass(frozen=True)
class PipelineReportData:
    """The forensic report snapshot produced alongside an analysis result.

    Built by the pipeline from the fused decision so the report layer never
    needs to re-run fusion. ``hypothesis_scores`` holds the normalized support
    for (original, ai_edited, ai_generated); ``contributions`` are ordered by
    decreasing influence (strongest first).
    """

    hypothesis_scores: tuple[float, float, float] = (0.0, 0.0, 0.0)
    runner_up_verdict: Verdict | None = None
    classification_margin: float = 0.0
    contributions: tuple[ReportContribution, ...] = ()


@dataclass(frozen=True)
class PipelineResult:
    """The complete, validated output of an analysis pipeline."""

    verdict: Verdict
    confidence: float
    risk_level: RiskLevel
    explanation: str
    duration_ms: int
    scores: list[ScoreResult] = field(default_factory=list)
    indicators: list[IndicatorResult] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)
    heatmap: HeatmapResult | None = None
    report_data: PipelineReportData | None = None


class AnalysisPipeline(ABC):
    """Abstract contract for forensic image analysis.

    Implementations receive the raw image bytes plus upload context and return
    a :class:`PipelineResult`. They must never touch HTTP, FastAPI, the database
    or object storage; persistence and DTO mapping are the service layer's
    responsibility.
    """

    @abstractmethod
    def analyze(
        self,
        image_bytes: bytes,
        *,
        content_type: str | None = None,
        file_name: str | None = None,
    ) -> PipelineResult:
        """Analyze ``image_bytes`` and return the resulting verdict and signals."""

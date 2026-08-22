"""Report DTOs.

The canonical home of the forensic report shapes. ``ShareTextResponse`` is part
of the frozen API contract; the rest are typed report DTOs produced by
:class:`ReportService` and surfaced by the reports endpoints. They are stable,
deterministic and never carry ORM objects, secrets or filesystem paths.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import RiskLevel, Verdict


class ShareTextResponse(BaseModel):
    """Shareable plain-text summary of an analysis."""

    model_config = ConfigDict(extra="forbid")

    text: str


class EvidenceItemDTO(BaseModel):
    """A single piece of forensic evidence (supporting or contradicting)."""

    model_config = ConfigDict(extra="forbid")

    source_detector: str | None = None
    text: str
    importance: float = Field(ge=0.0, le=1.0)
    contribution: float | None = Field(default=None, ge=0.0, le=1.0)
    severity: str | None = None
    supports_verdict: bool


class ClassificationSummaryDTO(BaseModel):
    """The clean, deterministic classification summary."""

    model_config = ConfigDict(extra="forbid")

    verdict: Verdict
    classification: str
    confidence: float = Field(ge=0.0, le=1.0)
    confidence_percent: int = Field(ge=0, le=100)
    risk: RiskLevel
    margin: float | None = Field(default=None, ge=0.0, le=1.0)
    summary: str


class ClassificationComparisonDTO(BaseModel):
    """The two-class comparison: winner, runner-up and margin.

    Values are the classifier's normalized support scores, not calibrated
    posterior probabilities; ``note`` states this explicitly.
    """

    model_config = ConfigDict(extra="forbid")

    original: float = Field(ge=0.0, le=1.0)
    ai_generated: float = Field(ge=0.0, le=1.0)
    winner: str
    runner_up: str | None = None
    margin: float | None = Field(default=None, ge=0.0, le=1.0)
    note: str


class DetectorContributionDTO(BaseModel):
    """A structured per-detector contribution breakdown.

    The frontend can render this without performing any fusion math itself.
    """

    model_config = ConfigDict(extra="forbid")

    detector: str
    detector_version: str
    normalized_score: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    reliability_weight: float = Field(ge=0.0)
    weight_share: float = Field(ge=0.0, le=1.0)
    contribution: float = Field(ge=0.0, le=1.0)
    contribution_original: float = Field(ge=0.0, le=1.0)
    contribution_ai_generated: float = Field(ge=0.0, le=1.0)
    contribution_winning_class: float = Field(ge=0.0, le=1.0)
    direction: str
    preferred_hypothesis: str
    reasoning: str
    processing_time_ms: int | None = None


class HeatmapRegionReportDTO(BaseModel):
    """A localized suspicious region with coordinates, severity and attribution."""

    model_config = ConfigDict(extra="forbid")

    x: float = Field(ge=0.0, le=1.0)
    y: float = Field(ge=0.0, le=1.0)
    width: float = Field(ge=0.0, le=1.0)
    height: float = Field(ge=0.0, le=1.0)
    intensity: float = Field(ge=0.0, le=1.0)
    severity: str | None = None
    label: str
    detectors: list[str] = Field(default_factory=list)


class HeatmapReportSummaryDTO(BaseModel):
    """A deterministic narrative summary of the spatial findings."""

    model_config = ConfigDict(extra="forbid")

    present: bool
    overall_manipulation: float = Field(ge=0.0, le=1.0)
    region_count: int = Field(ge=0)
    regions: list[HeatmapRegionReportDTO] = Field(default_factory=list)
    detector_attribution: list[str] = Field(default_factory=list)
    narrative: str


class ImageMetadataReportSummaryDTO(BaseModel):
    """Image metadata summary distinguishing present, absent and suspicious."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["present", "absent", "suspicious"]
    exif_present: bool
    camera_present: bool
    software_present: bool
    has_suspicious_entries: bool
    suspicious_entries: list[str] = Field(default_factory=list)
    items: dict[str, str] = Field(default_factory=dict)
    narrative: str


class DetectorExecutionDTO(BaseModel):
    """Processing-time record for a single detector."""

    model_config = ConfigDict(extra="forbid")

    detector: str
    processing_time_ms: int


class ProcessingReportSummaryDTO(BaseModel):
    """The lightweight processing statistics of the analysis run."""

    model_config = ConfigDict(extra="forbid")

    total_analysis_ms: int
    active_detector_count: int = Field(ge=0)
    detector_execution: list[DetectorExecutionDTO] = Field(default_factory=list)
    pipeline_version: str = ""
    fusion_version: str = ""
    framework_version: str = ""
    detector_versions: list[str] = Field(default_factory=list)


class ForensicReportDTO(BaseModel):
    """The complete, structured forensic report for one analysis."""

    model_config = ConfigDict(extra="forbid")

    analysis_id: str
    timestamp: str
    pipeline_version: str = ""
    classification: ClassificationSummaryDTO
    comparison: ClassificationComparisonDTO
    supporting_evidence: list[EvidenceItemDTO] = Field(default_factory=list)
    contradicting_evidence: list[EvidenceItemDTO] = Field(default_factory=list)
    detector_contributions: list[DetectorContributionDTO] = Field(default_factory=list)
    heatmap: HeatmapReportSummaryDTO | None = None
    image_metadata: ImageMetadataReportSummaryDTO
    processing: ProcessingReportSummaryDTO

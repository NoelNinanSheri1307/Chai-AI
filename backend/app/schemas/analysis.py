"""Analysis DTOs mirroring the Flutter frontend and the API contract.

Implements the ``AnalysisResult`` graph (Section 12 of the architecture spec)
together with its forensic score, indicator, evidence and heatmap components.
Field names use the camelCase shapes published in the API contract; ``imageBytes``
is an in-memory client field and is never serialized into the JSON payload.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import RiskLevel, ScoreCategory, Verdict

#: Indicator severity as serialized by the API (capitalized labels).
SeverityLabel = Literal["Low", "Moderate", "Strong"]


class ForensicScoreDTO(BaseModel):
    """A per-category forensic confidence measurement."""

    category: ScoreCategory
    value: float = Field(ge=0.0, le=1.0)


class DetectedIndicatorDTO(BaseModel):
    """A discrete manipulation signal found by the pipeline."""

    type: Literal[
        "frequency", "texture", "metadata", "diffusion", "compression", "lighting"
    ]
    confidence: float = Field(ge=0.0, le=1.0)
    severity: SeverityLabel
    description: str = Field(min_length=1)


class HeatmapRegionDTO(BaseModel):
    """A normalized manipulation rectangle within the image."""

    x: float = Field(ge=0.0, le=1.0)
    y: float = Field(ge=0.0, le=1.0)
    width: float = Field(ge=0.0, le=1.0)
    height: float = Field(ge=0.0, le=1.0)
    intensity: float = Field(ge=0.0, le=1.0)
    label: str = Field(min_length=1)


class HeatmapDataDTO(BaseModel):
    """Aggregate manipulation heatmap for an analysis."""

    regions: list[HeatmapRegionDTO] = Field(default_factory=list)
    overallManipulation: float = Field(ge=0.0, le=1.0)


class DecisionProvenanceDTO(BaseModel):
    """Provenance and audit trail for the external-assisted classification decision."""

    model_config = ConfigDict(extra="forbid")

    finalClassification: Verdict
    finalConfidence: float = Field(ge=0.0, le=1.0)
    chaiClassification: Verdict
    chaiConfidence: float = Field(ge=0.0, le=1.0)
    chaiAiProbability: float = Field(ge=0.0, le=1.0)
    chaiEditScore: float = Field(ge=0.0, le=1.0)
    sightengineStatus: str
    sightengineAiProbability: float | None = None
    fusionWeightChai: float
    fusionWeightSightengine: float
    finalFusedProbability: float = Field(ge=0.0, le=1.0)
    decisionReason: str
    evidence: list[str] = Field(default_factory=list)


class AnalysisResultDTO(BaseModel):
    """Full analysis result returned to the client."""

    model_config = ConfigDict(extra="forbid")

    id: str
    imagePath: str | None = None
    fileName: str | None = None
    verdict: Verdict
    confidence: float = Field(ge=0.0, le=1.0)
    riskLevel: RiskLevel
    explanation: str = Field(min_length=1)
    analysisDuration: str
    timestamp: str
    scores: list[ForensicScoreDTO] = Field(default_factory=list)
    indicators: list[DetectedIndicatorDTO] = Field(default_factory=list)
    heatmap: HeatmapDataDTO | None = None
    evidence: list[str] = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)
    provenance: DecisionProvenanceDTO | None = None

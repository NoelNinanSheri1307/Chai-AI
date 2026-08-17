"""Data models and schemas for the automated benchmark dataset and evaluation harness.

Provides strong typing for ground-truth labels, manifest entries, benchmark
image results, confusion matrices, and run evaluation reports.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class GroundTruthLabel(str, Enum):
    """Authoritative ground-truth label categories for benchmark images."""

    ORIGINAL = "original"
    AI_GENERATED = "ai_generated"
    AI_EDITED = "ai_edited"
    REAL_TRANSFORMED = "real_transformed"
    SCREENSHOTS = "screenshots"
    DIFFICULT_CASES = "difficult_cases"
    REAL_MANIPULATED = "real_manipulated"

    @property
    def is_three_class_compatible(self) -> bool:
        """Return True if label directly maps to Chai's 3-class classifier."""
        return self in {
            GroundTruthLabel.ORIGINAL,
            GroundTruthLabel.AI_GENERATED,
            GroundTruthLabel.AI_EDITED,
        }


class ManifestEntry(BaseModel):
    """A single labeled image entry in the benchmark dataset manifest."""

    model_config = ConfigDict(extra="forbid")

    id: str
    sha256: str
    path: str
    dataset: str
    source_url: str | None = None
    ground_truth: GroundTruthLabel
    license: str | None = None
    width: int
    height: int
    format: str
    file_size_bytes: int
    split: str = "benchmark"
    metadata: dict[str, str] = Field(default_factory=dict)


class BenchmarkManifest(BaseModel):
    """A collection of manifest entries constituting a benchmark dataset."""

    model_config = ConfigDict(extra="forbid")

    version: str = "1.0"
    created_at: str
    description: str
    entries: list[ManifestEntry] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DetectorScoreRecord(BaseModel):
    """Captured output from a single forensic detector for an image."""

    model_config = ConfigDict(extra="forbid")

    detector_name: str
    raw_score: float
    normalized_score: float
    confidence: float
    evidence: list[str] = Field(default_factory=list)
    processing_time_ms: int = 0


class ImageBenchmarkResult(BaseModel):
    """Evaluation result for one image analyzed through Chai's pipeline."""

    model_config = ConfigDict(extra="forbid")

    image_id: str
    sha256: str
    dataset: str
    ground_truth: GroundTruthLabel
    file_path: str
    chai_verdict: str
    chai_confidence: float
    chai_risk_level: str
    analysis_duration_ms: int
    detector_scores: dict[str, float] = Field(default_factory=dict)
    detector_details: list[DetectorScoreRecord] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    heatmap_region_count: int = 0
    overall_manipulation_score: float = 0.0
    external_result: dict[str, Any] | None = None
    is_binary_match: bool | None = None
    is_three_class_match: bool | None = None


class ConfusionMatrixData(BaseModel):
    """3x3 or 2x2 confusion matrix counts."""

    labels: list[str]
    matrix: list[list[int]]


class BenchmarkRunResult(BaseModel):
    """Complete aggregated evaluation report for a benchmark run."""

    model_config = ConfigDict(extra="forbid")

    run_id: str
    timestamp: str
    pipeline_version: str
    manifest_hash: str
    total_images: int
    successful_analyses: int
    failed_analyses: int
    duration_seconds: float
    results: list[ImageBenchmarkResult] = Field(default_factory=list)
    overall_accuracy: float = 0.0
    macro_f1: float = 0.0
    weighted_f1: float = 0.0
    per_class_metrics: dict[str, dict[str, float]] = Field(default_factory=dict)
    confusion_matrix: ConfusionMatrixData
    detector_statistics: dict[str, dict[str, Any]] = Field(default_factory=dict)
    failure_cases: dict[str, list[dict[str, Any]]] = Field(default_factory=dict)

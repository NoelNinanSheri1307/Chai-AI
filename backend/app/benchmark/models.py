"""Data models and schemas for the automated benchmark dataset and evaluation harness.

Provides strong typing for ground-truth labels, manifest entries, benchmark
image results, 2x2 confusion matrices, detector statistics, confidence analysis,
and evaluation reports.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class GroundTruthLabel(str, Enum):
    """Authoritative ground-truth label categories for benchmark images (2-Class)."""

    ORIGINAL = "original"
    AI_GENERATED = "ai_generated"

    @property
    def is_two_class_compatible(self) -> bool:
        """Return True if label maps to Chai's 2-class classifier."""
        return self in {
            GroundTruthLabel.ORIGINAL,
            GroundTruthLabel.AI_GENERATED,
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

    version: str = "2.0"
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
    predicted_class: str
    correct: bool
    confidence: float
    risk_level: str
    analysis_duration_ms: int
    detector_scores: dict[str, float] = Field(default_factory=dict)
    detector_confidences: dict[str, float] = Field(default_factory=dict)
    detector_details: list[DetectorScoreRecord] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    heatmap_region_count: int = 0
    overall_manipulation_score: float = 0.0
    error: str | None = None
    external_result: dict[str, Any] | None = None


class ConfusionMatrixData(BaseModel):
    """2x2 confusion matrix counts: rows = Actual, cols = Predicted."""

    labels: list[str] = Field(default_factory=lambda: ["original", "ai_generated"])
    matrix: list[list[int]] = Field(default_factory=lambda: [[0, 0], [0, 0]])


class ConfidenceAnalysis(BaseModel):
    """Confidence statistics across correct and incorrect predictions."""

    model_config = ConfigDict(extra="forbid")

    mean_confidence_correct: float = 0.0
    mean_confidence_incorrect: float = 0.0
    high_confidence_failures_count: int = 0
    low_confidence_correct_count: int = 0


class BenchmarkRunResult(BaseModel):
    """Complete aggregated evaluation report for a benchmark run."""

    model_config = ConfigDict(extra="forbid")

    run_id: str
    timestamp: str
    pipeline_version: str
    manifest_hash: str
    total_images: int
    real_count: int = 0
    ai_generated_count: int = 0
    successful_analyses: int
    failed_analyses: int
    skipped_count: int = 0
    duplicate_count: int = 0
    cross_category_duplicates: list[str] = Field(default_factory=list)
    duration_seconds: float
    results: list[ImageBenchmarkResult] = Field(default_factory=list)
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0
    macro_f1: float = 0.0
    weighted_f1: float = 0.0
    tp: int = 0
    tn: int = 0
    fp: int = 0
    fn: int = 0
    per_class_metrics: dict[str, dict[str, float]] = Field(default_factory=dict)
    confusion_matrix: ConfusionMatrixData = Field(default_factory=ConfusionMatrixData)
    confidence_analysis: ConfidenceAnalysis = Field(default_factory=ConfidenceAnalysis)
    detector_statistics: dict[str, dict[str, Any]] = Field(default_factory=dict)
    failure_cases: dict[str, list[dict[str, Any]]] = Field(default_factory=dict)
    calibration_candidates: list[str] = Field(default_factory=list)

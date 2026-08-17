"""Unit tests for the Milestone 12 automated benchmark dataset & evaluation harness."""

from __future__ import annotations

from pathlib import Path
import pytest

from app.benchmark.downloader import DATASET_SOURCES
from app.benchmark.manifest import (
    compute_manifest_hash,
    create_manifest,
    sample_manifest,
)
from app.benchmark.metrics import compute_benchmark_run_result
from app.benchmark.models import (
    BenchmarkManifest,
    BenchmarkRunResult,
    GroundTruthLabel,
    ImageBenchmarkResult,
    ManifestEntry,
)
from app.benchmark.reports import generate_markdown_report
from app.benchmark.runner import run_benchmark
from app.benchmark.validation import (
    ImageValidationError,
    calculate_sha256,
    inspect_and_validate_image,
)
from tests.sample_images import GARBAGE_BYTES, JPEG_BYTES, PNG_BYTES


def test_image_validation_and_metadata_extraction() -> None:
    meta = inspect_and_validate_image(JPEG_BYTES)
    assert meta["width"] > 0
    assert meta["height"] > 0
    assert meta["format"] in {"JPEG", "PNG", "WEBP"}
    assert meta["file_size_bytes"] == len(JPEG_BYTES)

    with pytest.raises(ImageValidationError):
        inspect_and_validate_image(GARBAGE_BYTES)


def test_duplicate_sha256_hash_calculation() -> None:
    hash1 = calculate_sha256(JPEG_BYTES)
    hash2 = calculate_sha256(JPEG_BYTES)
    hash3 = calculate_sha256(PNG_BYTES)

    assert len(hash1) == 64
    assert hash1 == hash2
    assert hash1 != hash3


def test_manifest_creation_and_sampling() -> None:
    entry1 = ManifestEntry(
        id="m1",
        sha256="hash1",
        path="tests/fixtures/sample_a.jpg",
        dataset="test_ds",
        ground_truth=GroundTruthLabel.ORIGINAL,
        width=100,
        height=100,
        format="JPEG",
        file_size_bytes=1000,
    )
    entry2 = ManifestEntry(
        id="m2",
        sha256="hash2",
        path="tests/fixtures/sample_b.png",
        dataset="test_ds",
        ground_truth=GroundTruthLabel.AI_GENERATED,
        width=100,
        height=100,
        format="PNG",
        file_size_bytes=1200,
    )

    manifest = create_manifest([entry1, entry2], description="Test manifest")
    assert len(manifest.entries) == 2

    # Deterministic sampling with seed
    sampled = sample_manifest(manifest, limit=1, seed=42)
    assert len(sampled.entries) == 1

    # Manifest hash deterministic check
    h1 = compute_manifest_hash(manifest)
    h2 = compute_manifest_hash(manifest)
    assert h1 == h2


def test_ground_truth_label_compatibility() -> None:
    assert GroundTruthLabel.ORIGINAL.is_three_class_compatible is True
    assert GroundTruthLabel.AI_GENERATED.is_three_class_compatible is True
    assert GroundTruthLabel.AI_EDITED.is_three_class_compatible is True
    assert GroundTruthLabel.SCREENSHOTS.is_three_class_compatible is False
    assert GroundTruthLabel.REAL_TRANSFORMED.is_three_class_compatible is False
    assert GroundTruthLabel.DIFFICULT_CASES.is_three_class_compatible is False


def test_metrics_and_confusion_matrix_calculation() -> None:
    res1 = ImageBenchmarkResult(
        image_id="img1",
        sha256="hash1",
        dataset="ds1",
        ground_truth=GroundTruthLabel.ORIGINAL,
        file_path="a.jpg",
        chai_verdict="original",
        chai_confidence=0.90,
        chai_risk_level="low",
        analysis_duration_ms=100,
        detector_scores={
            "metadata": 0.1, "frequency": 0.2, "ela": 0.1,
            "noise": 0.15, "compression": 0.1, "texture": 0.2, "lighting": 0.1
        },
        is_three_class_match=True,
    )
    res2 = ImageBenchmarkResult(
        image_id="img2",
        sha256="hash2",
        dataset="ds1",
        ground_truth=GroundTruthLabel.AI_GENERATED,
        file_path="b.jpg",
        chai_verdict="ai_generated",
        chai_confidence=0.95,
        chai_risk_level="high",
        analysis_duration_ms=120,
        detector_scores={
            "metadata": 0.8, "frequency": 0.9, "ela": 0.85,
            "noise": 0.9, "compression": 0.8, "texture": 0.85, "lighting": 0.9
        },
        is_three_class_match=True,
    )
    res3 = ImageBenchmarkResult(
        image_id="img3",
        sha256="hash3",
        dataset="ds1",
        ground_truth=GroundTruthLabel.ORIGINAL,
        file_path="c.jpg",
        chai_verdict="ai_generated",
        chai_confidence=0.85,
        chai_risk_level="high",
        analysis_duration_ms=110,
        detector_scores={
            "metadata": 0.7, "frequency": 0.8, "ela": 0.75,
            "noise": 0.7, "compression": 0.7, "texture": 0.8, "lighting": 0.7
        },
        is_three_class_match=False,  # False Positive
    )

    run_res = compute_benchmark_run_result(
        run_id="run_test",
        timestamp="2026-08-17T00:00:00Z",
        manifest_hash="hash_manifest",
        duration_seconds=1.5,
        successful_count=3,
        failed_count=0,
        results=[res1, res2, res3],
    )

    assert run_res.total_images == 3
    assert run_res.overall_accuracy == pytest.approx(2 / 3, abs=0.01)
    assert run_res.confusion_matrix.labels == ["original", "ai_edited", "ai_generated"]
    assert len(run_res.confusion_matrix.matrix) == 3

    # Check detector statistics computed for all 7 detectors
    for det in ["metadata", "frequency", "ela", "noise", "compression", "texture", "lighting"]:
        assert det in run_res.detector_statistics
        assert "original_mean" in run_res.detector_statistics[det]
        assert "ai_generated_mean" in run_res.detector_statistics[det]

    # Check failure cases extraction
    fps = run_res.failure_cases.get("false_positives", [])
    assert len(fps) == 1
    assert fps[0]["image_id"] == "img3"


def test_markdown_report_generation() -> None:
    res = ImageBenchmarkResult(
        image_id="img1",
        sha256="hash1",
        dataset="ds1",
        ground_truth=GroundTruthLabel.ORIGINAL,
        file_path="a.jpg",
        chai_verdict="original",
        chai_confidence=0.90,
        chai_risk_level="low",
        analysis_duration_ms=100,
        detector_scores={
            "metadata": 0.1, "frequency": 0.2, "ela": 0.1,
            "noise": 0.15, "compression": 0.1, "texture": 0.2, "lighting": 0.1
        },
        is_three_class_match=True,
    )
    run_res = compute_benchmark_run_result(
        run_id="run_test_report",
        timestamp="2026-08-17T00:00:00Z",
        manifest_hash="hash_manifest",
        duration_seconds=1.0,
        successful_count=1,
        failed_count=0,
        results=[res],
    )

    report_md = generate_markdown_report(run_res)
    assert "# Chai AI — Benchmark Evaluation Report (`run_test_report`)" in report_md
    assert "Overall Accuracy" in report_md
    assert "Detector-Level Performance Breakdown" in report_md
    assert "Main Observations & Calibration Investigation Areas" in report_md


def test_dataset_sources_catalog_integrity() -> None:
    assert "coco_val2017" in DATASET_SOURCES
    assert "diffusion_db_subset" in DATASET_SOURCES
    assert "cifake_ai_generated" in DATASET_SOURCES
    assert DATASET_SOURCES["coco_val2017"]["ground_truth"] == GroundTruthLabel.ORIGINAL

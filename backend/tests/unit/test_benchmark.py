"""Unit tests for the Milestone 12 automated benchmark dataset & evaluation harness (Real vs AI Generated)."""

from __future__ import annotations

import tempfile
from pathlib import Path
import pytest

from app.benchmark.downloader import DATASET_SOURCES
from app.benchmark.manifest import (
    compute_manifest_hash,
    create_manifest,
    discover_benchmark_images,
    load_manifest,
    sample_manifest,
    save_manifest,
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
from app.benchmark.runner import build_benchmark_pipeline, run_benchmark
from app.benchmark.validation import (
    ImageValidationError,
    calculate_file_sha256,
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


def test_duplicate_sha256_hash_calculation(tmp_path: Path) -> None:
    hash1 = calculate_sha256(JPEG_BYTES)
    hash2 = calculate_sha256(JPEG_BYTES)
    hash3 = calculate_sha256(PNG_BYTES)

    assert len(hash1) == 64
    assert hash1 == hash2
    assert hash1 != hash3

    # File SHA-256
    file_p = tmp_path / "sample.jpg"
    file_p.write_bytes(JPEG_BYTES)
    assert calculate_file_sha256(file_p) == hash1


def test_manifest_creation_and_deterministic_sampling() -> None:
    entry1 = ManifestEntry(
        id="real_1",
        sha256="hash1",
        path="tests/fixtures/sample_a.jpg",
        dataset="coco_val2017",
        ground_truth=GroundTruthLabel.ORIGINAL,
        width=100,
        height=100,
        format="JPEG",
        file_size_bytes=1000,
    )
    entry2 = ManifestEntry(
        id="ai_1",
        sha256="hash2",
        path="tests/fixtures/sample_b.png",
        dataset="ai_generated",
        ground_truth=GroundTruthLabel.AI_GENERATED,
        width=100,
        height=100,
        format="PNG",
        file_size_bytes=1200,
    )

    manifest = create_manifest([entry1, entry2], description="Test manifest")
    assert len(manifest.entries) == 2

    # Deterministic sampling with seed
    sampled1 = sample_manifest(manifest, limit=1, seed=42)
    sampled2 = sample_manifest(manifest, limit=1, seed=42)
    assert len(sampled1.entries) == 1
    assert sampled1.entries[0].id == sampled2.entries[0].id

    # Manifest hash deterministic check
    h1 = compute_manifest_hash(manifest)
    h2 = compute_manifest_hash(manifest)
    assert h1 == h2


def test_dataset_discovery_and_deduplication(tmp_path: Path) -> None:
    real_dir = tmp_path / "Real" / "val2017"
    ai_dir = tmp_path / "AI_Generated"
    real_dir.mkdir(parents=True)
    ai_dir.mkdir(parents=True)

    # 1 Real image, 1 AI Gen image, 1 duplicate Real image
    (real_dir / "img1.jpg").write_bytes(JPEG_BYTES)
    (real_dir / "img1_dup.jpg").write_bytes(JPEG_BYTES)
    (ai_dir / "aigen1.png").write_bytes(PNG_BYTES)

    manifest, stats = discover_benchmark_images(tmp_path)
    assert stats["real_count"] == 1
    assert stats["ai_generated_count"] == 1
    assert stats["duplicate_count"] == 1
    assert stats["skipped_count"] == 0
    assert len(manifest.entries) == 2


def test_cross_category_collision_detection(tmp_path: Path) -> None:
    real_dir = tmp_path / "Real"
    ai_dir = tmp_path / "AI_Generated"
    real_dir.mkdir(parents=True)
    ai_dir.mkdir(parents=True)

    # Same exact image placed in both real and ai_generated
    (real_dir / "conflict.jpg").write_bytes(JPEG_BYTES)
    (ai_dir / "conflict.jpg").write_bytes(JPEG_BYTES)

    manifest, stats = discover_benchmark_images(tmp_path)
    assert len(stats["cross_category_duplicates"]) == 1
    assert len(manifest.entries) == 0  # Conflicting items excluded


def test_ground_truth_label_two_class() -> None:
    assert GroundTruthLabel.ORIGINAL.is_two_class_compatible is True
    assert GroundTruthLabel.AI_GENERATED.is_two_class_compatible is True
    assert GroundTruthLabel.ORIGINAL.value == "original"
    assert GroundTruthLabel.AI_GENERATED.value == "ai_generated"


def test_metrics_and_2x2_confusion_matrix() -> None:
    res1 = ImageBenchmarkResult(
        image_id="img1",
        sha256="hash1",
        dataset="coco_val2017",
        ground_truth=GroundTruthLabel.ORIGINAL,
        file_path="a.jpg",
        predicted_class="original",
        correct=True,
        confidence=0.90,
        risk_level="low",
        analysis_duration_ms=100,
        detector_scores={
            "metadata": 0.1, "frequency": 0.2, "ela": 0.1,
            "noise": 0.15, "compression": 0.1, "texture": 0.2, "lighting": 0.1
        },
    )
    res2 = ImageBenchmarkResult(
        image_id="img2",
        sha256="hash2",
        dataset="ai_generated",
        ground_truth=GroundTruthLabel.AI_GENERATED,
        file_path="b.jpg",
        predicted_class="ai_generated",
        correct=True,
        confidence=0.95,
        risk_level="high",
        analysis_duration_ms=120,
        detector_scores={
            "metadata": 0.8, "frequency": 0.9, "ela": 0.85,
            "noise": 0.9, "compression": 0.8, "texture": 0.85, "lighting": 0.9
        },
    )
    res3 = ImageBenchmarkResult(
        image_id="img3",
        sha256="hash3",
        dataset="coco_val2017",
        ground_truth=GroundTruthLabel.ORIGINAL,
        file_path="c.jpg",
        predicted_class="ai_generated",
        correct=False,
        confidence=0.85,
        risk_level="high",
        analysis_duration_ms=110,
        detector_scores={
            "metadata": 0.7, "frequency": 0.8, "ela": 0.75,
            "noise": 0.7, "compression": 0.7, "texture": 0.8, "lighting": 0.7
        },
    )

    run_res = compute_benchmark_run_result(
        run_id="run_test",
        timestamp="2026-08-17T00:00:00Z",
        manifest_hash="hash_manifest",
        duration_seconds=1.5,
        successful_count=3,
        failed_count=0,
        results=[res1, res2, res3],
        discovery_stats={"real_count": 2, "ai_generated_count": 1},
    )

    assert run_res.total_images == 3
    assert run_res.accuracy == pytest.approx(2 / 3, abs=0.01)
    assert run_res.precision == pytest.approx(1 / 2, abs=0.01)  # TP=1, FP=1
    assert run_res.recall == 1.0  # TP=1, FN=0
    assert run_res.tp == 1
    assert run_res.tn == 1
    assert run_res.fp == 1
    assert run_res.fn == 0

    assert run_res.confusion_matrix.labels == ["original", "ai_generated"]
    assert run_res.confusion_matrix.matrix == [[1, 1], [0, 1]]

    # Confidence analysis
    assert run_res.confidence_analysis.high_confidence_failures_count == 1
    assert run_res.confidence_analysis.mean_confidence_correct == pytest.approx(0.925, abs=0.01)

    # Check detector statistics computed for all 7 detectors
    for det in ["metadata", "frequency", "ela", "noise", "compression", "texture", "lighting"]:
        assert det in run_res.detector_statistics
        assert "original_mean" in run_res.detector_statistics[det]
        assert "ai_generated_mean" in run_res.detector_statistics[det]
        assert "separation_margin" in run_res.detector_statistics[det]

    # Check failure cases extraction
    fps = run_res.failure_cases.get("false_positives", [])
    assert len(fps) == 1
    assert fps[0]["image_id"] == "img3"


def test_markdown_report_generation() -> None:
    res = ImageBenchmarkResult(
        image_id="img1",
        sha256="hash1",
        dataset="coco_val2017",
        ground_truth=GroundTruthLabel.ORIGINAL,
        file_path="a.jpg",
        predicted_class="original",
        correct=True,
        confidence=0.90,
        risk_level="low",
        analysis_duration_ms=100,
        detector_scores={
            "metadata": 0.1, "frequency": 0.2, "ela": 0.1,
            "noise": 0.15, "compression": 0.1, "texture": 0.2, "lighting": 0.1
        },
    )
    run_res = compute_benchmark_run_result(
        run_id="run_test_report",
        timestamp="2026-08-17T00:00:00Z",
        manifest_hash="hash_manifest",
        duration_seconds=1.0,
        successful_count=1,
        failed_count=0,
        results=[res],
        discovery_stats={"real_count": 1, "ai_generated_count": 0},
    )

    report_md = generate_markdown_report(run_res)
    assert "# Chai AI Benchmark Report (`run_test_report`)" in report_md
    assert "Overall Accuracy" in report_md
    assert "Confusion Matrix" in report_md
    assert "Detector Analysis" in report_md
    assert "Calibration Candidates" in report_md


def test_production_pipeline_benchmark_execution(tmp_path: Path) -> None:
    # Integration-level test executing images through ModularAnalysisPipeline
    img_path = tmp_path / "sample.jpg"
    img_path.write_bytes(JPEG_BYTES)

    entry = ManifestEntry(
        id="sample_test_1",
        sha256=calculate_sha256(JPEG_BYTES),
        path=str(img_path),
        dataset="test_suite",
        ground_truth=GroundTruthLabel.ORIGINAL,
        width=100,
        height=100,
        format="JPEG",
        file_size_bytes=len(JPEG_BYTES),
    )
    manifest = create_manifest([entry])
    pipeline = build_benchmark_pipeline()

    result = run_benchmark(manifest=manifest, pipeline=pipeline)
    assert result.total_images == 1
    assert result.successful_analyses == 1
    assert result.failed_analyses == 0
    assert result.results[0].predicted_class in {"original", "ai_generated"}
    assert len(result.results[0].detector_scores) == 7


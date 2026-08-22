"""Unit tests for the Milestone 13 forensic investigation and calibration module."""

from __future__ import annotations

import math
from pathlib import Path
import pytest

from app.benchmark.calibration.evaluator import (
    BASELINE_M12,
    CalibrationCandidate,
    evaluate_calibration,
)
from app.benchmark.calibration.investigation import (
    compute_distribution_overlap,
    run_forensic_investigation,
)
from app.benchmark.models import (
    BenchmarkRunResult,
    ConfusionMatrixData,
    GroundTruthLabel,
    ImageBenchmarkResult,
)


def _build_synthetic_benchmark_result() -> BenchmarkRunResult:
    """Construct a deterministic synthetic benchmark result for testing."""
    # Real image with authentic properties
    r1 = ImageBenchmarkResult(
        image_id="real_01",
        sha256="hash_r1",
        dataset="coco_val2017",
        ground_truth=GroundTruthLabel.ORIGINAL,
        file_path="real/img1.jpg",
        predicted_class="original",
        correct=True,
        confidence=0.92,
        risk_level="low",
        analysis_duration_ms=50,
        detector_scores={
            "metadata": 0.05,
            "frequency": 0.20,
            "ela": 0.15,
            "noise": 0.12,
            "compression": 0.10,
            "texture": 0.15,
            "lighting": 0.35,
        },
    )
    # Real image with false positive triggered by lighting & texture
    r2 = ImageBenchmarkResult(
        image_id="real_02",
        sha256="hash_r2",
        dataset="coco_val2017",
        ground_truth=GroundTruthLabel.ORIGINAL,
        file_path="real/img2.jpg",
        predicted_class="ai_generated",
        correct=False,
        confidence=0.88,
        risk_level="high",
        analysis_duration_ms=60,
        detector_scores={
            "metadata": 0.40,
            "frequency": 0.20,
            "ela": 0.15,
            "noise": 0.40,
            "compression": 0.88,
            "texture": 0.83,
            "lighting": 0.85,
        },
    )
    # AI image correctly caught by frequency
    a1 = ImageBenchmarkResult(
        image_id="ai_01",
        sha256="hash_a1",
        dataset="ai_generated",
        ground_truth=GroundTruthLabel.AI_GENERATED,
        file_path="ai_generated/gen1.png",
        predicted_class="ai_generated",
        correct=True,
        confidence=0.94,
        risk_level="high",
        analysis_duration_ms=55,
        detector_scores={
            "metadata": 0.40,
            "frequency": 0.90,
            "ela": 0.15,
            "noise": 0.50,
            "compression": 0.10,
            "texture": 0.75,
            "lighting": 0.35,
        },
    )
    # AI AVIF image false negative due to fallback decoding
    a2 = ImageBenchmarkResult(
        image_id="ai_02",
        sha256="hash_a2",
        dataset="ai_generated",
        ground_truth=GroundTruthLabel.AI_GENERATED,
        file_path="ai_generated/gen2.avif",
        predicted_class="original",
        correct=False,
        confidence=0.9539,
        risk_level="low",
        analysis_duration_ms=45,
        detector_scores={
            "metadata": 0.40,
            "frequency": 0.40,
            "ela": 0.15,
            "noise": 0.40,
            "compression": 0.15,
            "texture": 0.40,
            "lighting": 0.40,
        },
    )

    return BenchmarkRunResult(
        run_id="test_m13_run",
        timestamp="2026-08-22T00:00:00Z",
        pipeline_version="2.0",
        manifest_hash="hash_manifest",
        total_images=4,
        real_count=2,
        ai_generated_count=2,
        successful_analyses=4,
        failed_analyses=0,
        duration_seconds=0.2,
        results=[r1, r2, a1, a2],
        accuracy=0.50,
        precision=0.50,
        recall=0.50,
        f1=0.50,
        macro_f1=0.50,
        weighted_f1=0.50,
        tp=1,
        tn=1,
        fp=1,
        fn=1,
        confusion_matrix=ConfusionMatrixData(
            labels=["original", "ai_generated"],
            matrix=[[1, 1], [1, 1]],
        ),
    )


def test_distribution_overlap_calculation() -> None:
    # Identical distributions -> overlap 1.0
    assert compute_distribution_overlap(0.5, 0.1, 0.5, 0.1) == pytest.approx(1.0, abs=0.01)
    # Well-separated distributions -> overlap near 0.0
    assert compute_distribution_overlap(0.1, 0.05, 0.9, 0.05) < 0.01


def test_forensic_investigation_execution() -> None:
    bench_data = _build_synthetic_benchmark_result()
    report = run_forensic_investigation(bench_data)

    assert report.total_images == 4
    assert report.real_count == 2
    assert report.ai_count == 2
    assert len(report.detector_stats) == 7
    assert len(report.usefulness_ranking) == 7

    # Frequency has high AI score (0.90, 0.40) vs Real (0.20, 0.20) -> positive separation
    freq_stat = report.detector_stats["frequency"]
    assert freq_stat.separation_margin > 0.0
    assert freq_stat.direction_correct is True

    # Check format breakdown
    assert "PNG" in report.format_analysis
    assert "AVIF" in report.format_analysis
    assert report.format_analysis["AVIF"].fallback_rate > 0.0

    # Failure analysis
    assert report.failures_summary.total_fps == 1
    assert report.failures_summary.total_fns == 1
    assert report.failures_summary.fn_avif_count == 1

    # Bug and recommendation checks
    assert len(report.implementation_bugs_identified) >= 3
    assert len(report.calibration_recommendations) >= 3


def test_calibration_evaluator_simulation() -> None:
    bench_data = _build_synthetic_benchmark_result()
    # Baseline evaluation
    base_res = evaluate_calibration(BASELINE_M12, bench_data)
    assert base_res.total_evaluated == 4
    assert base_res.name == "BASELINE_M12"

    # Candidate with wider Gaussian
    candidate = CalibrationCandidate(
        name="TEST_WIDER_GAUSSIAN",
        description="Wider gaussian resolution test",
        classifier_resolution=0.35,
        classifier_contribution_matrix=BASELINE_M12.classifier_contribution_matrix,
        detector_reliability=BASELINE_M12.detector_reliability,
        disabled_detectors=[],
    )
    cand_res = evaluate_calibration(candidate, bench_data, baseline_result=base_res)
    assert cand_res.total_evaluated == 4
    assert isinstance(cand_res.delta_macro_f1_vs_baseline, float)


def test_mathematical_gaussian_resolution_bias() -> None:
    # Verify the mathematical reason for 85x bias at score=0.40 with sigma=0.15
    sigma = 0.15
    score = 0.40
    d_orig = (score - 0.0) ** 2
    d_gen = (score - 1.0) ** 2
    support_orig = math.exp(-d_orig / (2.0 * sigma**2))
    support_gen = math.exp(-d_gen / (2.0 * sigma**2))
    ratio = support_orig / support_gen
    assert ratio > 80.0  # Confirms mathematical asymmetry responsible for 95.4% false confidence

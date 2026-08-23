"""Unit tests for Milestone 18 — Production Validation of EXP_4 and Promotion Logic."""

from __future__ import annotations

import pytest

from app.benchmark.calibration.validator import (
    PromotionValidationReport,
    validate_production_promotion,
)
from app.benchmark.models import (
    BenchmarkRunResult,
    ConfusionMatrixData,
    GroundTruthLabel,
    ImageBenchmarkResult,
)
from app.pipeline.config import (
    CALIBRATION_PROFILES,
    PipelineConfig,
)


def _build_mock_run_result(
    run_id: str,
    results: list[ImageBenchmarkResult],
    failed_count: int = 0,
) -> BenchmarkRunResult:
    total = len(results)
    real_cnt = sum(1 for r in results if r.ground_truth == GroundTruthLabel.ORIGINAL)
    ai_cnt = sum(1 for r in results if r.ground_truth == GroundTruthLabel.AI_GENERATED)

    tp = sum(
        1
        for r in results
        if r.ground_truth == GroundTruthLabel.AI_GENERATED and r.correct
    )
    tn = sum(
        1 for r in results if r.ground_truth == GroundTruthLabel.ORIGINAL and r.correct
    )
    fp = sum(
        1
        for r in results
        if r.ground_truth == GroundTruthLabel.ORIGINAL and not r.correct
    )
    fn = sum(
        1
        for r in results
        if r.ground_truth == GroundTruthLabel.AI_GENERATED and not r.correct
    )

    acc = (tp + tn) / total if total > 0 else 0.0
    prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0

    return BenchmarkRunResult(
        run_id=run_id,
        timestamp="2026-08-23T00:00:00Z",
        pipeline_version="2.0",
        manifest_hash="test_manifest_hash",
        total_images=total,
        real_count=real_cnt,
        ai_generated_count=ai_cnt,
        successful_analyses=total - failed_count,
        failed_analyses=failed_count,
        duration_seconds=1.0,
        results=results,
        accuracy=round(acc, 4),
        precision=round(prec, 4),
        recall=round(rec, 4),
        f1=round(f1, 4),
        macro_f1=round(acc, 4),
        weighted_f1=round(acc, 4),
        tp=tp,
        tn=tn,
        fp=fp,
        fn=fn,
        confusion_matrix=ConfusionMatrixData(
            labels=["original", "ai_generated"],
            matrix=[[tn, fp], [fn, tp]],
        ),
    )


# ---------------------------------------------------------------------------
# 1. Configuration Selection & Profile Loading
# ---------------------------------------------------------------------------


def test_configuration_selection_and_profiles() -> None:
    # Baseline M14
    cfg_m14 = PipelineConfig.for_profile("m14")
    assert cfg_m14.calibration_profile == "m14"
    assert cfg_m14.detector_reliability["frequency"] == 0.18
    assert cfg_m14.detector_reliability["lighting"] == 0.17
    assert cfg_m14.detector_reliability["texture"] == 0.15

    # EXP_4 Rebalance
    cfg_exp4 = PipelineConfig.for_profile("exp_4")
    assert cfg_exp4.calibration_profile == "exp_4"
    assert cfg_exp4.detector_reliability["frequency"] == 0.40
    assert cfg_exp4.detector_reliability["lighting"] == 0.05
    assert cfg_exp4.detector_reliability["texture"] == 0.05

    # Direct helper classmethods
    assert PipelineConfig.baseline_m14().detector_reliability["frequency"] == 0.18
    assert PipelineConfig.exp_4().detector_reliability["frequency"] == 0.40

    # Invalid profile raises ValueError
    with pytest.raises(ValueError, match="Unknown calibration profile"):
        PipelineConfig.for_profile("invalid_profile_name")


def test_m14_baseline_preservation() -> None:
    prof = CALIBRATION_PROFILES["m14"]
    assert prof["detector_reliability"]["metadata"] == 0.10
    assert prof["detector_reliability"]["frequency"] == 0.18
    assert prof["detector_reliability"]["ela"] == 0.18
    assert prof["detector_reliability"]["noise"] == 0.12
    assert prof["detector_reliability"]["compression"] == 0.10
    assert prof["detector_reliability"]["texture"] == 0.15
    assert prof["detector_reliability"]["lighting"] == 0.17
    assert prof["classifier_resolution"] == 0.15


def test_exp_4_parameter_loading() -> None:
    prof = CALIBRATION_PROFILES["exp_4"]
    assert prof["detector_reliability"]["frequency"] == 0.40
    assert prof["detector_reliability"]["lighting"] == 0.05
    assert prof["detector_reliability"]["texture"] == 0.05
    assert prof["detector_reliability"]["ela"] == 0.18
    assert prof["detector_reliability"]["noise"] == 0.12
    assert prof["detector_reliability"]["compression"] == 0.10
    assert prof["detector_reliability"]["metadata"] == 0.10
    assert prof["classifier_resolution"] == 0.15


# ---------------------------------------------------------------------------
# 2. Promotion Decision Logic & Regression Detection
# ---------------------------------------------------------------------------


def test_promotion_decision_logic_approved() -> None:
    # Construct a baseline run with 100 Real (50 FP) and 20 AI (10 TP)
    base_results: list[ImageBenchmarkResult] = []
    for i in range(50):
        base_results.append(
            ImageBenchmarkResult(
                image_id=f"r_tn_{i}",
                sha256=f"hash_r_tn_{i}",
                dataset="test",
                ground_truth=GroundTruthLabel.ORIGINAL,
                file_path="real/img.jpg",
                predicted_class="original",
                correct=True,
                confidence=0.85,
                risk_level="low",
                analysis_duration_ms=10,
            )
        )
    for i in range(50):
        base_results.append(
            ImageBenchmarkResult(
                image_id=f"r_fp_{i}",
                sha256=f"hash_r_fp_{i}",
                dataset="test",
                ground_truth=GroundTruthLabel.ORIGINAL,
                file_path="real/img.jpg",
                predicted_class="ai_generated",
                correct=False,
                confidence=0.75,
                risk_level="high",
                analysis_duration_ms=10,
            )
        )
    for i in range(10):
        base_results.append(
            ImageBenchmarkResult(
                image_id=f"a_tp_{i}",
                sha256=f"hash_a_tp_{i}",
                dataset="test",
                ground_truth=GroundTruthLabel.AI_GENERATED,
                file_path="ai/img.png",
                predicted_class="ai_generated",
                correct=True,
                confidence=0.90,
                risk_level="high",
                analysis_duration_ms=10,
            )
        )
    for i in range(10):
        base_results.append(
            ImageBenchmarkResult(
                image_id=f"a_fn_{i}",
                sha256=f"hash_a_fn_{i}",
                dataset="test",
                ground_truth=GroundTruthLabel.AI_GENERATED,
                file_path="ai/img.avif",
                predicted_class="original",
                correct=False,
                confidence=0.60,
                risk_level="low",
                analysis_duration_ms=10,
            )
        )

    base_run = _build_mock_run_result("base_run_1", base_results)

    # Candidate run where 40 of the 50 FPs are fixed -> 10 FPs left, recall preserved
    cand_results: list[ImageBenchmarkResult] = []
    for r in base_results:
        c_pred = r.predicted_class
        if r.image_id.startswith("r_fp_") and int(r.image_id.split("_")[2]) < 40:
            c_pred = "original"  # Fixed FP!
        cand_results.append(
            ImageBenchmarkResult(
                image_id=r.image_id,
                sha256=r.sha256,
                dataset=r.dataset,
                ground_truth=r.ground_truth,
                file_path=r.file_path,
                predicted_class=c_pred,
                correct=c_pred == r.ground_truth.value,
                confidence=r.confidence,
                risk_level=r.risk_level,
                analysis_duration_ms=r.analysis_duration_ms,
            )
        )

    cand_run = _build_mock_run_result("cand_run_1", cand_results)

    report = validate_production_promotion(base_run, cand_run)

    assert isinstance(report, PromotionValidationReport)
    assert report.passed_all_criteria is True
    assert report.promotion_verdict == "APPROVED_FOR_PROMOTION"
    assert len(report.transitions.fixed_false_positives) == 40
    assert len(report.transitions.newly_introduced_false_positives) == 0


def test_regression_detection_rejected() -> None:
    # Candidate where AI recall drops significantly (e.g. 5 TPs lost)
    base_results = [
        ImageBenchmarkResult(
            image_id="a1",
            sha256="h1",
            dataset="test",
            ground_truth=GroundTruthLabel.AI_GENERATED,
            file_path="ai/img.png",
            predicted_class="ai_generated",
            correct=True,
            confidence=0.90,
            risk_level="high",
            analysis_duration_ms=10,
        ),
        ImageBenchmarkResult(
            image_id="r1",
            sha256="h2",
            dataset="test",
            ground_truth=GroundTruthLabel.ORIGINAL,
            file_path="real/img.jpg",
            predicted_class="original",
            correct=True,
            confidence=0.85,
            risk_level="low",
            analysis_duration_ms=10,
        ),
    ]
    base_run = _build_mock_run_result("base_run", base_results)

    # Candidate regressed: a1 missed as original
    cand_results = [
        ImageBenchmarkResult(
            image_id="a1",
            sha256="h1",
            dataset="test",
            ground_truth=GroundTruthLabel.AI_GENERATED,
            file_path="ai/img.png",
            predicted_class="original",
            correct=False,
            confidence=0.60,
            risk_level="low",
            analysis_duration_ms=10,
        ),
        ImageBenchmarkResult(
            image_id="r1",
            sha256="h2",
            dataset="test",
            ground_truth=GroundTruthLabel.ORIGINAL,
            file_path="real/img.jpg",
            predicted_class="original",
            correct=True,
            confidence=0.85,
            risk_level="low",
            analysis_duration_ms=10,
        ),
    ]
    cand_run = _build_mock_run_result("cand_run", cand_results)

    report = validate_production_promotion(base_run, cand_run)

    assert report.passed_all_criteria is False
    assert report.promotion_verdict == "REJECTED_RETAIN_M14"
    rec_check = next(
        c for c in report.criteria_checks if c.name == "AI Recall Non-Regression"
    )
    assert rec_check.passed is False

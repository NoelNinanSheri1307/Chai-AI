"""Statistical metrics, 2x2 confusion matrix computation, detector analysis, and failure extraction."""

from __future__ import annotations

import statistics
from typing import Any

from app.benchmark.models import (
    BenchmarkRunResult,
    ConfidenceAnalysis,
    ConfusionMatrixData,
    GroundTruthLabel,
    ImageBenchmarkResult,
)


def compute_benchmark_run_result(
    run_id: str,
    timestamp: str,
    manifest_hash: str,
    duration_seconds: float,
    successful_count: int,
    failed_count: int,
    results: list[ImageBenchmarkResult],
    discovery_stats: dict[str, Any] | None = None,
) -> BenchmarkRunResult:
    """Compute 2-class aggregated metrics, 2x2 confusion matrix, detector stats, and failure cases."""
    labels = ["original", "ai_generated"]

    # 2x2 Confusion Matrix: rows = Ground Truth, cols = Predicted Verdict
    # Row 0 (original): [TN, FP]
    # Row 1 (ai_generated): [FN, TP]
    cm = [[0, 0], [0, 0]]

    tp = 0
    tn = 0
    fp = 0
    fn = 0

    real_count = 0
    ai_gen_count = 0

    valid_evaluated = [r for r in results if r.predicted_class in {"original", "ai_generated"}]

    for r in valid_evaluated:
        gt_val = r.ground_truth.value
        pred_val = r.predicted_class

        if gt_val == "original":
            real_count += 1
            if pred_val == "original":
                tn += 1
                cm[0][0] += 1
            else:
                fp += 1
                cm[0][1] += 1
        elif gt_val == "ai_generated":
            ai_gen_count += 1
            if pred_val == "ai_generated":
                tp += 1
                cm[1][1] += 1
            else:
                fn += 1
                cm[1][0] += 1

    total_valid = len(valid_evaluated)

    # Overall Binary Metrics (Positive Class = AI Generated)
    accuracy = round((tp + tn) / total_valid, 4) if total_valid > 0 else 0.0
    precision = round(tp / (tp + fp), 4) if (tp + fp) > 0 else 0.0
    recall = round(tp / (tp + fn), 4) if (tp + fn) > 0 else 0.0
    f1 = (
        round(2 * precision * recall / (precision + recall), 4)
        if (precision + recall) > 0
        else 0.0
    )

    # Per-Class Precision, Recall, F1
    orig_prec = round(tn / (tn + fn), 4) if (tn + fn) > 0 else 0.0
    orig_rec = round(tn / (tn + fp), 4) if (tn + fp) > 0 else 0.0
    orig_f1 = (
        round(2 * orig_prec * orig_rec / (orig_prec + orig_rec), 4)
        if (orig_prec + orig_rec) > 0
        else 0.0
    )

    per_class: dict[str, dict[str, float]] = {
        "original": {
            "precision": orig_prec,
            "recall": orig_rec,
            "f1": orig_f1,
            "support": float(real_count),
        },
        "ai_generated": {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "support": float(ai_gen_count),
        },
    }

    macro_f1 = round((orig_f1 + f1) / 2, 4)
    weighted_f1 = (
        round((orig_f1 * real_count + f1 * ai_gen_count) / total_valid, 4)
        if total_valid > 0
        else 0.0
    )

    # Confidence Analysis
    conf_analysis = _compute_confidence_analysis(valid_evaluated)

    # Compute 7 Detector statistics
    detector_stats, calib_candidates = _compute_detector_statistics(valid_evaluated)

    # Failure case extraction
    failure_cases = _extract_failure_cases(results)

    stats = discovery_stats or {}

    return BenchmarkRunResult(
        run_id=run_id,
        timestamp=timestamp,
        pipeline_version="2.0",
        manifest_hash=manifest_hash,
        total_images=len(results),
        real_count=stats.get("real_count", real_count),
        ai_generated_count=stats.get("ai_generated_count", ai_gen_count),
        successful_analyses=successful_count,
        failed_analyses=failed_count,
        skipped_count=stats.get("skipped_count", 0),
        duplicate_count=stats.get("duplicate_count", 0),
        cross_category_duplicates=stats.get("cross_category_duplicates", []),
        duration_seconds=round(duration_seconds, 2),
        results=results,
        accuracy=accuracy,
        precision=precision,
        recall=recall,
        f1=f1,
        macro_f1=macro_f1,
        weighted_f1=weighted_f1,
        tp=tp,
        tn=tn,
        fp=fp,
        fn=fn,
        per_class_metrics=per_class,
        confusion_matrix=ConfusionMatrixData(labels=labels, matrix=cm),
        confidence_analysis=conf_analysis,
        detector_statistics=detector_stats,
        failure_cases=failure_cases,
        calibration_candidates=calib_candidates,
    )


def _compute_confidence_analysis(
    results: list[ImageBenchmarkResult],
) -> ConfidenceAnalysis:
    """Analyze predictions by confidence distribution."""
    correct_confs: list[float] = [r.confidence for r in results if r.correct]
    incorrect_confs: list[float] = [r.confidence for r in results if not r.correct]

    mean_corr = round(statistics.mean(correct_confs), 4) if correct_confs else 0.0
    mean_inc = round(statistics.mean(incorrect_confs), 4) if incorrect_confs else 0.0

    high_conf_failures = sum(1 for r in results if not r.correct and r.confidence >= 0.80)
    low_conf_correct = sum(1 for r in results if r.correct and r.confidence <= 0.60)

    return ConfidenceAnalysis(
        mean_confidence_correct=mean_corr,
        mean_confidence_incorrect=mean_inc,
        high_confidence_failures_count=high_conf_failures,
        low_confidence_correct_count=low_conf_correct,
    )


def _compute_detector_statistics(
    results: list[ImageBenchmarkResult],
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    """Compute score distributions per detector across Real vs AI Generated."""
    detector_names = [
        "metadata",
        "frequency",
        "ela",
        "noise",
        "compression",
        "texture",
        "lighting",
    ]

    stats: dict[str, dict[str, Any]] = {}
    calibration_candidates: list[str] = []

    for det in sorted(detector_names):
        real_scores: list[float] = []
        real_confs: list[float] = []
        ai_scores: list[float] = []
        ai_confs: list[float] = []

        for r in results:
            score = r.detector_scores.get(det)
            conf = r.detector_confidences.get(det, 1.0)
            if score is not None:
                if r.ground_truth == GroundTruthLabel.ORIGINAL:
                    real_scores.append(score)
                    real_confs.append(conf)
                elif r.ground_truth == GroundTruthLabel.AI_GENERATED:
                    ai_scores.append(score)
                    ai_confs.append(conf)

        orig_mean = round(statistics.mean(real_scores), 4) if real_scores else 0.0
        orig_std = round(statistics.stdev(real_scores), 4) if len(real_scores) > 1 else 0.0
        orig_min = round(min(real_scores), 4) if real_scores else 0.0
        orig_max = round(max(real_scores), 4) if real_scores else 0.0
        orig_conf_mean = round(statistics.mean(real_confs), 4) if real_confs else 0.0

        gen_mean = round(statistics.mean(ai_scores), 4) if ai_scores else 0.0
        gen_std = round(statistics.stdev(ai_scores), 4) if len(ai_scores) > 1 else 0.0
        gen_min = round(min(ai_scores), 4) if ai_scores else 0.0
        gen_max = round(max(ai_scores), 4) if ai_scores else 0.0
        gen_conf_mean = round(statistics.mean(ai_confs), 4) if ai_confs else 0.0

        sep_margin = round(abs(gen_mean - orig_mean), 4)

        suspicious: list[str] = []
        if orig_mean >= 0.60:
            msg = f"{det}: High false-alarm bias on authentic images (mean {orig_mean:.2f} >= 0.60)"
            suspicious.append(msg)
            calibration_candidates.append(msg)
        if gen_mean <= 0.40 and ai_scores:
            msg = f"{det}: Low sensitivity on AI-generated images (mean {gen_mean:.2f} <= 0.40)"
            suspicious.append(msg)
            calibration_candidates.append(msg)
        if sep_margin < 0.10 and real_scores and ai_scores:
            msg = f"{det}: Poor discriminative separation between classes (margin {sep_margin:.2f} < 0.10)"
            suspicious.append(msg)
            calibration_candidates.append(msg)

        stats[det] = {
            "original_count": len(real_scores),
            "original_mean": orig_mean,
            "original_std": orig_std,
            "original_min": orig_min,
            "original_max": orig_max,
            "original_confidence_mean": orig_conf_mean,
            "ai_generated_count": len(ai_scores),
            "ai_generated_mean": gen_mean,
            "ai_generated_std": gen_std,
            "ai_generated_min": gen_min,
            "ai_generated_max": gen_max,
            "ai_generated_confidence_mean": gen_conf_mean,
            "separation_margin": sep_margin,
            "suspicious_behavior": suspicious,
        }

    return stats, calibration_candidates


def _extract_failure_cases(
    results: list[ImageBenchmarkResult],
) -> dict[str, list[dict[str, Any]]]:
    """Extract false positives, false negatives, high-confidence failures, and low-confidence correct."""
    fps: list[dict[str, Any]] = []
    fns: list[dict[str, Any]] = []
    high_conf_failures: list[dict[str, Any]] = []
    low_conf_correct: list[dict[str, Any]] = []

    for r in results:
        gt = r.ground_truth.value
        pred = r.predicted_class
        conf = r.confidence

        influential = sorted(
            r.detector_scores.items(),
            key=lambda item: item[1],
            reverse=(pred == "ai_generated"),
        )
        top_detectors = [f"{k}: {v:.2f}" for k, v in influential[:3]]

        item = {
            "image_id": r.image_id,
            "dataset": r.dataset,
            "ground_truth": gt,
            "predicted_class": pred,
            "confidence": round(conf, 4),
            "file_path": r.file_path,
            "detector_scores": r.detector_scores,
            "most_influential_detectors": top_detectors,
            "evidence_summary": r.evidence[:3] if r.evidence else [],
        }

        if not r.correct and pred in {"original", "ai_generated"}:
            if gt == "original" and pred == "ai_generated":
                fps.append(item)
            elif gt == "ai_generated" and pred == "original":
                fns.append(item)

            if conf >= 0.80:
                high_conf_failures.append(item)
        elif r.correct and pred in {"original", "ai_generated"}:
            if conf <= 0.60:
                low_conf_correct.append(item)

    return {
        "false_positives": fps,
        "false_negatives": fns,
        "high_confidence_failures": high_conf_failures,
        "low_confidence_correct": low_conf_correct,
    }


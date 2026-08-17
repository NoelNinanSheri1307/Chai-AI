"""Statistical metrics, confusion matrix computation, and failure extraction for benchmarks."""

from __future__ import annotations

import statistics
from typing import Any

from app.benchmark.models import (
    BenchmarkRunResult,
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
) -> BenchmarkRunResult:
    """Compute aggregated metrics, confusion matrix, detector stats, and failure cases."""
    # Filter 3-class compatible results for 3-class metrics
    three_class_results = [
        r for r in results if r.ground_truth.is_three_class_compatible
    ]

    labels = ["original", "ai_edited", "ai_generated"]
    label_to_idx = {lbl: i for i, lbl in enumerate(labels)}

    # Build 3x3 Confusion Matrix: rows = Ground Truth, cols = Predicted Verdict
    cm = [[0, 0, 0] for _ in range(3)]

    for r in three_class_results:
        gt_str = r.ground_truth.value
        pred_str = r.chai_verdict
        # Normalize pred_str
        if pred_str == "aiEdited":
            pred_str = "ai_edited"
        elif pred_str == "aiGenerated":
            pred_str = "ai_generated"

        if gt_str in label_to_idx and pred_str in label_to_idx:
            cm[label_to_idx[gt_str]][label_to_idx[pred_str]] += 1

    # Per-class Precision, Recall, F1
    per_class: dict[str, dict[str, float]] = {}
    f1_scores: list[float] = []
    class_counts: list[int] = []

    for i, lbl in enumerate(labels):
        tp = cm[i][i]
        fp = sum(cm[j][i] for j in range(3) if j != i)
        fn = sum(cm[i][j] for j in range(3) if j != i)
        total_gt = sum(cm[i][j] for j in range(3))

        precision = round(tp / (tp + fp), 4) if (tp + fp) > 0 else 0.0
        recall = round(tp / (tp + fn), 4) if (tp + fn) > 0 else 0.0
        f1 = (
            round(2 * precision * recall / (precision + recall), 4)
            if (precision + recall) > 0
            else 0.0
        )

        per_class[lbl] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "total_samples": total_gt,
        }
        f1_scores.append(f1)
        class_counts.append(total_gt)

    total_3class = sum(class_counts)
    correct_3class = sum(cm[i][i] for i in range(3))
    overall_acc = (
        round(correct_3class / total_3class, 4) if total_3class > 0 else 0.0
    )
    macro_f1 = round(sum(f1_scores) / len(f1_scores), 4) if f1_scores else 0.0

    weighted_f1 = (
        round(sum(f1 * cnt for f1, cnt in zip(f1_scores, class_counts)) / total_3class, 4)
        if total_3class > 0
        else 0.0
    )

    # Compute 7 Detector statistics
    detector_stats = _compute_detector_statistics(results)

    # Failure case extraction
    failure_cases = _extract_failure_cases(results)

    return BenchmarkRunResult(
        run_id=run_id,
        timestamp=timestamp,
        pipeline_version="1.0",
        manifest_hash=manifest_hash,
        total_images=len(results),
        successful_analyses=successful_count,
        failed_analyses=failed_count,
        duration_seconds=round(duration_seconds, 2),
        results=results,
        overall_accuracy=overall_acc,
        macro_f1=macro_f1,
        weighted_f1=weighted_f1,
        per_class_metrics=per_class,
        confusion_matrix=ConfusionMatrixData(labels=labels, matrix=cm),
        detector_statistics=detector_stats,
        failure_cases=failure_cases,
    )


def _compute_detector_statistics(
    results: list[ImageBenchmarkResult],
) -> dict[str, dict[str, Any]]:
    """Compute mean score per class and separation metrics for all 7 detectors."""
    detector_names = {
        "metadata",
        "frequency",
        "ela",
        "noise",
        "compression",
        "texture",
        "lighting",
    }

    stats: dict[str, dict[str, Any]] = {}

    for det in sorted(detector_names):
        by_class: dict[str, list[float]] = {
            "original": [],
            "ai_edited": [],
            "ai_generated": [],
        }

        for r in results:
            score = r.detector_scores.get(det)
            if score is not None:
                gt = r.ground_truth.value
                if gt in by_class:
                    by_class[gt].append(score)

        det_stat: dict[str, Any] = {}
        for cls_name, scores in by_class.items():
            if scores:
                det_stat[f"{cls_name}_mean"] = round(statistics.mean(scores), 4)
                det_stat[f"{cls_name}_std"] = (
                    round(statistics.stdev(scores), 4) if len(scores) > 1 else 0.0
                )
                det_stat[f"{cls_name}_count"] = len(scores)
            else:
                det_stat[f"{cls_name}_mean"] = 0.0
                det_stat[f"{cls_name}_std"] = 0.0
                det_stat[f"{cls_name}_count"] = 0

        # Calculate Separation Margin between Original and AI Generated
        orig_mean = det_stat.get("original_mean", 0.0)
        gen_mean = det_stat.get("ai_generated_mean", 0.0)
        det_stat["separation_margin"] = round(abs(gen_mean - orig_mean), 4)
        stats[det] = det_stat

    return stats


def _extract_failure_cases(
    results: list[ImageBenchmarkResult],
) -> dict[str, list[dict[str, Any]]]:
    """Extract false positives, false negatives, high-confidence failures, and disagreements."""
    fps: list[dict[str, Any]] = []
    fns: list[dict[str, Any]] = []
    high_conf_failures: list[dict[str, Any]] = []
    low_conf_correct: list[dict[str, Any]] = []
    external_disagreements: list[dict[str, Any]] = []

    for r in results:
        gt = r.ground_truth.value
        pred = r.chai_verdict
        conf = r.chai_confidence
        item = {
            "image_id": r.image_id,
            "dataset": r.dataset,
            "ground_truth": gt,
            "chai_verdict": pred,
            "confidence": conf,
            "file_path": r.file_path,
        }

        if r.is_three_class_match is False:
            if gt == "original" and pred != "original":
                fps.append(item)
            elif gt in {"ai_generated", "ai_edited"} and pred == "original":
                fns.append(item)

            if conf >= 0.8:
                high_conf_failures.append(item)
        elif r.is_three_class_match is True:
            if conf <= 0.6:
                low_conf_correct.append(item)

        if r.external_result:
            ext_detected = r.external_result.get("detected_as_ai")
            if ext_detected is not None:
                chai_ai = pred != "original"
                if chai_ai != ext_detected:
                    external_disagreements.append({
                        **item,
                        "external_detected_as_ai": ext_detected,
                    })

    return {
        "false_positives": fps,
        "false_negatives": fns,
        "high_confidence_failures": high_conf_failures,
        "low_confidence_correct": low_conf_correct,
        "external_disagreements": external_disagreements,
    }

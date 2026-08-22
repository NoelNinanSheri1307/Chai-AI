"""Human-readable report generator for benchmark evaluation runs (Real vs AI Generated)."""

from __future__ import annotations

from pathlib import Path

from app.benchmark.models import BenchmarkRunResult


def generate_markdown_report(result: BenchmarkRunResult) -> str:
    """Generate a comprehensive GitHub-flavored Markdown benchmark report."""
    lines: list[str] = []

    lines.append(f"# Chai AI Benchmark Report (`{result.run_id}`)")
    lines.append("")
    lines.append(f"**Run Timestamp:** `{result.timestamp}`  ")
    lines.append(f"**Pipeline Version:** `{result.pipeline_version}`  ")
    lines.append(f"**Manifest Hash:** `{result.manifest_hash[:16]}...`  ")
    lines.append(f"**Total Run Duration:** `{result.duration_seconds}s`  ")
    lines.append("")
    lines.append("---")
    lines.append("")

    # 1. Dataset
    lines.append("## Dataset")
    lines.append("")
    lines.append(f"- **Total Discovered/Evaluated Images:** {result.total_images}")
    lines.append(f"- **Real Images (Authentic):** {result.real_count}")
    lines.append(f"- **AI Generated Images:** {result.ai_generated_count}")
    lines.append(f"- **Successful Analyses:** {result.successful_analyses}")
    lines.append(f"- **Failed Analyses:** {result.failed_analyses}")
    lines.append(f"- **Skipped (Corrupt / Unsupported):** {result.skipped_count}")
    lines.append(f"- **Intra-category Duplicates Excluded:** {result.duplicate_count}")
    if result.cross_category_duplicates:
        lines.append(f"- **Cross-category Collision Errors Excluded:** {len(result.cross_category_duplicates)}")
    else:
        lines.append("- **Cross-category Collisions:** 0 (clean dataset separation)")
    lines.append("")

    # 2. Overall Performance
    lines.append("## Overall Performance")
    lines.append("")
    lines.append("| Metric | Value | Interpretation |")
    lines.append("| --- | --- | --- |")
    lines.append(f"| **Overall Accuracy** | `{result.accuracy * 100:.2f}%` | Fraction of total images classified correctly |")
    lines.append(f"| **Precision (AI Generated)** | `{result.precision * 100:.2f}%` | When Chai predicts AI Generated, how often is it right? |")
    lines.append(f"| **Recall (AI Generated)** | `{result.recall * 100:.2f}%` | How many of the actual AI Generated images did Chai catch? |")
    lines.append(f"| **F1 Score (AI Generated)** | `{result.f1:.4f}` | Harmonic mean of AI Generated precision & recall |")
    lines.append(f"| **Macro F1 Score** | `{result.macro_f1:.4f}` | Unweighted average across Real and AI Generated |")
    lines.append(f"| **Weighted F1 Score** | `{result.weighted_f1:.4f}` | Support-weighted average F1 across classes |")
    lines.append("")
    lines.append(f"*Counts:* **TP** = `{result.tp}`, **TN** = `{result.tn}`, **FP** = `{result.fp}`, **FN** = `{result.fn}`")
    lines.append("")

    # 3. Confusion Matrix
    lines.append("## Confusion Matrix")
    lines.append("")
    lines.append("Rows represent **Actual Ground Truth**, columns represent **Predicted Verdict**.")
    lines.append("")
    lines.append("| Actual \\ Predicted | Real (Original) | AI Generated |")
    lines.append("| --- | --- | --- |")
    cm = result.confusion_matrix.matrix
    lines.append(f"| **Actual Real** | `{cm[0][0]}` (TN) | `{cm[0][1]}` (FP) |")
    lines.append(f"| **Actual AI Generated** | `{cm[1][0]}` (FN) | `{cm[1][1]}` (TP) |")
    lines.append("")

    # 4. Per-Class Performance
    lines.append("## Per-Class Performance")
    lines.append("")
    lines.append("| Class | Support (Count) | Precision | Recall | F1 Score |")
    lines.append("| --- | --- | --- | --- | --- |")
    for cls_name, metrics in sorted(result.per_class_metrics.items()):
        label = "Real (Original)" if cls_name == "original" else "AI Generated"
        lines.append(
            f"| **{label}** | {int(metrics['support'])} | "
            f"`{metrics['precision'] * 100:.2f}%` | `{metrics['recall'] * 100:.2f}%` | `{metrics['f1']:.4f}` |"
        )
    lines.append("")

    # 5. Confidence Analysis
    lines.append("## Confidence Analysis")
    lines.append("")
    ca = result.confidence_analysis
    lines.append("| Statistic | Value |")
    lines.append("| --- | --- |")
    lines.append(f"| **Average Confidence on Correct Predictions** | `{ca.mean_confidence_correct * 100:.2f}%` |")
    lines.append(f"| **Average Confidence on Incorrect Predictions** | `{ca.mean_confidence_incorrect * 100:.2f}%` |")
    lines.append(f"| **High-Confidence Failures (Confidence >= 80%)** | `{ca.high_confidence_failures_count}` cases |")
    lines.append(f"| **Low-Confidence Correct (Confidence <= 60%)** | `{ca.low_confidence_correct_count}` cases |")
    lines.append("")

    # 6. Detector Analysis
    lines.append("## Detector Analysis")
    lines.append("")
    lines.append("Mean normalized scores, standard deviations, and class separation across all 7 production detectors:")
    lines.append("")
    lines.append("| Detector | Real Mean ± Std | AI Generated Mean ± Std | Separation Margin | Diagnostic Status |")
    lines.append("| --- | --- | --- | --- | --- |")
    for det_name, det_stat in sorted(result.detector_statistics.items()):
        orig_m = det_stat.get("original_mean", 0.0)
        orig_s = det_stat.get("original_std", 0.0)
        gen_m = det_stat.get("ai_generated_mean", 0.0)
        gen_s = det_stat.get("ai_generated_std", 0.0)
        sep = det_stat.get("separation_margin", 0.0)
        suspicious = det_stat.get("suspicious_behavior", [])
        status = ", ".join(suspicious) if suspicious else "Well-separated"
        lines.append(
            f"| `{det_name}` | `{orig_m:.2f} ± {orig_s:.2f}` | `{gen_m:.2f} ± {gen_s:.2f}` | `{sep:.2f}` | {status} |"
        )
    lines.append("")

    # 7. Failure Analysis
    lines.append("## Failure Analysis")
    lines.append("")
    fps = result.failure_cases.get("false_positives", [])
    fns = result.failure_cases.get("false_negatives", [])

    lines.append(f"### 7.1 False Positives ({len(fps)} Real images predicted as AI Generated)")
    if fps:
        lines.append("| Image ID | Predicted | Confidence | Top Detectors | Relative Path |")
        lines.append("| --- | --- | --- | --- | --- |")
        for item in fps[:10]:
            top_det = ", ".join(item.get("most_influential_detectors", [])[:2])
            lines.append(f"| `{item['image_id']}` | `{item['predicted_class']}` | `{item['confidence'] * 100:.1f}%` | `{top_det}` | `{Path(item['file_path']).name}` |")
        if len(fps) > 10:
            lines.append(f"*... and {len(fps) - 10} more false positives recorded in JSON.*")
    else:
        lines.append("No false positives observed.")
    lines.append("")

    lines.append(f"### 7.2 False Negatives ({len(fns)} AI Generated images predicted as Real)")
    if fns:
        lines.append("| Image ID | Predicted | Confidence | Top Detectors | Relative Path |")
        lines.append("| --- | --- | --- | --- | --- |")
        for item in fns[:10]:
            top_det = ", ".join(item.get("most_influential_detectors", [])[:2])
            lines.append(f"| `{item['image_id']}` | `{item['predicted_class']}` | `{item['confidence'] * 100:.1f}%` | `{top_det}` | `{Path(item['file_path']).name}` |")
        if len(fns) > 10:
            lines.append(f"*... and {len(fns) - 10} more false negatives recorded in JSON.*")
    else:
        lines.append("No false negatives observed.")
    lines.append("")

    # 8. High-Confidence Failures
    high_conf = result.failure_cases.get("high_confidence_failures", [])
    lines.append(f"## High-Confidence Failures ({len(high_conf)} cases with Confidence >= 80%)")
    lines.append("")
    if high_conf:
        lines.append("| Image ID | Ground Truth | Predicted | Confidence | Top Detectors | File |")
        lines.append("| --- | --- | --- | --- | --- | --- |")
        for item in high_conf[:10]:
            top_det = ", ".join(item.get("most_influential_detectors", [])[:2])
            lines.append(f"| `{item['image_id']}` | `{item['ground_truth']}` | `{item['predicted_class']}` | `{item['confidence'] * 100:.1f}%` | `{top_det}` | `{Path(item['file_path']).name}` |")
    else:
        lines.append("No high-confidence failures observed.")
    lines.append("")

    # 9. Low-Confidence Correct
    low_conf = result.failure_cases.get("low_confidence_correct", [])
    lines.append(f"## Low-Confidence Correct ({len(low_conf)} cases with Confidence <= 60%)")
    lines.append("")
    if low_conf:
        lines.append("| Image ID | Ground Truth | Predicted | Confidence | File |")
        lines.append("| --- | --- | --- | --- | --- |")
        for item in low_conf[:10]:
            lines.append(f"| `{item['image_id']}` | `{item['ground_truth']}` | `{item['predicted_class']}` | `{item['confidence'] * 100:.1f}%` | `{Path(item['file_path']).name}` |")
    else:
        lines.append("No low-confidence correct cases observed.")
    lines.append("")

    # 10. Recommended Calibration Candidates
    lines.append("## Calibration Candidates")
    lines.append("")
    lines.append("> [!IMPORTANT]")
    lines.append("> The following are empirical findings for investigation and calibration in subsequent milestones. No detector weights or fusion thresholds were altered in Milestone 12.")
    lines.append("")
    if result.calibration_candidates:
        for candidate in result.calibration_candidates:
            lines.append(f"- **Detector Behavior:** {candidate}")
    else:
        lines.append("- All detector distributions exhibit healthy separation.")
    lines.append("")
    lines.append("---")
    lines.append("*Report generated automatically by Chai AI Milestone 12 Evaluation Harness.*")

    return "\n".join(lines)


def save_markdown_report(report_text: str, output_path: Path) -> None:
    """Save generated markdown report text to file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report_text, encoding="utf-8")


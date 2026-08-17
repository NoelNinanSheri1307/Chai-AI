"""Human-readable report generator for benchmark evaluation runs."""

from __future__ import annotations

from pathlib import Path

from app.benchmark.models import BenchmarkRunResult


def generate_markdown_report(result: BenchmarkRunResult) -> str:
    """Generate a detailed GitHub-flavored Markdown report from benchmark run results."""
    lines: list[str] = []

    lines.append(f"# Chai AI — Benchmark Evaluation Report (`{result.run_id}`)")
    lines.append("")
    lines.append(f"**Run Timestamp:** `{result.timestamp}`")
    lines.append(f"**Pipeline Version:** `{result.pipeline_version}`")
    lines.append(f"**Manifest Hash:** `{result.manifest_hash[:16]}...`")
    lines.append(f"**Total Duration:** `{result.duration_seconds}s`")
    lines.append(f"**Total Evaluated Images:** `{result.total_images}` ({result.successful_analyses} success, {result.failed_analyses} failed)")
    lines.append("")
    lines.append("---")
    lines.append("")

    # 1. Performance Overview
    lines.append("## 1. Performance Overview")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("| --- | --- |")
    lines.append(f"| **Overall Accuracy** | `{result.overall_accuracy * 100:.2f}%` |")
    lines.append(f"| **Macro F1 Score** | `{result.macro_f1:.4f}` |")
    lines.append(f"| **Weighted F1 Score** | `{result.weighted_f1:.4f}` |")
    lines.append("")

    # 2. Per-Class Metrics
    lines.append("## 2. Per-Class Performance")
    lines.append("")
    lines.append("| Class | Total Samples | Precision | Recall | F1 Score |")
    lines.append("| --- | --- | --- | --- | --- |")
    for cls_name, metrics in result.per_class_metrics.items():
        lines.append(
            f"| `{cls_name}` | {metrics['total_samples']} | "
            f"`{metrics['precision']:.4f}` | `{metrics['recall']:.4f}` | `{metrics['f1']:.4f}` |"
        )
    lines.append("")

    # 3. Confusion Matrix
    lines.append("## 3. Confusion Matrix")
    lines.append("")
    lines.append("Columns represent **Predicted Verdict**, rows represent **Ground Truth**.")
    lines.append("")
    cm = result.confusion_matrix
    lines.append("| Ground Truth \\ Predicted | Original | AI Edited | AI Generated |")
    lines.append("| --- | --- | --- | --- |")
    for i, row_label in enumerate(cm.labels):
        row = cm.matrix[i]
        lines.append(f"| **{row_label}** | `{row[0]}` | `{row[1]}` | `{row[2]}` |")
    lines.append("")

    # 4. Detector-Level Performance Breakdown
    lines.append("## 4. Detector-Level Performance Breakdown")
    lines.append("")
    lines.append("Mean normalized scores and separation margins across all 7 internal detectors:")
    lines.append("")
    lines.append("| Detector | Original Mean | AI Edited Mean | AI Generated Mean | Separation Margin |")
    lines.append("| --- | --- | --- | --- | --- |")
    for det_name, det_stat in sorted(result.detector_statistics.items()):
        orig_m = det_stat.get("original_mean", 0.0)
        edit_m = det_stat.get("ai_edited_mean", 0.0)
        gen_m = det_stat.get("ai_generated_mean", 0.0)
        sep = det_stat.get("separation_margin", 0.0)
        lines.append(
            f"| `{det_name}` | `{orig_m:.4f}` | `{edit_m:.4f}` | `{gen_m:.4f}` | `{sep:.4f}` |"
        )
    lines.append("")

    # 5. Failure Case Analysis
    lines.append("## 5. Failure Case Analysis")
    lines.append("")

    fps = result.failure_cases.get("false_positives", [])
    fns = result.failure_cases.get("false_negatives", [])
    high_conf = result.failure_cases.get("high_confidence_failures", [])

    lines.append(f"### 5.1 False Positives ({len(fps)})")
    lines.append("Authentic images misclassified as AI content:")
    lines.append("")
    if fps:
        lines.append("| Image ID | Dataset | Ground Truth | Chai Verdict | Confidence |")
        lines.append("| --- | --- | --- | --- | --- |")
        for item in fps[:10]:
            lines.append(f"| `{item['image_id']}` | `{item['dataset']}` | `{item['ground_truth']}` | `{item['chai_verdict']}` | `{item['confidence']:.2f}` |")
    else:
        lines.append("No false positives observed.")
    lines.append("")

    lines.append(f"### 5.2 False Negatives ({len(fns)})")
    lines.append("AI content misclassified as authentic:")
    lines.append("")
    if fns:
        lines.append("| Image ID | Dataset | Ground Truth | Chai Verdict | Confidence |")
        lines.append("| --- | --- | --- | --- | --- |")
        for item in fns[:10]:
            lines.append(f"| `{item['image_id']}` | `{item['dataset']}` | `{item['ground_truth']}` | `{item['chai_verdict']}` | `{item['confidence']:.2f}` |")
    else:
        lines.append("No false negatives observed.")
    lines.append("")

    lines.append(f"### 5.3 High-Confidence Failures ({len(high_conf)})")
    lines.append("Incorrect classifications with high confidence (>= 0.80):")
    lines.append("")
    if high_conf:
        lines.append("| Image ID | Ground Truth | Verdict | Confidence | File Path |")
        lines.append("| --- | --- | --- | --- | --- |")
        for item in high_conf[:10]:
            lines.append(f"| `{item['image_id']}` | `{item['ground_truth']}` | `{item['chai_verdict']}` | `{item['confidence']:.2f}` | `{Path(item['file_path']).name}` |")
    else:
        lines.append("No high-confidence failures observed.")
    lines.append("")

    # 6. Main Observations & Recommendations
    lines.append("## 6. Main Observations & Calibration Investigation Areas")
    lines.append("")
    lines.append("> [!NOTE]")
    lines.append("> The following are observational findings for future calibration milestones. No detector thresholds were altered in Milestone 12.")
    lines.append("")
    lines.append("1. **Frequency & ELA Sensitivity:** Observe if frequency domain anomaly detection shows elevated false positives on screenshots or heavily compressed JPEG images.")
    lines.append("2. **Metadata Weighting:** Validate camera EXIF metadata contribution in distinguishing uncompressed authentic photos from generated images.")
    lines.append("3. **Texture & Lighting Separation:** Review texture micro-structure and directional lighting consistency across difficult photographic cases.")
    lines.append("")
    lines.append("---")
    lines.append("*Report generated by Chai AI Automated Evaluation Harness (Milestone 12).*")

    return "\n".join(lines)


def save_markdown_report(report_text: str, output_path: Path) -> None:
    """Save generated markdown report text to file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report_text, encoding="utf-8")

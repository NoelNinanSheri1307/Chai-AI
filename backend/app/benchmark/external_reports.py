"""Markdown and JSON report generators for Milestone 15 external benchmarking."""

from __future__ import annotations

from pathlib import Path

from app.benchmark.external_metrics import ExternalBenchmarkReportResult


def generate_external_markdown_report(result: ExternalBenchmarkReportResult) -> str:
    """Render a comprehensive 13-section comparative Markdown report."""
    ds = result.dataset_summary
    chai = result.chai_metrics
    ext = result.external_metrics
    agr = result.agreement
    conf = result.confidence_analysis
    fail = result.failures

    lines: list[str] = [
        "# Chai AI vs Sightengine External Benchmark Report",
        "",
        f"**Run ID**: `{result.run_id}`  ",
        f"**Timestamp**: `{result.timestamp}`  ",
        f"**Manifest Hash**: `{ds.get('manifest_hash', 'N/A')[:16]}...`  ",
        "",
        "---",
        "",
        "## 1. Dataset Summary",
        "",
        f"- **Total Images Evaluated**: {ds.get('total_images', 0)}",
        f"- **Real / Authentic Images**: {ds.get('real_count', 0)} ({ds.get('real_count', 0) / max(1, ds.get('total_images', 1)) * 100:.1f}%)",
        f"- **AI Generated Images**: {ds.get('ai_generated_count', 0)} ({ds.get('ai_generated_count', 0) / max(1, ds.get('total_images', 1)) * 100:.1f}%)",
        "",
        "> [!NOTE]",
        f"> **Dataset Imbalance**: The benchmark dataset contains {ds.get('real_count', 0)} Real images vs {ds.get('ai_generated_count', 0)} AI Generated images. Due to this class imbalance, accuracy alone is insufficient; evaluation must prioritize AI Recall, Precision, and Macro F1.",
        "",
        "---",
        "",
        "## 2. Chai Internal Pipeline Performance Metrics",
        "",
        "| Metric | Chai AI Value |",
        "| :--- | :--- |",
        f"| **Overall Accuracy** | {chai.get('accuracy', 0.0) * 100:.2f}% |",
        f"| **AI Precision** | {chai.get('precision', 0.0) * 100:.2f}% |",
        f"| **AI Recall** | {chai.get('recall', 0.0) * 100:.2f}% |",
        f"| **AI F1 Score** | {chai.get('f1', 0.0):.4f} |",
        f"| **Macro F1 Score** | {chai.get('macro_f1', 0.0):.4f} |",
        f"| **True Positives (TP)** | {chai.get('tp', 0)} |",
        f"| **True Negatives (TN)** | {chai.get('tn', 0)} |",
        f"| **False Positives (FP)** | {chai.get('fp', 0)} |",
        f"| **False Negatives (FN)** | {chai.get('fn', 0)} |",
        "",
        "---",
        "",
        "## 3. Sightengine Benchmark Metrics",
        "",
        f"**Provider**: `{ext.provider_name}` (v{ext.provider_version})  ",
        f"**Successful Analyses**: {ext.successful_analyses} / {ext.total_evaluated}  ",
        f"**Failures / Timeouts / Unconfigured**: {ext.failed_analyses} failures, {ext.timeouts} timeouts, {ext.unconfigured_or_disabled} unconfigured  ",
        "",
        "| Metric | Sightengine Value |",
        "| :--- | :--- |",
        f"| **Overall Accuracy** | {ext.accuracy * 100:.2f}% |",
        f"| **AI Precision** | {ext.precision * 100:.2f}% |",
        f"| **AI Recall** | {ext.recall * 100:.2f}% |",
        f"| **AI F1 Score** | {ext.f1:.4f} |",
        f"| **Macro F1 Score** | {ext.macro_f1:.4f} |",
        f"| **True Positives (TP)** | {ext.tp} |",
        f"| **True Negatives (TN)** | {ext.tn} |",
        f"| **False Positives (FP)** | {ext.fp} |",
        f"| **False Negatives (FN)** | {ext.fn} |",
        "",
        "---",
        "",
        "## 4. Chai vs Sightengine Agreement",
        "",
        f"- **Total Compared**: {agr.total_compared}",
        f"- **Agreement Count**: {agr.agree_count} ({agr.agreement_rate * 100:.2f}%)",
        f"- **Disagreement Count**: {agr.disagree_count} ({(1.0 - agr.agreement_rate) * 100:.2f}%)",
        "",
        "### Agreement by Ground-Truth Partition",
        f"- **Ground-Truth Real Partition**: {agr.real_subset_agree_count} / {agr.real_subset_count} agree ({agr.real_subset_agree_rate * 100:.2f}%)",
        f"- **Ground-Truth AI Partition**: {agr.ai_subset_agree_count} / {agr.ai_subset_count} agree ({agr.ai_subset_agree_rate * 100:.2f}%)",
        "",
        "### Decision Quadrants",
        "| Category | Count | Interpretation |",
        "| :--- | :--- | :--- |",
        f"| **Chai Real & Sightengine Real** | {agr.chai_real_ext_real} | Both systems judged image authentic |",
        f"| **Chai AI & Sightengine AI** | {agr.chai_ai_ext_ai} | Both systems detected AI generation |",
        f"| **Chai AI & Sightengine Real** | {agr.chai_ai_ext_real} | Chai flagged AI, Sightengine judged authentic |",
        f"| **Chai Real & Sightengine AI** | {agr.chai_real_ext_ai} | Chai judged authentic, Sightengine flagged AI |",
        "",
        "---",
        "",
        "## 5. Three-Way Ground-Truth Comparison",
        "",
        "| Ground Truth | Chai Verdict | Sightengine | Count | Pct | Interpretation |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |",
    ]

    for tw in result.three_way_comparison:
        lines.append(
            f"| `{tw.ground_truth}` | `{tw.chai_verdict}` | `{tw.external_verdict}` | {tw.count} | {tw.percentage * 100:.1f}% | {tw.interpretation} |"
        )

    lines.extend(
        [
            "",
            "---",
            "",
            "## 6. Format-Specific Comparison",
            "",
            "| Format | Count | Chai Accuracy | Sightengine Accuracy | Chai AI Recall | Sightengine AI Recall | Agreement Rate |",
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
        ]
    )

    for fmt_name, fmt_data in sorted(result.format_breakdown.items()):
        lines.append(
            f"| **{fmt_name}** | {fmt_data.image_count} | {fmt_data.chai_accuracy * 100:.1f}% | {fmt_data.external_accuracy * 100:.1f}% | {fmt_data.chai_ai_recall * 100:.1f}% | {fmt_data.external_ai_recall * 100:.1f}% | {fmt_data.agreement_rate * 100:.1f}% |"
        )

    lines.extend(
        [
            "",
            "---",
            "",
            "## 7. Confidence Analysis",
            "",
            "> [!NOTE]",
            f"> {conf.note}",
            "",
            "| System | Mean Conf on Correct | Mean Conf on Incorrect |",
            "| :--- | :--- | :--- |",
            f"| **Chai AI** | {conf.chai_mean_confidence_correct:.4f} | {conf.chai_mean_confidence_incorrect:.4f} |",
            f"| **Sightengine** | {conf.external_mean_confidence_correct:.4f} | {conf.external_mean_confidence_incorrect:.4f} |",
            "",
            "---",
            "",
            "## 8. Provider Failures & Status",
            "",
            f"- **Successful API Calls**: {ext.successful_analyses}",
            f"- **Failed API Calls**: {ext.failed_analyses}",
            f"- **Timeouts**: {ext.timeouts}",
            f"- **Unconfigured / Disabled**: {ext.unconfigured_or_disabled}",
            "",
            "---",
            "",
            f"## 9. Chai-Only Failures (Sightengine Correct, Chai Wrong: {len(fail.external_correct_chai_wrong)})",
            "",
        ]
    )

    if fail.external_correct_chai_wrong:
        lines.append(
            "| Image ID | Ground Truth | Chai Verdict (Conf) | Sightengine (Conf) | Format | Path |"
        )
        lines.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
        for item in fail.external_correct_chai_wrong[:10]:
            lines.append(
                f"| `{item.image_id}` | `{item.ground_truth}` | `{item.chai_verdict}` ({item.chai_confidence:.2f}) | `{item.external_verdict}` ({item.external_confidence or 0.0:.2f}) | {item.file_format} | `{item.file_path}` |"
            )
        if len(fail.external_correct_chai_wrong) > 10:
            lines.append(
                f"*...and {len(fail.external_correct_chai_wrong) - 10} more cases.*"
            )
    else:
        lines.append("*No cases where Sightengine was correct and Chai was wrong.*")

    lines.extend(
        [
            "",
            "---",
            "",
            f"## 10. Sightengine-Only Failures (Chai Correct, Sightengine Wrong: {len(fail.chai_correct_external_wrong)})",
            "",
        ]
    )

    if fail.chai_correct_external_wrong:
        lines.append(
            "| Image ID | Ground Truth | Chai Verdict (Conf) | Sightengine (Conf) | Format | Path |"
        )
        lines.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
        for item in fail.chai_correct_external_wrong[:10]:
            lines.append(
                f"| `{item.image_id}` | `{item.ground_truth}` | `{item.chai_verdict}` ({item.chai_confidence:.2f}) | `{item.external_verdict}` ({item.external_confidence or 0.0:.2f}) | {item.file_format} | `{item.file_path}` |"
            )
        if len(fail.chai_correct_external_wrong) > 10:
            lines.append(
                f"*...and {len(fail.chai_correct_external_wrong) - 10} more cases.*"
            )
    else:
        lines.append("*No cases where Chai was correct and Sightengine was wrong.*")

    lines.extend(
        [
            "",
            "---",
            "",
            f"## 11. Dual-System Failures (Both Wrong: {len(fail.both_wrong)})",
            "",
        ]
    )

    if fail.both_wrong:
        lines.append(
            "| Image ID | Ground Truth | Chai Verdict (Conf) | Sightengine (Conf) | Format | Path |"
        )
        lines.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
        for item in fail.both_wrong[:10]:
            lines.append(
                f"| `{item.image_id}` | `{item.ground_truth}` | `{item.chai_verdict}` ({item.chai_confidence:.2f}) | `{item.external_verdict}` ({item.external_confidence or 0.0:.2f}) | {item.file_format} | `{item.file_path}` |"
            )
        if len(fail.both_wrong) > 10:
            lines.append(f"*...and {len(fail.both_wrong) - 10} more cases.*")
    else:
        lines.append("*No cases where both systems were wrong.*")

    lines.extend(
        [
            "",
            "---",
            "",
            "## 12. Interpretation",
            "",
        ]
    )
    for note in result.methodology_notes:
        lines.append(f"- {note}")

    lines.extend(
        [
            "",
            "---",
            "",
            "## 13. Limitations",
            "",
        ]
    )
    for lim in result.limitations:
        lines.append(f"- {lim}")

    lines.append("")
    return "\n".join(lines)


def save_external_reports(
    result: ExternalBenchmarkReportResult,
    out_dir: Path,
) -> tuple[Path, Path]:
    """Save external benchmark Markdown and JSON reports to disk."""
    out_dir.mkdir(parents=True, exist_ok=True)
    latest_md = out_dir / "latest_external.md"
    latest_json = out_dir / "latest_external.json"

    md_content = generate_external_markdown_report(result)
    latest_md.write_text(md_content, encoding="utf-8")

    json_content = result.model_dump_json(indent=2)
    latest_json.write_text(json_content, encoding="utf-8")

    return latest_md, latest_json

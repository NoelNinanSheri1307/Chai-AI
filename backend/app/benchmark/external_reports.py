"""Markdown and JSON report generators for Milestone 15 & 16 external benchmarking."""

from __future__ import annotations

from pathlib import Path

from app.benchmark.external_metrics import ExternalBenchmarkReportResult


def generate_external_markdown_report(result: ExternalBenchmarkReportResult) -> str:
    """Render a comprehensive 16-section comparative Markdown report."""
    ds = result.dataset_summary
    chai = result.chai_metrics
    ext = result.external_metrics
    deltas = result.metric_deltas
    agr = result.agreement
    conf = result.confidence_analysis
    fail = result.failures
    tax = result.error_taxonomy
    ai_grp = result.ai_subgroup_analysis
    base = result.baseline_comparison
    dec = result.decision

    lines: list[str] = [
        "# Milestone 16 — Full Sightengine Benchmark Analysis & Calibration Decision",
        "",
        f"**Run ID**: `{result.run_id}`  ",
        f"**Timestamp**: `{result.timestamp}`  ",
        f"**Manifest Hash**: `{ds.get('manifest_hash', 'N/A')[:16]}...`  ",
        "",
        "---",
        "",
        "## 1. Executive Summary",
        "",
        f"- **Dataset Evaluated**: {ds.get('total_images', 0)} images ({ds.get('real_count', 0)} Real, {ds.get('ai_generated_count', 0)} AI Generated).",
        f"- **Chai AI Accuracy**: {chai.get('accuracy', 0.0) * 100:.2f}% | **AI Recall**: {chai.get('recall', 0.0) * 100:.2f}% | **AI Precision**: {chai.get('precision', 0.0) * 100:.2f}% | **AI F1**: {chai.get('f1', 0.0):.4f} | **Macro F1**: {chai.get('macro_f1', 0.0):.4f}.",
        f"- **Sightengine Accuracy**: {ext.accuracy * 100:.2f}% | **AI Recall**: {ext.recall * 100:.2f}% | **AI Precision**: {ext.precision * 100:.2f}% | **AI F1**: {ext.f1:.4f} | **Macro F1**: {ext.macro_f1:.4f}.",
        f"- **Verdict Agreement**: {agr.agree_count} / {agr.total_compared} ({agr.agreement_rate * 100:.2f}%).",
        f"- **M12 to M14 Improvement**: AI Recall improved from 9.62% -> {chai.get('recall', 0.0) * 100:.2f}% (+{base.delta_recall * 100:.2f} pp); High-confidence failures reduced from 35 -> {base.current_high_conf_failures}.",
        f"- **Recommendation**: **{dec.recommended_option}** — {dec.title}.",
        "",
        "---",
        "",
        "## 2. Dataset",
        "",
        f"- **Total Images**: {ds.get('total_images', 0)}",
        f"- **Real Images (COCO val2017)**: {ds.get('real_count', 0)} ({ds.get('real_count', 0) / max(1, ds.get('total_images', 1)) * 100:.1f}%)",
        f"- **AI-Generated Images**: {ds.get('ai_generated_count', 0)} ({ds.get('ai_generated_count', 0) / max(1, ds.get('total_images', 1)) * 100:.1f}%)",
        "",
        "> [!NOTE]",
        "> **Class Imbalance**: The benchmark exhibits an authentic-to-synthetic ratio of ~12:1. Overall accuracy is heavily dominated by performance on the 616 Real images. AI Recall, AI Precision, and Macro F1 serve as the primary evaluation benchmarks.",
        "",
        "---",
        "",
        "## 3. Milestone 12 Baseline Performance",
        "",
        "| Metric | M12 Baseline Value |",
        "| :--- | :--- |",
        f"| **Overall Accuracy** | {base.m12_accuracy * 100:.2f}% |",
        f"| **AI Precision** | {base.m12_ai_precision * 100:.2f}% |",
        f"| **AI Recall** | {base.m12_ai_recall * 100:.2f}% |",
        f"| **AI F1 Score** | {base.m12_ai_f1:.4f} |",
        f"| **Macro F1 Score** | {base.m12_macro_f1:.4f} |",
        f"| **True Positives (TP)** | {base.m12_tp} |",
        f"| **True Negatives (TN)** | {base.m12_tn} |",
        f"| **False Positives (FP)** | {base.m12_fp} |",
        f"| **False Negatives (FN)** | {base.m12_fn} |",
        f"| **High-Confidence Failures** | {base.m12_high_conf_failures} |",
        "",
        "---",
        "",
        "## 4. Current / Milestone 14 Results",
        "",
        "| Metric | Current Calibrated Value | Delta vs M12 Baseline |",
        "| :--- | :--- | :--- |",
        f"| **Overall Accuracy** | {chai.get('accuracy', 0.0) * 100:.2f}% | {base.delta_accuracy * 100:+.2f} pp |",
        f"| **AI Precision** | {chai.get('precision', 0.0) * 100:.2f}% | {base.delta_precision * 100:+.2f} pp |",
        f"| **AI Recall** | {chai.get('recall', 0.0) * 100:.2f}% | {base.delta_recall * 100:+.2f} pp |",
        f"| **AI F1 Score** | {chai.get('f1', 0.0):.4f} | {base.delta_f1:+.4f} |",
        f"| **Macro F1 Score** | {chai.get('macro_f1', 0.0):.4f} | {base.delta_macro_f1:+.4f} |",
        f"| **Real Recall (Specificity)** | {chai.get('real_recall', 0.0) * 100:.2f}% | {(chai.get('real_recall', 0.0) - (base.m12_tn / 616)) * 100:+.2f} pp |",
        f"| **True Positives (TP)** | {chai.get('tp', 0)} | {base.delta_tp:+d} |",
        f"| **True Negatives (TN)** | {chai.get('tn', 0)} | {chai.get('tn', 0) - base.m12_tn:+d} |",
        f"| **False Positives (FP)** | {chai.get('fp', 0)} | {base.delta_fp:+d} |",
        f"| **False Negatives (FN)** | {chai.get('fn', 0)} | {base.delta_fn:+d} |",
        f"| **High-Confidence Failures** | {base.current_high_conf_failures} | {base.delta_high_conf_failures:+d} |",
        "",
        "---",
        "",
        "## 5. Sightengine Results",
        "",
        f"**Provider Status**: {ext.successful_analyses} / {ext.total_evaluated} successful ({ext.failed_analyses} failures, {ext.timeouts} timeouts, {ext.unconfigured_or_disabled} unconfigured).",
        "",
        "| Metric | Sightengine Value |",
        "| :--- | :--- |",
        f"| **Overall Accuracy** | {ext.accuracy * 100:.2f}% |",
        f"| **AI Precision** | {ext.precision * 100:.2f}% |",
        f"| **AI Recall** | {ext.recall * 100:.2f}% |",
        f"| **AI F1 Score** | {ext.f1:.4f} |",
        f"| **Macro F1 Score** | {ext.macro_f1:.4f} |",
        f"| **Real Recall** | {ext.real_recall * 100:.2f}% |",
        f"| **Real Precision** | {ext.real_precision * 100:.2f}% |",
        f"| **True Positives (TP)** | {ext.tp} |",
        f"| **True Negatives (TN)** | {ext.tn} |",
        f"| **False Positives (FP)** | {ext.fp} |",
        f"| **False Negatives (FN)** | {ext.fn} |",
        "",
        "---",
        "",
        "## 6. Chai vs Sightengine Comparison",
        "",
        "| Metric | Chai AI | Sightengine | Delta (Sightengine - Chai) |",
        "| :--- | :--- | :--- | :--- |",
        f"| **Accuracy** | {chai.get('accuracy', 0.0) * 100:.2f}% | {ext.accuracy * 100:.2f}% | {deltas.accuracy_delta * 100:+.2f} pp |",
        f"| **AI Precision** | {chai.get('precision', 0.0) * 100:.2f}% | {ext.precision * 100:.2f}% | {deltas.precision_delta * 100:+.2f} pp |",
        f"| **AI Recall** | {chai.get('recall', 0.0) * 100:.2f}% | {ext.recall * 100:.2f}% | {deltas.recall_delta * 100:+.2f} pp |",
        f"| **AI F1 Score** | {chai.get('f1', 0.0):.4f} | {ext.f1:.4f} | {deltas.f1_delta:+.4f} |",
        f"| **Macro F1 Score** | {chai.get('macro_f1', 0.0):.4f} | {ext.macro_f1:.4f} | {deltas.macro_f1_delta:+.4f} |",
        "",
        f"- **Total Compared Pairs**: {agr.total_compared}",
        f"- **Overall Agreement Rate**: {agr.agree_count} / {agr.total_compared} ({agr.agreement_rate * 100:.2f}%)",
        f"- **Disagreement Rate**: {agr.disagree_count} / {agr.total_compared} ({(1.0 - agr.agreement_rate) * 100:.2f}%)",
        f"- **Agreement on Ground-Truth Real**: {agr.real_subset_agree_count} / {agr.real_subset_count} ({agr.real_subset_agree_rate * 100:.2f}%)",
        f"- **Agreement on Ground-Truth AI**: {agr.ai_subset_agree_count} / {agr.ai_subset_count} ({agr.ai_subset_agree_rate * 100:.2f}%)",
        "",
        "---",
        "",
        "## 7. Ground Truth × Chai × Sightengine",
        "",
        "| Ground Truth | Chai Verdict | Sightengine | Count | Pct | Diagnostic Interpretation |",
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
            "## 8. Format Analysis",
            "",
            "| Format | Count | Chai Acc | Sightengine Acc | Chai AI Recall | Sightengine AI Recall | Chai F1 | Sightengine F1 | Agreement |",
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
        ]
    )

    for fmt_name, fmt_data in sorted(result.format_breakdown.items()):
        lines.append(
            f"| **{fmt_name}** | {fmt_data.image_count} | {fmt_data.chai_accuracy * 100:.1f}% | {fmt_data.external_accuracy * 100:.1f}% | {fmt_data.chai_ai_recall * 100:.1f}% | {fmt_data.external_ai_recall * 100:.1f}% | {fmt_data.chai_f1:.4f} | {fmt_data.external_f1:.4f} | {fmt_data.agreement_rate * 100:.1f}% |"
        )

    lines.extend(
        [
            "",
            "### AVIF Container Forensic Impact",
            "- **Historical Context (M12/M13)**: In Milestone 12/13, 36 AI-generated AVIF images failed OpenCV decoding, resulting in silent fallback detector scores and 35 high-confidence false negatives.",
            "- **Milestone 14 Fix**: Switching to Pillow-backed multi-format decoding restored pixel accessibility, increasing Chai AVIF AI True Positives from 0 to 11 and completely eliminating the 35 high-confidence failures.",
            "",
            "---",
            "",
            "## 9. Detector Analysis",
            "",
            "Statistical analysis across all 668 benchmark image scores:",
            "",
            "| Rank | Detector | Real Mean ± Std | AI Mean ± Std | Separation | Direction | Fallback Count (%) | Empirical Forensic Verdict |",
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
        ]
    )

    for det in result.detector_analysis:
        dir_badge = "Correct (+)" if det.direction_correct else "Inverted (-)"
        lines.append(
            f"| {det.empirical_rank} | **{det.detector_name}** | {det.real_mean:.2f} ± {det.real_std:.2f} | {det.ai_mean:.2f} ± {det.ai_std:.2f} | {det.separation_margin:+.2f} | {dir_badge} | {det.fallback_count} ({det.fallback_pct * 100:.1f}%) | {det.empirical_verdict} |"
        )

    lines.extend(
        [
            "",
            "---",
            "",
            "## 10. Confidence Analysis",
            "",
            "> [!NOTE]",
            f"> {conf.note}",
            "",
            "| Metric | Chai AI | Sightengine |",
            "| :--- | :--- | :--- |",
            f"| **Mean Confidence on Correct Predictions** | {conf.chai_mean_confidence_correct:.4f} | {conf.external_mean_confidence_correct:.4f} |",
            f"| **Mean Confidence on Incorrect Predictions** | {conf.chai_mean_confidence_incorrect:.4f} | {conf.external_mean_confidence_incorrect:.4f} |",
            f"| **High-Confidence Failures (>= 80%)** | {conf.chai_high_confidence_failures_80} | {conf.external_high_confidence_failures_80} |",
            f"| **Very-High-Confidence Failures (>= 90%)** | {conf.chai_very_high_confidence_failures_90} | N/A |",
            f"| **Low-Confidence Correct (<= 60%)** | {conf.chai_low_confidence_correct_60} | N/A |",
            "",
            "### Top High-Confidence Failures",
            "",
        ]
    )

    if conf.worst_high_confidence_failures:
        lines.append(
            "| Image ID | Ground Truth | Chai Verdict | Chai Conf | Format | Path |"
        )
        lines.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
        for wf in conf.worst_high_confidence_failures[:5]:
            lines.append(
                f"| `{wf.image_id}` | `{wf.ground_truth}` | `{wf.chai_verdict}` | {wf.chai_confidence:.4f} | {wf.file_format} | `{wf.file_path}` |"
            )
    else:
        lines.append("*No high-confidence failures recorded.*")

    lines.extend(
        [
            "",
            "---",
            "",
            "## 11. Error Taxonomy",
            "",
            "| Error Category | Count | Percentage |",
            "| :--- | :--- | :--- |",
            f"| **Both Correct** | {tax.both_correct_count} | {tax.both_correct_pct * 100:.2f}% |",
            f"| **Both Wrong** | {tax.both_wrong_count} | {tax.both_wrong_pct * 100:.2f}% |",
            f"| **Chai Correct / Sightengine Wrong** | {tax.chai_correct_ext_wrong_count} | {tax.chai_correct_ext_wrong_pct * 100:.2f}% |",
            f"| **Sightengine Correct / Chai Wrong** | {tax.ext_correct_chai_wrong_count} | {tax.ext_correct_chai_wrong_pct * 100:.2f}% |",
            f"| **Chai False Positives (Real flagged as AI)** | {tax.chai_fp_count} | {tax.chai_fp_pct * 100:.2f}% |",
            f"| **Chai False Negatives (AI missed as Real)** | {tax.chai_fn_count} | {tax.chai_fn_pct * 100:.2f}% |",
            f"| **Sightengine False Positives** | {tax.ext_fp_count} | {tax.ext_fp_pct * 100:.2f}% |",
            f"| **Sightengine False Negatives** | {tax.ext_fn_count} | {tax.ext_fn_pct * 100:.2f}% |",
            "",
            "---",
            "",
            "## 12. AI-Generated Subgroup Analysis",
            "",
            f"Breakdown of the {ai_grp.total_ai_images} AI-generated benchmark images:",
            "",
            "| Format | Image Count | Chai AI Recall | Sightengine AI Recall |",
            "| :--- | :--- | :--- | :--- |",
        ]
    )

    for fmt, cnt in sorted(ai_grp.format_distribution.items()):
        c_rec = ai_grp.format_recall_chai.get(fmt, 0.0)
        e_rec = ai_grp.format_recall_ext.get(fmt, 0.0)
        lines.append(
            f"| **{fmt}** | {cnt} | {c_rec * 100:.1f}% | {e_rec * 100:.1f}% |"
        )

    lines.extend(
        [
            "",
            "---",
            "",
            "## 13. Calibration Assessment",
            "",
            f"{base.tradeoff_summary}",
            "",
            "| Metric | M12 Baseline | Current (M14) | Absolute Change |",
            "| :--- | :--- | :--- | :--- |",
            f"| **AI True Positives (TP)** | {base.m12_tp} | {base.current_tp} | {base.delta_tp:+d} |",
            f"| **AI False Negatives (FN)** | {base.m12_fn} | {base.current_fn} | {base.delta_fn:+d} |",
            f"| **Real False Positives (FP)** | {base.m12_fp} | {base.current_fp} | {base.delta_fp:+d} |",
            f"| **AI Recall** | {base.m12_ai_recall * 100:.2f}% | {base.current_ai_recall * 100:.2f}% | {base.delta_recall * 100:+.2f} pp |",
            f"| **AI Precision** | {base.m12_ai_precision * 100:.2f}% | {base.current_ai_precision * 100:.2f}% | {base.delta_precision * 100:+.2f} pp |",
            f"| **AI F1 Score** | {base.m12_ai_f1:.4f} | {base.current_ai_f1:.4f} | {base.delta_f1:+.4f} |",
            f"| **Macro F1 Score** | {base.m12_macro_f1:.4f} | {base.current_macro_f1:.4f} | {base.delta_macro_f1:+.4f} |",
            f"| **High-Confidence Failures** | {base.m12_high_conf_failures} | {base.current_high_conf_failures} | {base.delta_high_conf_failures:+d} |",
            "",
            "---",
            "",
            "## 14. Statistical Limitations",
            "",
        ]
    )

    for lim in result.limitations:
        lines.append(f"- {lim}")

    lines.extend(
        [
            "",
            "---",
            "",
            "## 15. Final Calibration Decision",
            "",
            f"### Recommendation: {dec.recommended_option}",
            f"**{dec.title}**",
            "",
            "#### Rationale:",
        ]
    )

    for r_item in dec.rationale:
        lines.append(f"- {r_item}")

    lines.extend(
        [
            "",
            "#### Planned Action Plan:",
        ]
    )

    for step in dec.next_steps:
        lines.append(f"1. {step}")

    lines.extend(
        [
            "",
            "---",
            "",
            "## 16. Recommended Next Milestone",
            "",
            "- **Milestone 17**: *Targeted Fusion Calibration & False-Alarm Suppression*. Conduct an offline simulated calibration to dampen Lighting and Texture reliability weights while boosting Frequency weight, validating the trade-off curve across all 668 benchmark images.",
            "",
        ]
    )

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

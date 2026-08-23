"""CLI tool for running Milestone 17 isolated calibration experiments."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app.benchmark.calibration.evaluator import (
    BASELINE_M14,
    EXP_4_TARGETED_DETECTOR_REBALANCE,
    CalibrationComparisonReport,
    compare_calibration_runs,
)


def find_default_results_json() -> Path:
    """Locate benchmark latest.json across common relative paths."""
    candidates = [
        Path("reports/benchmark_m16/latest.json"),
        Path("reports/benchmark_m15/latest.json"),
        Path("reports/m14a_check/latest.json"),
        Path("../chai_benchmark/results/latest.json"),
        Path("../chai-benchmark/results/latest.json"),
        Path("chai_benchmark/results/latest.json"),
        Path("chai-benchmark/results/latest.json"),
        Path("c:/Users/VICTUS/Chai-AI/chai-benchmark/results/latest.json"),
    ]
    for c in candidates:
        if c.is_file():
            return c.resolve()
    return Path("reports/benchmark_m16/latest.json").resolve()


def generate_calibration_markdown_report(report: CalibrationComparisonReport) -> str:
    """Render a comprehensive Markdown report for Milestone 17."""
    base = report.baseline
    cand = report.candidate
    trans = report.transitions
    sub = report.ai_subgroup

    lines: list[str] = [
        "# Milestone 17 — Targeted Calibration Experiment Report",
        "",
        f"**Baseline Configuration**: `{base.name}` ({base.description})  ",
        f"**Candidate Configuration**: `{cand.name}` ({cand.description})  ",
        f"**Promotion Status**: `{report.promotion_status}`  ",
        "",
        "---",
        "",
        "## 1. Executive Summary",
        "",
        f"- **Evaluated Images**: {base.total_evaluated}",
        f"- **Accuracy**: {base.accuracy * 100:.2f}% -> **{cand.accuracy * 100:.2f}%** ({cand.delta_accuracy_vs_baseline * 100:+.2f} pp)",
        f"- **AI Precision**: {base.precision * 100:.2f}% -> **{cand.precision * 100:.2f}%** ({cand.delta_precision_vs_baseline * 100:+.2f} pp)",
        f"- **AI Recall**: {base.recall * 100:.2f}% -> **{cand.recall * 100:.2f}%** ({cand.delta_recall_vs_baseline * 100:+.2f} pp)",
        f"- **AI F1 Score**: {base.f1:.4f} -> **{cand.f1:.4f}** ({cand.delta_f1_vs_baseline:+.4f})",
        f"- **Macro F1 Score**: {base.macro_f1:.4f} -> **{cand.macro_f1:.4f}** ({cand.delta_macro_f1_vs_baseline:+.4f})",
        f"- **False Positives (Real -> AI)**: {base.fp} -> **{cand.fp}** ({cand.delta_fp_vs_baseline:+d} FP)",
        f"- **High-Confidence Failures**: {base.high_conf_failures} -> **{cand.high_conf_failures}**",
        f"- **Experiment Result**: **{report.decision_status}**",
        "",
        "---",
        "",
        "## 2. Overall Performance Comparison",
        "",
        "| Metric | Baseline (M14) | Candidate (EXP_4) | Delta |",
        "| :--- | :--- | :--- | :--- |",
        f"| **Overall Accuracy** | {base.accuracy * 100:.2f}% | {cand.accuracy * 100:.2f}% | {cand.delta_accuracy_vs_baseline * 100:+.2f} pp |",
        f"| **AI Precision** | {base.precision * 100:.2f}% | {cand.precision * 100:.2f}% | {cand.delta_precision_vs_baseline * 100:+.2f} pp |",
        f"| **AI Recall** | {base.recall * 100:.2f}% | {cand.recall * 100:.2f}% | {cand.delta_recall_vs_baseline * 100:+.2f} pp |",
        f"| **AI F1 Score** | {base.f1:.4f} | {cand.f1:.4f} | {cand.delta_f1_vs_baseline:+.4f} |",
        f"| **Macro F1 Score** | {base.macro_f1:.4f} | {cand.macro_f1:.4f} | {cand.delta_macro_f1_vs_baseline:+.4f} |",
        f"| **Weighted F1 Score** | {base.weighted_f1:.4f} | {cand.weighted_f1:.4f} | {cand.weighted_f1 - base.weighted_f1:+.4f} |",
        f"| **Real Recall (Specificity)** | {base.real_recall * 100:.2f}% | {cand.real_recall * 100:.2f}% | {(cand.real_recall - base.real_recall) * 100:+.2f} pp |",
        f"| **Real Precision** | {base.real_precision * 100:.2f}% | {cand.real_precision * 100:.2f}% | {(cand.real_precision - base.real_precision) * 100:+.2f} pp |",
        "",
        "---",
        "",
        "## 3. Confusion Matrix Comparison",
        "",
        "| Matrix Cell | Baseline (M14) | Candidate (EXP_4) | Delta |",
        "| :--- | :--- | :--- | :--- |",
        f"| **True Positives (TP)** | {base.tp} | {cand.tp} | {cand.delta_tp_vs_baseline:+d} |",
        f"| **True Negatives (TN)** | {base.tn} | {cand.tn} | {cand.tn - base.tn:+d} |",
        f"| **False Positives (FP)** | {base.fp} | {cand.fp} | {cand.delta_fp_vs_baseline:+d} |",
        f"| **False Negatives (FN)** | {base.fn} | {cand.fn} | {cand.delta_fn_vs_baseline:+d} |",
        "",
        "---",
        "",
        "## 4. Detector Contribution Rebalancing",
        "",
        "| Detector | Real Mean | AI Mean | Separation | Weight Before | Weight After | Share Before | Share After |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
    ]

    for det in report.detector_impacts:
        lines.append(
            f"| **{det.detector_name}** | {det.real_mean:.2f} | {det.ai_mean:.2f} | {det.separation:+.2f} | {det.weight_before:.2f} | {det.weight_after:.2f} | {det.share_before_pct:.1f}% | {det.share_after_pct:.1f}% |"
        )

    lines.extend(
        [
            "",
            "---",
            "",
            "## 5. Failure Transitions",
            "",
            f"- **Fixed False Positives** (Real -> AI in M14, now correctly Real): **{len(trans.fixed_false_positives)} images**",
            f"- **Newly Introduced False Positives** (Real -> Real in M14, now incorrectly AI): **{len(trans.newly_introduced_false_positives)} images**",
            f"- **Fixed False Negatives** (AI -> Real in M14, now correctly AI): **{len(trans.fixed_false_negatives)} images**",
            f"- **Newly Introduced False Negatives** (AI -> AI in M14, now incorrectly Real): **{len(trans.newly_introduced_false_negatives)} images**",
            "",
        ]
    )

    if trans.fixed_false_positives:
        lines.append("### Sample Fixed False Positives (First 5):")
        for item in trans.fixed_false_positives[:5]:
            lines.append(
                f"- `{item.image_id}` ({item.format}): `{item.file_path}` (Conf: {item.baseline_conf:.2f} -> {item.candidate_conf:.2f})"
            )
        lines.append("")

    lines.extend(
        [
            "---",
            "",
            "## 6. Confidence Safety Analysis",
            "",
            "| Confidence Metric | Baseline (M14) | Candidate (EXP_4) |",
            "| :--- | :--- | :--- |",
            f"| **Mean Confidence on Correct** | {base.mean_conf_correct:.4f} | {cand.mean_conf_correct:.4f} |",
            f"| **Mean Confidence on Incorrect** | {base.mean_conf_incorrect:.4f} | {cand.mean_conf_incorrect:.4f} |",
            f"| **High-Confidence Failures (>= 80%)** | {base.high_conf_failures} | {cand.high_conf_failures} |",
            f"| **Very-High-Confidence Failures (>= 90%)** | {base.very_high_conf_failures} | {cand.very_high_conf_failures} |",
            f"| **Low-Confidence Correct (<= 60%)** | {base.low_conf_correct} | {cand.low_conf_correct} |",
            "",
            "---",
            "",
            "## 7. Format Breakdown",
            "",
            "| Format | Count | Baseline Acc | Candidate Acc | Baseline Recall | Candidate Recall | Baseline FP | Candidate FP |",
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
        ]
    )

    for fmt, fc in sorted(report.format_breakdown.items()):
        lines.append(
            f"| **{fmt}** | {fc.image_count} | {fc.baseline_accuracy * 100:.1f}% | {fc.candidate_accuracy * 100:.1f}% | {fc.baseline_ai_recall * 100:.1f}% | {fc.candidate_ai_recall * 100:.1f}% | {fc.baseline_fp} | {fc.candidate_fp} |"
        )

    lines.extend(
        [
            "",
            "---",
            "",
            "## 8. AI-Generated Subgroup Analysis (52 Images)",
            "",
            f"- **Total AI Images**: {sub.total_ai_images}",
            f"- **Baseline Caught**: {sub.baseline_caught_count} / {sub.total_ai_images} ({sub.baseline_recall * 100:.2f}%)",
            f"- **Candidate Caught**: {sub.candidate_caught_count} / {sub.total_ai_images} ({sub.candidate_recall * 100:.2f}%)",
            f"- **Newly Caught AI Images**: {len(sub.newly_detected)}",
            f"- **Newly Missed AI Images**: {len(sub.newly_missed)}",
            "",
            "| Format | AI Images | Baseline Recall | Candidate Recall |",
            "| :--- | :--- | :--- | :--- |",
        ]
    )

    for fmt, d in sorted(sub.by_format.items()):
        lines.append(
            f"| **{fmt}** | {d['count']} | {d['baseline_recall'] * 100:.1f}% ({d['baseline_caught']}/{d['count']}) | {d['candidate_recall'] * 100:.1f}% ({d['candidate_caught']}/{d['count']}) |"
        )

    lines.extend(
        [
            "",
            "---",
            "",
            "## 9. Decision & Production Status",
            "",
            f"### Experiment Result: **{report.decision_status}**",
            "",
            "#### Rationale:",
        ]
    )

    for rat in report.decision_rationale:
        lines.append(f"- {rat}")

    lines.extend(
        [
            "",
            f"> [!IMPORTANT]",
            f"> **{report.promotion_status}**",
            "",
        ]
    )

    return "\n".join(lines)


def run_cli() -> None:
    """Run the Milestone 17 isolated calibration experiment CLI."""
    parser = argparse.ArgumentParser(
        description="Chai AI Milestone 17 Targeted Calibration Experiment CLI"
    )
    parser.add_argument(
        "--results-json",
        type=str,
        default=None,
        help="Path to benchmark results latest.json file",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="reports/calibration_m17",
        help="Output directory for calibration reports (default: reports/calibration_m17)",
    )

    args = parser.parse_args()

    results_path = (
        Path(args.results_json).resolve()
        if args.results_json
        else find_default_results_json()
    )
    if not results_path.is_file():
        print(
            f"Error: Benchmark results file not found at {results_path}",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"Loading recorded benchmark results from: {results_path}")
    raw_data = json.loads(results_path.read_text(encoding="utf-8"))

    # Execute isolated comparative experiment
    report = compare_calibration_runs(
        benchmark_data=raw_data,
        baseline_candidate=BASELINE_M14,
        test_candidate=EXP_4_TARGETED_DETECTOR_REBALANCE,
    )

    # Save reports
    out_dir = Path(args.output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    latest_md = out_dir / "latest.md"
    latest_json = out_dir / "latest.json"

    md_content = generate_calibration_markdown_report(report)
    latest_md.write_text(md_content, encoding="utf-8")
    latest_json.write_text(report.model_dump_json(indent=2), encoding="utf-8")

    # Terminal output
    base = report.baseline
    cand = report.candidate
    trans = report.transitions

    print("\n" + "=" * 80)
    print("MILESTONE 17 — TARGETED CALIBRATION EXPERIMENT (EXP_4 vs BASELINE_M14)")
    print("=" * 80)
    print(f"Promotion Status: {report.promotion_status}")
    print("-" * 80)
    print(
        f"{'Metric':<25} {'Baseline (M14)':<18} {'Candidate (EXP_4)':<18} {'Delta'}"
    )
    print("-" * 80)
    print(
        f"{'Overall Accuracy':<25} {base.accuracy * 100:>6.2f}%            {cand.accuracy * 100:>6.2f}%            {cand.delta_accuracy_vs_baseline * 100:>+6.2f} pp"
    )
    print(
        f"{'AI Precision':<25} {base.precision * 100:>6.2f}%            {cand.precision * 100:>6.2f}%            {cand.delta_precision_vs_baseline * 100:>+6.2f} pp"
    )
    print(
        f"{'AI Recall':<25} {base.recall * 100:>6.2f}%            {cand.recall * 100:>6.2f}%            {cand.delta_recall_vs_baseline * 100:>+6.2f} pp"
    )
    print(
        f"{'AI F1 Score':<25} {base.f1:>6.4f}             {cand.f1:>6.4f}             {cand.delta_f1_vs_baseline:>+6.4f}"
    )
    print(
        f"{'Macro F1 Score':<25} {base.macro_f1:>6.4f}             {cand.macro_f1:>6.4f}             {cand.delta_macro_f1_vs_baseline:>+6.4f}"
    )
    print(
        f"{'False Positives (Real->AI)':<25} {base.fp:>5d}               {cand.fp:>5d}               {cand.delta_fp_vs_baseline:>+5d}"
    )
    print(
        f"{'False Negatives (AI->Real)':<25} {base.fn:>5d}               {cand.fn:>5d}               {cand.delta_fn_vs_baseline:>+5d}"
    )
    print(
        f"{'True Positives (AI Caught)':<25} {base.tp:>5d}               {cand.tp:>5d}               {cand.delta_tp_vs_baseline:>+5d}"
    )
    print(
        f"{'High-Conf Failures (>=80%)':<25} {base.high_conf_failures:>5d}               {cand.high_conf_failures:>5d}               {cand.high_conf_failures - base.high_conf_failures:>+5d}"
    )
    print("-" * 80)
    print(
        f"Failure Transitions: Fixed FP={len(trans.fixed_false_positives)}, New FP={len(trans.newly_introduced_false_positives)}, Fixed FN={len(trans.fixed_false_negatives)}, New FN={len(trans.newly_introduced_false_negatives)}"
    )
    print(f"Final Decision: {report.decision_status}")
    print("=" * 80)
    print(f"Report Markdown: {latest_md}")
    print(f"Report JSON:     {latest_json}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    run_cli()

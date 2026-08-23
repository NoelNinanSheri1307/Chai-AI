"""Production validation and promotion decision engine for Milestone 18."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.benchmark.models import (
    BenchmarkRunResult,
    GroundTruthLabel,
)


class TransitionDetail(BaseModel):
    """Record of an individual image transitioning classification state."""

    model_config = ConfigDict(extra="forbid")

    image_id: str
    file_path: str
    format: str
    ground_truth: str
    baseline_pred: str
    baseline_conf: float
    candidate_pred: str
    candidate_conf: float


class ValidationTransitions(BaseModel):
    """Failure transition summary between baseline and candidate fresh runs."""

    model_config = ConfigDict(extra="forbid")

    fixed_false_positives: list[TransitionDetail] = Field(default_factory=list)
    newly_introduced_false_positives: list[TransitionDetail] = Field(
        default_factory=list
    )
    fixed_false_negatives: list[TransitionDetail] = Field(default_factory=list)
    newly_introduced_false_negatives: list[TransitionDetail] = Field(
        default_factory=list
    )


class PromotionCheck(BaseModel):
    """An individual acceptance criteria check."""

    model_config = ConfigDict(extra="forbid")

    name: str
    description: str
    passed: bool
    baseline_val: Any
    candidate_val: Any
    detail: str


class PromotionValidationReport(BaseModel):
    """Complete aggregated validation report for Milestone 18 promotion decision."""

    model_config = ConfigDict(extra="forbid")

    baseline_run_id: str
    candidate_run_id: str
    passed_all_criteria: bool
    promotion_verdict: str  # "APPROVED_FOR_PROMOTION", "REJECTED_RETAIN_M14"
    criteria_checks: list[PromotionCheck] = Field(default_factory=list)

    # Core metrics comparison
    baseline_accuracy: float
    candidate_accuracy: float
    baseline_precision: float
    candidate_precision: float
    baseline_recall: float
    candidate_recall: float
    baseline_f1: float
    candidate_f1: float
    baseline_macro_f1: float
    candidate_macro_f1: float
    baseline_fp: int
    candidate_fp: int
    baseline_fn: int
    candidate_fn: int
    baseline_tp: int
    candidate_tp: int
    baseline_tn: int
    candidate_tn: int

    # Confidence safety
    baseline_hcf: int
    candidate_hcf: int
    baseline_mean_conf_correct: float
    candidate_mean_conf_correct: float
    baseline_mean_conf_incorrect: float
    candidate_mean_conf_incorrect: float

    # Detailed breakdowns
    transitions: ValidationTransitions
    format_comparison: dict[str, dict[str, Any]] = Field(default_factory=dict)
    ai_subgroup_comparison: dict[str, dict[str, Any]] = Field(
        default_factory=dict
    )
    recommendation_summary: str


def _safe_div(num: float, den: float) -> float:
    return round(num / den, 4) if den > 0 else 0.0


def validate_production_promotion(
    baseline_run: BenchmarkRunResult | dict[str, Any] | Path,
    candidate_run: BenchmarkRunResult | dict[str, Any] | Path,
) -> PromotionValidationReport:
    """Validate a fresh production benchmark run of EXP_4 against Baseline M14."""
    if isinstance(baseline_run, Path):
        baseline_run = BenchmarkRunResult.model_validate(
            json.loads(baseline_run.read_text(encoding="utf-8"))
        )
    elif isinstance(baseline_run, dict):
        baseline_run = BenchmarkRunResult.model_validate(baseline_run)

    if isinstance(candidate_run, Path):
        candidate_run = BenchmarkRunResult.model_validate(
            json.loads(candidate_run.read_text(encoding="utf-8"))
        )
    elif isinstance(candidate_run, dict):
        candidate_run = BenchmarkRunResult.model_validate(candidate_run)

    # Index results by image_id
    base_map = {r.image_id: r for r in baseline_run.results}
    cand_map = {r.image_id: r for r in candidate_run.results}

    fixed_fp: list[TransitionDetail] = []
    new_fp: list[TransitionDetail] = []
    fixed_fn: list[TransitionDetail] = []
    new_fn: list[TransitionDetail] = []

    formats = ["JPEG", "PNG", "WEBP", "AVIF"]
    fmt_data: dict[str, dict[str, Any]] = {
        f: {
            "count": 0,
            "b_tp": 0,
            "b_tn": 0,
            "b_fp": 0,
            "b_fn": 0,
            "c_tp": 0,
            "c_tn": 0,
            "c_fp": 0,
            "c_fn": 0,
            "ai_count": 0,
        }
        for f in formats
    }

    ai_sub_data: dict[str, dict[str, Any]] = {}

    for img_id, b_res in base_map.items():
        c_res = cand_map.get(img_id)
        if not c_res:
            continue

        gt_is_ai = b_res.ground_truth == GroundTruthLabel.AI_GENERATED
        gt_val = "ai_generated" if gt_is_ai else "original"

        ext_str = (
            b_res.file_path.split(".")[-1].upper()
            if "." in b_res.file_path
            else "UNKNOWN"
        )
        fmt = (
            "JPEG"
            if ext_str in {"JPG", "JPEG"}
            else ext_str
            if ext_str in formats
            else "OTHER"
        )
        if fmt not in fmt_data:
            fmt_data[fmt] = {
                "count": 0,
                "b_tp": 0,
                "b_tn": 0,
                "b_fp": 0,
                "b_fn": 0,
                "c_tp": 0,
                "c_tn": 0,
                "c_fp": 0,
                "c_fn": 0,
                "ai_count": 0,
            }

        fmt_data[fmt]["count"] += 1
        if gt_is_ai:
            fmt_data[fmt]["ai_count"] += 1

        b_pred = b_res.predicted_class
        c_pred = c_res.predicted_class

        if gt_is_ai:
            if b_pred == "ai_generated":
                fmt_data[fmt]["b_tp"] += 1
            else:
                fmt_data[fmt]["b_fn"] += 1
            if c_pred == "ai_generated":
                fmt_data[fmt]["c_tp"] += 1
            else:
                fmt_data[fmt]["c_fn"] += 1
        else:
            if b_pred == "original":
                fmt_data[fmt]["b_tn"] += 1
            else:
                fmt_data[fmt]["b_fp"] += 1
            if c_pred == "original":
                fmt_data[fmt]["c_tn"] += 1
            else:
                fmt_data[fmt]["c_fp"] += 1

        detail = TransitionDetail(
            image_id=img_id,
            file_path=b_res.file_path,
            format=fmt,
            ground_truth=gt_val,
            baseline_pred=b_pred,
            baseline_conf=b_res.confidence,
            candidate_pred=c_pred,
            candidate_conf=c_res.confidence,
        )

        if not gt_is_ai:
            if b_pred == "ai_generated" and c_pred == "original":
                fixed_fp.append(detail)
            elif b_pred == "original" and c_pred == "ai_generated":
                new_fp.append(detail)
        else:
            if b_pred == "original" and c_pred == "ai_generated":
                fixed_fn.append(detail)
            elif b_pred == "ai_generated" and c_pred == "original":
                new_fn.append(detail)

            ai_sub_data[img_id] = {
                "format": fmt,
                "file_path": b_res.file_path,
                "baseline_caught": b_pred == "ai_generated",
                "candidate_caught": c_pred == "ai_generated",
                "baseline_conf": b_res.confidence,
                "candidate_conf": c_res.confidence,
            }

    # Format metrics
    fmt_report: dict[str, dict[str, Any]] = {}
    for f, d_f in fmt_data.items():
        cnt = d_f["count"]
        if cnt == 0:
            continue
        fmt_report[f] = {
            "image_count": cnt,
            "baseline_accuracy": _safe_div(d_f["b_tp"] + d_f["b_tn"], cnt),
            "candidate_accuracy": _safe_div(d_f["c_tp"] + d_f["c_tn"], cnt),
            "baseline_ai_recall": _safe_div(
                d_f["b_tp"], d_f["b_tp"] + d_f["b_fn"]
            ),
            "candidate_ai_recall": _safe_div(
                d_f["c_tp"], d_f["c_tp"] + d_f["c_fn"]
            ),
            "baseline_fp": d_f["b_fp"],
            "candidate_fp": d_f["c_fp"],
        }

    # Acceptance Criteria Verification
    checks: list[PromotionCheck] = []

    # Criterion 1: AI Recall Non-Regression
    rec_pass = candidate_run.recall >= (baseline_run.recall - 0.001)
    checks.append(
        PromotionCheck(
            name="AI Recall Non-Regression",
            description="Candidate AI recall must not regress relative to Baseline M14.",
            passed=rec_pass,
            baseline_val=f"{baseline_run.recall * 100:.2f}%",
            candidate_val=f"{candidate_run.recall * 100:.2f}%",
            detail=f"Candidate recall is {candidate_run.recall * 100:.2f}% vs baseline {baseline_run.recall * 100:.2f}%.",
        )
    )

    # Criterion 2: Meaningful False Positive Reduction
    fp_pass = candidate_run.fp < baseline_run.fp and (
        (baseline_run.fp - candidate_run.fp) >= 30
    )
    checks.append(
        PromotionCheck(
            name="Real False Positive Reduction",
            description="Candidate must achieve substantial FP reduction on authentic images (>=30 fewer FPs).",
            passed=fp_pass,
            baseline_val=baseline_run.fp,
            candidate_val=candidate_run.fp,
            detail=f"Candidate false positives dropped from {baseline_run.fp} to {candidate_run.fp} (delta: {candidate_run.fp - baseline_run.fp}).",
        )
    )

    # Criterion 3: False Negative Containment
    fn_pass = candidate_run.fn <= (baseline_run.fn + 2)
    checks.append(
        PromotionCheck(
            name="False Negative Containment",
            description="Candidate must not materially increase false negatives on AI images.",
            passed=fn_pass,
            baseline_val=baseline_run.fn,
            candidate_val=candidate_run.fn,
            detail=f"Candidate false negatives: {candidate_run.fn} vs baseline {baseline_run.fn}.",
        )
    )

    # Criterion 4: High-Confidence Failure Safety
    b_hcf = (
        baseline_run.confidence_analysis.high_confidence_failures_count
        if baseline_run.confidence_analysis
        else 0
    )
    c_hcf = (
        candidate_run.confidence_analysis.high_confidence_failures_count
        if candidate_run.confidence_analysis
        else 0
    )
    hcf_pass = c_hcf <= b_hcf
    checks.append(
        PromotionCheck(
            name="High-Confidence Failure Safety",
            description="Candidate must not introduce new high-confidence failures (>=80%).",
            passed=hcf_pass,
            baseline_val=b_hcf,
            candidate_val=c_hcf,
            detail=f"Candidate high-confidence failures: {c_hcf} vs baseline {b_hcf}.",
        )
    )

    # Criterion 5: Zero Pipeline Runtime Failures
    rt_pass = candidate_run.failed_analyses == 0
    checks.append(
        PromotionCheck(
            name="Pipeline Runtime Reliability",
            description="Candidate must execute across all benchmark images with 0 unhandled exceptions.",
            passed=rt_pass,
            baseline_val=baseline_run.failed_analyses,
            candidate_val=candidate_run.failed_analyses,
            detail=f"Candidate failed analyses count: {candidate_run.failed_analyses}.",
        )
    )

    # Criterion 6: Directional Consistency with Simulation
    sim_pass = (
        candidate_run.accuracy > baseline_run.accuracy
        and candidate_run.precision > baseline_run.precision
    )
    checks.append(
        PromotionCheck(
            name="Directional Consistency with Simulation",
            description="Fresh production run must confirm accuracy and precision gains observed in M17 simulation.",
            passed=sim_pass,
            baseline_val=f"Acc: {baseline_run.accuracy * 100:.2f}%, Prec: {baseline_run.precision * 100:.2f}%",
            candidate_val=f"Acc: {candidate_run.accuracy * 100:.2f}%, Prec: {candidate_run.precision * 100:.2f}%",
            detail=f"Accuracy improved by {(candidate_run.accuracy - baseline_run.accuracy) * 100:+.2f} pp, Precision by {(candidate_run.precision - baseline_run.precision) * 100:+.2f} pp.",
        )
    )

    all_passed = all(c.passed for c in checks)
    verdict = (
        "APPROVED_FOR_PROMOTION" if all_passed else "REJECTED_RETAIN_M14"
    )

    summary = (
        "Candidate EXP_4 meets all strict production promotion criteria. False positives on Real images "
        f"reduced from {baseline_run.fp} to {candidate_run.fp} (-{baseline_run.fp - candidate_run.fp}), AI recall was preserved "
        f"at {candidate_run.recall * 100:.2f}%, AI F1 increased from {baseline_run.f1:.4f} to {candidate_run.f1:.4f}, and high-confidence "
        f"failures remained at {c_hcf}."
        if all_passed
        else "Candidate EXP_4 failed one or more required acceptance criteria. Production configuration remains at Baseline M14."
    )

    return PromotionValidationReport(
        baseline_run_id=baseline_run.run_id,
        candidate_run_id=candidate_run.run_id,
        passed_all_criteria=all_passed,
        promotion_verdict=verdict,
        criteria_checks=checks,
        baseline_accuracy=baseline_run.accuracy,
        candidate_accuracy=candidate_run.accuracy,
        baseline_precision=baseline_run.precision,
        candidate_precision=candidate_run.precision,
        baseline_recall=baseline_run.recall,
        candidate_recall=candidate_run.recall,
        baseline_f1=baseline_run.f1,
        candidate_f1=candidate_run.f1,
        baseline_macro_f1=baseline_run.macro_f1,
        candidate_macro_f1=candidate_run.macro_f1,
        baseline_fp=baseline_run.fp,
        candidate_fp=candidate_run.fp,
        baseline_fn=baseline_run.fn,
        candidate_fn=candidate_run.fn,
        baseline_tp=baseline_run.tp,
        candidate_tp=candidate_run.tp,
        baseline_tn=baseline_run.tn,
        candidate_tn=candidate_run.tn,
        baseline_hcf=b_hcf,
        candidate_hcf=c_hcf,
        baseline_mean_conf_correct=baseline_run.confidence_analysis.mean_confidence_correct
        if baseline_run.confidence_analysis
        else 0.0,
        candidate_mean_conf_correct=candidate_run.confidence_analysis.mean_confidence_correct
        if candidate_run.confidence_analysis
        else 0.0,
        baseline_mean_conf_incorrect=baseline_run.confidence_analysis.mean_confidence_incorrect
        if baseline_run.confidence_analysis
        else 0.0,
        candidate_mean_conf_incorrect=candidate_run.confidence_analysis.mean_confidence_incorrect
        if candidate_run.confidence_analysis
        else 0.0,
        transitions=ValidationTransitions(
            fixed_false_positives=fixed_fp,
            newly_introduced_false_positives=new_fp,
            fixed_false_negatives=fixed_fn,
            newly_introduced_false_negatives=new_fn,
        ),
        format_comparison=fmt_report,
        ai_subgroup_comparison=ai_sub_data,
        recommendation_summary=summary,
    )


def generate_validation_markdown_report(
    report: PromotionValidationReport,
) -> str:
    """Render a comprehensive Markdown validation and promotion decision document."""
    lines: list[str] = [
        "# Milestone 18 — Production Validation & Promotion Decision Report",
        "",
        f"**Baseline Run ID**: `{report.baseline_run_id}`  ",
        f"**Candidate Run ID**: `{report.candidate_run_id}`  ",
        f"**Final Promotion Verdict**: **`{report.promotion_verdict}`**  ",
        "",
        "---",
        "",
        "## 1. Promotion Criteria Verification",
        "",
        "| Criteria Check | Status | Baseline | Candidate | Detail |",
        "| :--- | :--- | :--- | :--- | :--- |",
    ]

    for chk in report.criteria_checks:
        status_badge = "PASS [OK]" if chk.passed else "FAIL [X]"
        lines.append(
            f"| **{chk.name}** | `{status_badge}` | {chk.baseline_val} | {chk.candidate_val} | {chk.detail} |"
        )

    lines.extend(
        [
            "",
            "---",
            "",
            "## 2. Production Performance Comparison",
            "",
            "| Metric | Baseline (M14) | Candidate (EXP_4) | Delta |",
            "| :--- | :--- | :--- | :--- |",
            f"| **Overall Accuracy** | {report.baseline_accuracy * 100:.2f}% | {report.candidate_accuracy * 100:.2f}% | {(report.candidate_accuracy - report.baseline_accuracy) * 100:+.2f} pp |",
            f"| **AI Precision** | {report.baseline_precision * 100:.2f}% | {report.candidate_precision * 100:.2f}% | {(report.candidate_precision - report.baseline_precision) * 100:+.2f} pp |",
            f"| **AI Recall** | {report.baseline_recall * 100:.2f}% | {report.candidate_recall * 100:.2f}% | {(report.candidate_recall - report.baseline_recall) * 100:+.2f} pp |",
            f"| **AI F1 Score** | {report.baseline_f1:.4f} | {report.candidate_f1:.4f} | {report.candidate_f1 - report.baseline_f1:+.4f} |",
            f"| **Macro F1 Score** | {report.baseline_macro_f1:.4f} | {report.candidate_macro_f1:.4f} | {report.candidate_macro_f1 - report.baseline_macro_f1:+.4f} |",
            f"| **False Positives (Real -> AI)** | {report.baseline_fp} | {report.candidate_fp} | {report.candidate_fp - report.baseline_fp:+d} |",
            f"| **False Negatives (AI -> Real)** | {report.baseline_fn} | {report.candidate_fn} | {report.candidate_fn - report.baseline_fn:+d} |",
            f"| **True Positives (AI Caught)** | {report.baseline_tp} | {report.candidate_tp} | {report.candidate_tp - report.baseline_tp:+d} |",
            f"| **High-Confidence Failures (>=80%)** | {report.baseline_hcf} | {report.candidate_hcf} | {report.candidate_hcf - report.baseline_hcf:+d} |",
            "",
            "---",
            "",
            "## 3. Failure Transitions",
            "",
            f"- **Fixed False Positives**: {len(report.transitions.fixed_false_positives)} images (Real photos previously misclassified as AI)",
            f"- **Newly Introduced False Positives**: {len(report.transitions.newly_introduced_false_positives)} images",
            f"- **Fixed False Negatives**: {len(report.transitions.fixed_false_negatives)} images",
            f"- **Newly Introduced False Negatives**: {len(report.transitions.newly_introduced_false_negatives)} images",
            "",
            "---",
            "",
            "## 4. Per-Format Breakdown",
            "",
            "| Format | Count | Baseline Acc | Candidate Acc | Baseline Recall | Candidate Recall | Baseline FP | Candidate FP |",
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
        ]
    )

    for fmt, fd in sorted(report.format_comparison.items()):
        lines.append(
            f"| **{fmt}** | {fd['image_count']} | {fd['baseline_accuracy'] * 100:.1f}% | {fd['candidate_accuracy'] * 100:.1f}% | {fd['baseline_ai_recall'] * 100:.1f}% | {fd['candidate_ai_recall'] * 100:.1f}% | {fd['baseline_fp']} | {fd['candidate_fp']} |"
        )

    lines.extend(
        [
            "",
            "---",
            "",
            "## 5. Promotion Verdict & Recommendation",
            "",
            f"**Verdict**: `{report.promotion_verdict}`",
            "",
            f"{report.recommendation_summary}",
            "",
        ]
    )

    return "\n".join(lines)


def find_default_baseline_json() -> Path | None:
    """Find the baseline M14 benchmark result across common locations."""
    candidates = [
        Path("reports/m14a_check/latest.json"),
        Path("reports/benchmark_m15/latest.json"),
        Path("reports/benchmark_m16/latest.json"),
        Path("reports/benchmark_m14a/latest.json"),
        Path("chai_benchmark/results/latest.json"),
        Path("../chai_benchmark/results/latest.json"),
        Path("chai-benchmark/results/latest.json"),
        Path("../chai-benchmark/results/latest.json"),
    ]
    for c in candidates:
        if c.is_file():
            return c.resolve()
    return None


def run_validator_cli() -> None:
    """CLI tool for comparing fresh benchmark runs and deciding promotion."""
    parser = argparse.ArgumentParser(
        description="Chai AI Milestone 18 Production Promotion Validator CLI"
    )
    parser.add_argument(
        "--baseline",
        type=str,
        default=None,
        help="Path to Baseline M14 benchmark JSON result (defaults to auto-detected baseline)",
    )
    parser.add_argument(
        "--candidate",
        type=str,
        default="reports/benchmark_m18_exp4/latest.json",
        help="Path to Candidate EXP_4 benchmark JSON result (default: reports/benchmark_m18_exp4/latest.json)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="reports/validation_m18",
        help="Output directory for validation reports (default: reports/validation_m18)",
    )

    args = parser.parse_args()

    if args.baseline:
        base_p = Path(args.baseline).resolve()
        if not base_p.is_file():
            # Fall back to default if specified path is missing
            fallback_p = find_default_baseline_json()
            if fallback_p and fallback_p.is_file():
                print(f"Warning: Baseline '{base_p}' not found. Using auto-discovered baseline: {fallback_p}")
                base_p = fallback_p
            else:
                print(f"Error: Baseline file not found at {base_p}", file=sys.stderr)
                sys.exit(1)
    else:
        fallback_p = find_default_baseline_json()
        if fallback_p and fallback_p.is_file():
            base_p = fallback_p
        else:
            print("Error: No baseline benchmark result found. Please specify --baseline <path>.", file=sys.stderr)
            sys.exit(1)

    cand_p = Path(args.candidate).resolve()
    if not cand_p.is_file():
        print(f"Error: Candidate file not found at {cand_p}", file=sys.stderr)
        sys.exit(1)


    report = validate_production_promotion(base_p, cand_p)

    out_dir = Path(args.output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    latest_md = out_dir / "promotion_report.md"
    latest_json = out_dir / "promotion_report.json"

    md_content = generate_validation_markdown_report(report)
    latest_md.write_text(md_content, encoding="utf-8")
    latest_json.write_text(report.model_dump_json(indent=2), encoding="utf-8")

    print("\n" + "=" * 80)
    print("MILESTONE 18 — PRODUCTION PROMOTION VALIDATION REPORT")
    print("=" * 80)
    print(f"Promotion Verdict: {report.promotion_verdict}")
    print(
        f"All Criteria Passed: {'YES' if report.passed_all_criteria else 'NO'}"
    )
    print("-" * 80)
    for chk in report.criteria_checks:
        status_str = "PASS" if chk.passed else "FAIL"
        print(f"  [{status_str}] {chk.name}: {chk.detail}")
    print("-" * 80)
    print(
        f"Accuracy:  {report.baseline_accuracy * 100:.2f}% -> {report.candidate_accuracy * 100:.2f}% ({(report.candidate_accuracy - report.baseline_accuracy) * 100:+.2f} pp)"
    )
    print(
        f"AI Precision: {report.baseline_precision * 100:.2f}% -> {report.candidate_precision * 100:.2f}% ({(report.candidate_precision - report.baseline_precision) * 100:+.2f} pp)"
    )
    print(
        f"AI Recall: {report.baseline_recall * 100:.2f}% -> {report.candidate_recall * 100:.2f}%"
    )
    print(
        f"Real FP:   {report.baseline_fp} -> {report.candidate_fp} ({report.candidate_fp - report.baseline_fp:+d})"
    )
    print("=" * 80)
    print(f"Validation Report Markdown: {latest_md}")
    print(f"Validation Report JSON:     {latest_json}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    run_validator_cli()

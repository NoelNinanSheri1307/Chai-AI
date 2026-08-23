"""CLI tool for running Milestone 13 forensic investigation and calibration experiments."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app.benchmark.calibration.evaluator import (
    BASELINE_M12,
    CalibrationCandidate,
    evaluate_calibration,
)
from app.benchmark.calibration.investigation import run_forensic_investigation


def find_default_results_json() -> Path:
    """Locate latest.json across common relative paths."""
    candidates = [
        Path("../chai_benchmark/results/latest.json"),
        Path("../chai-benchmark/results/latest.json"),
        Path("chai_benchmark/results/latest.json"),
        Path("chai-benchmark/results/latest.json"),
        Path("../../chai-benchmark/results/latest.json"),
        Path("c:/Users/VICTUS/Chai-AI/chai-benchmark/results/latest.json"),
    ]
    for c in candidates:
        if c.is_file():
            return c.resolve()
    return Path("../chai-benchmark/results/latest.json").resolve()


def run_cli() -> None:
    """Run the forensic investigation and calibration simulation suite."""
    parser = argparse.ArgumentParser(
        description="Chai AI Milestone 13 Forensic Investigation & Calibration CLI"
    )
    parser.add_argument(
        "--results-json",
        type=str,
        default=None,
        help="Path to benchmark results latest.json file",
    )
    parser.add_argument(
        "--output-report",
        type=str,
        default=None,
        help="Optional path to output markdown investigation report",
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

    print(f"Loading benchmark dataset results from: {results_path}")
    raw_data = json.loads(results_path.read_text(encoding="utf-8"))

    # 1. Run Forensic Investigation
    inv_report = run_forensic_investigation(raw_data)

    print("\n" + "=" * 80)
    print(f"MILESTONE 13 — FORENSIC INVESTIGATION REPORT ({inv_report.run_id})")
    print("=" * 80)
    print(
        f"Total Evaluated: {inv_report.total_images} (Real: {inv_report.real_count}, AI Generated: {inv_report.ai_count})"
    )
    print(
        f"Baseline Accuracy: {inv_report.accuracy * 100:.2f}% | AI F1: {inv_report.f1:.4f} | Macro F1: {inv_report.macro_f1:.4f}"
    )
    print(
        f"Confusion Matrix: TN={inv_report.tn}, FP={inv_report.fp}, FN={inv_report.fn}, TP={inv_report.tp}"
    )
    print("-" * 80)

    print("\n1. DETECTOR USEFULNESS RANKING & STATISTICAL BREAKDOWN:")
    print(
        f"{'Rank':<5} {'Detector':<13} {'Real Mean':<11} {'AI Mean':<10} {'Sep':<6} {'Dir':<5} {'Overlap':<8} {'Tier'}"
    )
    print("-" * 80)
    for s in inv_report.usefulness_ranking:
        dir_flag = "OK" if s.direction_correct else "REV"
        print(
            f"{s.usefulness_rank:<5} {s.detector_name:<13} "
            f"{s.real_mean:.2f}±{s.real_std:.2f}   "
            f"{s.ai_mean:.2f}±{s.ai_std:.2f}  "
            f"{s.separation_margin:.2f}   "
            f"{dir_flag:<5} {s.distribution_overlap:<8.2f} {s.usefulness_tier}"
        )

    print("\n2. FORMAT-SPECIFIC PERFORMANCE BREAKDOWN:")
    print(
        f"{'Format':<8} {'Total':<7} {'Real':<6} {'AI':<5} {'Acc':<8} {'Fallback Rate':<15} {'Notes'}"
    )
    print("-" * 80)
    for fmt, fa in inv_report.format_analysis.items():
        note_str = fa.notes[0] if fa.notes else "Normal processing"
        print(
            f"{fmt:<8} {fa.total_count:<7} {fa.real_count:<6} {fa.ai_count:<5} "
            f"{fa.accuracy * 100:>5.1f}%  {fa.fallback_rate * 100:>6.1f}%          {note_str[:35]}"
        )

    print("\n3. IDENTIFIED ROOT CAUSES & IMPLEMENTATION BUGS:")
    for b in inv_report.implementation_bugs_identified:
        print(f"  [{b['id']}] {b['component']}: {b['issue']}")
        print(f"         Impact: {b['impact']}")

    # 2. Run Isolated Calibration Simulations
    print("\n" + "=" * 80)
    print("ISOLATED CALIBRATION EXPERIMENTS (COMPARED AGAINST BASELINE_M12)")
    print("=" * 80)

    # Candidate 1: Baseline
    res_base = evaluate_calibration(BASELINE_M12, raw_data)

    # Candidate 2: Wider Gaussian Resolution (sigma=0.35)
    cand_wider = CalibrationCandidate(
        name="EXP_1_WIDER_GAUSSIAN",
        description="Widen Gaussian resolution from 0.15 to 0.35 (removes 85x bias on fallback scores)",
        classifier_resolution=0.35,
        classifier_contribution_matrix=BASELINE_M12.classifier_contribution_matrix,
        detector_reliability=BASELINE_M12.detector_reliability,
        disabled_detectors=[],
    )
    res_wider = evaluate_calibration(cand_wider, raw_data, baseline_result=res_base)

    # Candidate 3: Dampen Lighting & Inverted False Alarms
    cand_dampen = CalibrationCandidate(
        name="EXP_2_DAMPEN_LIGHTING",
        description="Reduce lighting & texture weights to prevent false positives on natural photos",
        classifier_resolution=0.35,
        classifier_contribution_matrix={
            "metadata": {"original": 0.90, "ai_generated": 0.20},
            "frequency": {"original": 0.10, "ai_generated": 1.00},
            "ela": {"original": 0.10, "ai_generated": 0.10},
            "noise": {"original": 0.10, "ai_generated": 0.10},
            "compression": {"original": 0.40, "ai_generated": 0.40},
            "texture": {"original": 0.30, "ai_generated": 0.40},
            "lighting": {"original": 0.30, "ai_generated": 0.20},
        },
        detector_reliability={
            "metadata": 0.15,
            "frequency": 0.40,
            "ela": 0.05,
            "noise": 0.05,
            "compression": 0.10,
            "texture": 0.15,
            "lighting": 0.10,
        },
        disabled_detectors=[],
    )
    res_dampen = evaluate_calibration(cand_dampen, raw_data, baseline_result=res_base)

    # Candidate 4: Frequency Promoted & Zero-Separation Detectors Dampened
    cand_promoted = CalibrationCandidate(
        name="EXP_3_FREQUENCY_PROMOTED",
        description="Prioritize FFT energy concentration (highest true separator) & prune uninformative ELA/Noise",
        classifier_resolution=0.30,
        classifier_contribution_matrix={
            "metadata": {"original": 0.85, "ai_generated": 0.15},
            "frequency": {"original": 0.05, "ai_generated": 1.00},
            "ela": {"original": 0.10, "ai_generated": 0.10},
            "noise": {"original": 0.10, "ai_generated": 0.10},
            "compression": {"original": 0.50, "ai_generated": 0.20},
            "texture": {"original": 0.30, "ai_generated": 0.40},
            "lighting": {"original": 0.40, "ai_generated": 0.20},
        },
        detector_reliability={
            "metadata": 0.15,
            "frequency": 0.50,
            "ela": 0.02,
            "noise": 0.02,
            "compression": 0.10,
            "texture": 0.15,
            "lighting": 0.06,
        },
        disabled_detectors=["ela", "noise"],
    )
    res_promoted = evaluate_calibration(
        cand_promoted, raw_data, baseline_result=res_base
    )

    candidates_evaluated = [res_base, res_wider, res_dampen, res_promoted]

    print(
        f"{'Configuration':<26} {'Accuracy':<10} {'AI F1':<8} {'Macro F1':<10} {'FP':<5} {'FN':<5} {'TP':<5} {'Delta Macro F1'}"
    )
    print("-" * 80)
    for c in candidates_evaluated:
        delta_str = (
            f"{c.delta_macro_f1_vs_baseline:+.4f}"
            if c.name != "BASELINE_M12"
            else "BASELINE"
        )
        print(
            f"{c.name:<26} {c.accuracy * 100:>6.2f}%   {c.f1:>6.4f}  {c.macro_f1:>7.4f}    "
            f"{c.fp:<5} {c.fn:<5} {c.tp:<5} {delta_str}"
        )
    print("=" * 80 + "\n")


if __name__ == "__main__":
    run_cli()

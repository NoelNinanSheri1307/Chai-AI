"""Isolated calibration experiment evaluator for Milestone 17 (Targeted Detector Rebalance)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.benchmark.models import (
    BenchmarkRunResult,
    GroundTruthLabel,
)
from app.core.enums import ScoreCategory
from app.pipeline.config import PipelineConfig
from app.pipeline.fusion.classify import compute_classification
from app.pipeline.fusion.normalize import NormalizedSignal


@dataclass(frozen=True)
class CalibrationCandidate:
    """A candidate calibration configuration to test against the benchmark baseline."""

    name: str
    description: str
    classifier_resolution: float
    classifier_contribution_matrix: dict[str, dict[str, float]]
    detector_reliability: dict[str, float]
    disabled_detectors: list[str] = field(default_factory=list)


# Production baseline configuration from Milestone 14
_prod_cfg = PipelineConfig()

BASELINE_M14 = CalibrationCandidate(
    name="BASELINE_M14",
    description="Current production configuration (Lighting=0.17, Texture=0.15, Frequency=0.18, sigma=0.15)",
    classifier_resolution=_prod_cfg.classifier_resolution,
    classifier_contribution_matrix=_prod_cfg.classifier_contribution_matrix,
    detector_reliability=_prod_cfg.detector_reliability,
    disabled_detectors=_prod_cfg.disabled_detectors,
)

# Milestone 17 Proposed Candidate: Lighting/Texture Dampening + Frequency Promotion
EXP_4_TARGETED_DETECTOR_REBALANCE = CalibrationCandidate(
    name="EXP_4_TARGETED_DETECTOR_REBALANCE",
    description="Targeted dampening of lighting (0.05) and texture (0.05) with frequency promotion (0.40)",
    classifier_resolution=0.15,
    classifier_contribution_matrix=_prod_cfg.classifier_contribution_matrix,
    detector_reliability={
        "metadata": 0.10,
        "frequency": 0.40,
        "ela": 0.18,
        "noise": 0.12,
        "compression": 0.10,
        "texture": 0.05,
        "lighting": 0.05,
    },
    disabled_detectors=[],
)

BASELINE_M12 = BASELINE_M14


class CandidateEvaluationResult(BaseModel):
    """Evaluation metrics for a candidate calibration configuration."""

    model_config = ConfigDict(extra="forbid")

    name: str
    description: str
    total_evaluated: int
    accuracy: float
    precision: float
    recall: float
    f1: float
    macro_f1: float
    weighted_f1: float
    tp: int
    tn: int
    fp: int
    fn: int
    real_precision: float = 0.0
    real_recall: float = 0.0
    high_conf_failures: int = 0
    very_high_conf_failures: int = 0
    low_conf_correct: int = 0
    mean_conf_correct: float = 0.0
    mean_conf_incorrect: float = 0.0
    delta_accuracy_vs_baseline: float = 0.0
    delta_f1_vs_baseline: float = 0.0
    delta_macro_f1_vs_baseline: float = 0.0
    delta_recall_vs_baseline: float = 0.0
    delta_precision_vs_baseline: float = 0.0
    delta_fp_vs_baseline: int = 0
    delta_fn_vs_baseline: int = 0
    delta_tp_vs_baseline: int = 0


class TransitionItem(BaseModel):
    """Detailed record of an individual image transitioning classification between runs."""

    model_config = ConfigDict(extra="forbid")

    image_id: str
    file_path: str
    format: str
    ground_truth: str
    baseline_pred: str
    baseline_conf: float
    candidate_pred: str
    candidate_conf: float


class FailureTransitions(BaseModel):
    """Categorized transitions between Baseline and Candidate."""

    model_config = ConfigDict(extra="forbid")

    fixed_false_positives: list[TransitionItem] = Field(default_factory=list)
    newly_introduced_false_positives: list[TransitionItem] = Field(
        default_factory=list
    )
    fixed_false_negatives: list[TransitionItem] = Field(default_factory=list)
    newly_introduced_false_negatives: list[TransitionItem] = Field(
        default_factory=list
    )


class FormatComparisonItem(BaseModel):
    """Per-format comparison between baseline and candidate."""

    model_config = ConfigDict(extra="forbid")

    format_name: str
    image_count: int
    baseline_accuracy: float
    candidate_accuracy: float
    baseline_ai_recall: float
    candidate_ai_recall: float
    baseline_ai_precision: float
    candidate_ai_precision: float
    baseline_f1: float
    candidate_f1: float
    baseline_fp: int
    candidate_fp: int
    baseline_fn: int
    candidate_fn: int


class AISubgroupItemM17(BaseModel):
    """AI-generated subgroup record."""

    model_config = ConfigDict(extra="forbid")

    image_id: str
    file_path: str
    format: str
    baseline_pred: str
    baseline_conf: float
    candidate_pred: str
    candidate_conf: float
    caught_by_baseline: bool
    caught_by_candidate: bool


class AISubgroupReport(BaseModel):
    """Subgroup analysis for the 52 AI-generated benchmark images."""

    model_config = ConfigDict(extra="forbid")

    total_ai_images: int
    baseline_caught_count: int
    baseline_recall: float
    candidate_caught_count: int
    candidate_recall: float
    newly_detected: list[AISubgroupItemM17] = Field(default_factory=list)
    newly_missed: list[AISubgroupItemM17] = Field(default_factory=list)
    by_format: dict[str, dict[str, Any]] = Field(default_factory=dict)


class DetectorImpactStat(BaseModel):
    """Forensic measurement of detector impact before and after calibration."""

    model_config = ConfigDict(extra="forbid")

    detector_name: str
    real_mean: float
    ai_mean: float
    separation: float
    weight_before: float
    weight_after: float
    share_before_pct: float
    share_after_pct: float


class CalibrationComparisonReport(BaseModel):
    """Complete aggregated Milestone 17 calibration comparison report."""

    model_config = ConfigDict(extra="forbid")

    baseline: CandidateEvaluationResult
    candidate: CandidateEvaluationResult
    detector_impacts: list[DetectorImpactStat] = Field(default_factory=list)
    transitions: FailureTransitions
    format_breakdown: dict[str, FormatComparisonItem] = Field(default_factory=dict)
    ai_subgroup: AISubgroupReport
    decision_status: str  # "SUCCESSFUL", "MIXED", "FAILED"
    decision_rationale: list[str] = Field(default_factory=list)
    promotion_status: str = "Experimental candidate only — not promoted to production."


def _safe_div(num: float, den: float) -> float:
    return round(num / den, 4) if den > 0 else 0.0


def _mean(vals: list[float]) -> float:
    return round(sum(vals) / len(vals), 4) if vals else 0.0


def evaluate_calibration(
    candidate: CalibrationCandidate,
    benchmark_data: BenchmarkRunResult | dict[str, Any] | Path,
    baseline_result: CandidateEvaluationResult | None = None,
) -> CandidateEvaluationResult:
    """Evaluate a candidate configuration over the recorded benchmark detector signals."""
    if isinstance(benchmark_data, Path):
        raw = json.loads(benchmark_data.read_text(encoding="utf-8"))
        run_res = BenchmarkRunResult.model_validate(raw)
    elif isinstance(benchmark_data, dict):
        run_res = BenchmarkRunResult.model_validate(benchmark_data)
    else:
        run_res = benchmark_data

    test_config = PipelineConfig(
        classifier_resolution=candidate.classifier_resolution,
        classifier_contribution_matrix=candidate.classifier_contribution_matrix,
        detector_reliability=candidate.detector_reliability,
        disabled_detectors=candidate.disabled_detectors,
    )

    tp = tn = fp = fn = 0
    high_conf_failures = 0
    very_high_conf_failures = 0
    low_conf_correct = 0
    total_valid = 0

    conf_correct: list[float] = []
    conf_incorrect: list[float] = []

    real_count = 0
    ai_count = 0

    for r in run_res.results:
        gt_val = r.ground_truth.value
        signals: list[NormalizedSignal] = []
        for det_name, raw_score in r.detector_scores.items():
            if det_name in test_config.disabled_detectors:
                continue
            reliability = test_config.reliability_for(det_name)
            det_conf = r.detector_confidences.get(det_name, 0.80)
            signals.append(
                NormalizedSignal(
                    detector=det_name,
                    detector_version="1.0",
                    category=ScoreCategory.METADATA,
                    score=raw_score,
                    confidence=det_conf,
                    reliability=reliability,
                )
            )

        if not signals:
            continue

        res = compute_classification(
            signals=signals,
            config=test_config,
            total_capacity=len(signals),
        )

        pred = "original" if res.winner.value == 0 else "ai_generated"
        is_correct = pred == gt_val
        conf = res.confidence

        total_valid += 1
        if is_correct:
            conf_correct.append(conf)
            if conf <= 0.60:
                low_conf_correct += 1
        else:
            conf_incorrect.append(conf)
            if conf >= 0.80:
                high_conf_failures += 1
            if conf >= 0.90:
                very_high_conf_failures += 1

        if gt_val == "original":
            real_count += 1
            if pred == "original":
                tn += 1
            else:
                fp += 1
        elif gt_val == "ai_generated":
            ai_count += 1
            if pred == "ai_generated":
                tp += 1
            else:
                fn += 1

    accuracy = _safe_div(tp + tn, total_valid)
    precision = _safe_div(tp, tp + fp)
    recall = _safe_div(tp, tp + fn)
    f1 = _safe_div(2 * precision * recall, precision + recall)

    orig_prec = _safe_div(tn, tn + fn)
    orig_rec = _safe_div(tn, tn + fp)
    orig_f1 = _safe_div(2 * orig_prec * orig_rec, orig_prec + orig_rec)

    macro_f1 = round((orig_f1 + f1) / 2, 4)
    weighted_f1 = (
        round((orig_f1 * real_count + f1 * ai_count) / total_valid, 4)
        if total_valid > 0
        else 0.0
    )

    delta_acc = (
        round(accuracy - baseline_result.accuracy, 4) if baseline_result else 0.0
    )
    delta_prec = (
        round(precision - baseline_result.precision, 4) if baseline_result else 0.0
    )
    delta_rec = round(recall - baseline_result.recall, 4) if baseline_result else 0.0
    delta_f1 = round(f1 - baseline_result.f1, 4) if baseline_result else 0.0
    delta_macro = (
        round(macro_f1 - baseline_result.macro_f1, 4) if baseline_result else 0.0
    )
    delta_fp = fp - baseline_result.fp if baseline_result else 0
    delta_fn = fn - baseline_result.fn if baseline_result else 0
    delta_tp = tp - baseline_result.tp if baseline_result else 0

    return CandidateEvaluationResult(
        name=candidate.name,
        description=candidate.description,
        total_evaluated=total_valid,
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
        real_precision=orig_prec,
        real_recall=orig_rec,
        high_conf_failures=high_conf_failures,
        very_high_conf_failures=very_high_conf_failures,
        low_conf_correct=low_conf_correct,
        mean_conf_correct=_mean(conf_correct),
        mean_conf_incorrect=_mean(conf_incorrect),
        delta_accuracy_vs_baseline=delta_acc,
        delta_precision_vs_baseline=delta_prec,
        delta_recall_vs_baseline=delta_rec,
        delta_f1_vs_baseline=delta_f1,
        delta_macro_f1_vs_baseline=delta_macro,
        delta_fp_vs_baseline=delta_fp,
        delta_fn_vs_baseline=delta_fn,
        delta_tp_vs_baseline=delta_tp,
    )


def compare_calibration_runs(
    benchmark_data: BenchmarkRunResult | dict[str, Any] | Path,
    baseline_candidate: CalibrationCandidate = BASELINE_M14,
    test_candidate: CalibrationCandidate = EXP_4_TARGETED_DETECTOR_REBALANCE,
) -> CalibrationComparisonReport:
    """Run full comparative investigation between Baseline M14 and Candidate EXP_4."""
    if isinstance(benchmark_data, Path):
        raw = json.loads(benchmark_data.read_text(encoding="utf-8"))
        run_res = BenchmarkRunResult.model_validate(raw)
    elif isinstance(benchmark_data, dict):
        run_res = BenchmarkRunResult.model_validate(benchmark_data)
    else:
        run_res = benchmark_data

    base_eval = evaluate_calibration(baseline_candidate, run_res)
    cand_eval = evaluate_calibration(
        test_candidate, run_res, baseline_result=base_eval
    )

    base_cfg = PipelineConfig(
        classifier_resolution=baseline_candidate.classifier_resolution,
        classifier_contribution_matrix=baseline_candidate.classifier_contribution_matrix,
        detector_reliability=baseline_candidate.detector_reliability,
        disabled_detectors=baseline_candidate.disabled_detectors,
    )
    cand_cfg = PipelineConfig(
        classifier_resolution=test_candidate.classifier_resolution,
        classifier_contribution_matrix=test_candidate.classifier_contribution_matrix,
        detector_reliability=test_candidate.detector_reliability,
        disabled_detectors=test_candidate.disabled_detectors,
    )

    # 1. Failure Transitions
    fixed_fp: list[TransitionItem] = []
    new_fp: list[TransitionItem] = []
    fixed_fn: list[TransitionItem] = []
    new_fn: list[TransitionItem] = []

    # 2. Per-Format buckets
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

    # 3. AI Subgroup items
    ai_subgroup_items: list[AISubgroupItemM17] = []

    # 4. Detector stats tracking
    all_detectors = [
        "frequency",
        "lighting",
        "texture",
        "compression",
        "metadata",
        "ela",
        "noise",
    ]
    det_real_scores: dict[str, list[float]] = {d: [] for d in all_detectors}
    det_ai_scores: dict[str, list[float]] = {d: [] for d in all_detectors}

    for r in run_res.results:
        gt_is_ai = r.ground_truth == GroundTruthLabel.AI_GENERATED
        gt_val = "ai_generated" if gt_is_ai else "original"

        ext_str = (
            r.file_path.split(".")[-1].upper() if "." in r.file_path else "UNKNOWN"
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

        for d in all_detectors:
            s_val = r.detector_scores.get(d)
            if s_val is not None:
                if gt_is_ai:
                    det_ai_scores[d].append(s_val)
                else:
                    det_real_scores[d].append(s_val)

        # Evaluate Baseline
        b_signals = [
            NormalizedSignal(
                detector=d,
                detector_version="1.0",
                category=ScoreCategory.METADATA,
                score=sc,
                confidence=r.detector_confidences.get(d, 0.80),
                reliability=base_cfg.reliability_for(d),
            )
            for d, sc in r.detector_scores.items()
        ]
        b_res = compute_classification(b_signals, base_cfg, len(b_signals))
        b_pred = "original" if b_res.winner.value == 0 else "ai_generated"
        b_conf = b_res.confidence

        # Evaluate Candidate
        c_signals = [
            NormalizedSignal(
                detector=d,
                detector_version="1.0",
                category=ScoreCategory.METADATA,
                score=sc,
                confidence=r.detector_confidences.get(d, 0.80),
                reliability=cand_cfg.reliability_for(d),
            )
            for d, sc in r.detector_scores.items()
        ]
        c_res = compute_classification(c_signals, cand_cfg, len(c_signals))
        c_pred = "original" if c_res.winner.value == 0 else "ai_generated"
        c_conf = c_res.confidence

        # Update format counters
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

        # Check transitions
        t_item = TransitionItem(
            image_id=r.image_id,
            file_path=r.file_path,
            format=fmt,
            ground_truth=gt_val,
            baseline_pred=b_pred,
            baseline_conf=b_conf,
            candidate_pred=c_pred,
            candidate_conf=c_conf,
        )

        if not gt_is_ai:
            if b_pred == "ai_generated" and c_pred == "original":
                fixed_fp.append(t_item)
            elif b_pred == "original" and c_pred == "ai_generated":
                new_fp.append(t_item)
        else:
            if b_pred == "original" and c_pred == "ai_generated":
                fixed_fn.append(t_item)
            elif b_pred == "ai_generated" and c_pred == "original":
                new_fn.append(t_item)

            ai_subgroup_items.append(
                AISubgroupItemM17(
                    image_id=r.image_id,
                    file_path=r.file_path,
                    format=fmt,
                    baseline_pred=b_pred,
                    baseline_conf=b_conf,
                    candidate_pred=c_pred,
                    candidate_conf=c_conf,
                    caught_by_baseline=b_pred == "ai_generated",
                    caught_by_candidate=c_pred == "ai_generated",
                )
            )

    # Compile Detector Impacts
    total_w_base = sum(baseline_candidate.detector_reliability.values())
    total_w_cand = sum(test_candidate.detector_reliability.values())
    det_impacts: list[DetectorImpactStat] = []

    for d in ["lighting", "texture", "frequency", "compression", "metadata", "ela", "noise"]:
        r_list = det_real_scores[d]
        a_list = det_ai_scores[d]
        r_m = _mean(r_list)
        a_m = _mean(a_list)
        w_b = baseline_candidate.detector_reliability.get(d, 0.10)
        w_c = test_candidate.detector_reliability.get(d, 0.10)
        det_impacts.append(
            DetectorImpactStat(
                detector_name=d,
                real_mean=r_m,
                ai_mean=a_m,
                separation=round(a_m - r_m, 4),
                weight_before=w_b,
                weight_after=w_c,
                share_before_pct=_safe_div(w_b, total_w_base) * 100,
                share_after_pct=_safe_div(w_c, total_w_cand) * 100,
            )
        )

    # Compile Format Comparisons
    format_comp: dict[str, FormatComparisonItem] = {}
    for f, d_f in fmt_data.items():
        cnt = d_f["count"]
        if cnt == 0:
            continue
        b_acc = _safe_div(d_f["b_tp"] + d_f["b_tn"], cnt)
        c_acc = _safe_div(d_f["c_tp"] + d_f["c_tn"], cnt)
        b_rec = _safe_div(d_f["b_tp"], d_f["b_tp"] + d_f["b_fn"])
        c_rec = _safe_div(d_f["c_tp"], d_f["c_tp"] + d_f["c_fn"])
        b_prec = _safe_div(d_f["b_tp"], d_f["b_tp"] + d_f["b_fp"])
        c_prec = _safe_div(d_f["c_tp"], d_f["c_tp"] + d_f["c_fp"])
        b_f1 = _safe_div(2 * b_prec * b_rec, b_prec + b_rec)
        c_f1 = _safe_div(2 * c_prec * c_rec, c_prec + c_rec)

        format_comp[f] = FormatComparisonItem(
            format_name=f,
            image_count=cnt,
            baseline_accuracy=b_acc,
            candidate_accuracy=c_acc,
            baseline_ai_recall=b_rec,
            candidate_ai_recall=c_rec,
            baseline_ai_precision=b_prec,
            candidate_ai_precision=c_prec,
            baseline_f1=b_f1,
            candidate_f1=c_f1,
            baseline_fp=d_f["b_fp"],
            candidate_fp=d_f["c_fp"],
            baseline_fn=d_f["b_fn"],
            candidate_fn=d_f["c_fn"],
        )

    # AI Subgroup Summary
    b_ai_caught = sum(1 for it in ai_subgroup_items if it.caught_by_baseline)
    c_ai_caught = sum(1 for it in ai_subgroup_items if it.caught_by_candidate)
    ai_subgroup_report = AISubgroupReport(
        total_ai_images=len(ai_subgroup_items),
        baseline_caught_count=b_ai_caught,
        baseline_recall=_safe_div(b_ai_caught, len(ai_subgroup_items)),
        candidate_caught_count=c_ai_caught,
        candidate_recall=_safe_div(c_ai_caught, len(ai_subgroup_items)),
        newly_detected=[it for it in ai_subgroup_items if not it.caught_by_baseline and it.caught_by_candidate],
        newly_missed=[it for it in ai_subgroup_items if it.caught_by_baseline and not it.caught_by_candidate],
        by_format={
            f: {
                "count": fmt_data[f]["ai_count"],
                "baseline_caught": fmt_data[f]["b_tp"],
                "candidate_caught": fmt_data[f]["c_tp"],
                "baseline_recall": _safe_div(fmt_data[f]["b_tp"], fmt_data[f]["ai_count"]),
                "candidate_recall": _safe_div(fmt_data[f]["c_tp"], fmt_data[f]["ai_count"]),
            }
            for f in formats if fmt_data[f]["ai_count"] > 0
        },
    )

    # Decision logic
    fp_reduced = cand_eval.fp < base_eval.fp
    recall_maintained = cand_eval.recall >= base_eval.recall
    f1_improved = cand_eval.f1 >= base_eval.f1
    no_hcf_increase = cand_eval.high_conf_failures <= base_eval.high_conf_failures

    rationale: list[str] = []
    if fp_reduced and recall_maintained and f1_improved and no_hcf_increase:
        decision_status = "SUCCESSFUL"
        rationale.append(f"Substantial False Positive reduction on Real images: {base_eval.fp} -> {cand_eval.fp} ({cand_eval.delta_fp_vs_baseline:+d} FP).")
        rationale.append(f"AI Recall maintained or increased: {base_eval.recall * 100:.2f}% -> {cand_eval.recall * 100:.2f}% ({cand_eval.delta_recall_vs_baseline * 100:+.2f} pp).")
        rationale.append(f"AI F1 Score improved: {base_eval.f1:.4f} -> {cand_eval.f1:.4f} ({cand_eval.delta_f1_vs_baseline:+.4f}).")
        rationale.append(f"High-confidence failures remained at zero ({cand_eval.high_conf_failures}).")
    elif cand_eval.fp < base_eval.fp and not recall_maintained:
        decision_status = "MIXED"
        rationale.append(f"False Positives reduced from {base_eval.fp} to {cand_eval.fp}, but AI Recall dropped from {base_eval.recall * 100:.2f}% to {cand_eval.recall * 100:.2f}%.")
    else:
        decision_status = "FAILED"
        rationale.append("Candidate did not achieve the required diagnostic performance bounds.")

    return CalibrationComparisonReport(
        baseline=base_eval,
        candidate=cand_eval,
        detector_impacts=det_impacts,
        transitions=FailureTransitions(
            fixed_false_positives=fixed_fp,
            newly_introduced_false_positives=new_fp,
            fixed_false_negatives=fixed_fn,
            newly_introduced_false_negatives=new_fn,
        ),
        format_breakdown=format_comp,
        ai_subgroup=ai_subgroup_report,
        decision_status=decision_status,
        decision_rationale=rationale,
    )

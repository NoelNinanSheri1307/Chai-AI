"""Isolated calibration experiment evaluator for simulating candidate pipeline parameters."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.benchmark.models import (
    BenchmarkRunResult,
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


@dataclass
class CandidateEvaluationResult:
    """Evaluation metrics for a candidate calibration configuration."""

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
    high_conf_failures: int
    delta_accuracy_vs_baseline: float = 0.0
    delta_f1_vs_baseline: float = 0.0
    delta_macro_f1_vs_baseline: float = 0.0


# Baseline production configuration preserved from Milestone 12
_prod_cfg = PipelineConfig()
BASELINE_M12 = CalibrationCandidate(
    name="BASELINE_M12",
    description="Production Milestone 12 baseline configuration (uncalibrated)",
    classifier_resolution=_prod_cfg.classifier_resolution,
    classifier_contribution_matrix=_prod_cfg.classifier_contribution_matrix,
    detector_reliability=_prod_cfg.detector_reliability,
    disabled_detectors=_prod_cfg.disabled_detectors,
)


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

    # Construct isolated PipelineConfig instance without altering global settings
    test_config = PipelineConfig(
        classifier_resolution=candidate.classifier_resolution,
        classifier_contribution_matrix=candidate.classifier_contribution_matrix,
        detector_reliability=candidate.detector_reliability,
        disabled_detectors=candidate.disabled_detectors,
    )

    tp = 0
    tn = 0
    fp = 0
    fn = 0
    high_conf_failures = 0
    total_valid = 0

    real_count = 0
    ai_count = 0

    for r in run_res.results:
        gt_val = r.ground_truth.value
        # Reconstruct normalized signals from recorded detector scores
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

        if not is_correct and conf >= 0.80:
            high_conf_failures += 1

    accuracy = round((tp + tn) / total_valid, 4) if total_valid > 0 else 0.0
    precision = round(tp / (tp + fp), 4) if (tp + fp) > 0 else 0.0
    recall = round(tp / (tp + fn), 4) if (tp + fn) > 0 else 0.0
    f1 = (
        round(2 * precision * recall / (precision + recall), 4)
        if (precision + recall) > 0
        else 0.0
    )

    orig_prec = round(tn / (tn + fn), 4) if (tn + fn) > 0 else 0.0
    orig_rec = round(tn / (tn + fp), 4) if (tn + fp) > 0 else 0.0
    orig_f1 = (
        round(2 * orig_prec * orig_rec / (orig_prec + orig_rec), 4)
        if (orig_prec + orig_rec) > 0
        else 0.0
    )

    macro_f1 = round((orig_f1 + f1) / 2, 4)
    weighted_f1 = (
        round((orig_f1 * real_count + f1 * ai_count) / total_valid, 4)
        if total_valid > 0
        else 0.0
    )

    delta_acc = (
        round(accuracy - baseline_result.accuracy, 4) if baseline_result else 0.0
    )
    delta_f1 = round(f1 - baseline_result.f1, 4) if baseline_result else 0.0
    delta_macro = (
        round(macro_f1 - baseline_result.macro_f1, 4) if baseline_result else 0.0
    )

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
        high_conf_failures=high_conf_failures,
        delta_accuracy_vs_baseline=delta_acc,
        delta_f1_vs_baseline=delta_f1,
        delta_macro_f1_vs_baseline=delta_macro,
    )

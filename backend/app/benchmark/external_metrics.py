"""Comparative metrics engine for independent external detector benchmarking (Milestone 15).

Calculates independent performance metrics for external detection providers (e.g. Sightengine),
evaluates agreement and disagreement with Chai AI's internal pipeline, produces three-way
ground-truth comparisons, format-specific breakdowns, and failure categorizations.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.benchmark.models import (
    BenchmarkRunResult,
    ConfusionMatrixData,
    GroundTruthLabel,
    ImageBenchmarkResult,
)


class ExternalProviderMetrics(BaseModel):
    """Independent binary evaluation metrics for an external detection provider."""

    model_config = ConfigDict(extra="forbid")

    provider_name: str
    provider_version: str = "1.0"
    total_evaluated: int = 0
    successful_analyses: int = 0
    failed_analyses: int = 0
    timeouts: int = 0
    unconfigured_or_disabled: int = 0
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0
    macro_f1: float = 0.0
    weighted_f1: float = 0.0
    tp: int = 0
    tn: int = 0
    fp: int = 0
    fn: int = 0
    confusion_matrix: ConfusionMatrixData = Field(default_factory=ConfusionMatrixData)


class ChaiVsExternalAgreement(BaseModel):
    """Agreement and disagreement statistics between Chai and the external provider."""

    model_config = ConfigDict(extra="forbid")

    total_compared: int = 0
    agree_count: int = 0
    disagree_count: int = 0
    agreement_rate: float = 0.0
    chai_ai_ext_ai: int = 0
    chai_real_ext_real: int = 0
    chai_ai_ext_real: int = 0
    chai_real_ext_ai: int = 0
    # Ground-truth partitioned agreement
    real_subset_count: int = 0
    real_subset_agree_count: int = 0
    real_subset_agree_rate: float = 0.0
    ai_subset_count: int = 0
    ai_subset_agree_count: int = 0
    ai_subset_agree_rate: float = 0.0


class ThreeWayCase(BaseModel):
    """A row in the three-way ground-truth comparison truth table."""

    model_config = ConfigDict(extra="forbid")

    ground_truth: str
    chai_verdict: str
    external_verdict: str
    interpretation: str
    count: int = 0
    percentage: float = 0.0
    sample_image_ids: list[str] = Field(default_factory=list)


class FormatComparativeMetrics(BaseModel):
    """Comparative performance breakdown for a specific image format."""

    model_config = ConfigDict(extra="forbid")

    format_name: str
    image_count: int = 0
    chai_accuracy: float = 0.0
    external_accuracy: float = 0.0
    chai_ai_recall: float = 0.0
    external_ai_recall: float = 0.0
    agreement_rate: float = 0.0


class ComparativeConfidenceAnalysis(BaseModel):
    """Separate confidence metrics for Chai and the external provider."""

    model_config = ConfigDict(extra="forbid")

    chai_mean_confidence_correct: float = 0.0
    chai_mean_confidence_incorrect: float = 0.0
    external_mean_confidence_correct: float = 0.0
    external_mean_confidence_incorrect: float = 0.0
    note: str = (
        "Chai confidence and external provider confidence are distinct scoring systems "
        "and should not be directly compared on a shared scale."
    )


class ComparativeFailureCase(BaseModel):
    """Detailed record of a benchmark case where at least one system failed or disagreed."""

    model_config = ConfigDict(extra="forbid")

    image_id: str
    sha256: str
    ground_truth: str
    file_format: str
    file_path: str
    chai_verdict: str
    chai_confidence: float
    chai_correct: bool
    external_status: str
    external_detected_as_ai: bool | None = None
    external_verdict: str | None = None
    external_confidence: float | None = None
    external_correct: bool | None = None
    category: str


class ComparativeFailureSummary(BaseModel):
    """Aggregated lists of failure and disagreement cases."""

    model_config = ConfigDict(extra="forbid")

    chai_correct_external_wrong: list[ComparativeFailureCase] = Field(
        default_factory=list
    )
    external_correct_chai_wrong: list[ComparativeFailureCase] = Field(
        default_factory=list
    )
    both_wrong: list[ComparativeFailureCase] = Field(default_factory=list)
    disagreements: list[ComparativeFailureCase] = Field(default_factory=list)


class ExternalBenchmarkReportResult(BaseModel):
    """Complete aggregated benchmark report comparing Chai with an external provider."""

    model_config = ConfigDict(extra="forbid")

    run_id: str
    timestamp: str
    dataset_summary: dict[str, Any] = Field(default_factory=dict)
    chai_metrics: dict[str, Any] = Field(default_factory=dict)
    external_metrics: ExternalProviderMetrics
    agreement: ChaiVsExternalAgreement
    three_way_comparison: list[ThreeWayCase] = Field(default_factory=list)
    format_breakdown: dict[str, FormatComparativeMetrics] = Field(default_factory=dict)
    confidence_analysis: ComparativeConfidenceAnalysis
    failures: ComparativeFailureSummary
    methodology_notes: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


def _safe_div(num: float, den: float) -> float:
    return round(num / den, 4) if den > 0 else 0.0


def compute_external_provider_metrics(
    results: list[ImageBenchmarkResult],
    provider_name: str = "sightengine",
    provider_version: str = "1.0",
) -> ExternalProviderMetrics:
    """Compute binary classification metrics for the external provider against ground truth."""
    tp = tn = fp = fn = 0
    successes = failures = timeouts = unconfigured = 0

    for r in results:
        ext = r.external_result
        if not ext:
            unconfigured += 1
            continue

        status = ext.get("status", "unconfigured")
        if status in {"unconfigured", "disabled"}:
            unconfigured += 1
            continue
        elif status == "timeout":
            timeouts += 1
            failures += 1
            continue
        elif status != "success":
            failures += 1
            continue

        detected_as_ai = ext.get("detected_as_ai")
        if detected_as_ai is None:
            failures += 1
            continue

        successes += 1
        gt_is_ai = r.ground_truth == GroundTruthLabel.AI_GENERATED

        if gt_is_ai and detected_as_ai:
            tp += 1
        elif not gt_is_ai and not detected_as_ai:
            tn += 1
        elif not gt_is_ai and detected_as_ai:
            fp += 1
        elif gt_is_ai and not detected_as_ai:
            fn += 1

    total_valid = tp + tn + fp + fn
    accuracy = _safe_div(tp + tn, total_valid)
    precision = _safe_div(tp, tp + fp)
    recall = _safe_div(tp, tp + fn)
    f1 = _safe_div(2 * precision * recall, precision + recall)

    # Real class metrics for Macro/Weighted F1
    real_prec = _safe_div(tn, tn + fn)
    real_rec = _safe_div(tn, tn + fp)
    real_f1 = _safe_div(2 * real_prec * real_rec, real_prec + real_rec)

    macro_f1 = round((f1 + real_f1) / 2.0, 4)
    weighted_f1 = (
        round(((tp + fn) * f1 + (tn + fp) * real_f1) / total_valid, 4)
        if total_valid > 0
        else 0.0
    )

    return ExternalProviderMetrics(
        provider_name=provider_name,
        provider_version=provider_version,
        total_evaluated=len(results),
        successful_analyses=successes,
        failed_analyses=failures,
        timeouts=timeouts,
        unconfigured_or_disabled=unconfigured,
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
        confusion_matrix=ConfusionMatrixData(
            labels=["original", "ai_generated"],
            matrix=[[tn, fp], [fn, tp]],
        ),
    )


def compute_agreement_metrics(
    results: list[ImageBenchmarkResult],
) -> ChaiVsExternalAgreement:
    """Evaluate agreement and disagreement between Chai and the external provider."""
    total = agree = disagree = 0
    c_ai_e_ai = c_real_e_real = c_ai_e_real = c_real_e_ai = 0
    real_count = real_agree = 0
    ai_count = ai_agree = 0

    for r in results:
        ext = r.external_result
        if not ext or ext.get("status") != "success":
            continue
        ext_ai = ext.get("detected_as_ai")
        if ext_ai is None:
            continue

        chai_ai = r.predicted_class == "ai_generated"
        gt_is_ai = r.ground_truth == GroundTruthLabel.AI_GENERATED
        total += 1

        if chai_ai == ext_ai:
            agree += 1
            if gt_is_ai:
                ai_agree += 1
            else:
                real_agree += 1
        else:
            disagree += 1

        if gt_is_ai:
            ai_count += 1
        else:
            real_count += 1

        if chai_ai and ext_ai:
            c_ai_e_ai += 1
        elif not chai_ai and not ext_ai:
            c_real_e_real += 1
        elif chai_ai and not ext_ai:
            c_ai_e_real += 1
        elif not chai_ai and ext_ai:
            c_real_e_ai += 1

    return ChaiVsExternalAgreement(
        total_compared=total,
        agree_count=agree,
        disagree_count=disagree,
        agreement_rate=_safe_div(agree, total),
        chai_ai_ext_ai=c_ai_e_ai,
        chai_real_ext_real=c_real_e_real,
        chai_ai_ext_real=c_ai_e_real,
        chai_real_ext_ai=c_real_e_ai,
        real_subset_count=real_count,
        real_subset_agree_count=real_agree,
        real_subset_agree_rate=_safe_div(real_agree, real_count),
        ai_subset_count=ai_count,
        ai_subset_agree_count=ai_agree,
        ai_subset_agree_rate=_safe_div(ai_agree, ai_count),
    )


def compute_three_way_comparison(
    results: list[ImageBenchmarkResult],
) -> list[ThreeWayCase]:
    """Compute the 8-state truth table: Ground Truth vs Chai vs External Provider."""
    definitions = [
        ("original", "original", "original", "Both correct (Authentic)"),
        (
            "original",
            "ai_generated",
            "original",
            "Chai false positive / Provider correct",
        ),
        (
            "original",
            "original",
            "ai_generated",
            "Provider false positive / Chai correct",
        ),
        ("original", "ai_generated", "ai_generated", "Both false positive (AI error)"),
        ("ai_generated", "ai_generated", "ai_generated", "Both correct (AI caught)"),
        (
            "ai_generated",
            "original",
            "ai_generated",
            "Chai false negative / Provider correct",
        ),
        (
            "ai_generated",
            "ai_generated",
            "original",
            "Provider false negative / Chai correct",
        ),
        ("ai_generated", "original", "original", "Both false negative (Both missed)"),
    ]

    counts: dict[tuple[str, str, str], list[str]] = {
        (gt, c, e): [] for gt, c, e, _ in definitions
    }
    total_valid = 0

    for r in results:
        ext = r.external_result
        if (
            not ext
            or ext.get("status") != "success"
            or ext.get("detected_as_ai") is None
        ):
            continue

        gt_str = (
            "ai_generated"
            if r.ground_truth == GroundTruthLabel.AI_GENERATED
            else "original"
        )
        c_str = (
            "ai_generated" if r.predicted_class == "ai_generated" else "original"
        )
        e_str = "ai_generated" if ext.get("detected_as_ai") else "original"

        key = (gt_str, c_str, e_str)
        if key in counts:
            counts[key].append(r.image_id)
            total_valid += 1

    cases: list[ThreeWayCase] = []
    for gt, c, e, interp in definitions:
        matched_ids = counts.get((gt, c, e), [])
        cases.append(
            ThreeWayCase(
                ground_truth=gt,
                chai_verdict=c,
                external_verdict=e,
                interpretation=interp,
                count=len(matched_ids),
                percentage=_safe_div(len(matched_ids), total_valid),
                sample_image_ids=matched_ids[:5],
            )
        )
    return cases


def compute_format_comparisons(
    results: list[ImageBenchmarkResult],
) -> dict[str, FormatComparativeMetrics]:
    """Compute per-format comparative accuracy and recall breakdown."""
    by_format: dict[str, list[ImageBenchmarkResult]] = {}
    for r in results:
        ext = r.file_path.split(".")[-1].upper() if "." in r.file_path else "UNKNOWN"
        if ext in {"JPG", "JPEG"}:
            fmt = "JPEG"
        elif ext in {"PNG", "WEBP", "AVIF"}:
            fmt = ext
        else:
            fmt = "OTHER"
        by_format.setdefault(fmt, []).append(r)

    metrics_by_format: dict[str, FormatComparativeMetrics] = {}
    for fmt, subset in by_format.items():
        total = len(subset)
        c_correct = sum(1 for x in subset if x.correct)
        chai_acc = _safe_div(c_correct, total)

        # AI Recall for Chai
        ai_subset = [
            x for x in subset if x.ground_truth == GroundTruthLabel.AI_GENERATED
        ]
        c_ai_caught = sum(1 for x in ai_subset if x.predicted_class == "ai_generated")
        chai_recall = _safe_div(c_ai_caught, len(ai_subset))

        # External metrics on this format subset
        ext_valid = [
            x
            for x in subset
            if x.external_result
            and x.external_result.get("status") == "success"
            and x.external_result.get("detected_as_ai") is not None
        ]
        ext_total = len(ext_valid)
        ext_correct = 0
        ext_ai_caught = 0
        ext_ai_total = 0
        agrees = 0

        for x in ext_valid:
            ext_ai = x.external_result.get("detected_as_ai")
            gt_is_ai = x.ground_truth == GroundTruthLabel.AI_GENERATED
            if (gt_is_ai and ext_ai) or (not gt_is_ai and not ext_ai):
                ext_correct += 1

            if gt_is_ai:
                ext_ai_total += 1
                if ext_ai:
                    ext_ai_caught += 1

            chai_ai = x.predicted_class == "ai_generated"
            if chai_ai == ext_ai:
                agrees += 1

        ext_acc = _safe_div(ext_correct, ext_total)
        ext_recall = _safe_div(ext_ai_caught, ext_ai_total)
        agree_rate = _safe_div(agrees, ext_total)

        metrics_by_format[fmt] = FormatComparativeMetrics(
            format_name=fmt,
            image_count=total,
            chai_accuracy=chai_acc,
            external_accuracy=ext_acc,
            chai_ai_recall=chai_recall,
            external_ai_recall=ext_recall,
            agreement_rate=agree_rate,
        )

    return metrics_by_format


def compute_comparative_confidence(
    results: list[ImageBenchmarkResult],
) -> ComparativeConfidenceAnalysis:
    """Compute independent confidence statistics for Chai vs external provider."""
    c_conf_correct: list[float] = []
    c_conf_incorrect: list[float] = []
    e_conf_correct: list[float] = []
    e_conf_incorrect: list[float] = []

    for r in results:
        if r.correct:
            c_conf_correct.append(r.confidence)
        else:
            c_conf_incorrect.append(r.confidence)

        ext = r.external_result
        if (
            ext
            and ext.get("status") == "success"
            and ext.get("detected_as_ai") is not None
        ):
            ext_conf = ext.get("confidence")
            if ext_conf is not None:
                gt_is_ai = r.ground_truth == GroundTruthLabel.AI_GENERATED
                ext_ai = ext.get("detected_as_ai")
                ext_is_correct = (gt_is_ai and ext_ai) or (not gt_is_ai and not ext_ai)
                if ext_is_correct:
                    e_conf_correct.append(float(ext_conf))
                else:
                    e_conf_incorrect.append(float(ext_conf))

    def _mean(vals: list[float]) -> float:
        return round(sum(vals) / len(vals), 4) if vals else 0.0

    return ComparativeConfidenceAnalysis(
        chai_mean_confidence_correct=_mean(c_conf_correct),
        chai_mean_confidence_incorrect=_mean(c_conf_incorrect),
        external_mean_confidence_correct=_mean(e_conf_correct),
        external_mean_confidence_incorrect=_mean(e_conf_incorrect),
    )


def categorize_comparative_failures(
    results: list[ImageBenchmarkResult],
) -> ComparativeFailureSummary:
    """Categorize cases into Chai-correct, Provider-correct, Both-wrong, and Disagreements."""
    chai_right_ext_wrong: list[ComparativeFailureCase] = []
    ext_right_chai_wrong: list[ComparativeFailureCase] = []
    both_wrong: list[ComparativeFailureCase] = []
    disagreements: list[ComparativeFailureCase] = []

    for r in results:
        ext = r.external_result or {}
        ext_status = ext.get("status", "unconfigured")
        ext_ai = ext.get("detected_as_ai")
        ext_conf = ext.get("confidence")
        ext_verdict = (
            "ai_generated"
            if ext_ai is True
            else "original"
            if ext_ai is False
            else None
        )

        gt_is_ai = r.ground_truth == GroundTruthLabel.AI_GENERATED
        ext_correct = (
            ((gt_is_ai and ext_ai) or (not gt_is_ai and not ext_ai))
            if ext_ai is not None
            else None
        )
        chai_correct = r.correct
        chai_ai = r.predicted_class == "ai_generated"

        fmt = r.file_path.split(".")[-1].upper() if "." in r.file_path else "UNKNOWN"

        record = ComparativeFailureCase(
            image_id=r.image_id,
            sha256=r.sha256,
            ground_truth=r.ground_truth.value,
            file_format=fmt,
            file_path=r.file_path,
            chai_verdict=r.predicted_class,
            chai_confidence=r.confidence,
            chai_correct=chai_correct,
            external_status=ext_status,
            external_detected_as_ai=ext_ai,
            external_verdict=ext_verdict,
            external_confidence=ext_conf,
            external_correct=ext_correct,
            category="",
        )

        if ext_correct is not None:
            if chai_correct and not ext_correct:
                record.category = "chai_correct_external_wrong"
                chai_right_ext_wrong.append(record)
            elif not chai_correct and ext_correct:
                record.category = "external_correct_chai_wrong"
                ext_right_chai_wrong.append(record)
            elif not chai_correct and not ext_correct:
                record.category = "both_wrong"
                both_wrong.append(record)

            if chai_ai != ext_ai:
                record.category = "disagreement"
                disagreements.append(record)

    return ComparativeFailureSummary(
        chai_correct_external_wrong=chai_right_ext_wrong,
        external_correct_chai_wrong=ext_right_chai_wrong,
        both_wrong=both_wrong,
        disagreements=disagreements,
    )


def compute_complete_external_benchmark(
    run_result: BenchmarkRunResult,
    provider_name: str = "sightengine",
    provider_version: str = "1.0",
) -> ExternalBenchmarkReportResult:
    """Build a complete comparative external benchmark report from a benchmark run result."""
    ext_metrics = compute_external_provider_metrics(
        run_result.results,
        provider_name=provider_name,
        provider_version=provider_version,
    )
    agreement = compute_agreement_metrics(run_result.results)
    three_way = compute_three_way_comparison(run_result.results)
    format_breakdown = compute_format_comparisons(run_result.results)
    conf_analysis = compute_comparative_confidence(run_result.results)
    failures = categorize_comparative_failures(run_result.results)

    methodology = [
        "Chai AI and Sightengine operate completely independent pipelines with zero cross-influence.",
        "External results are normalized from Sightengine GenAI endpoint (models=genai) using threshold 0.5.",
        "Agreement rate measures verdict concordance between systems, not truth or correctness.",
        "Evaluation against ground truth is the authoritative measure of individual system accuracy.",
    ]

    limitations = [
        f"Dataset contains {run_result.real_count} Real and {run_result.ai_generated_count} AI Generated images (imbalanced).",
        "External API rate-limits and network latency apply to live benchmark runs.",
        "Confidence scores from Chai and Sightengine reflect different internal calibration functions and cannot be compared directly.",
    ]

    return ExternalBenchmarkReportResult(
        run_id=run_result.run_id,
        timestamp=run_result.timestamp,
        dataset_summary={
            "total_images": run_result.total_images,
            "real_count": run_result.real_count,
            "ai_generated_count": run_result.ai_generated_count,
            "manifest_hash": run_result.manifest_hash,
        },
        chai_metrics={
            "accuracy": run_result.accuracy,
            "precision": run_result.precision,
            "recall": run_result.recall,
            "f1": run_result.f1,
            "macro_f1": run_result.macro_f1,
            "weighted_f1": run_result.weighted_f1,
            "tp": run_result.tp,
            "tn": run_result.tn,
            "fp": run_result.fp,
            "fn": run_result.fn,
        },
        external_metrics=ext_metrics,
        agreement=agreement,
        three_way_comparison=three_way,
        format_breakdown=format_breakdown,
        confidence_analysis=conf_analysis,
        failures=failures,
        methodology_notes=methodology,
        limitations=limitations,
    )

"""Fusion decision logic: verdict, confidence and risk.

This module turns the aggregation metrics into the three outputs the rest of the
application consumes. The decision rules are deliberately simple, threshold- and
weight-driven rules sourced from configuration, so every verdict can be traced
back to the configured constants and the input metrics:

* **verdict** — a two-bound rule on the weighted manipulation score combined
  with detector agreement:
    * ``manipulation <= original_max_manipulation`` → ``ORIGINAL`` (the signal
      profile is honest/natural).
    * ``manipulation >= generated_min_manipulation AND agreement >=
      generated_min_agreement`` → ``AI_GENERATED`` (the image is consistently,
      strongly synthetic).
    * otherwise → ``AI_EDITED`` (localized, partial or conflicting evidence).
* **confidence** — a weighted blend of four transparent factors: agreement
  (signals point the same way), decisiveness (the mean is far from the ambiguous
  ``0.5``), coverage (how many intended detectors ran) and reliability (how much
  the detectors trust their own signals). Borderline or sparse evidence lowers
  confidence; strong, unanimous evidence raises it.
* **risk** — derived from the fused confidence via the configured thresholds.

All thresholds and blend weights come from :class:`PipelineConfig`.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.enums import RiskLevel, Verdict
from app.pipeline.config import PipelineConfig

from .metrics import FusionMetrics
from .normalize import clamp01


@dataclass(frozen=True)
class FusionDecision:
    """The executable decision derived from the fusion metrics."""

    verdict: Verdict
    confidence: float
    risk_level: RiskLevel
    reason: str


def compute_confidence(metrics: FusionMetrics, config: PipelineConfig) -> float:
    """Blend agreement, decisiveness, coverage and reliability into confidence."""
    if metrics.active_count == 0:
        return 0.0
    total_inv = 1.0 / config.confidence_weight_sum()
    confidence = (
        config.confidence_agreement_weight * metrics.agreement
        + config.confidence_decisiveness_weight * metrics.decisiveness
        + config.confidence_coverage_weight * metrics.coverage
        + config.confidence_reliability_weight * metrics.reliability
    ) * total_inv
    return round(clamp01(confidence), 4)


def decide_verdict(
    metrics: FusionMetrics, config: PipelineConfig
) -> tuple[Verdict, str]:
    """Choose a verdict from the manipulation score and detector agreement."""
    manipulation = metrics.manipulation
    if metrics.active_count == 0:
        return (
            Verdict.ORIGINAL,
            "No detector produced a usable signal, so no manipulation "
            "evidence was found.",
        )
    if manipulation <= config.original_max_manipulation:
        return (
            Verdict.ORIGINAL,
            (
                f"Fused manipulation score {manipulation:.2f} is at or below "
                f"the original ceiling ({config.original_max_manipulation:.2f})."
            ),
        )
    if (
        manipulation >= config.generated_min_manipulation
        and metrics.agreement >= config.generated_min_agreement
    ):
        return (
            Verdict.AI_GENERATED,
            (
                f"Fused manipulation score {manipulation:.2f} exceeds "
                f"{config.generated_min_manipulation:.2f} and detector agreement "
                f"{metrics.agreement:.2f} exceeds "
                f"{config.generated_min_agreement:.2f}, "
                "indicating strong, coherent synthetic content."
            ),
        )
    return (
        Verdict.AI_EDITED,
        (
            f"Fused manipulation {manipulation:.2f} is above the original ceiling "
            f"but below the AI-generated threshold "
            f"({config.generated_min_manipulation:.2f}) "
            "or the detectors disagree, indicating localized/partial editing."
        ),
    )


def make_decision(metrics: FusionMetrics, config: PipelineConfig) -> FusionDecision:
    """Assemble the full decision (verdict + confidence + risk + reason)."""
    verdict, reason = decide_verdict(metrics, config)
    confidence = compute_confidence(metrics, config)
    risk_level = config.risk_for(verdict, confidence)
    return FusionDecision(
        verdict=verdict,
        confidence=confidence,
        risk_level=risk_level,
        reason=reason,
    )

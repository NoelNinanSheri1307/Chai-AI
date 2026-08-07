"""Fusion decision logic: three-class classification, confidence and risk.

This module turns the normalized detector signals into the executable decision
the rest of the application consumes. It replaces the earlier manipulation-score
thresholding with a genuine three-class comparison:

* **verdict** — the hypothesis (Original / AI Edited / AI Generated) that the
  accumulated detector evidence supports most strongly. Confidence is *not* a
  single manipulation gate; each detector contributes different evidence to each
  hypothesis via the contribution matrix.
* **margin** — how far the winning hypothesis clears its runner-up; this drives
  confidence.
* **confidence** — a calibrated blend of the classification margin, detector
  agreement, winning-hypothesis separation, active-detector coverage and the
  detectors' own self-assessed reliability. It expresses *certainty about the
     classification*, not merely how manipulated the image looks.
* **risk** — derived from verdict + confidence via the configured thresholds.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.core.enums import RiskLevel, Verdict
from app.pipeline.config import PipelineConfig

from .classify import (
    ClassificationResult,
    DetectorHypothesisContribution,
    compute_classification,
)
from .hypotheses import Hypothesis

_VERDICT_TO_LABEL = {
    Verdict.ORIGINAL: "Original",
    Verdict.AI_EDITED: "AI Edited",
    Verdict.AI_GENERATED: "AI Generated",
}

_HYPOTHESIS_TO_VERDICT = {
    Hypothesis.ORIGINAL: Verdict.ORIGINAL,
    Hypothesis.AI_EDITED: Verdict.AI_EDITED,
    Hypothesis.AI_GENERATED: Verdict.AI_GENERATED,
}


@dataclass(frozen=True)
class FusionDecision:
    """The executable decision derived from the classifier."""

    verdict: Verdict
    confidence: float
    risk_level: RiskLevel
    reason: str
    # Three-class transparency (also mirrored onto FusionResult).
    hypothesis_scores: tuple[float, float, float] = (0.0, 0.0, 0.0)
    runner_up_verdict: Verdict | None = None
    classification_margin: float = 0.0
    detector_contributions: list[DetectorHypothesisContribution] = field(
        default_factory=list
    )


def verdict_for_hypothesis(hypothesis: Hypothesis) -> Verdict:
    """Map a hypothesis enum to its equivalent verdict enum."""
    return _HYPOTHESIS_TO_VERDICT[hypothesis]


def hypothesis_label(verdict: Verdict) -> str:
    """Return the display label of the hypothesis matching ``verdict``."""
    return _VERDICT_TO_LABEL[verdict]


def _intro_for(verdict: Verdict, config: PipelineConfig) -> str:
    """Return the configured reasoning intro paragraph for a verdict."""
    return {
        Verdict.ORIGINAL: config.reasoning_intro_original,
        Verdict.AI_EDITED: config.reasoning_intro_edited,
        Verdict.AI_GENERATED: config.reasoning_intro_generated,
    }[verdict]


def _reason(classification: ClassificationResult, config: PipelineConfig) -> str:
    """Compose a deterministic human-readable decision reason."""
    verdict = _HYPOTHESIS_TO_VERDICT[classification.winner]
    label = _VERDICT_TO_LABEL[verdict]
    return (
        f"{_intro_for(verdict, config)} Classified as {label} with "
        f"{classification.confidence:.0%} certainty (margin "
        f"{classification.margin:.0%} over its runner-up)."
    )


def make_decision(
    normalized,
    config: PipelineConfig,
    total_capacity: int,
) -> FusionDecision:
    """Classify ``normalized`` signals into the final decision."""
    classification = compute_classification(
        normalized, config, total_capacity=total_capacity
    )
    risk_level = config.risk_for(classification.verdict, classification.confidence)
    return FusionDecision(
        verdict=classification.verdict,
        confidence=classification.confidence,
        risk_level=risk_level,
        reason=_reason(classification, config),
        hypothesis_scores=(
            classification.scores.original,
            classification.scores.edited,
            classification.scores.generated,
        ),
        runner_up_verdict=_HYPOTHESIS_TO_VERDICT[classification.runner_up],
        classification_margin=classification.margin,
        detector_contributions=classification.detector_contributions,
    )

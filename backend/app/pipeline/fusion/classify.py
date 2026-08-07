"""Three-class forensic classification engine.

This module builds the decision the rest of the application consumes. It answers
*"which hypothesis does the detector evidence most strongly support?"* rather
than *"how manipulated is the image?"*.

The flow is fully deterministic:

    1. **accumulate** — every normalized detector signal contributes a soft
       amount of evidence to each of the three hypotheses through the
       contribution matrix (``hypotheses.GaussianResponse``).
    2. **normalize** — the raw hypothesis totals are mapped to probabilities that
       sum to ``1`` (when any evidence exists).
    3. **rank** — the winning hypothesis, its runner-up and the classification
       margin (winner minus runner-up probability) are derived.
    4. **confidence** — a calibrated blend of margin, detector agreement, winning
       separation, active-detector coverage and detector reliability.

Nothing here touches HTTP, the database, detectors or heatmaps. It is a pure,
deterministic function of its inputs plus configuration.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from app.core.enums import Verdict
from app.pipeline.config import PipelineConfig

from .hypotheses import (
    HYPOTHESES,
    GaussianResponse,
    Hypothesis,
    HypothesisScores,
    build_response,
)
from .normalize import NormalizedSignal, clamp01

_HYPOTHESIS_TO_VERDICT = {
    Hypothesis.ORIGINAL: Verdict.ORIGINAL,
    Hypothesis.AI_EDITED: Verdict.AI_EDITED,
    Hypothesis.AI_GENERATED: Verdict.AI_GENERATED,
}


@dataclass(frozen=True)
class DetectorHypothesisContribution:
    """A single detector's support allocation across the three hypotheses.

    ``weights`` holds this detector's (already weighted) share across
    ``HYPOTHESES`` summing to ``1.0`` when the detector contributed nothing else;
    ``preferred`` is the hypothesis the detector most supports.
    """

    detector: str
    weights: tuple[float, float, float]
    normalized_score: float

    @property
    def preferred(self) -> Hypothesis:
        """The hypothesis this detector most strongly supports."""
        return HYPOTHESES[max(range(3), key=lambda i: self.weights[i])]

    def share_of(self, hypothesis: Hypothesis) -> float:
        """Return this detector's normalized support for ``hypothesis``."""
        return self.weights[hypothesis]


@dataclass(frozen=True)
class ClassificationResult:
    """The normalized, ranked outcome of the three-class classifier."""

    scores: HypothesisScores  # probabilities summing to ~1
    winner: Hypothesis
    runner_up: Hypothesis
    winner_score: float
    runner_up_score: float
    margin: float
    agreement: float  # fraction of detectors sharing the winning hypothesis
    coverage: float  # fraction of intended detectors that ran
    reliability: float  # weighted mean detector self-confidence
    confidence: float
    detector_contributions: list[DetectorHypothesisContribution] = field(
        default_factory=list
    )

    @property
    def verdict(self) -> Verdict:
        """The winning hypothesis as the public verdict enum."""
        return _HYPOTHESIS_TO_VERDICT[self.winner]


def _evaluate_response(
    signals: Sequence[NormalizedSignal],
    response: GaussianResponse,
    config: PipelineConfig,
) -> tuple[HypothesisScores, list[DetectorHypothesisContribution]]:
    """Accumulate per-detector evidence into per-hypothesis raw totals.

    Returns the raw (unnormalized) totals and the per-detector contribution list.
    """
    totals = {h: 0.0 for h in HYPOTHESES}
    detector_rows: list[DetectorHypothesisContribution] = []

    for signal in signals:
        weights = config.contribution_weights_for(signal.detector)
        row: list[float] = []
        for h in HYPOTHESES:
            support = weights[h] * response.support(signal.score, h)
            contribution = support * signal.reliability * signal.confidence
            totals[h] += contribution
            row.append(contribution)
        # Normalize each detector row so its weights read as a percentage even
        # when hypothesis totals differ in scale at the per-signal level.
        row_total = sum(row) or 0.0
        normalized_row = tuple((v / row_total) if row_total else 0.0 for v in row)
        detector_rows.append(
            DetectorHypothesisContribution(
                detector=signal.detector,
                weights=normalized_row,
                normalized_score=signal.score,
            )
        )

    return HypothesisScores(
        original=totals[Hypothesis.ORIGINAL],
        edited=totals[Hypothesis.AI_EDITED],
        generated=totals[Hypothesis.AI_GENERATED],
    ), detector_rows


def _probabilify(raw: HypothesisScores) -> HypothesisScores:
    """Normalize the raw hypothesis totals into probabilities summing to 1."""
    total = raw.original + raw.edited + raw.generated
    if total <= 0.0:
        return HypothesisScores(0.0, 0.0, 0.0)
    return HypothesisScores(
        raw.original / total,
        raw.edited / total,
        raw.generated / total,
    )


def _rank(
    scores: HypothesisScores,
) -> tuple[Hypothesis, Hypothesis, float, float, float]:
    """Return (winner, runner_up, winner_score, runner_up_score, margin)."""
    ordered = sorted(HYPOTHESES, key=lambda h: scores[h], reverse=True)
    winner, runner = ordered[0], ordered[1]
    return (
        winner,
        runner,
        scores[winner],
        scores[runner],
        scores[winner] - scores[runner],
    )


def _agreement(
    detector_rows: Sequence[DetectorHypothesisContribution], winner: Hypothesis
) -> float:
    """Fraction of active detectors whose preferred hypothesis matches ``winner``."""
    if not detector_rows:
        return 0.0
    agree = sum(1 for c in detector_rows if c.preferred is winner)
    return agree / len(detector_rows)


def _separation(winner_score: float, runner_up_score: float) -> float:
    """How dominant the winner is over the runner-up, scaled into ``[0, 1]``.

    ``0.0`` when the two leaders tie; ``1.0`` when the winner holds all evidence.
    """
    spread = max(1e-9, winner_score + runner_up_score)
    return (winner_score - runner_up_score) / spread


def compute_classification(
    signals: Sequence[NormalizedSignal],
    config: PipelineConfig,
    total_capacity: int,
) -> ClassificationResult:
    """Run the deterministic three-class classifier over ``signals``.

    ``total_capacity`` is how many detectors the pipeline intended to run; it
    drives the coverage factor of the confidence model. No signals yields a
    degenerate result whose confidence is ``0.0`` and verdict is ORIGINAL.
    """
    response = build_response(config)
    raw, detector_rows = _evaluate_response(signals, response, config)
    scores = _probabilify(raw)
    winner, runner, winner_score, runner_score, margin = _rank(scores)

    if not signals or (scores.original + scores.edited + scores.generated) == 0.0:
        return ClassificationResult(
            scores=scores,
            winner=Hypothesis.ORIGINAL,
            runner_up=Hypothesis.AI_EDITED,
            winner_score=0.0,
            runner_up_score=0.0,
            margin=0.0,
            agreement=0.0,
            coverage=0.0,
            reliability=0.0,
            confidence=0.0,
            detector_contributions=detector_rows,
        )

    agreement = _agreement(detector_rows, winner)
    separation = _separation(winner_score, runner_score)
    coverage = clamp01(len(signals) / total_capacity) if total_capacity else 0.0
    reliability = _weighted_reliability(signals)
    confidence = _compute_confidence(
        config=config,
        margin=margin,
        agreement=agreement,
        separation=separation,
        coverage=coverage,
        reliability=reliability,
    )

    return ClassificationResult(
        scores=scores,
        winner=winner,
        runner_up=runner,
        winner_score=winner_score,
        runner_up_score=runner_score,
        margin=margin,
        agreement=agreement,
        coverage=coverage,
        reliability=reliability,
        confidence=confidence,
        detector_contributions=detector_rows,
    )


def _weighted_reliability(
    signals: Sequence[NormalizedSignal],
) -> float:
    """Weighted mean of the detectors' self-assessed confidence."""
    total = sum(s.reliability for s in signals) or 0.0
    if total <= 0.0:
        return 0.0
    return clamp01(sum(s.reliability * s.confidence for s in signals) / total)


def _compute_confidence(
    *,
    config: PipelineConfig,
    margin: float,
    agreement: float,
    separation: float,
    coverage: float,
    reliability: float,
) -> float:
    """Blend the classification factors into a single ``[0, 1]`` confidence."""
    weight_sum = config.classification_weight_sum() or 1.0
    blended = (
        config.classification_margin_weight * margin
        + config.classification_agreement_weight * agreement
        + config.classification_separation_weight * separation
        + config.classification_coverage_weight * coverage
        + config.classification_reliability_weight * reliability
    )
    return round(clamp01(blended / weight_sum), 4)

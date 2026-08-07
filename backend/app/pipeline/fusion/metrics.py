"""Fusion aggregation metrics.

This module holds the small, pure mathematics that turn a set of normalized
detector signals into the scalar values the decision layer consumes:

* **manipulation** — the reliability-weighted mean of the normalized scores;
  it represents "how manipulated is the image" on ``[0, 1]`` (``0`` clean,
  ``1`` synthetic).
* **agreement** — how consistently the detectors point the same direction,
  ``1`` when they fully agree, ``0`` when they contradict. Derived from the
  weighted standard deviation of the scores.
* **decisiveness** — how far the weighted manipulation is from the ambiguous
  midpoint ``0.5``; ``1`` for an unambiguous clean/synthetic reading, ``0`` for
  a perfectly ambiguous one.
* **coverage** — the fraction of the detectors the pipeline intends to run that
  actually produced a usable signal.
* **reliability** — the weighted mean of the detectors' own self-confidence.

Every formula is anonymous and depends only on the inputs, so the metrics are
reproducible and easy to audit.
"""

from __future__ import annotations

from dataclasses import dataclass

from .normalize import NormalizedSignal, clamp01


@dataclass(frozen=True)
class FusionMetrics:
    """The scalar aggregation of a set of normalized signals."""

    manipulation: float
    agreement: float
    decisiveness: float
    coverage: float
    reliability: float
    active_count: int
    intended_count: int


def _weighted_stats(  # noqa: ANN202
    signals: list[NormalizedSignal],
) -> tuple[float, float, float, float]:
    """Return (total_weight, mean, std, weighted_mean_confidence)."""
    total_weight = sum(s.reliability for s in signals) or 0.0
    if not signals or total_weight == 0.0:
        return 0.0, 0.0, 0.0, 0.0

    mean = sum(s.reliability * s.score for s in signals) / total_weight
    variance = (
        sum(s.reliability * (s.score - mean) ** 2 for s in signals) / total_weight
    )
    std = variance**0.5
    confidence = sum(s.reliability * s.confidence for s in signals) / total_weight
    return total_weight, mean, std, confidence


def compute_metrics(
    signals: list[NormalizedSignal], total_capacity: int
) -> FusionMetrics:
    """Aggregate ``signals`` into :class:`FusionMetrics`.

    ``total_capacity`` is the number of detectors the pipeline intends to run;
    it drives the coverage factor.
    """
    total_weight, _, std, confidence = _weighted_stats(signals)
    active_count = len(signals)

    if active_count == 0 or total_weight == 0.0:
        return FusionMetrics(
            manipulation=0.0,
            agreement=1.0,
            decisiveness=0.0,
            coverage=0.0,
            reliability=0.0,
            active_count=0,
            intended_count=total_capacity,
        )

    manipulation = sum(s.reliability * s.score for s in signals) / total_weight
    # Scores live in [0, 1] so the weighted standard deviation is at most 0.5;
    # scaling by 2 maps that maximum spread onto agreement == 0.
    agreement = clamp01(1.0 - 2.0 * std)
    decisiveness = abs(2.0 * manipulation - 1.0)
    coverage = clamp01(active_count / total_capacity) if total_capacity else 0.0
    reliability = confidence

    return FusionMetrics(
        manipulation=manipulation,
        agreement=agreement,
        decisiveness=decisiveness,
        coverage=coverage,
        reliability=reliability,
        active_count=active_count,
        intended_count=total_capacity,
    )

"""Detector contributions and evidence aggregation.

This module exposes *why* the final decision was reached:

* :class:`DetectorContribution` records, per detector, its normalized score,
  confidence, configured weight, its *share* of the total active weight, and how
  much of the fused manipulation evidence it explains (``contribution``). This
  is the per-detector attribution used for explainability and UI. Each
  contribution also carries the detector's three-class hypothesis allocation
  (``hypothesis_weights``) and the hypothesis it most preferred
  (``preferred_hypothesis``).
* :meth:`aggregate_evidence` merges the detectors' evidence into a single,
  deduplicated list, sorts it by contribution importance (strongest first) and
  preserves each item's detector source. No detector evidence is lost; identical
  text emitted by multiple detectors collapses to one entry.
"""

from __future__ import annotations

from collections.abc import Sequence

from app.pipeline.fusion.base import DetectorContribution
from app.pipeline.fusion.classify import DetectorHypothesisContribution
from app.pipeline.fusion.hypotheses import Hypothesis, hypothesis_label

from .normalize import NormalizedSignal

_HYPOTHESIS_ORDER = (
    Hypothesis.ORIGINAL,
    Hypothesis.AI_GENERATED,
)


def _direction(score: float, support_threshold: float) -> str:
    """Classify a detector signal as supporting manipulation or an original."""
    if score >= support_threshold:
        return "supports:manipulation"
    if score <= 1.0 - support_threshold:
        return "supports:original"
    return "supports:neutral"


def _preferred_hypothesis(weights: tuple[float, float]) -> Hypothesis:
    """Return the hypothesis with the largest allocation."""
    return _HYPOTHESIS_ORDER[max(range(2), key=lambda i: weights[i])]


def build_contributions(
    signals: list[NormalizedSignal],
    support_threshold: float,
    hypothesis_rows: Sequence[DetectorHypothesisContribution] | None = None,
) -> list[DetectorContribution]:
    """Rank each detector's contribution to the fused manipulation evidence.

    Returns contributions ordered by descending absolute importance so the head
    of the list is always the most influential detector. When ``hypothesis_rows``
    is provided (matching ``signals`` in order), each contribution is enriched
    with the detector's two-class hypothesis allocation.
    """
    total_weight = sum(s.reliability for s in signals) or 0.0
    total_manipulation = sum(s.reliability * s.score for s in signals) or 0.0

    hypothesis_by_detector = {row.detector: row for row in (hypothesis_rows or ())}

    contributions: list[DetectorContribution] = []
    for s in signals:
        weight_share = (s.reliability / total_weight) if total_weight else 0.0
        contribution = (
            (weight_share * s.score / total_manipulation) if total_manipulation else 0.0
        )
        row = hypothesis_by_detector.get(s.detector)
        weights = row.weights if row else (0.0, 0.0)
        preferred = _preferred_hypothesis(weights) if row else Hypothesis.ORIGINAL
        contributions.append(
            DetectorContribution(
                detector=s.detector,
                detector_version=s.detector_version,
                category=s.category,
                normalized_score=s.score,
                detector_confidence=s.confidence,
                reliability=s.reliability,
                weight_share=weight_share,
                contribution=contribution,
                direction=_direction(s.score, support_threshold),
                hypothesis_weights=weights,
                preferred_hypothesis=hypothesis_label(preferred),
            )
        )
    contributions.sort(
        key=lambda c: (abs(c.contribution), abs(c.normalized_score)),
        reverse=True,
    )
    return contributions


def aggregate_evidence(
    signals: list[NormalizedSignal],
    contributions: list[DetectorContribution],
) -> list[str]:
    """Merge detector evidence into one deduplicated, importance-ordered list.

    Each entry preserves its detector source as a ``"<detector> — ..."`` prefix.
    Duplicate lines (across or within detectors) collapse into a single entry;
    the strongest contributing detector appears first.
    """
    order = {c.detector: i for i, c in enumerate(contributions)}
    entries: dict[str, str] = {}
    for s in signals:
        for line in s.evidence:
            text = line.strip()
            if not text:
                continue
            key = text.casefold()
            if key in entries:
                continue
            entries[key] = f"{s.detector} — {text}"

    # Rank by detector importance (stable within one detector's lines).
    ranked = sorted(
        entries.items(),
        key=lambda item: order.get(item[1].split(" — ", 1)[0], 0),
    )
    return [text for _, text in ranked]

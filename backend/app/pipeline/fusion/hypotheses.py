"""Forensic hypotheses and the contribution matrix.

A detector never decides the verdict. Instead every detector signal is mapped,
through a *contribution matrix*, onto the three competing forensic hypotheses:

    ORIGINAL, AI_EDITED, AI_GENERATED

The matrix is configuration-driven (see ``PipelineConfig.classifier_*``) and
anchors the whole classifier: it tells us how strongly a detector *naturally*
supports each hypothesis given the score it measured. By keeping this in one
place we avoid scattering hand-written rules across the engine and let operators
recalibrate the classifier without changing code.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import IntEnum
from typing import NamedTuple

from app.pipeline.config import PipelineConfig


class Hypothesis(IntEnum):
    """The three mutually-exclusive forensic classes, in display order.

    Using an :class:`IntEnum` keeps opinions out of the code; the numeric values
    only order tuple positions that mirror :data:`HYPOTHESES`.
    """

    ORIGINAL = 0
    AI_EDITED = 1
    AI_GENERATED = 2


HYPOTHESES: tuple[Hypothesis, ...] = (
    Hypothesis.ORIGINAL,
    Hypothesis.AI_EDITED,
    Hypothesis.AI_GENERATED,
)

_HYPOTHESIS_LABELS = {
    Hypothesis.ORIGINAL: "Original",
    Hypothesis.AI_EDITED: "AI Edited",
    Hypothesis.AI_GENERATED: "AI Generated",
}


def hypothesis_label(hypothesis: Hypothesis) -> str:
    """Return the human-readable label for a hypothesis."""
    return _HYPOTHESIS_LABELS[hypothesis]


class HypothesisScores(NamedTuple):
    """The three raw support totals for one set of signals, pre-normalization."""

    original: float = 0.0
    edited: float = 0.0
    generated: float = 0.0

    def __getitem__(self, hypothesis: Hypothesis) -> float:  # type: ignore[override]
        return (self.original, self.edited, self.generated)[hypothesis]

    def as_dict(self) -> dict[str, float]:
        """Return the scores keyed by hypothesis label."""
        return {
            "original": self.original,
            "edited": self.edited,
            "generated": self.generated,
        }


@dataclass(frozen=True)
class GaussianResponse:
    """Configuration for a per-hypothesis soft response curve.

    A signal with normalized ``score`` supports a hypothesis ``h`` according to a
    Gaussian centred on that hypothesis's ``center``:

        response = exp(-(score - center)^2 / (2 * resolution^2))

    This yields a deterministic, smooth amount of evidence for *every*
    hypothesis — never a hard threshold — so a single reading can support a
    primary hypothesis while still weakly supporting the others.
    """

    centers: tuple[float, float, float]
    resolution: float

    def support(self, score: float, hypothesis: Hypothesis) -> float:
        """Return this hypothesis's evidence strength for ``score`` in ``[0, 1]``."""
        center = self.centers[hypothesis]
        distance_sq = (score - center) ** 2
        denom = 2.0 * self.resolution * self.resolution
        return math.exp(-distance_sq / denom) if denom else 0.0


def build_response(config: PipelineConfig) -> GaussianResponse:
    """Construct the configured response curves for the classifier."""
    centers = config.classifier_centers()
    return GaussianResponse(
        centers=(centers[0], centers[1], centers[2]),
        resolution=max(1e-6, config.classifier_resolution),
    )

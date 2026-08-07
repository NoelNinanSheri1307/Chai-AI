"""Detector signal normalization.

Detectors are free to report their measurements on any numeric scale. Before any
fusion math happens, every :class:`DetectorSignal` is mapped onto a single,
shared vocabulary:

* **normalized score** — a manipulation likelihood in ``[0, 1]`` (``0.0`` is a
  fully clean/photo-like reading, ``1.0`` is an unambiguous synthetic/manipulated
  reading). Every detector in this pipeline already emits its score in that range
  via calibrated threshold bands, so normalization deterministically clamps the
  raw score into the unit interval and records it verbatim.
* **detector confidence** — the detector's own self-assessed reliability in
  ``[0, 1]`` (clamped).
* **reliability** — the operator-configured weight for this detector, taken from
  ``PipelineConfig`` and used as the aggregation weight.

Normalization is a pure, stateless function: the same signal always yields the
same :class:`NormalizedSignal`, which is what keeps the whole engine
deterministic.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.core.enums import ScoreCategory
from app.pipeline.signals import DetectorSignal


def clamp01(value: float) -> float:
    """Clamp a float into the closed unit interval ``[0, 1]``."""
    return max(0.0, min(1.0, value))


@dataclass(frozen=True)
class NormalizedSignal:
    """A detector signal mapped onto the shared fusion vocabulary."""

    detector: str
    detector_version: str
    category: ScoreCategory
    score: float  # manipulation likelihood in [0, 1]
    confidence: float  # detector self-confidence in [0, 1]
    reliability: float  # configured fusion weight (>= 0)
    evidence: tuple[str, ...] = field(default_factory=tuple)


def normalize_signal(
    signal: DetectorSignal, reliability: float | None
) -> NormalizedSignal:
    """Normalize a single detector signal deterministically.

    ``reliability`` is the operator-configured weight for this detector
    (``None``/unknown falls back to ``1.0``); it is not modified here.
    """
    return NormalizedSignal(
        detector=signal.detector_name,
        detector_version=signal.detector_version,
        category=signal.category,
        score=clamp01(signal.score),
        confidence=clamp01(signal.confidence),
        reliability=1.0 if reliability is None else max(0.0, reliability),
        evidence=tuple(signal.evidence),
    )

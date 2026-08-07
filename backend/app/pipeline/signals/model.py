"""Strongly-typed internal signal objects.

Detectors never communicate through ad-hoc dictionaries. Every detector run
produces a :class:`DetectorSignal` carrying its measured score, its own
confidence, human-readable evidence, machine metadata, processing time, the
detector version — so downstream stages (fusion, evidence, explanation) operate
on a single, stable, typed contract — and, optionally, a set of localized
:class:`SpatialRegion` rectangles describing *where* manipulation was detected.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.core.enums import ScoreCategory
from app.pipeline.base import IndicatorResult


@dataclass(frozen=True)
class SpatialRegion:
    """A normalized manipulation rectangle located within the image.

    Coordinates and dimensions are normalized to ``[0, 1]`` so they can be drawn
    directly over any image size. ``confidence`` is the detector's localized
    manipulation estimate in ``[0, 1]``; ``severity`` is the detector's strength
    label (``low`` | ``moderate`` | ``strong``). ``detector`` records which
    detector produced the region (for attribution).
    """

    x: float
    y: float
    width: float
    height: float
    confidence: float = 0.0
    severity: str = "moderate"
    label: str = ""
    detector: str = ""

    @property
    def area(self) -> float:
        """Return the normalized area of the region (``width * height``)."""
        return self.width * self.height


@dataclass(frozen=True)
class DetectorHealth:
    """Health status reported by a detector."""

    status: str  # one of: ok | degraded | unavailable
    version: str
    detail: str

    @property
    def is_healthy(self) -> bool:
        """Whether the detector is available for execution."""
        return self.status == "ok"


@dataclass(frozen=True)
class DetectorSignal:
    """The typed output of a single detector execution."""

    detector_name: str
    detector_version: str
    category: ScoreCategory
    score: float
    confidence: float
    evidence: list[str] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)
    processing_time_ms: int = 0
    indicators: list[IndicatorResult] = field(default_factory=list)
    regions: tuple[SpatialRegion, ...] = field(default_factory=tuple)

"""Strongly-typed internal signal objects.

Detectors never communicate through ad-hoc dictionaries. Every detector run
produces a :class:`DetectorSignal` carrying its measured score, its own
confidence, human-readable evidence, machine metadata, processing time and the
detector version — so downstream stages (fusion, evidence, explanation) operate
on a single, stable, typed contract.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.core.enums import ScoreCategory
from app.pipeline.base import IndicatorResult


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

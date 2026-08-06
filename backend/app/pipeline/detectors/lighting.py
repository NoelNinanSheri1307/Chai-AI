"""Lighting-consistency detector placeholder."""

from __future__ import annotations

from app.core.enums import ScoreCategory
from app.pipeline.detectors.base import Detector
from app.pipeline.signals import DetectorSignal


class LightingDetector(Detector):
    """Placeholder lighting/shadow-consistency detector.

    Returns a deterministic mock signal; no photometric analysis is performed.
    """

    name = "lighting"
    version = "0.1.0"
    _capabilities = frozenset({"lighting", "photometry"})

    def execute(
        self,
        image_bytes: bytes,
        *,
        content_type: str | None = None,
        file_name: str | None = None,
    ) -> DetectorSignal:
        return DetectorSignal(
            detector_name=self.name,
            detector_version=self.version,
            category=ScoreCategory.LIGHTING,
            score=0.55,
            confidence=0.75,
            evidence=["Placeholder: lighting consistency is mildly anomalous."],
            metadata={"scope": "lighting", "mode": "placeholder"},
            processing_time_ms=4,
        )

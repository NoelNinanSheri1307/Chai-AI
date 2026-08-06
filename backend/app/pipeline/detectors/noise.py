"""Sensor-noise detector placeholder."""

from __future__ import annotations

from app.core.enums import ScoreCategory
from app.pipeline.detectors.base import Detector
from app.pipeline.signals import DetectorSignal


class NoiseDetector(Detector):
    """Placeholder sensor-noise (PRNU) detector.

    Returns a deterministic mock signal; no noise residual is computed.
    """

    name = "noise"
    version = "0.1.0"
    _capabilities = frozenset({"noise", "prnu", "sensor"})

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
            category=ScoreCategory.NOISE_PATTERN,
            score=0.12,
            confidence=0.8,
            evidence=["Placeholder: noise profile reads clean."],
            metadata={"scope": "noise", "mode": "placeholder"},
            processing_time_ms=5,
        )

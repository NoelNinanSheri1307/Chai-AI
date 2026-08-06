"""Texture-anomaly detector placeholder."""

from __future__ import annotations

from app.core.enums import ScoreCategory
from app.pipeline.detectors.base import Detector
from app.pipeline.signals import DetectorSignal


class TextureDetector(Detector):
    """Placeholder texture-anomaly detector.

    Returns a deterministic mock signal; no texture statistics are computed.
    """

    name = "texture"
    version = "0.1.0"
    _capabilities = frozenset({"texture", "wavelet"})

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
            category=ScoreCategory.TEXTURE,
            score=0.83,
            confidence=0.92,
            evidence=["Placeholder: texture homogeneity is low."],
            metadata={"scope": "texture", "mode": "placeholder"},
            processing_time_ms=6,
        )

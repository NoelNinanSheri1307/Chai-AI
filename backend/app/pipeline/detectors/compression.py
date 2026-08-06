"""Compression-block detector placeholder."""

from __future__ import annotations

from app.core.enums import IndicatorSeverity, IndicatorType, ScoreCategory
from app.pipeline.base import IndicatorResult
from app.pipeline.detectors.base import Detector
from app.pipeline.signals import DetectorSignal


class CompressionDetector(Detector):
    """Placeholder compression/blocking detector.

    Returns a deterministic mock signal; no block-grid analysis is performed.
    """

    name = "compression"
    version = "0.1.0"
    _capabilities = frozenset({"compression", "blocking"})

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
            category=ScoreCategory.EDGE_CONSISTENCY,
            score=0.68,
            confidence=0.85,
            evidence=["Placeholder: compression-block consistency is elevated."],
            metadata={"scope": "compression", "mode": "placeholder"},
            processing_time_ms=6,
            indicators=[
                IndicatorResult(
                    type=IndicatorType.COMPRESSION,
                    confidence=0.72,
                    severity=IndicatorSeverity.MODERATE,
                    description=(
                        "Spectral anomalies consistent with upscaled synthetic content."
                    ),
                )
            ],
        )

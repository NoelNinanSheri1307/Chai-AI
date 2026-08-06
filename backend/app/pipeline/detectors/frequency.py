"""Frequency analysis detector placeholder."""

from __future__ import annotations

from app.core.enums import IndicatorSeverity, IndicatorType, ScoreCategory
from app.pipeline.base import IndicatorResult
from app.pipeline.detectors.base import Detector
from app.pipeline.signals import DetectorSignal


class FrequencyDetector(Detector):
    """Placeholder FFT/frequency-domain detector.

    Returns a deterministic mock signal; no transform is actually computed.
    """

    name = "frequency"
    version = "0.1.0"
    _capabilities = frozenset({"frequency", "fft"})

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
            category=ScoreCategory.FREQUENCY,
            score=0.77,
            confidence=0.9,
            evidence=["Placeholder: frequency profile suggests synthetic content."],
            metadata={"scope": "frequency", "mode": "placeholder"},
            processing_time_ms=6,
            indicators=[
                IndicatorResult(
                    type=IndicatorType.DIFFUSION,
                    confidence=0.94,
                    severity=IndicatorSeverity.STRONG,
                    description=(
                        "Soft, watercolor-like artifacts consistent with diffusion "
                        "synthesis."
                    ),
                )
            ],
        )

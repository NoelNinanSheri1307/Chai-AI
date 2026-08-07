"""Error-level analysis (ELA) detector implementation."""

from __future__ import annotations

import io
import time

import numpy as np
from PIL import Image, ImageChops

from app.core.enums import IndicatorSeverity, IndicatorType, ScoreCategory
from app.pipeline.base import IndicatorResult
from app.pipeline.detectors.base import Detector
from app.pipeline.signals import DetectorHealth, DetectorSignal


class ELADetector(Detector):
    """Error-level analysis (ELA) detector.

    Saves the image at a known JPEG quality, computes the difference image,
    and analyzes brightness differences to identify digital manipulation indicators.
    """

    name = "ela"
    version = "0.1.0"
    _capabilities = frozenset({"ela", "compression_artifacts"})

    def execute(
        self,
        image_bytes: bytes,
        *,
        content_type: str | None = None,
        file_name: str | None = None,
    ) -> DetectorSignal:
        """Run the ELA detector over image_bytes and return a DetectorSignal."""
        start_time = time.perf_counter()

        try:
            original = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        except Exception:
            processing_time_ms = max(1, int((time.perf_counter() - start_time) * 1000))
            return DetectorSignal(
                detector_name=self.name,
                detector_version=self.version,
                category=ScoreCategory.COMPRESSION,
                score=0.40,
                confidence=0.50,
                evidence=["Failed to parse image for Error Level Analysis."],
                metadata={"scope": "ela", "error": "Invalid image bytes"},
                processing_time_ms=processing_time_ms,
            )

        # 1. Save compressed version in memory
        buffer = io.BytesIO()
        original.save(buffer, "JPEG", quality=90)
        buffer.seek(0)
        compressed = Image.open(buffer)

        # 2. Compute absolute difference between original and compressed versions
        ela_image = ImageChops.difference(original, compressed)

        # 3. Convert to numpy and compute mean brightness
        ela_array = np.array(ela_image)
        mean_brightness = float(np.mean(ela_array))

        # 4. Map mean brightness to risk score and metadata
        # (Legacy thresholds: <5 -> 0.15; <15 -> 0.40; <30 -> 0.65; >=30 -> 0.85)
        indicators = []
        if mean_brightness < 5:
            score = 0.15
            confidence = 0.90
            evidence = [
                "Error Level Analysis shows low, uniform compression error "
                "consistent with an original image."
            ]
        elif mean_brightness < 15:
            score = 0.40
            confidence = 0.85
            evidence = [
                "Error Level Analysis reveals minor anomalies in compression "
                "block boundaries."
            ]
        elif mean_brightness < 30:
            score = 0.65
            confidence = 0.85
            evidence = [
                "Error Level Analysis shows moderate variations in compression "
                "error, indicating potential local edits."
            ]
            indicators.append(
                IndicatorResult(
                    type=IndicatorType.COMPRESSION,
                    confidence=score,
                    severity=IndicatorSeverity.MODERATE,
                    description="Local compression block irregularities "
                    "detected via ELA.",
                )
            )
        else:
            score = 0.85
            confidence = 0.90
            evidence = [
                "Error Level Analysis indicates high compression difference, "
                "strongly suggesting tampering/local re-saving."
            ]
            indicators.append(
                IndicatorResult(
                    type=IndicatorType.COMPRESSION,
                    confidence=score,
                    severity=IndicatorSeverity.STRONG,
                    description="Significant compression block mismatch "
                    "detected via ELA.",
                )
            )

        processing_time_ms = max(1, int((time.perf_counter() - start_time) * 1000))

        return DetectorSignal(
            detector_name=self.name,
            detector_version=self.version,
            category=ScoreCategory.COMPRESSION,
            score=score,
            confidence=confidence,
            evidence=evidence,
            metadata={
                "scope": "ela",
                "mean_brightness": f"{mean_brightness:.4f}",
            },
            processing_time_ms=processing_time_ms,
            indicators=indicators,
        )

    def health(self) -> DetectorHealth:
        """Return the detector's current health status."""
        return DetectorHealth(
            status="ok",
            version=self.version,
            detail="available",
        )

    def capabilities(self) -> frozenset[str]:
        """Return the capabilities this detector provides."""
        return self._capabilities

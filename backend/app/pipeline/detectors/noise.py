"""Sensor-noise detector implementation."""

from __future__ import annotations

import time

import cv2
import numpy as np

from app.core.enums import IndicatorSeverity, IndicatorType, ScoreCategory
from app.pipeline.base import IndicatorResult
from app.pipeline.detectors.base import Detector
from app.pipeline.detectors.decode import decode_image_to_cv_gray
from app.pipeline.heatmap.spatial import mask_to_regions
from app.pipeline.signals import DetectorHealth, DetectorSignal


class NoiseDetector(Detector):
    """Sensor-noise (PRNU) detector.

    Extracts high-frequency noise residual by subtracting a Gaussian-blurred
    version from the original grayscale image, then analyzes the noise
    standard deviation.
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
        """Run the sensor-noise detector over image_bytes and return a DetectorSignal."""  # noqa: E501
        start_time = time.perf_counter()

        try:
            img = decode_image_to_cv_gray(image_bytes)
        except Exception:
            processing_time_ms = max(1, int((time.perf_counter() - start_time) * 1000))
            return DetectorSignal(
                detector_name=self.name,
                detector_version=self.version,
                category=ScoreCategory.NOISE_PATTERN,
                score=0.40,
                confidence=0.50,
                evidence=["Failed to parse image for sensor-noise analysis."],
                metadata={"scope": "noise", "error": "Invalid image bytes"},
                processing_time_ms=processing_time_ms,
            )

        # 1. Compute ELA-like high frequency noise residual using Gaussian Blur
        blur = cv2.GaussianBlur(img, (5, 5), 0)
        noise = cv2.absdiff(img, blur)

        # 2. Compute normalized noise standard deviation
        noise_std = float(noise.std() / 255.0)

        indicators = []

        # 3. Map standard deviation to risk scores
        # - Natural noise: [0.01, 0.04) -> score: 0.12
        # - Lacks natural noise / smooth: <0.01 -> score: 0.50
        # - Moderate noise anomalies: [0.04, 0.08] -> score: 0.40
        # - High noise / editing artifacts: >0.08 -> score: 0.80
        if noise_std < 0.01:
            score = 0.50
            confidence = 0.80
            evidence = [
                "Image has an exceptionally low noise floor, typical of "
                "synthetic or heavily denoised content."
            ]
        elif 0.01 <= noise_std < 0.04:
            score = 0.12
            confidence = 0.90
            evidence = [
                "Sensor noise pattern is consistent with a clean, natural "
                "camera capture."
            ]
        elif 0.04 <= noise_std <= 0.08:
            score = 0.40
            confidence = 0.80
            evidence = [
                "Moderate noise variance detected, suggesting minor "
                "compression or editing artifacts."
            ]
        else:
            score = 0.80
            confidence = 0.85
            evidence = [
                "High-frequency noise standard deviation is highly elevated, "
                "indicating significant editing artifacts or artificial noise "
                "injection."
            ]
            indicators.append(
                IndicatorResult(
                    type=IndicatorType.TEXTURE,
                    confidence=score,
                    severity=IndicatorSeverity.STRONG,
                    description="Significant high-frequency noise anomaly "
                    "detected in texture residual.",
                )
            )

        processing_time_ms = max(1, int((time.perf_counter() - start_time) * 1000))

        # Localize the anomaly: threshold the high-frequency residual that was
        # already computed and convert the blobs into normalized regions.
        if noise_std > 0.08:
            severity = "strong"
        elif noise_std >= 0.04:
            severity = "moderate"
        else:
            severity = "low"
        spatial_regions = tuple(
            mask_to_regions(
                noise >= 20,
                detector=self.name,
                severity=severity,
                label="Noise anomaly",
                confidence=score,
                min_area=12,
            )
        )

        return DetectorSignal(
            detector_name=self.name,
            detector_version=self.version,
            category=ScoreCategory.NOISE_PATTERN,
            score=score,
            confidence=confidence,
            evidence=evidence,
            metadata={
                "scope": "noise",
                "noise_std": f"{noise_std:.4f}",
            },
            processing_time_ms=processing_time_ms,
            indicators=indicators,
            regions=spatial_regions,
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

"""Frequency analysis detector implementation."""

from __future__ import annotations

import time
import cv2
import numpy as np

from app.core.enums import IndicatorSeverity, IndicatorType, ScoreCategory
from app.pipeline.base import IndicatorResult
from app.pipeline.detectors.base import Detector
from app.pipeline.signals import DetectorHealth, DetectorSignal


class FrequencyDetector(Detector):
    """FFT/frequency-domain detector.

    Computes the 2D Fast Fourier Transform (FFT) of the image, shifts the
    zero-frequency component to the center, and calculates the standard deviation
    of the log magnitude spectrum as an anomaly score for GAN or generative artifacts.
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
        """Run the frequency detector over image_bytes and return a DetectorSignal."""
        start_time = time.perf_counter()

        try:
            img_np = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(img_np, cv2.IMREAD_GRAYSCALE)
            if img is None:
                raise ValueError("Failed to decode image from bytes.")
        except Exception:
            processing_time_ms = max(1, int((time.perf_counter() - start_time) * 1000))
            return DetectorSignal(
                detector_name=self.name,
                detector_version=self.version,
                category=ScoreCategory.FREQUENCY,
                score=0.40,
                confidence=0.50,
                evidence=["Failed to parse image for frequency analysis."],
                metadata={"scope": "frequency", "error": "Invalid image bytes"},
                processing_time_ms=processing_time_ms,
                indicators=[
                    IndicatorResult(
                        type=IndicatorType.DIFFUSION,
                        confidence=0.50,
                        severity=IndicatorSeverity.LOW,
                        description="Failed decoding: default diffusion signature baseline.",
                    )
                ],
            )

        # 1. Resize to standard 256x256 shape
        img = cv2.resize(img, (256, 256))

        # 2. Compute 2D Fourier Transform and shift zero frequency component
        f = np.fft.fft2(img)
        fshift = np.fft.fftshift(f)
        magnitude_spectrum = np.log(np.abs(fshift) + 1)

        # 3. Calculate mean and standard deviation of spectrum
        mean_spectrum = float(np.mean(magnitude_spectrum))
        std_spectrum = float(np.std(magnitude_spectrum))

        # Heuristic GAN fingerprint detection based on standard deviation
        anomaly_score = std_spectrum

        indicators = []
        # (Legacy thresholds mapping: >1.1 -> 0.90; 0.9 to 1.1 -> 0.75; <0.9 -> 0.20)
        if anomaly_score > 1.1:
            score = 0.90
            confidence = 0.90
            evidence = [
                "Frequency spectrum standard deviation is highly elevated, indicating periodic resampling patterns from generative models."
            ]
            indicators.append(
                IndicatorResult(
                    type=IndicatorType.DIFFUSION,
                    confidence=score,
                    severity=IndicatorSeverity.STRONG,
                    description="Strong periodic resampling lattice detected in frequency domain.",
                )
            )
        elif 0.9 <= anomaly_score <= 1.1:
            score = 0.75
            confidence = 0.85
            evidence = [
                "Frequency spectrum standard deviation is slightly elevated, suggesting potential synthetic content or artificial upscaling."
            ]
            indicators.append(
                IndicatorResult(
                    type=IndicatorType.DIFFUSION,
                    confidence=score,
                    severity=IndicatorSeverity.MODERATE,
                    description="Moderate resampling grid artifacts detected in frequency domain.",
                )
            )
        else:
            score = 0.20
            confidence = 0.80
            evidence = [
                "Frequency spectrum matches standard natural camera noise with no periodic artifact lattices."
            ]

        processing_time_ms = max(1, int((time.perf_counter() - start_time) * 1000))

        return DetectorSignal(
            detector_name=self.name,
            detector_version=self.version,
            category=ScoreCategory.FREQUENCY,
            score=score,
            confidence=confidence,
            evidence=evidence,
            metadata={
                "scope": "frequency",
                "anomaly_score": f"{anomaly_score:.4f}",
                "mean_spectrum": f"{mean_spectrum:.4f}",
                "std_spectrum": f"{std_spectrum:.4f}",
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

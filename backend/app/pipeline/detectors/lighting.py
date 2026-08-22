"""Lighting-consistency detector implementation."""

from __future__ import annotations

import time

import cv2
import numpy as np

from app.core.enums import IndicatorSeverity, IndicatorType, ScoreCategory
from app.pipeline.base import IndicatorResult
from app.pipeline.detectors.base import Detector
from app.pipeline.detectors.decode import decode_image_to_cv_gray
from app.pipeline.signals import DetectorHealth, DetectorSignal, SpatialRegion


class LightingDetector(Detector):
    """Lighting/shadow-consistency detector.

    Splits the image into quadrants, computes the dominant light-gradient
    direction in each quadrant via Sobel filters, and measures the angular
    dispersion.  Consistent natural lighting yields low dispersion; spliced
    composites or AI-generated images with contradictory illumination show
    high dispersion.
    """

    name = "lighting"
    version = "0.1.0"
    _capabilities = frozenset({"lighting", "photometry"})

    _NUM_DIVISIONS = 2  # 2×2 = 4 quadrants

    def execute(
        self,
        image_bytes: bytes,
        *,
        content_type: str | None = None,
        file_name: str | None = None,
    ) -> DetectorSignal:
        """Run the lighting detector over image_bytes and return a DetectorSignal."""
        start_time = time.perf_counter()

        try:
            img = decode_image_to_cv_gray(image_bytes)
        except Exception:
            processing_time_ms = max(1, int((time.perf_counter() - start_time) * 1000))
            return DetectorSignal(
                detector_name=self.name,
                detector_version=self.version,
                category=ScoreCategory.LIGHTING,
                score=0.40,
                confidence=0.50,
                evidence=["Failed to parse image for lighting analysis."],
                metadata={"scope": "lighting", "error": "Invalid image bytes"},
                processing_time_ms=processing_time_ms,
            )

        # 1. Resize to canonical size
        img = cv2.resize(img, (256, 256))

        # 2. Compute Sobel gradients over the whole image
        gx = cv2.Sobel(img, cv2.CV_64F, 1, 0, ksize=3)
        gy = cv2.Sobel(img, cv2.CV_64F, 0, 1, ksize=3)

        # 3. Per-quadrant dominant gradient direction
        h, w = img.shape
        n = self._NUM_DIVISIONS
        qh, qw = h // n, w // n

        angles: list[float] = []
        for row in range(n):
            for col in range(n):
                y0, y1 = row * qh, (row + 1) * qh
                x0, x1 = col * qw, (col + 1) * qw
                mean_gx = float(gx[y0:y1, x0:x1].mean())
                mean_gy = float(gy[y0:y1, x0:x1].mean())
                angle = float(np.arctan2(mean_gy, mean_gx))
                angles.append(angle)

        # 4. Compute circular standard deviation of the angles
        # Using circular statistics: R = |mean of unit vectors|
        sin_sum = sum(np.sin(a) for a in angles)
        cos_sum = sum(np.cos(a) for a in angles)
        r_bar = np.sqrt(sin_sum**2 + cos_sum**2) / len(angles)
        # Circular std: sqrt(-2 * ln(R_bar)), clamped for numerical safety
        r_bar_clamped = max(r_bar, 1e-6)
        circ_std = float(np.sqrt(-2.0 * np.log(r_bar_clamped)))

        indicators: list[IndicatorResult] = []

        # 5. Map circular standard deviation to risk score
        # Low dispersion  -> consistent lighting -> natural
        # High dispersion -> contradictory illumination -> edited/synthetic
        if circ_std < 0.5:
            score = 0.10
            confidence = 0.90
            evidence = [
                "Light-gradient direction is highly consistent across all "
                "image quadrants, indicating uniform natural illumination."
            ]
        elif circ_std < 1.0:
            score = 0.35
            confidence = 0.80
            evidence = [
                "Minor lighting-direction variation detected across quadrants, "
                "within normal photographic range."
            ]
        elif circ_std < 1.5:
            score = 0.65
            confidence = 0.80
            evidence = [
                "Moderate lighting-direction inconsistency across image "
                "quadrants, suggesting possible compositing or local edits."
            ]
            indicators.append(
                IndicatorResult(
                    type=IndicatorType.LIGHTING,
                    confidence=score,
                    severity=IndicatorSeverity.MODERATE,
                    description=(
                        "Quadrant illumination gradients diverge moderately, "
                        "hinting at composited lighting."
                    ),
                )
            )
        else:
            score = 0.85
            confidence = 0.90
            evidence = [
                "Lighting-gradient directions are strongly contradictory "
                "across image quadrants, indicating composited or synthetic "
                "illumination."
            ]
            indicators.append(
                IndicatorResult(
                    type=IndicatorType.LIGHTING,
                    confidence=score,
                    severity=IndicatorSeverity.STRONG,
                    description=(
                        "Quadrant illumination gradients are strongly "
                        "contradictory — inconsistent with a single light source."
                    ),
                )
            )

        processing_time_ms = max(1, int((time.perf_counter() - start_time) * 1000))

        # Localize illumination inconsistencies: when lighting directions
        # diverge, attribute each image quadrant as a potential manipulation
        # area (coarse, whole-quadrant boxes).
        severity = (
            "strong" if score >= 0.85 else ("moderate" if score >= 0.65 else "low")
        )
        spacing = 1.0 / self._NUM_DIVISIONS
        spatial_regions = tuple(
            SpatialRegion(
                x=col * spacing,
                y=row * spacing,
                width=spacing,
                height=spacing,
                confidence=score,
                severity=severity,
                label="Lighting inconsistency",
                detector=self.name,
            )
            for row in range(self._NUM_DIVISIONS)
            for col in range(self._NUM_DIVISIONS)
            if circ_std >= 1.0
        )

        return DetectorSignal(
            detector_name=self.name,
            detector_version=self.version,
            category=ScoreCategory.LIGHTING,
            score=score,
            confidence=confidence,
            evidence=evidence,
            metadata={
                "scope": "lighting",
                "circular_std": f"{circ_std:.4f}",
                "r_bar": f"{r_bar:.4f}",
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

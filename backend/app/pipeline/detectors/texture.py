"""Texture-anomaly detector implementation."""

from __future__ import annotations

import time

import cv2
import numpy as np

from app.core.enums import IndicatorSeverity, IndicatorType, ScoreCategory
from app.pipeline.base import IndicatorResult
from app.pipeline.detectors.base import Detector
from app.pipeline.detectors.decode import decode_image_to_cv_gray
from app.pipeline.signals import DetectorHealth, DetectorSignal, SpatialRegion


class TextureDetector(Detector):
    """Texture-anomaly detector.

    Divides the image into local patches and computes per-patch Laplacian
    variance (a standard texture sharpness measure).  The coefficient of
    variation across patches reveals whether texture detail degrades in
    specific regions while staying sharp elsewhere — a hallmark of
    AI-generated or locally edited imagery.
    """

    name = "texture"
    version = "0.1.0"
    _capabilities = frozenset({"texture", "wavelet"})

    _PATCH_SIZE = 32  # Non-overlapping patch side length

    def execute(
        self,
        image_bytes: bytes,
        *,
        content_type: str | None = None,
        file_name: str | None = None,
    ) -> DetectorSignal:
        """Run the texture detector over image_bytes and return a DetectorSignal."""
        start_time = time.perf_counter()

        try:
            img = decode_image_to_cv_gray(image_bytes)
        except Exception:
            processing_time_ms = max(1, int((time.perf_counter() - start_time) * 1000))
            return DetectorSignal(
                detector_name=self.name,
                detector_version=self.version,
                category=ScoreCategory.TEXTURE,
                score=0.40,
                confidence=0.50,
                evidence=["Failed to parse image for texture analysis."],
                metadata={"scope": "texture", "error": "Invalid image bytes"},
                processing_time_ms=processing_time_ms,
            )

        # 1. Resize to a canonical size so patch count is stable
        img = cv2.resize(img, (256, 256))

        # 2. Compute per-patch Laplacian variance
        patch_variances = []
        cells: list[tuple[int, int]] = []
        ps = self._PATCH_SIZE
        for y in range(0, img.shape[0], ps):
            for x in range(0, img.shape[1], ps):
                patch = img[y : y + ps, x : x + ps]
                if patch.shape[0] < ps or patch.shape[1] < ps:
                    continue
                lap = cv2.Laplacian(patch, cv2.CV_64F)
                patch_variances.append(float(lap.var()))
                cells.append((x, y))

        if not patch_variances:
            processing_time_ms = max(1, int((time.perf_counter() - start_time) * 1000))
            return DetectorSignal(
                detector_name=self.name,
                detector_version=self.version,
                category=ScoreCategory.TEXTURE,
                score=0.40,
                confidence=0.50,
                evidence=["Image too small for patch-based texture analysis."],
                metadata={"scope": "texture", "error": "Insufficient patches"},
                processing_time_ms=processing_time_ms,
            )

        mean_var = float(np.mean(patch_variances))
        std_var = float(np.std(patch_variances))
        # Coefficient of variation: how unevenly texture is distributed
        cv = std_var / (mean_var + 1e-6)

        indicators: list[IndicatorResult] = []

        # 3. Map coefficient of variation to risk score
        # Low CV  -> uniform texture -> likely synthetic / AI-generated
        # Mid CV  -> natural variation
        # High CV -> patches differ wildly -> local edits or splicing
        if cv < 0.3:
            score = 0.75
            confidence = 0.85
            evidence = [
                "Texture sharpness is unusually uniform across all regions, "
                "consistent with synthetic or diffusion-generated content."
            ]
            indicators.append(
                IndicatorResult(
                    type=IndicatorType.TEXTURE,
                    confidence=score,
                    severity=IndicatorSeverity.MODERATE,
                    description=(
                        "Texture detail is uniformly distributed — typical of "
                        "AI-generated imagery lacking natural sensor variation."
                    ),
                )
            )
        elif cv < 0.8:
            score = 0.15
            confidence = 0.90
            evidence = [
                "Texture variation across image regions is consistent with "
                "natural photographic content."
            ]
        elif cv < 1.2:
            score = 0.55
            confidence = 0.80
            evidence = [
                "Moderate texture inconsistency detected between image regions, "
                "suggesting possible local edits."
            ]
        else:
            score = 0.83
            confidence = 0.90
            evidence = [
                "Texture detail degrades sharply in specific regions while "
                "staying crisp elsewhere, indicating local manipulation."
            ]
            indicators.append(
                IndicatorResult(
                    type=IndicatorType.TEXTURE,
                    confidence=score,
                    severity=IndicatorSeverity.STRONG,
                    description=(
                        "Texture detail degrades in specific regions while "
                        "staying sharp elsewhere."
                    ),
                )
            )

        processing_time_ms = max(1, int((time.perf_counter() - start_time) * 1000))

        # Localize the anomaly: mark patches whose texture variance deviates
        # sharply from the image mean (localized over- or under-detailed areas).
        if cv >= 1.2:
            severity = "strong"
        elif cv >= 0.8:
            severity = "moderate"
        else:
            severity = "low"
        deviation = 1.0 * max(std_var, 1e-3)
        cell = self._PATCH_SIZE / 256.0
        spatial_regions = tuple(
            SpatialRegion(
                x=x / 256.0,
                y=y / 256.0,
                width=cell,
                height=cell,
                confidence=score,
                severity=severity,
                label="Texture anomaly",
                detector=self.name,
            )
            for (x, y), var in zip(cells, patch_variances, strict=True)
            if abs(var - mean_var) > deviation
        )

        return DetectorSignal(
            detector_name=self.name,
            detector_version=self.version,
            category=ScoreCategory.TEXTURE,
            score=score,
            confidence=confidence,
            evidence=evidence,
            metadata={
                "scope": "texture",
                "mean_laplacian_var": f"{mean_var:.4f}",
                "std_laplacian_var": f"{std_var:.4f}",
                "coeff_of_variation": f"{cv:.4f}",
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

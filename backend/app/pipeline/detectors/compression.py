"""Compression-block and edge-consistency detector implementation."""

from __future__ import annotations

import time

import cv2
import numpy as np

from app.core.enums import IndicatorSeverity, IndicatorType, ScoreCategory
from app.pipeline.base import IndicatorResult
from app.pipeline.detectors.base import Detector
from app.pipeline.detectors.decode import decode_image_to_cv_bgr
from app.pipeline.heatmap.spatial import normalize_pixel_box
from app.pipeline.signals import DetectorHealth, DetectorSignal, SpatialRegion


class CompressionDetector(Detector):
    """Compression-block and edge-consistency detector.

    Extracts high-frequency details using a Laplacian filter to map noise,
    thresholds the map, and counts bounding regions of local edge inconsistencies
    (tamper blocks) to calculate a compression consistency risk score.
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
        """Run the compression detector over image_bytes and return a DetectorSignal."""
        start_time = time.perf_counter()

        try:
            img = decode_image_to_cv_bgr(image_bytes)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        except Exception:
            processing_time_ms = max(1, int((time.perf_counter() - start_time) * 1000))
            return DetectorSignal(
                detector_name=self.name,
                detector_version=self.version,
                category=ScoreCategory.EDGE_CONSISTENCY,
                score=0.40,
                confidence=0.50,
                evidence=["Failed to parse image for compression block analysis."],
                metadata={"scope": "compression", "error": "Invalid image bytes"},
                processing_time_ms=processing_time_ms,
            )

        # 1. Laplacian high-frequency edge/noise mapping
        noise_map = cv2.Laplacian(gray, cv2.CV_64F)
        noise_map = np.absolute(noise_map)

        # 2. Binary thresholding (threshold = 30)
        _, mask = cv2.threshold(
            noise_map.astype(np.uint8),
            30,
            255,
            cv2.THRESH_BINARY,
        )

        # 3. Contour detection and bounding box grouping
        contours, _ = cv2.findContours(
            mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
        )

        # 4. Filter contours to extract significant inconsistent regions (area > 100)
        regions = []
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            if w * h > 100:
                regions.append([int(x), int(y), int(w), int(h)])

        tamper_count = len(regions)
        indicators = []

        # 5. Map regional block anomalies to risk scores
        if tamper_count == 0:
            score = 0.10
            confidence = 0.90
            evidence = [
                "Edge and block boundary analysis shows high compression "
                "consistency throughout the image."
            ]
        elif 1 <= tamper_count <= 2:
            score = 0.35
            confidence = 0.80
            evidence = [
                f"Slight edge inconsistencies found in {tamper_count} local "
                "compression blocks."
            ]
        elif 3 <= tamper_count <= 5:
            score = 0.68
            confidence = 0.85
            evidence = [
                f"Moderate compression block boundary mismatches detected across "
                f"{tamper_count} regions."
            ]
            indicators.append(
                IndicatorResult(
                    type=IndicatorType.COMPRESSION,
                    confidence=score,
                    severity=IndicatorSeverity.MODERATE,
                    description=f"Local compression boundaries show {tamper_count} "
                    "edge anomalies.",
                )
            )
        else:
            score = 0.88
            confidence = 0.90
            evidence = [
                f"High density of compression edge inconsistencies found across "
                f"{tamper_count} distinct regions."
            ]
            indicators.append(
                IndicatorResult(
                    type=IndicatorType.COMPRESSION,
                    confidence=score,
                    severity=IndicatorSeverity.STRONG,
                    description=f"High density of compression block mismatch "
                    f"regions ({tamper_count} counts).",
                )
            )

        processing_time_ms = max(1, int((time.perf_counter() - start_time) * 1000))

        severity = "strong" if tamper_count >= 6 else "moderate"
        image_height, image_width = gray.shape[:2]
        spatial_regions = tuple(
            SpatialRegion(
                *normalize_pixel_box(x, y, w, h, image_width, image_height),
                confidence=score,
                severity=severity,
                label="Compression block",
                detector=self.name,
            )
            for x, y, w, h in regions
        )

        return DetectorSignal(
            detector_name=self.name,
            detector_version=self.version,
            category=ScoreCategory.EDGE_CONSISTENCY,
            score=score,
            confidence=confidence,
            evidence=evidence,
            metadata={
                "scope": "compression",
                "tamper_blocks_count": str(tamper_count),
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

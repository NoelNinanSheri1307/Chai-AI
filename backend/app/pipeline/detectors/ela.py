"""Error-level analysis (ELA) detector placeholder."""

from __future__ import annotations

from app.core.enums import ScoreCategory
from app.pipeline.detectors.base import Detector
from app.pipeline.signals import DetectorSignal


class ELADetector(Detector):
    """Placeholder error-level analysis detector.

    Returns a deterministic mock signal; no JPEG re-compression or diffing is
    performed.
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
        return DetectorSignal(
            detector_name=self.name,
            detector_version=self.version,
            category=ScoreCategory.COMPRESSION,
            score=0.71,
            confidence=0.85,
            evidence=["Placeholder: error-level analysis raised a compression flag."],
            metadata={"scope": "ela", "mode": "placeholder"},
            processing_time_ms=7,
        )

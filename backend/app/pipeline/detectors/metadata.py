"""Metadata detector placeholder."""

from __future__ import annotations

from app.core.enums import ScoreCategory
from app.pipeline.detectors.base import Detector
from app.pipeline.signals import DetectorSignal


class MetadataDetector(Detector):
    """Placeholder metadata-consistency detector.

    Returns a deterministic mock signal; no EXIF/metadata parsing is performed.
    """

    name = "metadata"
    version = "0.1.0"
    _capabilities = frozenset({"metadata", "exif"})

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
            category=ScoreCategory.METADATA,
            score=0.64,
            confidence=0.9,
            evidence=[
                "Placeholder: metadata consistency check returned a neutral signal."
            ],
            metadata={"scope": "metadata", "mode": "placeholder"},
            processing_time_ms=4,
        )

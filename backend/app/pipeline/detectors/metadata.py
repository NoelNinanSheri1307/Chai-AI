"""Metadata forensic detector implementation."""

from __future__ import annotations

import io
import time

from PIL import Image
from PIL.ExifTags import TAGS

from app.core.enums import IndicatorSeverity, IndicatorType, ScoreCategory
from app.pipeline.base import IndicatorResult
from app.pipeline.detectors.base import Detector
from app.pipeline.detectors.decode import decode_image_to_pil
from app.pipeline.signals import DetectorHealth, DetectorSignal


class MetadataDetector(Detector):
    """Metadata-consistency detector.

    Extracts EXIF metadata from the image and runs a forensic logic
    to compute an authenticity risk score.
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
        """Run the metadata detector over image_bytes and return a DetectorSignal."""
        start_time = time.perf_counter()

        # 1. Load image and try to parse EXIF
        try:
            image = decode_image_to_pil(image_bytes)
            exif_data = image._getexif() if hasattr(image, "_getexif") else None
        except Exception:
            processing_time_ms = max(1, int((time.perf_counter() - start_time) * 1000))
            return DetectorSignal(
                detector_name=self.name,
                detector_version=self.version,
                category=ScoreCategory.METADATA,
                score=0.40,
                confidence=0.60,
                evidence=["Failed to parse image or extract EXIF metadata."],
                metadata={
                    "Format": "Unknown",
                    "File size": f"{len(image_bytes)} bytes",
                    "Camera": "Unknown",
                    "Software": "None",
                },
                processing_time_ms=processing_time_ms,
            )

        # Basic image properties from PIL
        width, height = image.size
        resolution = f"{width} × {height}"
        img_format = image.format if image.format else "Unknown"
        file_size_mb = len(image_bytes) / (1024 * 1024)
        file_size_str = (
            f"{file_size_mb:.2f} MB"
            if file_size_mb >= 0.1
            else f"{len(image_bytes) / 1024:.1f} KB"
        )

        metadata_dict = {
            "Resolution": resolution,
            "Format": img_format,
            "File size": file_size_str,
            "Camera": "Unknown",
            "Software": "None",
        }

        if not exif_data:
            processing_time_ms = max(1, int((time.perf_counter() - start_time) * 1000))
            return DetectorSignal(
                detector_name=self.name,
                detector_version=self.version,
                category=ScoreCategory.METADATA,
                score=0.40,
                confidence=0.80,
                evidence=["No EXIF metadata was found in the image."],
                metadata=metadata_dict,
                processing_time_ms=processing_time_ms,
            )

        # Parse EXIF tags
        exif_tags = {}
        for tag_id, value in exif_data.items():
            tag = TAGS.get(tag_id, tag_id)
            if tag:
                exif_tags[str(tag)] = value

        # Retrieve relevant EXIF values
        make = str(exif_tags.get("Make", "")).strip()
        model = str(exif_tags.get("Model", "")).strip()
        software = str(exif_tags.get("Software", "")).strip()
        image_desc = str(exif_tags.get("ImageDescription", "")).strip()

        # Update metadata dict with extracted values
        if make or model:
            if make and model:
                if make.lower() in model.lower():
                    metadata_dict["Camera"] = model
                else:
                    metadata_dict["Camera"] = f"{make} {model}"
            else:
                metadata_dict["Camera"] = model or make

        if software:
            metadata_dict["Software"] = software

        # Extract standard optional EXIF fields for downstream visibility
        for clean_tag in ["DateTime", "DateTimeOriginal", "LensModel", "Copyright"]:
            if clean_tag in exif_tags:
                metadata_dict[clean_tag] = str(exif_tags[clean_tag])

        make_lower = make.lower()
        model_lower = model.lower()
        software_lower = software.lower()
        image_desc_lower = image_desc.lower()

        indicators = []

        # 2. Forensic scoring algorithm (extracted from legacy codebase)
        if make_lower and model_lower:
            # 🔵 Strong camera metadata
            score = 0.05
            confidence = 0.95
            evidence = [f"Valid camera metadata present: {metadata_dict['Camera']}."]
        elif "photoshop" in software_lower or "gimp" in software_lower:
            # 🔴 Suspicious software/editing pipeline
            score = 0.75
            confidence = 0.90
            evidence = [f"Software metadata indicates editing pipeline: {software}."]
            indicators.append(
                IndicatorResult(
                    type=IndicatorType.METADATA,
                    confidence=0.90,
                    severity=IndicatorSeverity.MODERATE,
                    description=f"Editing software signature detected: {software}.",
                )
            )
        elif (
            "artificial intelligence" in image_desc_lower
            or "generated by ai" in image_desc_lower
        ):
            # 🔴 AI provenance/keywords detected
            score = 0.85
            confidence = 0.95
            evidence = [f"AI keyword found in image description: '{image_desc}'."]
            indicators.append(
                IndicatorResult(
                    type=IndicatorType.METADATA,
                    confidence=0.95,
                    severity=IndicatorSeverity.STRONG,
                    description="AI generation signature found in description.",
                )
            )
        else:
            # Neutral case
            score = 0.20
            confidence = 0.80
            evidence = [
                "Metadata lacks standard camera markers but shows no signs of "
                "editing software or AI provenance."
            ]

        processing_time_ms = max(1, int((time.perf_counter() - start_time) * 1000))

        return DetectorSignal(
            detector_name=self.name,
            detector_version=self.version,
            category=ScoreCategory.METADATA,
            score=score,
            confidence=confidence,
            evidence=evidence,
            metadata=metadata_dict,
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

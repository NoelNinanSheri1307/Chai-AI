"""Detector framework: the abstract detector contract and its placeholders.

Detectors are the forensic "eyes" of the pipeline. Each exposes its ``name`` and
``version`` (for the versioning trail), a ``health()`` check, a set of
``capabilities()`` and an ``execute()`` that returns a strongly-typed
:class:`DetectorSignal`.

The concrete implementations shipped here are deterministic placeholders: they
perform no image analysis and only exist so the framework is fully exercisable.
The real detectors arrive in a later milestone and plug into this interface
without any pipeline changes.
"""

from app.pipeline.detectors.base import Detector
from app.pipeline.detectors.compression import CompressionDetector
from app.pipeline.detectors.decode import (
    ImageDecodeError,
    decode_image_to_cv_bgr,
    decode_image_to_cv_gray,
    decode_image_to_cv_rgb,
    decode_image_to_pil,
)
from app.pipeline.detectors.ela import ELADetector
from app.pipeline.detectors.frequency import FrequencyDetector
from app.pipeline.detectors.lighting import LightingDetector
from app.pipeline.detectors.metadata import MetadataDetector
from app.pipeline.detectors.noise import NoiseDetector
from app.pipeline.detectors.texture import TextureDetector

__all__ = [
    "CompressionDetector",
    "Detector",
    "ELADetector",
    "FrequencyDetector",
    "ImageDecodeError",
    "LightingDetector",
    "MetadataDetector",
    "NoiseDetector",
    "TextureDetector",
    "decode_image_to_cv_bgr",
    "decode_image_to_cv_gray",
    "decode_image_to_cv_rgb",
    "decode_image_to_pil",
]


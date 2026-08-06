"""Detector registry: config-driven selection of detector implementations.

The registry maps detector ``name`` → implementation class. The pipeline runner
builds its detector set from ``PipelineConfig.detector_order``, so enabling,
disabling or reordering detectors never requires touching the pipeline code.
Registering a new detector is a single entry here plus its module.
"""

from __future__ import annotations

from collections.abc import Sequence

from app.pipeline.detectors.base import Detector
from app.pipeline.detectors.compression import CompressionDetector
from app.pipeline.detectors.ela import ELADetector
from app.pipeline.detectors.frequency import FrequencyDetector
from app.pipeline.detectors.lighting import LightingDetector
from app.pipeline.detectors.metadata import MetadataDetector
from app.pipeline.detectors.noise import NoiseDetector
from app.pipeline.detectors.texture import TextureDetector

_REGISTRY: dict[str, type[Detector]] = {
    detector.name: detector
    for detector in (
        MetadataDetector,
        FrequencyDetector,
        ELADetector,
        NoiseDetector,
        CompressionDetector,
        TextureDetector,
        LightingDetector,
    )
}


def registered_detector_names() -> tuple[str, ...]:
    """Return every detector name known to the registry."""
    return tuple(_REGISTRY)


def build_detectors(enabled_names: Sequence[str]) -> list[Detector]:
    """Instantiate the detectors whose names are in ``enabled_names``.

    Unknown names are skipped so stale configuration never breaks the pipeline.
    """
    return [_REGISTRY[name]() for name in enabled_names if name in _REGISTRY]

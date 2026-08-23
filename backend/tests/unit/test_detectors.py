"""Tests for the detector framework and its placeholder implementations."""

from __future__ import annotations

import pytest

from app.core.enums import ScoreCategory
from app.pipeline.detectors import (
    CompressionDetector,
    ELADetector,
    FrequencyDetector,
    LightingDetector,
    MetadataDetector,
    NoiseDetector,
    TextureDetector,
)
from app.pipeline.detectors.base import Detector
from app.pipeline.detectors.registry import build_detectors, registered_detector_names
from app.pipeline.signals import DetectorSignal
from tests.sample_images import JPEG_BYTES

ALL_PLACEHOLDER_DETECTORS = [
    MetadataDetector,
    FrequencyDetector,
    ELADetector,
    NoiseDetector,
    CompressionDetector,
    TextureDetector,
    LightingDetector,
]

EXPECTED_CATEGORY_BY_NAME = {
    "metadata": ScoreCategory.METADATA,
    "frequency": ScoreCategory.FREQUENCY,
    "ela": ScoreCategory.COMPRESSION,
    "noise": ScoreCategory.NOISE_PATTERN,
    "compression": ScoreCategory.EDGE_CONSISTENCY,
    "texture": ScoreCategory.TEXTURE,
    "lighting": ScoreCategory.LIGHTING,
}


def test_all_placeholder_detectors_are_registered() -> None:
    assert registered_detector_names() == tuple(
        "metadata, frequency, ela, noise, compression, texture, lighting".split(", ")
    )


def test_registry_builds_detector_instances() -> None:
    detectors = build_detectors(registered_detector_names())
    assert len(detectors) == 7
    assert all(isinstance(detector, Detector) for detector in detectors)


def test_registry_skips_unknown_names() -> None:
    detectors = build_detectors(["metadata", "unknown", "texture"])
    assert [detector.name for detector in detectors] == ["metadata", "texture"]


@pytest.mark.parametrize("detector_cls", ALL_PLACEHOLDER_DETECTORS)
def test_each_detector_exposes_the_framework_contract(detector_cls: type) -> None:
    detector: Detector = detector_cls()
    assert detector.name
    assert detector.version
    assert detector.health().is_healthy
    assert detector.capabilities()

    signal = detector.execute(JPEG_BYTES, content_type="image/jpeg")
    assert isinstance(signal, DetectorSignal)
    assert signal.detector_name == detector.name
    assert signal.detector_version == detector.version
    assert 0.0 <= signal.score <= 1.0
    assert 0.0 <= signal.confidence <= 1.0
    assert signal.evidence


@pytest.mark.parametrize("detector_cls", ALL_PLACEHOLDER_DETECTORS)
def test_each_detector_maps_to_expected_category(detector_cls: type) -> None:
    detector: Detector = detector_cls()
    signal = detector.execute(JPEG_BYTES, content_type="image/jpeg")
    assert signal.category == EXPECTED_CATEGORY_BY_NAME[detector.name]


@pytest.mark.parametrize("detector_cls", ALL_PLACEHOLDER_DETECTORS)
def test_detector_output_is_deterministic(detector_cls: type) -> None:
    detector: Detector = detector_cls()
    first = detector.execute(JPEG_BYTES, content_type="image/jpeg")
    second = detector.execute(JPEG_BYTES, content_type="image/jpeg")
    assert first.detector_name == second.detector_name
    assert first.category == second.category
    assert first.score == second.score
    assert first.confidence == second.confidence
    assert first.indicators == second.indicators
    assert first.regions == second.regions


def test_frequency_detector_emits_indicators() -> None:
    signal = FrequencyDetector().execute(JPEG_BYTES, content_type="image/jpeg")
    assert signal.indicators
    assert signal.indicators[0].type.value == "diffusion"

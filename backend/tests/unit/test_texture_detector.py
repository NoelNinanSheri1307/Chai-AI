"""Unit tests for the concrete TextureDetector implementation."""

from __future__ import annotations

import io

import cv2
import numpy as np
from PIL import Image

from app.core.enums import IndicatorSeverity, IndicatorType, ScoreCategory
from app.pipeline.detectors.texture import TextureDetector
from app.pipeline.signals import DetectorSignal


def test_texture_detector_invalid_bytes() -> None:
    """Invalid image bytes produce fallback score of 0.40."""
    detector = TextureDetector()
    signal = detector.execute(b"not_an_image_file")

    assert isinstance(signal, DetectorSignal)
    assert signal.score == 0.40
    assert signal.confidence == 0.50
    assert "Failed to parse" in signal.evidence[0]
    assert signal.metadata["error"] == "Invalid image bytes"


def test_texture_detector_uniform_flat() -> None:
    """A solid-color image has zero Laplacian variance (CV ~ 0), scoring 0.75."""
    detector = TextureDetector()

    img = Image.new("L", (256, 256), color=128)
    buf = io.BytesIO()
    img.save(buf, format="PNG")

    signal = detector.execute(buf.getvalue())

    assert isinstance(signal, DetectorSignal)
    assert signal.category == ScoreCategory.TEXTURE
    assert signal.score == 0.75
    assert signal.confidence == 0.85
    assert float(signal.metadata["coeff_of_variation"]) < 0.3
    assert "unusually uniform" in signal.evidence[0]
    assert len(signal.indicators) == 1
    assert signal.indicators[0].type == IndicatorType.TEXTURE
    assert signal.indicators[0].severity == IndicatorSeverity.MODERATE


def test_texture_detector_natural_noise() -> None:
    """Moderate cross-region texture variation (photo-like) hits the natural band."""
    detector = TextureDetector()

    # Quadrant-dependent noise amplitude produces moderate, uneven texture (CV
    # in the mid range) rather than a flat (CV~0) or sharply spliced profile.
    rng = np.random.RandomState(123)
    img = np.zeros((256, 256), dtype=np.uint8)
    amps = [[30, 50], [70, 90]]
    for i in range(2):
        for j in range(2):
            amp = amps[i][j]
            img[i * 128 : (i + 1) * 128, j * 128 : (j + 1) * 128] = rng.randint(
                0, amp + 1, (128, 128), dtype=np.uint8
            )

    _, buf = cv2.imencode(".png", img)
    signal = detector.execute(buf.tobytes())

    assert isinstance(signal, DetectorSignal)
    assert signal.score == 0.15
    assert signal.confidence == 0.90
    assert "consistent with natural photographic content" in signal.evidence[0]
    assert len(signal.indicators) == 0


def test_texture_detector_spliced_regions() -> None:
    """A smooth image with a localized spliced noise patch has high CV (0.83)."""
    detector = TextureDetector()

    rng = np.random.RandomState(99)
    img = np.full((256, 256), 128, dtype=np.uint8)
    # A targeted, localized spliced patch of heavy noise over a mostly smooth
    # image drives the patch-variance CV well above the strong-manipulation band.
    col_start = 179
    img[:, col_start:] = rng.randint(0, 256, (256, 256 - col_start), dtype=np.uint8)

    _, buf = cv2.imencode(".png", img)
    signal = detector.execute(buf.tobytes())

    assert isinstance(signal, DetectorSignal)
    assert signal.score == 0.83
    assert signal.confidence == 0.90
    assert float(signal.metadata["coeff_of_variation"]) >= 1.2
    assert "degrades sharply" in signal.evidence[0]
    assert len(signal.indicators) == 1
    assert signal.indicators[0].type == IndicatorType.TEXTURE
    assert signal.indicators[0].severity == IndicatorSeverity.STRONG


def test_texture_detector_contract_details() -> None:
    """Verifies health, capabilities, name and version."""
    detector = TextureDetector()

    assert detector.name == "texture"
    assert detector.version == "0.1.0"
    assert detector.capabilities() == frozenset({"texture", "wavelet"})

    health = detector.health()
    assert health.status == "ok"
    assert health.version == "0.1.0"
    assert health.is_healthy

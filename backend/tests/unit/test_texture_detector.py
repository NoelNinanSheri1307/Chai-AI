"""Unit tests for the concrete TextureDetector implementation."""

from __future__ import annotations

import io
import cv2
import numpy as np
from PIL import Image, ImageDraw

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
    """A solid-color image has zero Laplacian variance everywhere (CV ~ 0), scoring 0.75 (synthetic)."""
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
    """Random noise has moderate, even variance across patches (mid-range CV), scoring 0.15."""
    detector = TextureDetector()

    rng = np.random.RandomState(42)
    noise = rng.randint(0, 256, (256, 256), dtype=np.uint8)
    _, buf = cv2.imencode(".png", noise)

    signal = detector.execute(buf.tobytes())

    assert isinstance(signal, DetectorSignal)
    assert signal.score == 0.15
    assert signal.confidence == 0.90
    assert "consistent with natural photographic content" in signal.evidence[0]
    assert len(signal.indicators) == 0


def test_texture_detector_spliced_regions() -> None:
    """An image with one half smooth and one half noisy has high CV, scoring 0.83 (local manipulation)."""
    detector = TextureDetector()

    rng = np.random.RandomState(99)
    img = np.zeros((256, 256), dtype=np.uint8)
    # Left half: flat
    img[:, :128] = 128
    # Right half: heavy random noise
    img[:, 128:] = rng.randint(0, 256, (256, 128), dtype=np.uint8)

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

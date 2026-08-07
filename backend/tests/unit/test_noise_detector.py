"""Unit tests for the concrete NoiseDetector implementation."""

from __future__ import annotations

import io

import cv2
import numpy as np
from PIL import Image

from app.core.enums import IndicatorSeverity, IndicatorType
from app.pipeline.detectors.noise import NoiseDetector
from app.pipeline.signals import DetectorSignal


def test_noise_detector_invalid_bytes() -> None:
    """Verifies that invalid image bytes result in fallback score of 0.40."""
    detector = NoiseDetector()
    invalid_bytes = b"not_an_image_file"

    signal = detector.execute(invalid_bytes)

    assert isinstance(signal, DetectorSignal)
    assert signal.score == 0.40
    assert signal.confidence == 0.50
    assert "Failed to parse" in signal.evidence[0]
    assert signal.metadata["error"] == "Invalid image bytes"


def test_noise_detector_flat_smooth() -> None:
    """A perfectly flat image has noise_std < 0.01, returning score of 0.50."""
    detector = NoiseDetector()

    # Flat image has zero high-frequency noise residual
    img = Image.new("L", (100, 100), color=128)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    solid_image_bytes = buf.getvalue()

    signal = detector.execute(solid_image_bytes)

    assert isinstance(signal, DetectorSignal)
    assert signal.score == 0.50
    assert signal.confidence == 0.80
    assert float(signal.metadata["noise_std"]) < 0.01
    assert "low noise floor" in signal.evidence[0]
    assert len(signal.indicators) == 0


def test_noise_detector_natural_noise() -> None:
    """Mild Gaussian noise sits in the natural band (0.01 <= noise_std < 0.04)."""
    detector = NoiseDetector()

    # Mild Gaussian noise (sigma ~12) leaves a small high-frequency residual
    # after the Gaussian-blur subtraction, landing in the natural-sensor band.
    rng = np.random.RandomState(7)
    noise = np.clip(rng.normal(128, 12, (100, 100)), 0, 255).astype(np.uint8)
    _, buf = cv2.imencode(".png", noise)
    natural_noise_bytes = buf.tobytes()

    signal = detector.execute(natural_noise_bytes)

    assert isinstance(signal, DetectorSignal)
    assert signal.score == 0.12
    assert signal.confidence == 0.90
    assert 0.01 <= float(signal.metadata["noise_std"]) < 0.04
    assert "consistent with a clean, natural camera capture" in signal.evidence[0]
    assert len(signal.indicators) == 0


def test_noise_detector_high_noise() -> None:
    """High noise variance (noise_std > 0.08) returns 0.80 and a strong indicator."""
    detector = NoiseDetector()

    # High uniform noise range [0, 256] has std of ~73.8. 73.8 / 255.0 = 0.29.
    noise = np.random.randint(0, 256, (100, 100), dtype=np.uint8)
    _, buf = cv2.imencode(".png", noise)
    high_noise_bytes = buf.tobytes()

    signal = detector.execute(high_noise_bytes)

    assert isinstance(signal, DetectorSignal)
    assert signal.score == 0.80
    assert signal.confidence == 0.85
    assert float(signal.metadata["noise_std"]) > 0.08
    assert "highly elevated" in signal.evidence[0]
    assert len(signal.indicators) == 1
    assert signal.indicators[0].type == IndicatorType.TEXTURE
    assert signal.indicators[0].severity == IndicatorSeverity.STRONG


def test_noise_detector_contract_details() -> None:
    """Verifies health, capabilities, name and version implementations."""
    detector = NoiseDetector()

    assert detector.name == "noise"
    assert detector.version == "0.1.0"
    assert detector.capabilities() == frozenset({"noise", "prnu", "sensor"})

    health = detector.health()
    assert health.status == "ok"
    assert health.version == "0.1.0"
    assert health.is_healthy

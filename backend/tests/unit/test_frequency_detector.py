"""Unit tests for the concrete FrequencyDetector implementation."""

from __future__ import annotations

import io
import cv2
import numpy as np
from PIL import Image

from app.core.enums import IndicatorSeverity, IndicatorType, ScoreCategory
from app.pipeline.detectors.frequency import FrequencyDetector
from app.pipeline.signals import DetectorSignal


def test_frequency_detector_invalid_bytes() -> None:
    """Verifies that invalid image bytes return fallback score of 0.40 and default indicators."""
    detector = FrequencyDetector()
    invalid_bytes = b"not_an_image_file"

    signal = detector.execute(invalid_bytes)

    assert isinstance(signal, DetectorSignal)
    assert signal.score == 0.40
    assert signal.confidence == 0.50
    assert "Failed to parse" in signal.evidence[0]
    assert signal.metadata["error"] == "Invalid image bytes"
    assert len(signal.indicators) == 1
    assert signal.indicators[0].type == IndicatorType.DIFFUSION


def test_frequency_detector_low_anomaly() -> None:
    """Verifies that a flat solid image has low frequency standard deviation, returning score of 0.20."""
    detector = FrequencyDetector()

    # Create solid gray image
    img = Image.new("L", (256, 256), color=128)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    solid_image_bytes = buf.getvalue()

    signal = detector.execute(solid_image_bytes)

    assert isinstance(signal, DetectorSignal)
    assert signal.score == 0.20
    assert signal.confidence == 0.80
    assert float(signal.metadata["anomaly_score"]) < 0.9
    assert "matches standard natural camera noise" in signal.evidence[0]
    assert len(signal.indicators) == 0


def test_frequency_detector_high_anomaly() -> None:
    """Verifies that a stripe pattern creates frequency spikes with high standard deviation, returning score of 0.90."""
    detector = FrequencyDetector()

    # Create image with clean high-contrast vertical stripe grating
    img = Image.new("L", (256, 256))
    pixels = img.load()
    for x in range(256):
        for y in range(256):
            if (x // 8) % 2 == 0:
                pixels[x, y] = 0
            else:
                pixels[x, y] = 255

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    grating_bytes = buf.getvalue()

    signal = detector.execute(grating_bytes)

    assert isinstance(signal, DetectorSignal)
    # Stripe grating creates sharp spikes in Fourier space leading to high standard deviation
    assert signal.score == 0.90
    assert signal.confidence == 0.90
    assert float(signal.metadata["anomaly_score"]) > 1.1
    assert "highly elevated" in signal.evidence[0]
    assert len(signal.indicators) == 1
    assert signal.indicators[0].type == IndicatorType.DIFFUSION
    assert signal.indicators[0].severity == IndicatorSeverity.STRONG


def test_frequency_detector_contract_details() -> None:
    """Verifies health, capabilities, name and version implementations."""
    detector = FrequencyDetector()

    assert detector.name == "frequency"
    assert detector.version == "0.1.0"
    assert detector.capabilities() == frozenset({"frequency", "fft"})
    
    health = detector.health()
    assert health.status == "ok"
    assert health.version == "0.1.0"
    assert health.is_healthy

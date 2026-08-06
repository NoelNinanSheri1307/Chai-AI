"""Unit tests for the concrete ELADetector implementation."""

from __future__ import annotations

import io
from PIL import Image

from app.core.enums import IndicatorSeverity, IndicatorType, ScoreCategory
from app.pipeline.detectors.ela import ELADetector
from app.pipeline.signals import DetectorSignal


def test_ela_detector_invalid_bytes() -> None:
    """Verifies that invalid image bytes result in fallback score of 0.40."""
    detector = ELADetector()
    invalid_bytes = b"not_an_image_file"

    signal = detector.execute(invalid_bytes)

    assert isinstance(signal, DetectorSignal)
    assert signal.score == 0.40
    assert signal.confidence == 0.50
    assert "Failed to parse" in signal.evidence[0]
    assert signal.metadata["error"] == "Invalid image bytes"


def test_ela_detector_low_brightness() -> None:
    """Verifies that a flat solid image has low ELA difference (brightness < 5), returning score of 0.15."""
    detector = ELADetector()
    
    # Solid gray image compressively degrades very little, ELA difference will be ~0
    img = Image.new("RGB", (100, 100), color=(128, 128, 128))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    solid_image_bytes = buf.getvalue()

    signal = detector.execute(solid_image_bytes)

    assert isinstance(signal, DetectorSignal)
    assert signal.score == 0.15
    assert signal.confidence == 0.90
    assert float(signal.metadata["mean_brightness"]) < 5.0
    assert "low, uniform compression error" in signal.evidence[0]
    assert len(signal.indicators) == 0


def test_ela_detector_high_brightness() -> None:
    """Verifies that a high-frequency checkerboard pattern creates high ELA differences, returning score of 0.85."""
    detector = ELADetector()

    # Create a high-frequency checkerboard image that compresses poorly at JPEG quality 90
    img = Image.new("RGB", (100, 100))
    pixels = img.load()
    for x in range(100):
        for y in range(100):
            if (x + y) % 2 == 0:
                pixels[x, y] = (255, 0, 0)
            else:
                pixels[x, y] = (0, 255, 0)

    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    noisy_image_bytes = buf.getvalue()

    signal = detector.execute(noisy_image_bytes)

    assert isinstance(signal, DetectorSignal)
    # The ELA diff mean brightness should be high (>= 30) for this pattern
    assert signal.score == 0.85
    assert signal.confidence == 0.90
    assert float(signal.metadata["mean_brightness"]) >= 30.0
    assert "high compression difference" in signal.evidence[0]
    assert len(signal.indicators) == 1
    assert signal.indicators[0].type == IndicatorType.COMPRESSION
    assert signal.indicators[0].severity == IndicatorSeverity.STRONG


def test_ela_detector_contract_details() -> None:
    """Verifies health, capabilities, name and version implementations."""
    detector = ELADetector()

    assert detector.name == "ela"
    assert detector.version == "0.1.0"
    assert detector.capabilities() == frozenset({"ela", "compression_artifacts"})
    
    health = detector.health()
    assert health.status == "ok"
    assert health.version == "0.1.0"
    assert health.is_healthy

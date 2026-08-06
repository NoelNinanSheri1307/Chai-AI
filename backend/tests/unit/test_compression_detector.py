"""Unit tests for the concrete CompressionDetector implementation."""

from __future__ import annotations

import io
from PIL import Image, ImageDraw

from app.core.enums import IndicatorSeverity, IndicatorType, ScoreCategory
from app.pipeline.detectors.compression import CompressionDetector
from app.pipeline.signals import DetectorSignal


def test_compression_detector_invalid_bytes() -> None:
    """Verifies that invalid image bytes result in fallback score of 0.40."""
    detector = CompressionDetector()
    invalid_bytes = b"not_an_image_file"

    signal = detector.execute(invalid_bytes)

    assert isinstance(signal, DetectorSignal)
    assert signal.score == 0.40
    assert signal.confidence == 0.50
    assert "Failed to parse" in signal.evidence[0]
    assert signal.metadata["error"] == "Invalid image bytes"


def test_compression_detector_no_anomalies() -> None:
    """Verifies that a solid flat image has zero local anomalies, returning score of 0.10."""
    detector = CompressionDetector()
    
    img = Image.new("RGB", (100, 100), color=(128, 128, 128))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    solid_image_bytes = buf.getvalue()

    signal = detector.execute(solid_image_bytes)

    assert isinstance(signal, DetectorSignal)
    assert signal.score == 0.10
    assert signal.confidence == 0.90
    assert int(signal.metadata["tamper_blocks_count"]) == 0
    assert "high compression consistency" in signal.evidence[0]
    assert len(signal.indicators) == 0


def test_compression_detector_moderate_anomalies() -> None:
    """Verifies that 4 distinct shape changes trigger moderate score of 0.68 and moderate indicator."""
    detector = CompressionDetector()

    img = Image.new("RGB", (150, 150), color="black")
    draw = ImageDraw.Draw(img)
    # Draw 4 distinct white squares (area = 144, which is > 100)
    draw.rectangle([10, 10, 22, 22], fill="white")
    draw.rectangle([40, 40, 52, 52], fill="white")
    draw.rectangle([70, 70, 82, 82], fill="white")
    draw.rectangle([100, 100, 112, 112], fill="white")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    moderate_image_bytes = buf.getvalue()

    signal = detector.execute(moderate_image_bytes)

    assert isinstance(signal, DetectorSignal)
    assert signal.score == 0.68
    assert signal.confidence == 0.85
    assert int(signal.metadata["tamper_blocks_count"]) == 4
    assert "Moderate compression block boundary mismatches" in signal.evidence[0]
    assert len(signal.indicators) == 1
    assert signal.indicators[0].type == IndicatorType.COMPRESSION
    assert signal.indicators[0].severity == IndicatorSeverity.MODERATE


def test_compression_detector_high_anomalies() -> None:
    """Verifies that 8 distinct shape changes trigger high score of 0.88 and strong indicator."""
    detector = CompressionDetector()

    img = Image.new("RGB", (200, 200), color="black")
    draw = ImageDraw.Draw(img)
    # Draw 8 distinct white squares (each area = 144, which is > 100)
    for i in range(8):
        offset = i * 22 + 5
        draw.rectangle([offset, offset, offset + 12, offset + 12], fill="white")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    high_image_bytes = buf.getvalue()

    signal = detector.execute(high_image_bytes)

    assert isinstance(signal, DetectorSignal)
    assert signal.score == 0.88
    assert signal.confidence == 0.90
    assert int(signal.metadata["tamper_blocks_count"]) == 8
    assert "High density of compression edge inconsistencies" in signal.evidence[0]
    assert len(signal.indicators) == 1
    assert signal.indicators[0].type == IndicatorType.COMPRESSION
    assert signal.indicators[0].severity == IndicatorSeverity.STRONG


def test_compression_detector_contract_details() -> None:
    """Verifies health, capabilities, name and version implementations."""
    detector = CompressionDetector()

    assert detector.name == "compression"
    assert detector.version == "0.1.0"
    assert detector.capabilities() == frozenset({"compression", "blocking"})
    
    health = detector.health()
    assert health.status == "ok"
    assert health.version == "0.1.0"
    assert health.is_healthy

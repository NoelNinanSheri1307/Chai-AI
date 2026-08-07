"""Unit tests for the concrete LightingDetector implementation."""

from __future__ import annotations

import io

import cv2
import numpy as np
from PIL import Image

from app.core.enums import IndicatorType, ScoreCategory
from app.pipeline.detectors.lighting import LightingDetector
from app.pipeline.signals import DetectorSignal


def test_lighting_detector_invalid_bytes() -> None:
    """Invalid image bytes produce fallback score of 0.40."""
    detector = LightingDetector()
    signal = detector.execute(b"not_an_image")

    assert isinstance(signal, DetectorSignal)
    assert signal.score == 0.40
    assert signal.confidence == 0.50
    assert "Failed to parse" in signal.evidence[0]
    assert signal.metadata["error"] == "Invalid image bytes"


def test_lighting_detector_uniform_gradient() -> None:
    """A smooth left-to-right gradient has consistent lighting (low circ_std)."""
    detector = LightingDetector()

    # Create a smooth horizontal gradient: all quadrants share the same light direction
    gradient = np.tile(np.arange(256, dtype=np.uint8), (256, 1))
    _, buf = cv2.imencode(".png", gradient)

    signal = detector.execute(buf.tobytes())

    assert isinstance(signal, DetectorSignal)
    assert signal.category == ScoreCategory.LIGHTING
    assert signal.score == 0.10
    assert signal.confidence == 0.90
    assert float(signal.metadata["circular_std"]) < 0.5
    assert "highly consistent" in signal.evidence[0]
    assert len(signal.indicators) == 0


def test_lighting_detector_contradictory_lighting() -> None:
    """Opposing gradients in different quadrants yield high circ_std (0.85)."""
    detector = LightingDetector()

    img = np.zeros((256, 256), dtype=np.uint8)
    ramp = np.arange(128, dtype=np.uint8)

    # Top-left: gradient going right (bright on right)
    img[:128, :128] = np.tile(ramp * 2, (128, 1))
    # Top-right: gradient going left (bright on left)
    img[:128, 128:] = np.tile((ramp * 2)[::-1], (128, 1))
    # Bottom-left: gradient going down (bright at bottom)
    img[128:, :128] = np.tile((ramp * 2).reshape(-1, 1), (1, 128))
    # Bottom-right: gradient going up (bright at top)
    img[128:, 128:] = np.tile((ramp * 2)[::-1].reshape(-1, 1), (1, 128))

    _, buf = cv2.imencode(".png", img)
    signal = detector.execute(buf.tobytes())

    assert isinstance(signal, DetectorSignal)
    assert signal.score >= 0.65  # at least moderate
    assert float(signal.metadata["circular_std"]) >= 1.0
    assert len(signal.indicators) >= 1
    assert signal.indicators[0].type == IndicatorType.LIGHTING


def test_lighting_detector_flat_image() -> None:
    """A flat image is numerically degenerate but handled gracefully."""
    detector = LightingDetector()

    img = Image.new("L", (256, 256), color=128)
    buf = io.BytesIO()
    img.save(buf, format="PNG")

    signal = detector.execute(buf.getvalue())

    # The detector should still return a valid DetectorSignal without crashing
    assert isinstance(signal, DetectorSignal)
    assert signal.category == ScoreCategory.LIGHTING
    assert 0.0 <= signal.score <= 1.0


def test_lighting_detector_contract_details() -> None:
    """Verifies health, capabilities, name and version."""
    detector = LightingDetector()

    assert detector.name == "lighting"
    assert detector.version == "0.1.0"
    assert detector.capabilities() == frozenset({"lighting", "photometry"})

    health = detector.health()
    assert health.status == "ok"
    assert health.version == "0.1.0"
    assert health.is_healthy

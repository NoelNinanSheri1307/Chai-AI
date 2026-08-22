"""Unit tests for Milestone 14 robust image decoding and forensic calibration regressions."""

from __future__ import annotations

import numpy as np
import pytest
from PIL import Image

from app.pipeline.config import PipelineConfig, get_pipeline_config
from app.pipeline.detectors.decode import (
    ImageDecodeError,
    decode_image_to_cv_bgr,
    decode_image_to_cv_gray,
    decode_image_to_cv_rgb,
    decode_image_to_pil,
)
from app.pipeline.detectors.registry import build_detectors
from app.pipeline.fusion.classify import compute_classification
from app.pipeline.fusion.normalize import NormalizedSignal
from tests.sample_images import GARBAGE_BYTES, JPEG_BYTES, PNG_BYTES


def test_decode_image_to_pil_and_arrays() -> None:
    # Valid JPEG
    pil_img = decode_image_to_pil(JPEG_BYTES)
    assert isinstance(pil_img, Image.Image)
    assert pil_img.width > 0
    assert pil_img.height > 0

    gray = decode_image_to_cv_gray(JPEG_BYTES)
    assert isinstance(gray, np.ndarray)
    assert gray.ndim == 2
    assert gray.shape == (pil_img.height, pil_img.width)

    bgr = decode_image_to_cv_bgr(JPEG_BYTES)
    assert isinstance(bgr, np.ndarray)
    assert bgr.ndim == 3
    assert bgr.shape == (pil_img.height, pil_img.width, 3)

    rgb = decode_image_to_cv_rgb(JPEG_BYTES)
    assert isinstance(rgb, np.ndarray)
    assert rgb.ndim == 3
    assert rgb.shape == (pil_img.height, pil_img.width, 3)


def test_decode_png_format() -> None:
    pil_img = decode_image_to_pil(PNG_BYTES)
    assert isinstance(pil_img, Image.Image)
    gray = decode_image_to_cv_gray(PNG_BYTES)
    assert gray.ndim == 2


def test_decode_invalid_and_corrupt_payloads() -> None:
    with pytest.raises(ImageDecodeError):
        decode_image_to_pil(b"")

    with pytest.raises(ImageDecodeError):
        decode_image_to_pil(b"short")

    with pytest.raises(ImageDecodeError):
        decode_image_to_pil(GARBAGE_BYTES)

    with pytest.raises(ImageDecodeError):
        decode_image_to_cv_gray(GARBAGE_BYTES)

    with pytest.raises(ImageDecodeError):
        decode_image_to_cv_bgr(GARBAGE_BYTES)


def test_all_detectors_execute_with_shared_decoder() -> None:
    config = PipelineConfig()
    detectors = build_detectors(config.enabled_detector_names())
    assert len(detectors) == 7

    for det in detectors:
        sig = det.execute(JPEG_BYTES)
        assert sig.detector_name == det.name
        assert 0.0 <= sig.score <= 1.0
        assert 0.0 <= sig.confidence <= 1.0


def test_calibrated_pipeline_config_parameters() -> None:
    config = get_pipeline_config()
    # 1. Resolution calibrated to 0.35
    assert config.classifier_resolution == pytest.approx(0.35)

    # 2. Reliability calibrated
    assert config.reliability_for("frequency") == pytest.approx(0.50)
    assert config.reliability_for("lighting") == pytest.approx(0.06)
    assert config.reliability_for("ela") == pytest.approx(0.02)
    assert config.reliability_for("noise") == pytest.approx(0.02)

    # 3. Contribution matrix calibrated
    matrix = config.classifier_contribution_matrix
    assert matrix["frequency"]["ai_generated"] == pytest.approx(1.00)
    assert matrix["frequency"]["original"] == pytest.approx(0.05)
    assert matrix["lighting"]["ai_generated"] == pytest.approx(0.20)
    assert matrix["texture"]["ai_generated"] == pytest.approx(0.40)


def test_fallback_scores_do_not_collapse_to_95_percent_confidence() -> None:
    config = get_pipeline_config()
    # Simulate neutral / fallback signals (0.40)
    signals = [
        NormalizedSignal(detector="frequency", score=0.40, confidence=0.50, reliability=0.50),
        NormalizedSignal(detector="texture", score=0.40, confidence=0.50, reliability=0.15),
        NormalizedSignal(detector="lighting", score=0.40, confidence=0.50, reliability=0.06),
        NormalizedSignal(detector="compression", score=0.15, confidence=0.80, reliability=0.10),
        NormalizedSignal(detector="metadata", score=0.40, confidence=0.60, reliability=0.15),
    ]

    res = compute_classification(signals=signals, config=config, total_capacity=len(signals))
    # In M12 baseline with sigma=0.15, confidence was 0.954. With calibrated sigma=0.35, confidence is restrained
    assert 0.0 <= res.confidence <= 0.85

"""Unit tests for Milestone 14A robust shared image decoding."""

from __future__ import annotations

import io

import numpy as np
import pytest
from PIL import Image

from app.pipeline.config import PipelineConfig
from app.pipeline.detectors.decode import (
    ImageDecodeError,
    decode_image_to_cv_bgr,
    decode_image_to_cv_gray,
    decode_image_to_cv_rgb,
    decode_image_to_pil,
    is_avif_supported,
)
from app.pipeline.detectors.registry import build_detectors
from tests.sample_images import GARBAGE_BYTES, JPEG_BYTES


def _create_sample_image(
    format_name: str, mode: str = "RGB", size: tuple[int, int] = (64, 64)
) -> bytes:
    """Helper to construct in-memory test images in different formats."""
    img = Image.new(
        mode, size, color=(128, 64, 32, 255) if mode == "RGBA" else (128, 64, 32)
    )
    buf = io.BytesIO()
    img.save(buf, format=format_name)
    return buf.getvalue()


def test_decode_image_to_pil_and_arrays() -> None:
    # Valid JPEG
    jpeg_bytes = _create_sample_image("JPEG")
    pil_img = decode_image_to_pil(jpeg_bytes)
    assert isinstance(pil_img, Image.Image)
    assert pil_img.width > 0
    assert pil_img.height > 0

    gray = decode_image_to_cv_gray(jpeg_bytes)
    assert isinstance(gray, np.ndarray)
    assert gray.ndim == 2
    assert gray.shape == (pil_img.height, pil_img.width)

    bgr = decode_image_to_cv_bgr(jpeg_bytes)
    assert isinstance(bgr, np.ndarray)
    assert bgr.ndim == 3
    assert bgr.shape == (pil_img.height, pil_img.width, 3)

    rgb = decode_image_to_cv_rgb(jpeg_bytes)
    assert isinstance(rgb, np.ndarray)
    assert rgb.ndim == 3
    assert rgb.shape == (pil_img.height, pil_img.width, 3)


def test_decode_png_format() -> None:
    png_bytes = _create_sample_image("PNG")
    pil_img = decode_image_to_pil(png_bytes)
    assert isinstance(pil_img, Image.Image)
    gray = decode_image_to_cv_gray(png_bytes)
    assert gray.ndim == 2
    bgr = decode_image_to_cv_bgr(png_bytes)
    assert bgr.ndim == 3


def test_decode_webp_format() -> None:
    webp_bytes = _create_sample_image("WEBP")
    pil_img = decode_image_to_pil(webp_bytes)
    assert isinstance(pil_img, Image.Image)
    gray = decode_image_to_cv_gray(webp_bytes)
    assert gray.ndim == 2
    bgr = decode_image_to_cv_bgr(webp_bytes)
    assert bgr.ndim == 3


def test_decode_rgba_mode_channel_conversion() -> None:
    rgba_bytes = _create_sample_image("PNG", mode="RGBA")
    pil_img = decode_image_to_pil(rgba_bytes)
    assert pil_img.mode == "RGBA"

    gray = decode_image_to_cv_gray(rgba_bytes)
    assert isinstance(gray, np.ndarray)
    assert gray.ndim == 2

    bgr = decode_image_to_cv_bgr(rgba_bytes)
    assert isinstance(bgr, np.ndarray)
    assert bgr.ndim == 3
    assert bgr.shape[2] == 3


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


def test_avif_decoding_capability() -> None:
    if not is_avif_supported():
        pytest.skip(
            "AVIF decoding is not registered in this Pillow runtime environment."
        )

    try:
        avif_bytes = _create_sample_image("AVIF")
        pil_img = decode_image_to_pil(avif_bytes)
        assert isinstance(pil_img, Image.Image)
        gray = decode_image_to_cv_gray(avif_bytes)
        assert gray.ndim == 2
    except Exception as exc:
        pytest.fail(f"AVIF decoding was expected to succeed but raised: {exc}")


def test_all_detectors_execute_with_shared_decoder() -> None:
    config = PipelineConfig()
    detectors = build_detectors(config.enabled_detector_names())
    assert len(detectors) == 7

    for det in detectors:
        sig = det.execute(JPEG_BYTES)
        assert sig.detector_name == det.name
        assert 0.0 <= sig.score <= 1.0
        assert 0.0 <= sig.confidence <= 1.0

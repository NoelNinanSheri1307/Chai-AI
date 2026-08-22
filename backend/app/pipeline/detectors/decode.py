"""Shared robust image decoding utilities for forensic detectors.

Provides a unified decoding path using Pillow for broad format support (JPEG,
PNG, WebP, AVIF) and converts safely to grayscale, RGB, or OpenCV BGR numpy arrays.
"""

from __future__ import annotations

import io
import cv2
import numpy as np
from PIL import Image, ImageOps


class ImageDecodeError(Exception):
    """Raised when an image payload cannot be decoded into valid pixels."""


def decode_image_to_pil(image_bytes: bytes) -> Image.Image:
    """Decode raw image bytes into a PIL Image, respecting EXIF orientation."""
    if not image_bytes or len(image_bytes) < 12:
        raise ImageDecodeError("Payload is empty or too short.")
    try:
        img = Image.open(io.BytesIO(image_bytes))
        img = ImageOps.exif_transpose(img)
        img.load()  # Force full pixel load to verify decodeability
        return img
    except Exception as exc:
        raise ImageDecodeError(f"Failed to decode image with PIL: {exc!s}") from exc


def decode_image_to_cv_gray(image_bytes: bytes) -> np.ndarray:
    """Decode raw image bytes into a single-channel grayscale 2D uint8 numpy array."""
    pil_img = decode_image_to_pil(image_bytes)
    try:
        if pil_img.mode != "L":
            pil_img = pil_img.convert("L")
        arr = np.array(pil_img, dtype=np.uint8)
        if arr.ndim != 2 or arr.size == 0:
            raise ValueError("Grayscale array is empty or not 2D.")
        return arr
    except Exception as exc:
        raise ImageDecodeError(f"Failed to convert image to grayscale array: {exc!s}") from exc


def decode_image_to_cv_bgr(image_bytes: bytes) -> np.ndarray:
    """Decode raw image bytes into an OpenCV standard BGR 3-channel uint8 numpy array."""
    pil_img = decode_image_to_pil(image_bytes)
    try:
        if pil_img.mode != "RGB":
            pil_img = pil_img.convert("RGB")
        rgb_arr = np.array(pil_img, dtype=np.uint8)
        bgr_arr = cv2.cvtColor(rgb_arr, cv2.COLOR_RGB2BGR)
        return bgr_arr
    except Exception as exc:
        raise ImageDecodeError(f"Failed to convert image to BGR array: {exc!s}") from exc


def decode_image_to_cv_rgb(image_bytes: bytes) -> np.ndarray:
    """Decode raw image bytes into an RGB 3-channel uint8 numpy array."""
    pil_img = decode_image_to_pil(image_bytes)
    try:
        if pil_img.mode != "RGB":
            pil_img = pil_img.convert("RGB")
        return np.array(pil_img, dtype=np.uint8)
    except Exception as exc:
        raise ImageDecodeError(f"Failed to convert image to RGB array: {exc!s}") from exc

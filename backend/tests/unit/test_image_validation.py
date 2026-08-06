"""Tests for upload validation: size, declared MIME and magic-byte sniffing."""

from __future__ import annotations

import pytest

from app.core import constants
from app.core.exceptions import (
    FileTooLargeError,
    InvalidImageError,
    UnsupportedMediaTypeError,
)
from app.utils.image import sniff_image_type, validate_image_upload
from tests.sample_images import (
    GARBAGE_BYTES,
    JPEG_BYTES,
    PNG_BYTES,
    WEBP_BYTES,
)


def test_sniff_recognises_supported_types() -> None:
    assert sniff_image_type(JPEG_BYTES) == "image/jpeg"
    assert sniff_image_type(PNG_BYTES) == "image/png"
    assert sniff_image_type(WEBP_BYTES) == "image/webp"


def test_sniff_rejects_garbage() -> None:
    assert sniff_image_type(GARBAGE_BYTES) is None
    assert sniff_image_type(b"") is None


def test_valid_uploads_return_sniffed_mime() -> None:
    assert validate_image_upload(JPEG_BYTES, content_type="image/jpeg") == "image/jpeg"
    assert validate_image_upload(PNG_BYTES, content_type="image/png") == "image/png"
    assert validate_image_upload(WEBP_BYTES, content_type="image/webp") == "image/webp"


def test_missing_content_type_falls_back_to_sniffing() -> None:
    assert validate_image_upload(JPEG_BYTES, content_type=None) == "image/jpeg"


def test_garbage_bytes_raise_invalid_image() -> None:
    with pytest.raises(InvalidImageError):
        validate_image_upload(GARBAGE_BYTES, content_type="image/jpeg")


def test_unsupported_declared_type_raises_unsupported_media() -> None:
    with pytest.raises(UnsupportedMediaTypeError):
        validate_image_upload(JPEG_BYTES, content_type="image/gif")


def test_declared_sniff_mismatch_raises_invalid_image() -> None:
    with pytest.raises(InvalidImageError):
        validate_image_upload(JPEG_BYTES, content_type="image/png")


def test_oversized_upload_raises_file_too_large() -> None:
    oversized = b"\x00" * (constants.MAX_UPLOAD_SIZE_BYTES + 1)
    with pytest.raises(FileTooLargeError):
        validate_image_upload(oversized, content_type="image/png")

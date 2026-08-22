"""Image file validation, metadata extraction, and deduplication helpers for the benchmark harness."""

from __future__ import annotations

import hashlib
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageOps


class ImageValidationError(Exception):
    """Raised when an image fails benchmark validation or is corrupt."""


def calculate_sha256(data: bytes) -> str:
    """Return hex-encoded SHA-256 digest of data bytes."""
    return hashlib.sha256(data).hexdigest()


def calculate_file_sha256(file_path: Path) -> str:
    """Return hex-encoded SHA-256 digest of a local file."""
    hasher = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def inspect_and_validate_image(data: bytes) -> dict[str, str | int]:
    """Validate image bytes with Pillow and return metadata dict.

    Raises :class:`ImageValidationError` if the data is corrupt or not a supported image.
    """
    if not data or len(data) < 12:
        raise ImageValidationError("File payload is empty or too short.")

    try:
        with Image.open(BytesIO(data)) as img:
            img.verify()
    except Exception as exc:
        raise ImageValidationError(f"Image verification failed: {exc!s}") from exc

    # Re-open for format/dimension reading after verify()
    try:
        with Image.open(BytesIO(data)) as img:
            img = ImageOps.exif_transpose(img)
            width, height = img.size
            fmt = (img.format or "UNKNOWN").upper()
            mime = f"image/{fmt.lower()}"
            if fmt in {"JPEG", "JPG"}:
                mime = "image/jpeg"
                fmt = "JPEG"
            elif fmt == "PNG":
                mime = "image/png"
            elif fmt == "WEBP":
                mime = "image/webp"
            elif fmt == "AVIF":
                mime = "image/avif"

            # Verify actual pixel decodeability (e.g. for AVIF or exotic formats)
            try:
                img.load()
            except Exception as dec_exc:
                raise ImageValidationError(
                    f"Image format {fmt} cannot be decoded by installed decoder: {dec_exc!s}"
                ) from dec_exc

            return {
                "width": width,
                "height": height,
                "format": fmt,
                "mime_type": mime,
                "file_size_bytes": len(data),
            }
    except ImageValidationError:
        raise
    except Exception as exc:
        raise ImageValidationError(f"Failed to read image attributes: {exc!s}") from exc


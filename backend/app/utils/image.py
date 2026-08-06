"""Image upload validation: size, declared MIME and magic-byte sniffing.

Validators here are pure functions over the raw uploaded bytes. They raise the
catalog error hierarchy (``app.core.exceptions``) so the API layer renders the
correct status: 413 file_too_large, 415 unsupported_media_type, 422
invalid_image. No image decoding or forensic processing is performed.
"""

from __future__ import annotations

from app.core import constants
from app.core.exceptions import (
    FileTooLargeError,
    InvalidImageError,
    UnsupportedMediaTypeError,
)

_JPEG_MAGIC = b"\xff\xd8\xff"
_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
_WEBP_RIFF = b"RIFF"
_WEBP_FORMAT = b"WEBP"


def sniff_image_type(data: bytes) -> str | None:
    """Return the MIME type implied by ``data`` magic bytes, or ``None``."""
    if data[: len(_JPEG_MAGIC)] == _JPEG_MAGIC:
        return "image/jpeg"
    if data[: len(_PNG_MAGIC)] == _PNG_MAGIC:
        return "image/png"
    if data[: len(_WEBP_RIFF)] == _WEBP_RIFF and data[8:12] == _WEBP_FORMAT:
        return "image/webp"
    return None


def _normalize_declared(content_type: str | None) -> str | None:
    """Lowercase and strip any media-type parameters from a declared MIME."""
    if not content_type:
        return None
    declared = content_type.split(";")[0].strip().lower()
    return declared or None


def validate_image_upload(
    data: bytes,
    *,
    content_type: str | None = None,
    filename: str | None = None,
) -> str:
    """Validate uploaded ``data`` and return its sniffed MIME type.

    Checks run in order: size limit, magic-byte sniffing, declared-MIME
    allowlist, then declared-vs-sniffed agreement. The caller never trusts the
    client-supplied type on its own; the sniffed type is authoritative and is
    what the rest of the pipeline sees.
    """
    if len(data) > constants.MAX_UPLOAD_SIZE_BYTES:
        raise FileTooLargeError(
            f"File exceeds the {constants.MAX_UPLOAD_SIZE_BYTES} byte upload limit."
        )

    sniffed = sniff_image_type(data)
    if sniffed is None:
        raise InvalidImageError("Uploaded bytes are not a supported image.")

    declared = _normalize_declared(content_type)
    if declared and declared not in constants.ALLOWED_IMAGE_MIME_TYPES:
        raise UnsupportedMediaTypeError(
            f"Unsupported media type {declared!r}; "
            f"expected one of {sorted(constants.ALLOWED_IMAGE_MIME_TYPES)}."
        )
    if declared and declared != sniffed:
        raise InvalidImageError(
            f"Declared media type {declared!r} does not match the detected "
            f"type {sniffed!r}."
        )
    return sniffed

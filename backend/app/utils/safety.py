"""Image resource-safety guards.

The forensic detectors decode the full image through numpy/OpenCV/PIL, so a
pathological upload (decompression bomb, insanely large claimed dimensions,
truncated frame) could otherwise exhaust memory or stall a worker. These helpers
cap what the pipeline is ever asked to decode: they parse only the image header
(never decoding pixel data) and reject images whose *declared* dimensions are
too large, before any detector runs.

A structured saneness rule: a header cannot be parsed at all, it is treated as
not decodable and falls through to detector baseline handling (the same
behaviour as today's magic-byte-only validation). Only images PIL can read and
that exceed the configured caps are rejected with a controlled error.
"""

from __future__ import annotations

import io

from PIL import Image, UnidentifiedImageError

from app.core.exceptions import InvalidImageError

# Arm PIL's own decompression-bomb protection so even defensive decodes in
# detectors cannot trigger unbounded allocation. Applied once at import.
_DEFAULT_PIL_MAX_PIXELS = 178_956_970  # PIL default (~178 MP); left as safety net
Image.MAX_IMAGE_PIXELS = _DEFAULT_PIL_MAX_PIXELS


def check_image_dimensions(
    data: bytes,
    *,
    max_pixels: int,
    max_dimension: int,
) -> tuple[int, int] | None:
    """Validate an image's declared dimensions without decoding pixels.

    Returns ``(width, height)`` when the header is parseable and within the
    configured caps. Returns ``None`` when the bytes are not a decodable image
    (callers fall through to detector baseline handling). Raises
    :class:`InvalidImageError` when the header declares dimensions beyond
    ``max_pixels`` / ``max_dimension``.
    """
    if not data:
        return None
    try:
        with Image.open(io.BytesIO(data)) as probe:
            width, height = probe.size
    except Image.DecompressionBombError as exc:
        raise InvalidImageError(
            f"Image exceeds the maximum allowed pixel count ({max_pixels} pixels)."
        ) from exc
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError):
        return None

    if width <= 0 or height <= 0:
        return None
    if width > max_dimension or height > max_dimension:
        raise InvalidImageError(
            "Image dimensions exceed the maximum allowed side length "
            f"({max_dimension}px)."
        )
    if width * height > max_pixels:
        raise InvalidImageError(
            f"Image exceeds the maximum allowed pixel count ({max_pixels} pixels)."
        )
    return width, height

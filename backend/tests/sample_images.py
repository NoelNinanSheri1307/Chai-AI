"""Minimal image byte samples carrying the correct magic-byte signatures.

These samples are never decoded — the placeholder pipeline inspects no image
content — they exist only to satisfy upload validation (magic bytes and size).
"""

from __future__ import annotations

JPEG_BYTES = b"\xff\xd8\xff\xe0" + b"jpeg-payload-" * 4
PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"png-payload-" * 4
WEBP_BYTES = b"RIFF" + (25).to_bytes(4, "little") + b"WEBPVP8 " + b" webp-payload"
GARBAGE_BYTES = b"this is definitively not an image"

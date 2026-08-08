"""Deterministic image byte builders for security and resource tests.

These build small, *valid-by-construction* PNG files whose headers claim huge
canvas sizes — classic decompression bombs — without allocating huge bitmaps.
"""

from __future__ import annotations

import struct
import zlib

_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _chunk(chunk_type: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + chunk_type
        + data
        + struct.pack(">I", zlib.crc32(chunk_type + data) & 0xFFFFFFFF)
    )


def _bomb_png(width: int, height: int) -> bytes:
    """A full PNG whose header claims ``width x height`` (tiny on disk)."""
    ihdr = struct.pack(">II", width, height) + bytes([8, 2, 0, 0, 0])
    idat = zlib.compress(b"\x00" * max(1, min(width, 8)))  # tiny plausible scanline
    return (
        _PNG_SIGNATURE
        + _chunk(b"IHDR", ihdr)
        + _chunk(b"IDAT", idat)
        + _chunk(b"IEND", b"")
    )


def bomb_png(width: int = 20_000, height: int = 20_000) -> bytes:
    """A PNG claiming 20k x 20k (400M pixels == decompression bomb)."""
    return _bomb_png(width, height)


def oversized_dimension_png(width: int = 100_000, height: int = 8) -> bytes:
    """A PNG whose width exceeds any sane dimension limit."""
    return _bomb_png(width, height)


def truncated_png(width: int = 8, height: int = 8) -> bytes:
    """A PNG whose IHDR payload is cut short (malformed/truncated input)."""
    ihdr = struct.pack(">II", width, height) + bytes([8, 2, 0, 0, 0])
    # Signature + a chunk header whose declared length is never delivered.
    return _PNG_SIGNATURE + struct.pack(">I", len(ihdr)) + b"IHDR" + ihdr[:3]

"""Forensic signals.

``signals.model`` defines the strongly-typed value objects (``DetectorHealth``,
``DetectorSignal``) shared by every framework component. The extractor modules
that turn a normalized image into signals (FFT, ELA, metadata, …) are implemented
by a later milestone and live in this package.
"""

from app.pipeline.signals.model import DetectorHealth, DetectorSignal

__all__ = ["DetectorHealth", "DetectorSignal"]

"""Abstract detector contract."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.pipeline.signals import DetectorHealth, DetectorSignal


class Detector(ABC):
    """A single forensic signal extractor.

    Implementations are stateless and deterministic: the same input produces the
    same signal. They never touch HTTP, FastAPI, the database or object storage.
    A detector can be added or removed from the pipeline purely through
    configuration (see ``PipelineConfig.detector_order``).
    """

    #: Stable identifier used for configuration, ordering and the version trail.
    name: str
    #: Semver-style version of this detector implementation.
    version: str
    #: Machine-readable capability labels exposed by :meth:`capabilities`.
    _capabilities: frozenset[str] = frozenset()

    @abstractmethod
    def execute(
        self,
        image_bytes: bytes,
        *,
        content_type: str | None = None,
        file_name: str | None = None,
    ) -> DetectorSignal:
        """Run this detector over ``image_bytes`` and return its signal."""

    def health(self) -> DetectorHealth:
        """Return the detector's current health status."""
        return DetectorHealth(status="ok", version=self.version, detail="available")

    def capabilities(self) -> frozenset[str]:
        """Return the capabilities this detector provides."""
        return self._capabilities

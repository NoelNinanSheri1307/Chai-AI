"""Abstract heatmap generator contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.pipeline.base import HeatmapResult
from app.pipeline.fusion.base import FusionResult
from app.pipeline.signals import DetectorSignal


@dataclass(frozen=True)
class HeatmapContext:
    """The inputs available to a heatmap generator."""

    image_bytes: bytes
    content_type: str | None = None
    file_name: str | None = None
    signals: tuple[DetectorSignal, ...] = ()
    fusion: FusionResult | None = None


class HeatmapGenerator(ABC):
    """Produce a manipulation heatmap from pipeline context."""

    @abstractmethod
    def generate(self, context: HeatmapContext) -> HeatmapResult:
        """Generate and return the manipulation heatmap for ``context``."""

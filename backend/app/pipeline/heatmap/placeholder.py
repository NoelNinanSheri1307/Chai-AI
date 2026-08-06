"""Deterministic placeholder heatmap generator.

Emits an empty-region heatmap with the configured overall manipulation score.
No saliency or region synthesis is performed; a later milestone replaces this
with real heatmap generation behind the same interface.
"""

from __future__ import annotations

from app.pipeline.base import HeatmapResult
from app.pipeline.config import PipelineConfig
from app.pipeline.heatmap.base import HeatmapContext, HeatmapGenerator


class PlaceholderHeatmapGenerator(HeatmapGenerator):
    """Configuration-driven placeholder heatmap."""

    def __init__(self, config: PipelineConfig) -> None:
        self._config = config

    def generate(self, context: HeatmapContext) -> HeatmapResult:
        """Return a deterministic placeholder heatmap for ``context``."""
        return HeatmapResult(
            overall_manipulation=self._config.heatmap_overall_manipulation,
            regions=[],
        )

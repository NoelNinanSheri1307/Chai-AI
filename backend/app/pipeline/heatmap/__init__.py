"""Heatmap generation framework.

Heatmap generators translate the fused signals into localized manipulation
rectangles plus an overall manipulation score. They operate on the typed
:class:`HeatmapContext` and return the pipeline's :class:`HeatmapResult`. The
shipped :class:`DeterministicHeatmapGenerator` merges the spatial regions exposed
by every detector into an explainable, frontend-ready manipulation map.
"""

from app.pipeline.heatmap.base import HeatmapContext, HeatmapGenerator
from app.pipeline.heatmap.fusion import MergedRegion, merge_regions
from app.pipeline.heatmap.generator import DeterministicHeatmapGenerator

__all__ = [
    "DeterministicHeatmapGenerator",
    "HeatmapContext",
    "HeatmapGenerator",
    "MergedRegion",
    "merge_regions",
]

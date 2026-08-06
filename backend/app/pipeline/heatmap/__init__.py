"""Heatmap generation framework.

Heatmap generators translate the fused signals into localized manipulation
rectangles plus an overall manipulation score. They operate on the typed
:class:`HeatmapContext` and return the pipeline's :class:`HeatmapResult`; the
placeholder shipped here produces a deterministic empty heatmap so no image
processing is performed yet.
"""

from app.pipeline.heatmap.base import HeatmapContext, HeatmapGenerator
from app.pipeline.heatmap.placeholder import PlaceholderHeatmapGenerator

__all__ = ["HeatmapContext", "HeatmapGenerator", "PlaceholderHeatmapGenerator"]

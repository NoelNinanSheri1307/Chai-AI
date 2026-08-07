"""Deterministic spatial heatmap generator.

The :class:`DeterministicHeatmapGenerator` turns the localized regions exposed by
every detector into a single manipulation map, answering **where** a verdict
applies. It replaces the placeholder and:

* collects the normalized :class:`SpatialRegion` rectangles from every signal;
* merges overlapping regions and **accumulates** their confidence;
* keeps detector attribution and assigns a severity;
* caps the result and renders each merged region as a frontend-ready
  ``HeatmapRegionResult`` (normalized box + intensity + label);
* returns an overall manipulation score derived from the fused result when
  available (falling back to configuration otherwise).

Everything is deterministic — region collection is ordered by detector and fusion
is ordered by confidence — and independent of any random state.
"""

from __future__ import annotations

from app.pipeline.base import HeatmapRegionResult, HeatmapResult
from app.pipeline.config import PipelineConfig
from app.pipeline.fusion.base import FusionResult
from app.pipeline.heatmap.base import HeatmapContext, HeatmapGenerator
from app.pipeline.heatmap.fusion import MergedRegion, merge_regions
from app.pipeline.heatmap.spatial import clamp01
from app.pipeline.signals import SpatialRegion

_LABEL_LIMIT = 100


def _render_label(region: MergedRegion) -> str:
    """Render a human-readable label carrying source and severity."""
    sources = "/".join(region.detectors)
    core = region.label
    if sources:
        core = f"{sources}: {core}"
    if region.severity:
        core = f"{core} ({region.severity})"
    return core[:_LABEL_LIMIT]


def _overall_manipulation(fusion: FusionResult | None, config: PipelineConfig) -> float:
    """Return the overall manipulation score, preferring the fused result."""
    if fusion is not None:
        return clamp01(round(fusion.manipulation, 4))
    return clamp01(config.heatmap_overall_manipulation)


def collect_regions(signals) -> list[SpatialRegion]:
    """Flatten the spatial regions exposed by every detector signal."""
    return [region for signal in signals for region in signal.regions]


class DeterministicHeatmapGenerator(HeatmapGenerator):
    """Configuration-driven, deterministic heatmap generator."""

    def __init__(self, config: PipelineConfig) -> None:
        self._config = config

    def generate(self, context: HeatmapContext) -> HeatmapResult:
        """Generate the manipulation heatmap for ``context``."""
        if not self._config.heatmap_enabled:
            return HeatmapResult(
                overall_manipulation=_overall_manipulation(
                    context.fusion, self._config
                ),
                regions=[],
            )

        regions = collect_regions(context.signals)
        overall = _overall_manipulation(context.fusion, self._config)

        if not regions:
            return HeatmapResult(overall_manipulation=overall, regions=[])

        merged = merge_regions(
            regions,
            iou_threshold=self._config.heatmap_iou_threshold,
            min_area=self._config.heatmap_min_region_area,
        )
        # Keep the strongest regions first, bounded by configuration.
        merged = merged[: self._config.heatmap_max_regions]

        heatmap_regions = [
            HeatmapRegionResult(
                x=region.x,
                y=region.y,
                width=region.width,
                height=region.height,
                intensity=clamp01(region.confidence),
                label=_render_label(region),
            )
            for region in merged
        ]
        return HeatmapResult(overall_manipulation=overall, regions=heatmap_regions)

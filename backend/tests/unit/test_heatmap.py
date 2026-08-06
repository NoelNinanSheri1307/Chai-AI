"""Tests for the heatmap generation framework."""

from __future__ import annotations

import pytest

from app.pipeline.base import HeatmapResult
from app.pipeline.config import PipelineConfig
from app.pipeline.heatmap import HeatmapContext, HeatmapGenerator
from app.pipeline.heatmap.placeholder import PlaceholderHeatmapGenerator
from tests.sample_images import JPEG_BYTES


def test_heatmap_generator_is_abstract() -> None:
    with pytest.raises(TypeError):
        HeatmapGenerator()


def test_placeholder_generator_returns_deterministic_heatmap(
    pipeline_config: PipelineConfig,
) -> None:
    generator = PlaceholderHeatmapGenerator(pipeline_config)
    context = HeatmapContext(
        image_bytes=JPEG_BYTES,
        content_type="image/jpeg",
        file_name="x.jpg",
        signals=(),
        fusion=None,
    )
    heatmap = generator.generate(context)
    assert isinstance(heatmap, HeatmapResult)
    assert heatmap.overall_manipulation == pipeline_config.heatmap_overall_manipulation
    assert heatmap.regions == []


def test_placeholder_heatmap_is_deterministic(
    pipeline_config: PipelineConfig,
) -> None:
    generator = PlaceholderHeatmapGenerator(pipeline_config)
    context = HeatmapContext(image_bytes=JPEG_BYTES, content_type="image/jpeg")
    assert generator.generate(context) == generator.generate(context)

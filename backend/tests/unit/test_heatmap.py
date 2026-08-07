"""Tests for the deterministic heatmap generator."""

from __future__ import annotations

import pytest

from app.core.enums import RiskLevel, ScoreCategory, Verdict
from app.pipeline.base import HeatmapResult
from app.pipeline.config import PipelineConfig
from app.pipeline.fusion.base import FusionResult
from app.pipeline.heatmap import DeterministicHeatmapGenerator, HeatmapContext
from app.pipeline.signals import DetectorSignal, SpatialRegion
from tests.sample_images import JPEG_BYTES


def _signal(
    size: float, x: float = 0.1, y: float = 0.1, region: bool = True
) -> DetectorSignal:
    regions = (
        (
            SpatialRegion(
                x=x,
                y=y,
                width=size,
                height=size,
                confidence=0.8,
                severity="strong",
                label="Anomaly",
                detector="texture",
            ),
        )
        if region
        else ()
    )
    return DetectorSignal(
        detector_name="texture",
        detector_version="1.0",
        category=ScoreCategory.TEXTURE,
        score=0.8,
        confidence=0.9,
        regions=regions,
    )


def _fusion(**overrides) -> FusionResult:
    args = dict(
        verdict=Verdict.AI_EDITED,
        confidence=0.6,
        risk_level=RiskLevel.MEDIUM,
        manipulation=0.55,
    )
    args.update(overrides)
    return FusionResult(**args)


def test_generator_is_abstract() -> None:
    from app.pipeline.heatmap.base import HeatmapGenerator

    with pytest.raises(TypeError):
        HeatmapGenerator()


def test_empty_regions_returns_clean_heatmap(pipeline_config: PipelineConfig) -> None:
    generator = DeterministicHeatmapGenerator(pipeline_config)
    context = HeatmapContext(
        image_bytes=JPEG_BYTES,
        signals=(_signal(0.0, region=False),),
        fusion=_fusion(manipulation=0.12),
    )
    heatmap = generator.generate(context)
    assert isinstance(heatmap, HeatmapResult)
    assert heatmap.regions == []
    assert heatmap.overall_manipulation == pytest.approx(0.12)


def test_overall_uses_fusion_when_available(pipeline_config: PipelineConfig) -> None:
    generator = DeterministicHeatmapGenerator(pipeline_config)
    heatmap = generator.generate(
        HeatmapContext(
            image_bytes=JPEG_BYTES, signals=(), fusion=_fusion(manipulation=0.88)
        )
    )
    assert heatmap.overall_manipulation == pytest.approx(0.88)


def test_overall_falls_back_to_config(pipeline_config: PipelineConfig) -> None:
    generator = DeterministicHeatmapGenerator(pipeline_config)
    heatmap = generator.generate(HeatmapContext(image_bytes=JPEG_BYTES))
    assert heatmap.overall_manipulation == pytest.approx(
        pipeline_config.heatmap_overall_manipulation
    )


def test_single_detector_region_is_preserved(pipeline_config: PipelineConfig) -> None:
    generator = DeterministicHeatmapGenerator(pipeline_config)
    heatmap = generator.generate(
        HeatmapContext(
            image_bytes=JPEG_BYTES,
            signals=(_signal(0.2),),
            fusion=_fusion(),
        )
    )
    assert len(heatmap.regions) == 1
    region = heatmap.regions[0]
    assert region.width == pytest.approx(0.2)
    assert region.height == pytest.approx(0.2)
    assert 0.0 <= region.intensity <= 1.0
    assert "texture" in region.label


def test_overlapping_regions_merge(pipeline_config: PipelineConfig) -> None:
    generator = DeterministicHeatmapGenerator(pipeline_config)
    signal_a = _signal(0.3, region=True)
    texture_region = SpatialRegion(
        x=0.1, y=0.1, width=0.3, height=0.3, confidence=0.7, detector="ela", label="ELA"
    )
    signal_b = DetectorSignal(
        detector_name="ela",
        detector_version="1.0",
        category=ScoreCategory.COMPRESSION,
        score=0.7,
        confidence=0.8,
        regions=(texture_region,),
    )
    heatmap = generator.generate(
        HeatmapContext(
            image_bytes=JPEG_BYTES, signals=(signal_a, signal_b), fusion=_fusion()
        )
    )
    assert len(heatmap.regions) == 1
    assert "ela" in heatmap.regions[0].label
    # Accumulated confidence strictly greater than any individual contribution.
    assert heatmap.regions[0].intensity > 0.8


def test_generator_is_deterministic(pipeline_config: PipelineConfig) -> None:
    generator = DeterministicHeatmapGenerator(pipeline_config)
    context = HeatmapContext(
        image_bytes=JPEG_BYTES,
        signals=(_signal(0.2, 0.1), _signal(0.2, 0.5, 0.5)),
        fusion=_fusion(),
    )
    assert generator.generate(context) == generator.generate(context)


def test_max_regions_is_respected(pipeline_config: PipelineConfig) -> None:
    config = pipeline_config.model_copy(update={"heatmap_max_regions": 2})
    generator = DeterministicHeatmapGenerator(config)
    signals = [_signal(0.15, x=0.05 + i * 0.25, y=0.1) for i in range(6)]
    heatmap = generator.generate(
        HeatmapContext(image_bytes=JPEG_BYTES, signals=signals)
    )
    assert len(heatmap.regions) <= 2


def test_heatmap_can_be_disabled(pipeline_config: PipelineConfig) -> None:
    config = pipeline_config.model_copy(update={"heatmap_enabled": False})
    generator = DeterministicHeatmapGenerator(config)
    heatmap = generator.generate(
        HeatmapContext(
            image_bytes=JPEG_BYTES, signals=(_signal(0.3),), fusion=_fusion()
        )
    )
    assert heatmap.regions == []

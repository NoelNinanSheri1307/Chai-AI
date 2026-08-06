"""Tests for the fusion engine framework."""

from __future__ import annotations

import pytest

from app.core.enums import RiskLevel
from app.pipeline.config import PipelineConfig
from app.pipeline.detectors.registry import build_detectors
from app.pipeline.fusion import FusionEngine, FusionResult
from app.pipeline.fusion.placeholder import PlaceholderFusionEngine
from tests.sample_images import JPEG_BYTES


def _signals(config: PipelineConfig):
    detectors = build_detectors(config.enabled_detector_names())
    return [
        detector.execute(JPEG_BYTES, content_type="image/jpeg")
        for detector in detectors
    ]


def test_fusion_engine_is_abstract() -> None:
    with pytest.raises(TypeError):
        FusionEngine()


def test_fusion_returns_typed_result(pipeline_config: PipelineConfig) -> None:
    engine = PlaceholderFusionEngine(pipeline_config)
    result = engine.fuse(_signals(pipeline_config))
    assert isinstance(result, FusionResult)
    assert result.verdict.value == "aiGenerated"
    assert result.confidence == pytest.approx(0.91)
    assert result.risk_level == RiskLevel.HIGH
    assert len(result.scores) == len(pipeline_config.enabled_detector_names())
    assert result.indicators
    assert result.weights


def test_fusion_is_deterministic(pipeline_config: PipelineConfig) -> None:
    engine = PlaceholderFusionEngine(pipeline_config)
    first = engine.fuse(_signals(pipeline_config))
    second = engine.fuse(_signals(pipeline_config))
    assert first == second


def test_fusion_weights_are_configured(pipeline_config: PipelineConfig) -> None:
    engine = PlaceholderFusionEngine(pipeline_config)
    result = engine.fuse(_signals(pipeline_config))
    assert result.weights
    assert all(
        pipeline_config.weight_for(category) == weight
        for category, weight in result.weights.items()
    )


def test_risk_level_derived_from_thresholds(pipeline_config: PipelineConfig) -> None:
    assert pipeline_config.risk_level_for(0.9) == RiskLevel.HIGH
    assert pipeline_config.risk_level_for(0.5) == RiskLevel.MEDIUM
    assert pipeline_config.risk_level_for(0.2) == RiskLevel.LOW

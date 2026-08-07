"""Tests for the modular pipeline runner orchestration."""

from __future__ import annotations

from app.core.enums import RiskLevel, ScoreCategory, Verdict
from app.pipeline.base import PipelineResult
from app.pipeline.config import PipelineConfig
from app.pipeline.detectors.registry import build_detectors
from app.pipeline.explanation.placeholder import (
    PlaceholderEvidenceGenerator,
    PlaceholderExplanationGenerator,
)
from app.pipeline.fusion.engine import DeterministicFusionEngine
from app.pipeline.heatmap.placeholder import PlaceholderHeatmapGenerator
from app.pipeline.runner import ModularAnalysisPipeline
from tests.sample_images import JPEG_BYTES


def test_pipeline_executes_full_stage_chain(
    pipeline: ModularAnalysisPipeline,
) -> None:
    result = pipeline.analyze(JPEG_BYTES, content_type="image/jpeg", file_name="x.jpg")
    assert isinstance(result, PipelineResult)
    assert result.verdict in Verdict
    assert 0.0 <= result.confidence <= 1.0
    assert result.risk_level in RiskLevel
    assert result.explanation
    assert result.scores
    assert result.indicators is not None
    assert result.evidence
    assert result.metadata
    assert result.heatmap is not None
    assert result.duration_ms > 0


def test_pipeline_is_deterministic(pipeline: ModularAnalysisPipeline) -> None:
    first = pipeline.analyze(JPEG_BYTES, content_type="image/jpeg")
    second = pipeline.analyze(JPEG_BYTES, content_type="image/jpeg")
    assert first == second


def test_pipeline_scores_reflect_configured_detectors(
    pipeline: ModularAnalysisPipeline,
    pipeline_config: PipelineConfig,
) -> None:
    result = pipeline.analyze(JPEG_BYTES, content_type="image/jpeg")
    assert len(result.scores) == len(pipeline_config.enabled_detector_names())


def test_disabling_a_detector_removes_its_signal(
    pipeline_config: PipelineConfig,
) -> None:
    disabled_config = pipeline_config.model_copy(
        update={"disabled_detectors": ["noise"]}
    )
    pipeline = ModularAnalysisPipeline(
        detectors=build_detectors(disabled_config.enabled_detector_names()),
        fusion=DeterministicFusionEngine(disabled_config),
        heatmap_generator=PlaceholderHeatmapGenerator(disabled_config),
        evidence_generator=PlaceholderEvidenceGenerator(disabled_config),
        explanation_generator=PlaceholderExplanationGenerator(disabled_config),
        pipeline_config=disabled_config,
    )
    result = pipeline.analyze(JPEG_BYTES, content_type="image/jpeg")
    assert all(score.category != ScoreCategory.NOISE_PATTERN for score in result.scores)


def test_removing_a_detector_does_not_change_pipeline(
    pipeline_config: PipelineConfig,
) -> None:
    """A detector is removable purely through configuration."""
    pruned_config = pipeline_config.model_copy(
        update={"detector_order": ["metadata", "texture"]}
    )
    pipeline = ModularAnalysisPipeline(
        detectors=build_detectors(pruned_config.enabled_detector_names()),
        fusion=DeterministicFusionEngine(pruned_config),
        heatmap_generator=PlaceholderHeatmapGenerator(pruned_config),
        evidence_generator=PlaceholderEvidenceGenerator(pruned_config),
        explanation_generator=PlaceholderExplanationGenerator(pruned_config),
        pipeline_config=pruned_config,
    )
    result = pipeline.analyze(JPEG_BYTES, content_type="image/jpeg")
    assert {score.category.value for score in result.scores} == {"metadata", "texture"}
    assert 0.0 <= result.confidence <= 1.0

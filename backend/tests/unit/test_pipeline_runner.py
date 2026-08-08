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
from app.pipeline.heatmap.generator import DeterministicHeatmapGenerator
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
    """Two runs produce identical deterministic outputs.

    Wall-clock measurements (``duration_ms`` and per-detector
    ``processing_time_ms``) are environment-dependent and excluded from the
    equality.
    """
    first = pipeline.analyze(JPEG_BYTES, content_type="image/jpeg")
    second = pipeline.analyze(JPEG_BYTES, content_type="image/jpeg")

    assert first.verdict == second.verdict
    assert first.confidence == second.confidence
    assert first.risk_level == second.risk_level
    assert first.explanation == second.explanation
    assert first.scores == second.scores
    assert first.indicators == second.indicators
    assert first.evidence == second.evidence
    assert first.metadata == second.metadata
    assert first.heatmap == second.heatmap

    assert first.report_data is not None and second.report_data is not None
    assert first.report_data.hypothesis_scores == second.report_data.hypothesis_scores
    assert first.report_data.runner_up_verdict == second.report_data.runner_up_verdict
    assert (
        first.report_data.classification_margin
        == second.report_data.classification_margin
    )
    assert _contributions_fingerprint(first) == _contributions_fingerprint(second)


def _contributions_fingerprint(result: PipelineResult) -> tuple[tuple, ...]:
    """Deterministic fingerprint of report contributions (times excluded)."""
    return tuple(
        (
            c.detector,
            c.detector_version,
            c.category,
            c.normalized_score,
            c.detector_confidence,
            c.reliability,
            c.weight_share,
            c.contribution,
            c.direction,
            c.hypothesis_weights,
            c.preferred_hypothesis,
        )
        for c in (result.report_data.contributions if result.report_data else ())
    )


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
        heatmap_generator=DeterministicHeatmapGenerator(disabled_config),
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
        heatmap_generator=DeterministicHeatmapGenerator(pruned_config),
        evidence_generator=PlaceholderEvidenceGenerator(pruned_config),
        explanation_generator=PlaceholderExplanationGenerator(pruned_config),
        pipeline_config=pruned_config,
    )
    result = pipeline.analyze(JPEG_BYTES, content_type="image/jpeg")
    assert {score.category.value for score in result.scores} == {"metadata", "texture"}
    assert 0.0 <= result.confidence <= 1.0

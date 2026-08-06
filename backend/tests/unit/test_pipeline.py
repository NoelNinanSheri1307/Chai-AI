"""Tests for the analysis pipeline abstraction and its placeholder."""

from __future__ import annotations

from app.core.enums import IndicatorType, RiskLevel, Verdict
from app.pipeline.base import AnalysisPipeline, PipelineResult
from app.pipeline.placeholder import PlaceholderAnalysisPipeline
from tests.sample_images import JPEG_BYTES


def test_placeholder_implements_abstract_contract() -> None:
    pipeline = PlaceholderAnalysisPipeline()
    assert isinstance(pipeline, AnalysisPipeline)


def test_abstract_contract_cannot_be_instantiated() -> None:
    import pytest

    with pytest.raises(TypeError):
        AnalysisPipeline()


def test_placeholder_returns_contract_shaped_result() -> None:
    result = PlaceholderAnalysisPipeline().analyze(
        JPEG_BYTES, content_type="image/jpeg"
    )
    assert isinstance(result, PipelineResult)
    assert result.verdict == Verdict.AI_GENERATED
    assert 0.0 <= result.confidence <= 1.0
    assert result.risk_level == RiskLevel.HIGH
    assert result.explanation
    assert result.duration_ms > 0
    assert result.scores
    assert all(0.0 <= score.value <= 1.0 for score in result.scores)
    assert any(
        indicator.type == IndicatorType.DIFFUSION for indicator in result.indicators
    )
    assert result.evidence
    assert result.metadata
    assert result.heatmap is not None
    assert 0.0 <= result.heatmap.overall_manipulation <= 1.0


def test_placeholder_is_deterministic() -> None:
    pipeline = PlaceholderAnalysisPipeline()
    first = pipeline.analyze(JPEG_BYTES, content_type="image/jpeg")
    second = pipeline.analyze(JPEG_BYTES, content_type="image/jpeg")
    assert first == second

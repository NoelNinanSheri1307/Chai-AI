"""Tests for the explainability framework (evidence and explanation)."""

from __future__ import annotations

from app.pipeline.config import PipelineConfig
from app.pipeline.explanation import EvidenceGenerator, ExplanationGenerator
from app.pipeline.explanation.placeholder import (
    PlaceholderEvidenceGenerator,
    PlaceholderExplanationGenerator,
)
from app.pipeline.fusion.engine import DeterministicFusionEngine


def test_generators_are_abstract() -> None:
    import pytest

    with pytest.raises(TypeError):
        EvidenceGenerator()
    with pytest.raises(TypeError):
        ExplanationGenerator()


def test_evidence_generator_returns_configured_lines(
    pipeline_config: PipelineConfig,
) -> None:
    fusion = DeterministicFusionEngine(pipeline_config).fuse([])
    generator = PlaceholderEvidenceGenerator(pipeline_config)
    evidence = generator.generate(fusion, [])
    assert evidence == pipeline_config.placeholder_evidence
    assert evidence


def test_evidence_output_is_deterministic(pipeline_config: PipelineConfig) -> None:
    fusion = DeterministicFusionEngine(pipeline_config).fuse([])
    generator = PlaceholderEvidenceGenerator(pipeline_config)
    assert generator.generate(fusion, []) == generator.generate(fusion, [])


def test_explanation_generator_returns_human_text(
    pipeline_config: PipelineConfig,
) -> None:
    fusion = DeterministicFusionEngine(pipeline_config).fuse([])
    generator = PlaceholderExplanationGenerator(pipeline_config)
    text = generator.explain(fusion, pipeline_config.placeholder_evidence, [])
    assert text == pipeline_config.placeholder_explanation
    assert "AI-generated" in text


def test_evidence_and_explanation_are_separate_concerns(
    pipeline_config: PipelineConfig,
) -> None:
    """Evidence (facts) and explanation (narrative) are distinct outputs."""
    fusion = DeterministicFusionEngine(pipeline_config).fuse([])
    evidence = PlaceholderEvidenceGenerator(pipeline_config).generate(fusion, [])
    explanation = PlaceholderExplanationGenerator(pipeline_config).explain(
        fusion, evidence, []
    )
    assert evidence != [explanation]

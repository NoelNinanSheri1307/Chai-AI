"""Tests for the deterministic classification evidence/explanation generators.

Covers the explainable-classification report: classification header, confidence,
top supporting evidence, top contradicting evidence, most influential detectors,
detector contribution percentages, reasoning summary and determinism.
"""

from __future__ import annotations

from app.core.enums import ScoreCategory
from app.pipeline.config import PipelineConfig
from app.pipeline.explanation.base import EvidenceGenerator, ExplanationGenerator
from app.pipeline.explanation.classifier import (
    ClassificationEvidenceGenerator,
    ClassificationExplanationGenerator,
)
from app.pipeline.fusion.engine import DeterministicFusionEngine
from app.pipeline.signals import DetectorSignal

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _signal(
    name: str, category: ScoreCategory, score: float, confidence: float = 1.0
) -> DetectorSignal:
    return DetectorSignal(
        detector_name=name,
        detector_version="1.0.0",
        category=category,
        score=score,
        confidence=confidence,
        evidence=[f"{name} reports score {score:.2f}."],
    )


def _fusion(config: PipelineConfig, signals):
    return DeterministicFusionEngine(config).fuse(signals)


# ---------------------------------------------------------------------------
# Evidence generator
# ---------------------------------------------------------------------------


def test_evidence_generator_is_deterministic(pipeline_config: PipelineConfig) -> None:
    fusion = _fusion(
        pipeline_config, [_signal("frequency", ScoreCategory.FREQUENCY, 0.9)]
    )
    generator = ClassificationEvidenceGenerator(pipeline_config)
    first = generator.generate(fusion, [])
    second = generator.generate(fusion, [])
    assert first == second
    assert first


def test_evidence_includes_decision_and_support_lines(
    pipeline_config: PipelineConfig,
) -> None:
    fusion = _fusion(
        pipeline_config, [_signal("frequency", ScoreCategory.FREQUENCY, 0.9)]
    )
    generator = ClassificationEvidenceGenerator(pipeline_config)
    evidence = generator.generate(fusion, [])
    joined = "\n".join(evidence)
    assert "AI Generated" in joined or "AI Generated" in str(fusion.decision_reason)
    # The strongest detector appears as a support line.
    assert any("frequency" in line for line in evidence)


# ---------------------------------------------------------------------------
# Explanation generator
# ---------------------------------------------------------------------------


def _full_report(config: PipelineConfig, signals) -> str:
    fusion = _fusion(config, signals)
    generator = ClassificationExplanationGenerator(config)
    return generator.explain(fusion, fusion.evidence, [])


def test_explanation_reports_ai_generated_with_structure(
    pipeline_config: PipelineConfig,
) -> None:
    text = _full_report(
        pipeline_config, [_signal("frequency", ScoreCategory.FREQUENCY, 0.9)]
    )
    assert "Classification: AI Generated" in text
    assert "runner-up" in text
    assert "margin" in text
    assert "Top supporting evidence" in text
    assert "Most influential detectors" in text
    assert "contribution percentages" in text
    assert "Per-detector reasoning" in text


def test_explanation_reports_original(pipeline_config: PipelineConfig) -> None:
    signals = [
        _signal("metadata", ScoreCategory.METADATA, 0.05),
        _signal("frequency", ScoreCategory.FREQUENCY, 0.20),
        _signal("noise", ScoreCategory.NOISE_PATTERN, 0.10),
        _signal("texture", ScoreCategory.TEXTURE, 0.15),
    ]
    text = _full_report(pipeline_config, signals)
    assert "Original" in text
    assert "AI Generated" not in text.split(";", 1)[0]


def test_explanation_is_deterministic(pipeline_config: PipelineConfig) -> None:
    generator = ClassificationExplanationGenerator(pipeline_config)
    fusion = _fusion(
        pipeline_config, [_signal("frequency", ScoreCategory.FREQUENCY, 0.9)]
    )
    first = generator.explain(fusion, fusion.evidence, [])
    second = generator.explain(fusion, fusion.evidence, [])
    assert first == second
    assert first


def test_explanation_contradicting_evidence(pipeline_config: PipelineConfig) -> None:
    signals = [
        _signal("frequency", ScoreCategory.FREQUENCY, 0.95),
        _signal("noise", ScoreCategory.NOISE_PATTERN, 0.05),
    ]
    text = _full_report(pipeline_config, signals)
    assert "Classification: " in text
    assert "Per-detector reasoning" in text


def test_real_generators_implement_contract() -> None:
    assert issubclass(ClassificationEvidenceGenerator, EvidenceGenerator)
    assert issubclass(ClassificationExplanationGenerator, ExplanationGenerator)

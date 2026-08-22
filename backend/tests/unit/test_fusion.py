"""Tests for the deterministic fusion engine framework."""

from __future__ import annotations

import pytest

from app.core.enums import (
    RiskLevel,
    ScoreCategory,
    Verdict,
)
from app.pipeline.config import PipelineConfig
from app.pipeline.fusion import DeterministicFusionEngine, FusionEngine, FusionResult
from app.pipeline.signals import DetectorSignal

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _signal(
    name: str,
    category: ScoreCategory,
    score: float,
    confidence: float = 1.0,
    evidence: list[str] | None = None,
) -> DetectorSignal:
    return DetectorSignal(
        detector_name=name,
        detector_version="1.0.0",
        category=category,
        score=score,
        confidence=confidence,
        evidence=evidence or [f"{name} reports score {score:.2f}."],
    )


def _engine(config: PipelineConfig) -> DeterministicFusionEngine:
    return DeterministicFusionEngine(config)


def _clean_signals() -> list[DetectorSignal]:
    """All detectors return low manipulation scores (photo-like)."""
    return [
        _signal("metadata", ScoreCategory.METADATA, 0.05),
        _signal("frequency", ScoreCategory.FREQUENCY, 0.20),
        _signal("ela", ScoreCategory.COMPRESSION, 0.15),
        _signal("noise", ScoreCategory.NOISE_PATTERN, 0.12),
        _signal("compression", ScoreCategory.EDGE_CONSISTENCY, 0.10),
        _signal("texture", ScoreCategory.TEXTURE, 0.15),
        _signal("lighting", ScoreCategory.LIGHTING, 0.10),
    ]


def _generated_signals() -> list[DetectorSignal]:
    """All detectors strongly and consistently report synthetic content."""
    return [
        _signal("metadata", ScoreCategory.METADATA, 0.85),
        _signal("frequency", ScoreCategory.FREQUENCY, 0.90),
        _signal("noise", ScoreCategory.NOISE_PATTERN, 0.80),
        _signal("compression", ScoreCategory.EDGE_CONSISTENCY, 0.88),
        _signal("texture", ScoreCategory.TEXTURE, 0.75),
        _signal("lighting", ScoreCategory.LIGHTING, 0.85),
    ]


# ---------------------------------------------------------------------------
# Contract
# ---------------------------------------------------------------------------


def test_fusion_engine_is_abstract() -> None:
    with pytest.raises(TypeError):
        FusionEngine()


def test_fusion_returns_typed_result(pipeline_config: PipelineConfig) -> None:
    result = _engine(pipeline_config).fuse(_generated_signals())
    assert isinstance(result, FusionResult)
    assert result.verdict in Verdict
    assert 0.0 <= result.confidence <= 1.0
    assert result.risk_level in RiskLevel
    assert result.scores
    assert result.indicators is not None
    assert result.weights
    assert result.contributions
    assert result.evidence
    assert result.decision_reason


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


def test_fusion_is_deterministic(pipeline_config: PipelineConfig) -> None:
    engine = _engine(pipeline_config)
    signals = _generated_signals()
    assert engine.fuse(signals) == engine.fuse(signals)


# ---------------------------------------------------------------------------
# Verdict decisions
# ---------------------------------------------------------------------------


def test_clean_image_is_original_high_confidence(
    pipeline_config: PipelineConfig,
) -> None:
    result = _engine(pipeline_config).fuse(_clean_signals())
    assert result.verdict == Verdict.ORIGINAL
    assert result.confidence >= 0.85
    assert result.risk_level == RiskLevel.LOW


def test_generated_image_is_ai_generated(pipeline_config: PipelineConfig) -> None:
    result = _engine(pipeline_config).fuse(_generated_signals())
    assert result.verdict == Verdict.AI_GENERATED
    assert result.confidence >= 0.8


def test_conflicting_detectors_resolve_to_low_margin(
    pipeline_config: PipelineConfig,
) -> None:
    # Half the detectors strongly indicate manipulation, half indicate original:
    # the evidence is mutually contradictory, so the classifier must not be
    # decisive. It may pick one class, but the margin over the runner-up and the
    # confidence must both be low.
    signals = [
        _signal("metadata", ScoreCategory.METADATA, 0.9),
        _signal("frequency", ScoreCategory.FREQUENCY, 0.9),
        _signal("noise", ScoreCategory.NOISE_PATTERN, 0.1),
        _signal("compression", ScoreCategory.EDGE_CONSISTENCY, 0.1),
        _signal("texture", ScoreCategory.TEXTURE, 0.1),
    ]
    result = _engine(pipeline_config).fuse(signals)
    assert 0.0 <= result.confidence < 0.7
    assert result.runner_up_verdict is not None


def test_single_detector_still_yields_valid_verdict(
    pipeline_config: PipelineConfig,
) -> None:
    signals = [_signal("frequency", ScoreCategory.FREQUENCY, 0.90)]
    result = _engine(pipeline_config).fuse(signals)
    assert result.verdict == Verdict.AI_GENERATED
    assert result.coverage < 1.0


def test_no_signals_returns_default_with_zero_confidence(
    pipeline_config: PipelineConfig,
) -> None:
    result = _engine(pipeline_config).fuse([])
    assert result.verdict == Verdict.ORIGINAL
    assert result.confidence == 0.0
    assert result.risk_level == RiskLevel.LOW


# ---------------------------------------------------------------------------
# Confidence
# ---------------------------------------------------------------------------


def test_more_detector_coverage_raises_confidence(
    pipeline_config: PipelineConfig,
) -> None:
    one = _engine(pipeline_config).fuse(
        [_signal("frequency", ScoreCategory.FREQUENCY, 0.90)]
    )
    many = _engine(pipeline_config).fuse(
        [_signal("frequency", ScoreCategory.FREQUENCY, 0.90) for _ in range(6)]
    )
    assert many.coverage > one.coverage
    assert many.confidence >= one.confidence


# ---------------------------------------------------------------------------
# Weights / configuration
# ---------------------------------------------------------------------------


def test_reliability_weights_come_from_configuration(
    pipeline_config: PipelineConfig,
) -> None:
    result = _engine(pipeline_config).fuse(_generated_signals())
    for signal in _generated_signals():
        assert result.weights[signal.category.value] == pipeline_config.reliability_for(
            signal.detector_name
        )


def test_configuration_override_changes_verdict(
    pipeline_config: PipelineConfig,
) -> None:
    # Re-weighting a detector in the contribution matrix flips the classification.
    matrix = {
        name: dict(weights)
        for name, weights in pipeline_config.classifier_contribution_matrix.items()
    }
    matrix["texture"] = {"original": 1.0, "ai_generated": 0.0}
    hard = pipeline_config.model_copy(update={"classifier_contribution_matrix": matrix})
    signals = [_signal("texture", ScoreCategory.TEXTURE, 0.6) for _ in range(6)]
    assert _engine(pipeline_config).fuse(signals).verdict == Verdict.AI_GENERATED
    assert _engine(hard).fuse(signals).verdict == Verdict.ORIGINAL


def test_risk_is_verdict_aware(pipeline_config: PipelineConfig) -> None:
    # An original is never high risk, however confident the reading is.
    assert _engine(pipeline_config).fuse(_clean_signals()).risk_level == RiskLevel.LOW
    # Strong, unanimous synthetic content is high risk.
    assert (
        _engine(pipeline_config).fuse(_generated_signals()).risk_level == RiskLevel.HIGH
    )


# ---------------------------------------------------------------------------
# Contributions / evidence
# ---------------------------------------------------------------------------


def test_contributions_expose_detector_attribution(
    pipeline_config: PipelineConfig,
) -> None:
    result = _engine(pipeline_config).fuse(_generated_signals())
    assert len(result.contributions) == len(_generated_signals())
    for contribution in result.contributions:
        assert contribution.detector
        assert 0.0 <= contribution.normalized_score <= 1.0
        assert contribution.weight_share >= 0.0
        assert contribution.contribution >= 0.0
        assert contribution.supports_manipulation()


def test_evidence_is_deduplicated_preserving_source(
    pipeline_config: PipelineConfig,
) -> None:
    shared = "identical evidence line"
    signals = [
        _signal("noise", ScoreCategory.NOISE_PATTERN, 0.9, evidence=[shared]),
        _signal("compression", ScoreCategory.EDGE_CONSISTENCY, 0.9, evidence=[shared]),
        _signal("texture", ScoreCategory.TEXTURE, 0.9, evidence=["unique line"]),
    ]
    result = _engine(pipeline_config).fuse(signals)
    # The duplicate collapses to a single entry that still names a detector
    # source, and the unique line survives with its own source prefix.
    assert len(result.evidence) == 2
    shared_entries = [
        line for line in result.evidence if "identical evidence line" in line
    ]
    assert len(shared_entries) == 1
    assert any(line.startswith(("noise", "compression")) for line in shared_entries)
    assert any(
        "unique line" in line and line.startswith("texture") for line in result.evidence
    )


def test_evidence_ranked_by_contribution(
    pipeline_config: PipelineConfig,
) -> None:
    # Despite having a lower reliability weight, the metadata detector's very
    # strong score makes it the largest contributor, so its evidence ranks first.
    strong_low_weight = _signal("metadata", ScoreCategory.METADATA, 0.99)
    weak_high_weight = _signal("frequency", ScoreCategory.FREQUENCY, 0.10)
    result = _engine(pipeline_config).fuse([strong_low_weight, weak_high_weight])
    contributions = {c.detector: c.contribution for c in result.contributions}
    assert contributions["metadata"] > contributions["frequency"]
    assert result.evidence
    assert result.evidence[0].startswith("metadata")


def test_weights_configuration_version_is_stamped(
    pipeline_config: PipelineConfig,
) -> None:
    result = _engine(pipeline_config).fuse(_generated_signals())
    assert result.weight_config_version == pipeline_config.weight_config_version
    assert result.fusion_version == pipeline_config.fusion_version
    assert result.pipeline_version == pipeline_config.pipeline_version
    assert result.detector_versions


def test_confidence_factors_sum_to_one(pipeline_config: PipelineConfig) -> None:
    assert pipeline_config.confidence_weight_sum() == pytest.approx(1.0)

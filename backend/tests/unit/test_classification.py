"""Tests for the two-hypothesis (Original / Real vs AI Generated) engine.

These cover the deterministic classifier: hypothesis scores, winner/runner-up and
margin, two-class verdicts, contribution percentages, confidence calibration,
explainable reasoning, determinism, conflicting evidence, configuration
overrides and explicit regression proving AI_EDITED is never returned.
"""

from __future__ import annotations

import pytest

from app.core.enums import ScoreCategory, Verdict
from app.pipeline.config import PipelineConfig
from app.pipeline.fusion.classify import (
    compute_classification,
)
from app.pipeline.fusion.engine import DeterministicFusionEngine
from app.pipeline.fusion.hypotheses import Hypothesis, HypothesisScores, build_response
from app.pipeline.fusion.normalize import NormalizedSignal, normalize_signal
from app.pipeline.signals import DetectorSignal

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _signal(
    name: str,
    category: ScoreCategory,
    score: float,
    confidence: float = 1.0,
    reliability: float | None = None,
) -> DetectorSignal:
    return DetectorSignal(
        detector_name=name,
        detector_version="1.0.0",
        category=category,
        score=score,
        confidence=confidence,
        evidence=[f"{name} reports score {score:.2f}."],
    )


def _normalized(
    signal: DetectorSignal, reliability: float | None = None
) -> NormalizedSignal:
    return normalize_signal(signal, reliability)


def _engine(config: PipelineConfig) -> DeterministicFusionEngine:
    return DeterministicFusionEngine(config)


# ---------------------------------------------------------------------------
# Hypothesis / response model
# ---------------------------------------------------------------------------


def test_response_peaks_at_each_centre(pipeline_config: PipelineConfig) -> None:
    response = build_response(pipeline_config)
    # A clean reading strongly supports Original and weakly supports Generated.
    assert response.support(0.0, Hypothesis.ORIGINAL) > 0.99
    assert response.support(1.0, Hypothesis.AI_GENERATED) > 0.99


def test_hypothesis_scores_are_typed(pipeline_config: PipelineConfig) -> None:
    classification = compute_classification(
        [_normalized(_signal("texture", ScoreCategory.TEXTURE, 0.5))],
        pipeline_config,
        total_capacity=7,
    )
    assert isinstance(classification.scores, HypothesisScores)
    assert len(classification.scores) == 2


# ---------------------------------------------------------------------------
# Verdict classification across the two classes
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("name", "category", "score", "expected"),
    [
        ("texture", ScoreCategory.TEXTURE, 0.10, Verdict.ORIGINAL),
        ("texture", ScoreCategory.TEXTURE, 0.90, Verdict.AI_GENERATED),
    ],
)
def test_score_direction_maps_to_expected_class(
    pipeline_config: PipelineConfig, name, category, score, expected
) -> None:
    signals = [_signal(name, category, score) for _ in range(6)]
    verdict = _engine(pipeline_config).fuse(signals).verdict
    assert verdict is expected


def test_original_classification_wins_for_clean_signals(
    pipeline_config: PipelineConfig,
) -> None:
    signals = [
        _signal("metadata", ScoreCategory.METADATA, 0.05),
        _signal("frequency", ScoreCategory.FREQUENCY, 0.20),
        _signal("ela", ScoreCategory.COMPRESSION, 0.15),
        _signal("noise", ScoreCategory.NOISE_PATTERN, 0.12),
        _signal("compression", ScoreCategory.EDGE_CONSISTENCY, 0.10),
        _signal("texture", ScoreCategory.TEXTURE, 0.15),
        _signal("lighting", ScoreCategory.LIGHTING, 0.10),
    ]
    result = _engine(pipeline_config).fuse(signals)
    assert result.verdict == Verdict.ORIGINAL
    # Original dominates the hypothesis probabilities.
    assert result.hypothesis_scores[0] > result.hypothesis_scores[1]
    assert result.confidence >= 0.85


def test_ai_generated_classification_wins_for_synthetic_evidence(
    pipeline_config: PipelineConfig,
) -> None:
    signals = [
        _signal("frequency", ScoreCategory.FREQUENCY, 0.90),
        _signal("texture", ScoreCategory.TEXTURE, 0.85),
        _signal("lighting", ScoreCategory.LIGHTING, 0.85),
        _signal("noise", ScoreCategory.NOISE_PATTERN, 0.80),
    ]
    result = _engine(pipeline_config).fuse(signals)
    assert result.verdict == Verdict.AI_GENERATED
    assert result.hypothesis_scores[1] > result.hypothesis_scores[0]


def test_borderline_real_vs_ai_generated(
    pipeline_config: PipelineConfig,
) -> None:
    # Borderline readings produce a valid verdict and measurable margin
    signals = [
        _signal("texture", ScoreCategory.TEXTURE, 0.52),
        _signal("lighting", ScoreCategory.LIGHTING, 0.48),
    ]
    result = _engine(pipeline_config).fuse(signals)
    assert result.verdict in {Verdict.ORIGINAL, Verdict.AI_GENERATED}
    assert 0.0 <= result.confidence <= 1.0
    assert result.classification_margin >= 0.0


def test_runner_up_and_margin_are_exposed(pipeline_config: PipelineConfig) -> None:
    result = _engine(pipeline_config).fuse(
        [_signal("frequency", ScoreCategory.FREQUENCY, 0.90)]
    )
    assert result.verdict == Verdict.AI_GENERATED
    assert result.runner_up_verdict is not None
    assert result.runner_up_verdict != result.verdict
    assert result.runner_up_verdict == Verdict.ORIGINAL
    assert result.classification_margin >= 0.0


# ---------------------------------------------------------------------------
# Contrasting / conflicting detectors
# ---------------------------------------------------------------------------


def test_conflicting_detectors_yield_weak_classification(
    pipeline_config: PipelineConfig,
) -> None:
    signals = [
        _signal("metadata", ScoreCategory.METADATA, 0.95),
        _signal("frequency", ScoreCategory.FREQUENCY, 0.95),
        _signal("noise", ScoreCategory.NOISE_PATTERN, 0.05),
        _signal("compression", ScoreCategory.EDGE_CONSISTENCY, 0.05),
        _signal("texture", ScoreCategory.TEXTURE, 0.05),
    ]
    result = _engine(pipeline_config).fuse(signals)
    assert result.confidence < 0.7


def test_detector_agreement_tracks_similarity(pipeline_config: PipelineConfig) -> None:
    agree = compute_classification(
        [
            _normalized(_signal("frequency", ScoreCategory.FREQUENCY, 0.9)),
            _normalized(_signal("lighting", ScoreCategory.LIGHTING, 0.85)),
        ],
        pipeline_config,
        total_capacity=7,
    )
    conflict = compute_classification(
        [
            _normalized(_signal("frequency", ScoreCategory.FREQUENCY, 0.9)),
            _normalized(_signal("noise", ScoreCategory.NOISE_PATTERN, 0.1)),
        ],
        pipeline_config,
        total_capacity=7,
    )
    assert agree.agreement > conflict.agreement
    assert agree.confidence > conflict.confidence


# ---------------------------------------------------------------------------
# Confidence
# ---------------------------------------------------------------------------


def test_margin_increases_confidence(pipeline_config: PipelineConfig) -> None:
    strong = [
        _signal("frequency", ScoreCategory.FREQUENCY, 0.9),
        _signal("lighting", ScoreCategory.LIGHTING, 0.85),
    ]
    weak = [
        _signal("frequency", ScoreCategory.FREQUENCY, 0.9),
        _signal("noise", ScoreCategory.NOISE_PATTERN, 0.3),
    ]
    strong_result = _engine(pipeline_config).fuse(strong)
    weak_result = _engine(pipeline_config).fuse(weak)
    assert strong_result.confidence > weak_result.confidence


def test_coverage_drops_with_fewer_active_detectors(
    pipeline_config: PipelineConfig,
) -> None:
    many = _engine(pipeline_config).fuse(
        [_signal("frequency", ScoreCategory.FREQUENCY, 0.9) for _ in range(6)]
    )
    one = _engine(pipeline_config).fuse(
        [_signal("frequency", ScoreCategory.FREQUENCY, 0.9)]
    )
    assert many.coverage > one.coverage
    assert many.confidence >= one.confidence


def test_reliability_from_detector_confidence(pipeline_config: PipelineConfig) -> None:
    low = _engine(pipeline_config).fuse(
        [_signal("frequency", ScoreCategory.FREQUENCY, 0.9, confidence=0.4)]
    )
    high = _engine(pipeline_config).fuse(
        [_signal("frequency", ScoreCategory.FREQUENCY, 0.9, confidence=1.0)]
    )
    assert low.reliability < high.reliability


def test_empty_signals_yield_zero_confidence(pipeline_config: PipelineConfig) -> None:
    result = _engine(pipeline_config).fuse([])
    assert result.verdict == Verdict.ORIGINAL
    assert result.confidence == 0.0
    assert result.classification_margin == 0.0


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


def test_classification_is_deterministic(pipeline_config: PipelineConfig) -> None:
    engine = _engine(pipeline_config)
    first = engine.fuse([_signal("frequency", ScoreCategory.FREQUENCY, 0.9)])
    second = engine.fuse([_signal("frequency", ScoreCategory.FREQUENCY, 0.9)])
    assert first == second


def test_reasoning_and_contributions_are_stable(
    pipeline_config: PipelineConfig,
) -> None:
    result = _engine(pipeline_config).fuse(
        [_signal("texture", ScoreCategory.TEXTURE, 0.9) for _ in range(4)]
    )
    assert result.detector_reasoning
    # Percentages always sum to 1 across the two hypotheses per detector.
    for entry in result.detector_reasoning:
        weights = entry["hypothesis_weights"]
        total = weights["original"] + weights["ai_generated"]
        assert total == pytest.approx(1.0, abs=0.01)


# ---------------------------------------------------------------------------
# Contribution matrix / configuration
# ---------------------------------------------------------------------------


def test_unknown_detector_falls_back_to_contribution_default(
    pipeline_config: PipelineConfig,
) -> None:
    classification = compute_classification(
        [_normalized(_signal("unknown", ScoreCategory.TEXTURE, 0.9))],
        pipeline_config,
        total_capacity=7,
    )
    assert classification.detector_contributions
    weights = classification.detector_contributions[0].weights
    assert pytest.approx(1.0) == sum(weights)


def test_contribution_matrix_recalibration_flips_winner(
    pipeline_config: PipelineConfig,
) -> None:
    # Re-weighting a detector to support Original flips texture reading.
    matrix = pipeline_config.classifier_contribution_matrix | {
        "texture": {"original": 1.0, "ai_generated": 0.0}
    }
    reconfigured = pipeline_config.model_copy(
        update={"classifier_contribution_matrix": matrix}
    )
    signals = [_signal("texture", ScoreCategory.TEXTURE, 0.6) for _ in range(6)]
    assert _engine(reconfigured).fuse(signals).verdict == Verdict.ORIGINAL


def test_classification_weight_sum_is_one(pipeline_config: PipelineConfig) -> None:
    assert pipeline_config.classification_weight_sum() == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# Regression Tests: AI_EDITED is never returned
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("score", [0.0, 0.1, 0.25, 0.45, 0.5, 0.55, 0.7, 0.85, 1.0])
def test_classifier_never_returns_ai_edited(
    pipeline_config: PipelineConfig, score: float
) -> None:
    for detector in ["metadata", "frequency", "ela", "noise", "compression", "texture", "lighting"]:
        result = _engine(pipeline_config).fuse([_signal(detector, ScoreCategory.TEXTURE, score)])
        assert result.verdict in {Verdict.ORIGINAL, Verdict.AI_GENERATED}
        assert result.verdict.value != "aiEdited"


def test_hypothesis_and_verdict_labels() -> None:
    from app.pipeline.fusion.decision import verdict_for_hypothesis

    assert verdict_for_hypothesis(Hypothesis.ORIGINAL) == Verdict.ORIGINAL
    assert verdict_for_hypothesis(Hypothesis.AI_GENERATED) == Verdict.AI_GENERATED

"""Tests for pipeline configuration loading and caching."""

from __future__ import annotations

import pytest

from app.core.enums import RiskLevel, Verdict
from app.pipeline.config import (
    PipelineConfig,
    clear_pipeline_config_cache,
    get_pipeline_config,
)


def test_defaults_are_deterministic() -> None:
    config = PipelineConfig()
    assert config.detector_order == [
        "metadata",
        "frequency",
        "ela",
        "noise",
        "compression",
        "texture",
        "lighting",
    ]
    assert config.default_confidence == 0.91
    assert config.enabled_detector_names() == config.detector_order


def test_disabled_detectors_are_excluded() -> None:
    config = PipelineConfig(disabled_detectors=["noise", "ela"])
    assert "noise" not in config.enabled_detector_names()
    assert "ela" not in config.enabled_detector_names()
    assert "metadata" in config.enabled_detector_names()


def test_weights_and_risk_thresholds() -> None:
    config = PipelineConfig()
    assert config.weight_for("texture") == 0.8
    assert config.risk_level_for(0.2) == RiskLevel.LOW
    assert config.risk_level_for(0.5) == RiskLevel.MEDIUM
    assert config.risk_level_for(0.8) == RiskLevel.HIGH


def test_risk_is_verdict_aware() -> None:
    config = PipelineConfig()
    # Originals are never high risk regardless of confidence.
    assert config.risk_for(Verdict.ORIGINAL, 0.99) == RiskLevel.LOW
    # Generated content is high risk once confidence reaches the medium band.
    assert config.risk_for(Verdict.AI_GENERATED, 0.9) == RiskLevel.HIGH
    # Edited risk tracks the confidence bands.
    assert config.risk_for(Verdict.AI_EDITED, 0.8) == RiskLevel.HIGH
    assert config.risk_for(Verdict.AI_EDITED, 0.2) == RiskLevel.LOW
    assert config.risk_for(Verdict.AI_GENERATED, 0.2) == RiskLevel.MEDIUM


def test_detector_reliability_defaults() -> None:
    config = PipelineConfig()
    assert config.reliability_for("frequency") == pytest.approx(0.18)
    assert config.reliability_for("unknown_detector") == pytest.approx(
        config.default_detector_reliability
    )


def test_confidence_factors_sum_to_one() -> None:
    assert PipelineConfig().confidence_weight_sum() == pytest.approx(1.0)


def test_environment_override(monkeypatch) -> None:
    monkeypatch.setenv("CHAI_PIPELINE_DEFAULT_CONFIDENCE", "0.5")
    config = PipelineConfig()
    assert config.default_confidence == 0.5


def test_cached_getter_is_singleton_and_clearable() -> None:
    first = get_pipeline_config()
    second = get_pipeline_config()
    assert first is second

    clear_pipeline_config_cache()
    assert get_pipeline_config() is not first

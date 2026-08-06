"""Pipeline configuration.

All pipeline knobs live here rather than being hardcoded in the stage
implementations: detector ordering and enablement, per-category fusion weights,
risk thresholds, the deterministic placeholder decision (verdict/confidence/risk)
and the placeholder heatmap/evidence/explanation content.

Values are read from ``CHAI_PIPELINE_*`` environment variables with deterministic
defaults, so the framework runs unchanged while every tunable is overridable in
configuration. ``clear_pipeline_config_cache`` is provided for the test suite.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.enums import RiskLevel, Verdict


class PipelineConfig(BaseSettings):
    """Deterministic, environment-overridable pipeline settings."""

    model_config = SettingsConfigDict(
        env_prefix="CHAI_PIPELINE_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Versioning --------------------------------------------------------
    framework_version: str = "0.1.0"
    pipeline_version: str = "1.0"
    fusion_version: str = "0.1.0"

    # Detector orchestration --------------------------------------------
    # Ordered list of detector names executed by the pipeline runner.
    detector_order: list[str] = Field(
        default_factory=lambda: [
            "metadata",
            "frequency",
            "ela",
            "noise",
            "compression",
            "texture",
            "lighting",
        ]
    )
    # Detectors removed from this set are simply skipped by the runner.
    disabled_detectors: list[str] = Field(default_factory=list)

    # Fusion -------------------------------------------------------------
    # Per-category weights used by the fusion engine when aggregating signals.
    category_weights: dict[str, float] = Field(
        default_factory=lambda: {
            "texture": 0.8,
            "metadata": 0.5,
            "lighting": 0.3,
            "frequency": 0.8,
            "noisePattern": 0.7,
            "compression": 0.6,
            "edgeConsistency": 0.6,
            "colorDistribution": 0.4,
        }
    )
    # Risk-level decision thresholds on the fused confidence score.
    medium_risk_threshold: float = 0.4
    high_risk_threshold: float = 0.7

    # Deterministic placeholder decision ---------------------------------
    # The placeholder pipeline does no real math; it emits this fixed decision
    # so the application lifecycle stays deterministic. The real fusion engine
    # (a later milestone) will derive these values from the signals. The risk
    # level is derived from ``default_confidence`` via the thresholds above.
    default_verdict: Verdict = Verdict.AI_GENERATED
    default_confidence: float = 0.91

    # Placeholder outputs ------------------------------------------------
    heatmap_overall_manipulation: float = 0.78
    placeholder_evidence: list[str] = Field(
        default_factory=lambda: [
            "Sensor and frequency analyses returned clean profiles."
        ]
    )
    placeholder_explanation: str = (
        "Image appears to be fully or largely AI-generated. Strongest signal: "
        "soft, watercolor-like artifacts consistent with diffusion synthesis."
    )

    # ------------------------------------------------------------------
    # Derived helpers
    # ------------------------------------------------------------------
    def enabled_detector_names(self) -> list[str]:
        """Return the detector names to execute, honouring disablement."""
        disabled = set(self.disabled_detectors)
        return [name for name in self.detector_order if name not in disabled]

    def weight_for(self, category: str) -> float:
        """Return the configured fusion weight for a score category."""
        return self.category_weights.get(category, 1.0)

    def risk_level_for(self, confidence: float) -> RiskLevel:
        """Map a fused confidence score to a risk level using thresholds."""
        if confidence >= self.high_risk_threshold:
            return RiskLevel.HIGH
        if confidence >= self.medium_risk_threshold:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW


@lru_cache(maxsize=1)
def get_pipeline_config() -> PipelineConfig:
    """Return the cached :class:`PipelineConfig` instance."""
    return PipelineConfig()


def clear_pipeline_config_cache() -> None:
    """Discard the cached pipeline configuration (used by the test suite)."""
    get_pipeline_config.cache_clear()

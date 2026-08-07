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

    # Fusion versioning ------------------------------------------------
    # Version stamped on every result by the fusion engine. Bump when the fusion
    # algorithm or its configuration changes so stored results stay auditable.
    weight_config_version: str = "1.0"

    # Detector reliability --------------------------------------------
    # Per-detector reliability weights used by the fusion engine. They express
    # how much each forensic signal is trusted relative to the others and are
    # provided purely from configuration so they can be re-calibrated without
    # touching code. Weights need not sum to one: the fusion engine normalizes
    # them each run.
    detector_reliability: dict[str, float] = Field(
        default_factory=lambda: {
            "metadata": 0.10,
            "frequency": 0.18,
            "ela": 0.18,
            "noise": 0.12,
            "compression": 0.10,
            "texture": 0.15,
            "lighting": 0.17,
        }
    )
    # Reliability applied to a detector that is not present in
    # ``detector_reliability`` (when a new detector ships before it is tuned).
    default_detector_reliability: float = 1.0

    # Verdict decision thresholds -------------------------------------
    # A fused manipulation score at or below this ceiling maps to ORIGINAL.
    original_max_manipulation: float = 0.30
    # AI_GENERATED requires both a strong manipulation score and coherent
    # detector agreement (see ``generated_min_agreement``); everything else that
    # is not clearly ORIGINAL is AI_EDITED (localized / partial / conflicting).
    generated_min_manipulation: float = 0.55
    generated_min_agreement: float = 0.60

    # Confidence model --------------------------------------------------
    # Confidence blends four explainable factors. The weights sum to roughly 1;
    # each factor lies in [0, 1], so the blended confidence stays in [0, 1].
    confidence_agreement_weight: float = 0.40
    confidence_decisiveness_weight: float = 0.25
    confidence_coverage_weight: float = 0.20
    confidence_reliability_weight: float = 0.15

    # Contribution classification --------------------------------------
    # A detector score at or above this bound is classed as evidencing
    # manipulation; at or below (1 - threshold) it evidences an original.
    manipulation_support_threshold: float = 0.5

    # ------------------------------------------------------------------
    # Three-class forensic classification (Original | AI Edited | AI Generated)
    # ------------------------------------------------------------------
    # Per-hypothesis response curve centres on the normalized manipulation
    # score: Original evidence peaks at a clean (low) reading, AI Edited peaks
    # at a localized/partial (mid) reading, AI Generated peaks at a strongly
    # synthetic (high) reading. The response is a Gaussian ``e^(-d^2/2sigma^2)``
    # over the signed distance from each centre, so the same score produces a
    # *soft* amount of evidence for every hypothesis rather than a hard cut.
    classifier_original_center: float = 0.0
    classifier_edited_center: float = 0.5
    classifier_generated_center: float = 1.0
    # Gaussian standard deviation (in score units) controlling how quickly
    # evidence for a hypothesis fades as the reading moves away from its center.
    classifier_resolution: float = 0.15

    # Detector contribution matrix. For each detector, how strongly its signal
    # may support each of the three hypotheses, given the score it measured.
    # High coefficients mark detectors whose evidence *naturally* speaks to a
    # hypothesis (e.g. ELA -> AI Edited, frequency -> AI Generated); low values
    # mean the detector rarely implies that hypothesis. All values are used as
    # relative weights and normalised at evaluation time.
    classifier_contribution_matrix: dict[str, dict[str, float]] = Field(
        default_factory=lambda: {
            "metadata": {
                "original": 0.90,
                "ai_edited": 0.20,
                "ai_generated": 0.25,
            },
            "frequency": {
                "original": 0.15,
                "ai_edited": 0.30,
                "ai_generated": 1.00,
            },
            "ela": {
                "original": 0.15,
                "ai_edited": 1.00,
                "ai_generated": 0.40,
            },
            "noise": {
                "original": 0.85,
                "ai_edited": 0.50,
                "ai_generated": 0.45,
            },
            "compression": {
                "original": 0.50,
                "ai_edited": 0.90,
                "ai_generated": 0.40,
            },
            "texture": {
                "original": 0.40,
                "ai_edited": 0.70,
                "ai_generated": 0.80,
            },
            "lighting": {
                "original": 0.40,
                "ai_edited": 0.60,
                "ai_generated": 0.60,
            },
        }
    )
    # Weight applied to a detector missing from ``classifier_contribution_matrix``.
    # All three hypotheses receive this same fallback so partial configuration
    # never fails (the detector still contributes proportionally to its reading).
    classifier_contribution_default: float = 0.5

    # Confidence model for classification. Blends the classification margin,
    # detector agreement, the winning-hypothesis probability, the active-detector
    # coverage and the detectors' self-assessed reliability. The weights sum to 1.
    classification_margin_weight: float = 0.40
    classification_agreement_weight: float = 0.20
    classification_separation_weight: float = 0.20
    classification_coverage_weight: float = 0.10
    classification_reliability_weight: float = 0.10

    # Deterministic reasoning templates used by the explainer. ``{}`` placeholders
    # are filled from each classification at runtime.
    reasoning_intro_original: str = (
        "Camera metadata is internally consistent, natural sensor noise is present, "
        "frequency analysis found no periodic artifacts, and lighting remains "
        "physically coherent."
    )
    reasoning_intro_edited: str = (
        "Localized ELA artifacts, inconsistent noise patterns, and compression "
        "discontinuities indicate modification of an authentic photograph."
    )
    reasoning_intro_generated: str = (
        "Strong frequency artifacts, globally uniform texture, inconsistent lighting, "
        "and synthetic noise characteristics strongly support AI generation."
    )
    reasoning_support_line: str = "{detector} supported {hypothesis_label}."
    reasoning_oppose_line: str = "{detector} opposed the winning hypothesis."
    reasoning_detailed_line: str = (
        "{detector} weighted {original:.0%} toward {original_label}, "
        "{edited:.0%} toward {edited_label}, and {generated:.0%} toward "
        "{generated_label}."
    )

    # Deterministic placeholder decision ---------------------------------
    # The placeholder pipeline does no real math; it emits this fixed decision
    # so the application lifecycle stays deterministic. The real fusion engine
    # (a later milestone) will derive these values from the signals. The risk
    # level is derived from ``default_confidence`` via the thresholds above.
    default_verdict: Verdict = Verdict.AI_GENERATED
    default_confidence: float = 0.91

    # Placeholder outputs ------------------------------------------------
    # Fallback overall manipulation score used when no fusion result is
    # available (for example in isolated heatmap tests).
    heatmap_overall_manipulation: float = 0.78

    # Real heatmap generation --------------------------------------------
    heatmap_enabled: bool = True
    # Regions overlapping above this IoU are merged into a single region.
    heatmap_iou_threshold: float = 0.4
    # Normalized area threshold below which regions are dropped as noise.
    heatmap_min_region_area: float = 0.0005
    # Maximum number of regions returned (strongest first).
    heatmap_max_regions: int = 12
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

    def reliability_for(self, detector: str) -> float:
        """Return the configured reliability weight for a detector.

        Unknown detectors fall back to ``default_detector_reliability`` so the
        pipeline never drops a signal just because its weight was not tuned yet.
        """
        return max(
            0.0,
            self.detector_reliability.get(detector, self.default_detector_reliability),
        )

    def confidence_weights(self) -> dict[str, float]:
        """Return the confidence-model blend factors keyed by role."""
        return {
            "agreement": self.confidence_agreement_weight,
            "decisiveness": self.confidence_decisiveness_weight,
            "coverage": self.confidence_coverage_weight,
            "reliability": self.confidence_reliability_weight,
        }

    def confidence_weight_sum(self) -> float:
        """Total of the confidence-model weights (documented as roughly 1)."""
        return sum(self.confidence_weights().values())

    # ------------------------------------------------------------------
    # Three-class classification helpers
    # ------------------------------------------------------------------
    def contribution_weights_for(self, detector: str) -> list[float]:
        """Return the per-hypothesis contribution weights for ``detector``.

        The order matches :data:`HYPOTHESES` (original, AI edited, AI generated)
        and every value is non-negative. Unknown detectors fall back to
        ``classifier_contribution_default`` for each hypothesis so partial
        configuration never drops a signal.
        """
        row = self.classifier_contribution_matrix.get(detector)
        if row is None:
            return [self.classifier_contribution_default] * 3
        return [
            max(0.0, row.get(name, self.classifier_contribution_default))
            for name in ("original", "ai_edited", "ai_generated")
        ]

    def classifier_centers(self) -> list[float]:
        """Return the response-curve centres in hypothesis order."""
        return [
            self.classifier_original_center,
            self.classifier_edited_center,
            self.classifier_generated_center,
        ]

    def classification_weights(self) -> dict[str, float]:
        """Return the classification-confidence blend factors by role."""
        return {
            "margin": self.classification_margin_weight,
            "agreement": self.classification_agreement_weight,
            "separation": self.classification_separation_weight,
            "coverage": self.classification_coverage_weight,
            "reliability": self.classification_reliability_weight,
        }

    def classification_weight_sum(self) -> float:
        """Total of the classification-confidence factor weights."""
        return sum(self.classification_weights().values())

    def risk_level_for(self, confidence: float) -> RiskLevel:
        """Map a fused confidence score to a risk level using thresholds."""
        if confidence >= self.high_risk_threshold:
            return RiskLevel.HIGH
        if confidence >= self.medium_risk_threshold:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW

    def risk_for(self, verdict: Verdict, confidence: float) -> RiskLevel:
        """Map a verdict and its confidence onto a risk level.

        The verdict encodes the manipulation threat while the confidence scales
        how strongly that threat is asserted:

        * ``ORIGINAL`` — no manipulation evidence, so always low risk.
        * ``AI_GENERATED`` — synthetic content is inherently risky; high risk
          whenever the confidence reaches at least the medium band.
        * ``AI_EDITED`` — risk tracks the confidence bands (strong editing
          evidence is high risk, weak evidence low risk).
        """
        if verdict is Verdict.ORIGINAL:
            return RiskLevel.LOW
        band = self.risk_level_for(confidence)
        if verdict is Verdict.AI_GENERATED:
            return RiskLevel.HIGH if band is not RiskLevel.LOW else RiskLevel.MEDIUM
        return band


@lru_cache(maxsize=1)
def get_pipeline_config() -> PipelineConfig:
    """Return the cached :class:`PipelineConfig` instance."""
    return PipelineConfig()


def clear_pipeline_config_cache() -> None:
    """Discard the cached pipeline configuration (used by the test suite)."""
    get_pipeline_config.cache_clear()

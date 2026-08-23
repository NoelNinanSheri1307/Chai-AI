"""Unit tests for Milestone 19 — Production Multi-Source Decision Layer."""

from io import BytesIO

from PIL import Image

from app.clients.external_detection.base import ExternalDetectionResult
from app.core.enums import RiskLevel, ScoreCategory, Verdict
from app.pipeline.base import HeatmapRegionResult, HeatmapResult, ScoreResult
from app.pipeline.config import PipelineConfig
from app.pipeline.decision.engine import ProductionDecisionEngine
from app.pipeline.decision.models import DecisionProvenance, ProductionDecisionResult
from app.pipeline.fusion.base import FusionResult


def _mock_fusion_result(
    verdict: Verdict,
    confidence: float = 0.80,
    scores: list[ScoreResult] | None = None,
) -> FusionResult:
    return FusionResult(
        verdict=verdict,
        confidence=confidence,
        risk_level=RiskLevel.HIGH if verdict != Verdict.ORIGINAL else RiskLevel.LOW,
        scores=scores or [ScoreResult(category=ScoreCategory.FREQUENCY, value=0.75)],
        indicators=[],
        contributions=(),
    )


# ---------------------------------------------------------------------------
# 1. Agreement Scenarios
# ---------------------------------------------------------------------------


def test_both_providers_agree_on_ai() -> None:
    engine = ProductionDecisionEngine()
    chai_fusion = _mock_fusion_result(Verdict.AI_GENERATED, confidence=0.85)
    ext_result = ExternalDetectionResult(
        provider="sightengine",
        provider_version="v1.0",
        is_configured=True,
        status="success",
        detected_as_ai=True,
        confidence=0.95,
    )

    res = engine.decide(chai_fusion=chai_fusion, external_result=ext_result)

    assert isinstance(res, ProductionDecisionResult)
    assert res.verdict == Verdict.AI_GENERATED
    assert res.confidence >= 0.85
    assert "agrees" in res.explanation.lower()
    assert res.provenance.sightengine_status == "success"
    assert res.provenance.sightengine_ai_probability == 0.95
    assert res.provenance.chai_classification == Verdict.AI_GENERATED
    assert res.provenance.fusion_weight_sightengine == 0.70
    assert res.provenance.fusion_weight_chai == 0.30


def test_both_providers_agree_on_real() -> None:
    engine = ProductionDecisionEngine()
    chai_fusion = _mock_fusion_result(Verdict.ORIGINAL, confidence=0.85)
    ext_result = ExternalDetectionResult(
        provider="sightengine",
        provider_version="v1.0",
        is_configured=True,
        status="success",
        detected_as_ai=False,
        confidence=0.05,
    )

    res = engine.decide(chai_fusion=chai_fusion, external_result=ext_result)

    assert res.verdict == Verdict.ORIGINAL
    assert res.confidence >= 0.70
    assert "authentic" in res.explanation.lower()
    assert res.provenance.final_classification == Verdict.ORIGINAL


# ---------------------------------------------------------------------------
# 2. Conflict Resolution Scenarios
# ---------------------------------------------------------------------------


def test_sightengine_ai_and_chai_real_conflict() -> None:
    """Sightengine (weight=0.70) detects strong AI while Chai detects Real."""
    engine = ProductionDecisionEngine()
    chai_fusion = _mock_fusion_result(Verdict.ORIGINAL, confidence=0.70)
    ext_result = ExternalDetectionResult(
        provider="sightengine",
        provider_version="v1.0",
        is_configured=True,
        status="success",
        detected_as_ai=True,
        confidence=0.90,
    )

    res = engine.decide(chai_fusion=chai_fusion, external_result=ext_result)

    # 0.70 * 0.90 + 0.30 * 0.15 = 0.63 + 0.045 = 0.675 >= 0.50 -> AI_GENERATED
    assert res.verdict == Verdict.AI_GENERATED
    assert "sightengine indicates ai generation" in res.explanation.lower()
    assert res.provenance.chai_classification == Verdict.ORIGINAL
    assert res.provenance.final_classification == Verdict.AI_GENERATED


def test_sightengine_real_and_chai_ai_conflict() -> None:
    """Sightengine detects Real (p=0.10) while Chai has moderate AI score (0.60)."""
    engine = ProductionDecisionEngine()
    chai_fusion = _mock_fusion_result(Verdict.AI_GENERATED, confidence=0.60)
    ext_result = ExternalDetectionResult(
        provider="sightengine",
        provider_version="v1.0",
        is_configured=True,
        status="success",
        detected_as_ai=False,
        confidence=0.10,
    )

    res = engine.decide(chai_fusion=chai_fusion, external_result=ext_result)

    # 0.70 * 0.10 + 0.30 * 0.80 = 0.07 + 0.24 = 0.31 < 0.50 -> ORIGINAL
    assert res.verdict == Verdict.ORIGINAL
    assert "sightengine indicates authentic content" in res.explanation.lower()


def test_sightengine_real_and_chai_ai_edited_conflict() -> None:
    """Sightengine detects Real but Chai detects strong localized editing."""
    engine = ProductionDecisionEngine()
    chai_fusion = _mock_fusion_result(Verdict.AI_EDITED, confidence=0.82)
    ext_result = ExternalDetectionResult(
        provider="sightengine",
        provider_version="v1.0",
        is_configured=True,
        status="success",
        detected_as_ai=False,
        confidence=0.05,
    )
    heatmap = HeatmapResult(
        overall_manipulation=0.80,
        regions=[
            HeatmapRegionResult(
                x=0.1, y=0.1, width=0.3, height=0.3, intensity=0.85, label="tampered"
            )
        ],
    )

    res = engine.decide(
        chai_fusion=chai_fusion,
        chai_heatmap=heatmap,
        external_result=ext_result,
    )

    assert res.verdict == Verdict.AI_EDITED
    assert res.confidence >= 0.70
    assert "editing/tampering" in res.explanation.lower()
    assert res.provenance.chai_edit_score >= 0.80


# ---------------------------------------------------------------------------
# 3. External Fallback & Unavailability Scenarios
# ---------------------------------------------------------------------------


def test_sightengine_unconfigured_fallback() -> None:
    engine = ProductionDecisionEngine()
    chai_fusion = _mock_fusion_result(Verdict.AI_GENERATED, confidence=0.88)
    ext_result = ExternalDetectionResult(
        provider="sightengine",
        provider_version="v1.0",
        is_configured=False,
        status="unconfigured",
    )

    res = engine.decide(chai_fusion=chai_fusion, external_result=ext_result)

    assert res.verdict == Verdict.AI_GENERATED
    assert res.provenance.sightengine_status == "unconfigured"
    assert res.provenance.sightengine_ai_probability is None
    assert res.provenance.fusion_weight_sightengine == 0.0
    assert res.provenance.fusion_weight_chai == 1.0
    assert "sightengine unconfigured" in res.explanation.lower()


def test_sightengine_timeout_error_fallback() -> None:
    engine = ProductionDecisionEngine()
    chai_fusion = _mock_fusion_result(Verdict.ORIGINAL, confidence=0.82)
    ext_result = ExternalDetectionResult(
        provider="sightengine",
        provider_version="v1.0",
        is_configured=True,
        status="timeout",
        error_message="Gateway timeout after 5.0s",
    )

    res = engine.decide(chai_fusion=chai_fusion, external_result=ext_result)

    assert res.verdict == Verdict.ORIGINAL
    assert res.provenance.sightengine_status == "timeout"
    assert "sightengine timeout" in res.explanation.lower()


# ---------------------------------------------------------------------------
# 4. Configuration Weights & Custom Thresholds
# ---------------------------------------------------------------------------


def test_custom_configuration_weights() -> None:
    cfg = PipelineConfig(
        decision_external_weight=0.50,
        decision_internal_weight=0.50,
        decision_ai_generated_threshold=0.55,
    )
    engine = ProductionDecisionEngine(cfg)
    chai_fusion = _mock_fusion_result(
        Verdict.AI_GENERATED, confidence=0.90
    )  # p_chai=0.95
    ext_result = ExternalDetectionResult(
        provider="sightengine",
        provider_version="v1.0",
        is_configured=True,
        status="success",
        detected_as_ai=False,
        confidence=0.20,  # p_ext=0.20
    )

    # (0.50 * 0.20 + 0.50 * 0.95) / 1.0 = 0.10 + 0.475 = 0.575 >= 0.55 -> AI_GENERATED
    res = engine.decide(chai_fusion=chai_fusion, external_result=ext_result)

    assert res.verdict == Verdict.AI_GENERATED
    assert res.provenance.fusion_weight_sightengine == 0.50
    assert res.provenance.fusion_weight_chai == 0.50


# ---------------------------------------------------------------------------
# 5. Provenance Structure Completeness
# ---------------------------------------------------------------------------


def test_decision_provenance_completeness() -> None:
    engine = ProductionDecisionEngine()
    chai_fusion = _mock_fusion_result(Verdict.ORIGINAL, confidence=0.90)
    ext_result = ExternalDetectionResult(
        provider="sightengine",
        provider_version="v1.0",
        is_configured=True,
        status="success",
        detected_as_ai=False,
        confidence=0.02,
    )

    res = engine.decide(chai_fusion=chai_fusion, external_result=ext_result)

    prov = res.provenance
    assert isinstance(prov, DecisionProvenance)
    assert prov.final_classification == Verdict.ORIGINAL
    assert isinstance(prov.final_confidence, float)
    assert isinstance(prov.chai_confidence, float)
    assert isinstance(prov.chai_ai_probability, float)
    assert isinstance(prov.chai_edit_score, float)
    assert isinstance(prov.final_fused_probability, float)
    assert isinstance(prov.decision_reason, str)
    assert len(prov.decision_reason) > 5


def test_production_pipeline_modular_integration() -> None:
    """Verify that ModularAnalysisPipeline executes both Chai detectors and decision engine."""
    from app.clients.external_detection.base import ExternalDetectorProvider
    from app.clients.external_detection.manager import ExternalDetectionManager
    from app.pipeline.detectors.registry import build_detectors
    from app.pipeline.explanation.classifier import (
        ClassificationEvidenceGenerator,
        ClassificationExplanationGenerator,
    )
    from app.pipeline.fusion.engine import DeterministicFusionEngine
    from app.pipeline.heatmap.generator import DeterministicHeatmapGenerator
    from app.pipeline.runner import ModularAnalysisPipeline

    class MockSightengineProvider(ExternalDetectorProvider):
        @property
        def provider_name(self) -> str:
            return "sightengine"

        @property
        def provider_version(self) -> str:
            return "v1.0"

        def is_configured(self) -> bool:
            return True

        def analyze(
            self,
            image_bytes: bytes,
            filename: str = "image.jpg",
            content_type: str = "image/jpeg",
        ) -> ExternalDetectionResult:
            return ExternalDetectionResult(
                provider="sightengine",
                provider_version="v1.0",
                is_configured=True,
                status="success",
                detected_as_ai=True,
                confidence=0.92,
            )

    cfg = PipelineConfig()
    detectors = build_detectors(cfg.enabled_detector_names())
    fusion = DeterministicFusionEngine(cfg)
    heatmap_gen = DeterministicHeatmapGenerator(cfg)
    evidence_gen = ClassificationEvidenceGenerator(cfg)
    explanation_gen = ClassificationExplanationGenerator(cfg)
    ext_mgr = ExternalDetectionManager(providers=[MockSightengineProvider()])

    pipeline = ModularAnalysisPipeline(
        detectors=detectors,
        fusion=fusion,
        heatmap_generator=heatmap_gen,
        evidence_generator=evidence_gen,
        explanation_generator=explanation_gen,
        pipeline_config=cfg,
        external_manager=ext_mgr,
    )

    # 100x100 RGB dummy image bytes
    buf = BytesIO()
    Image.new("RGB", (100, 100), color=(128, 128, 128)).save(buf, format="JPEG")
    dummy_bytes = buf.getvalue()

    result = pipeline.analyze(
        dummy_bytes, content_type="image/jpeg", file_name="test.jpg"
    )

    assert result.verdict == Verdict.AI_GENERATED
    assert result.provenance is not None
    assert result.provenance.sightengine_status == "success"
    assert result.provenance.sightengine_ai_probability == 0.92
    assert result.provenance.fusion_weight_sightengine == 0.70
    assert result.provenance.fusion_weight_chai == 0.30
    assert result.provenance.final_fused_probability > 0.50

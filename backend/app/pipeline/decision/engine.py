"""Production multi-source decision and fusion layer for Milestone 19."""

from __future__ import annotations

import logging

from app.clients.external_detection.base import ExternalDetectionResult
from app.core.enums import Verdict
from app.pipeline.base import HeatmapResult, ScoreResult
from app.pipeline.config import PipelineConfig
from app.pipeline.decision.models import DecisionProvenance, ProductionDecisionResult
from app.pipeline.fusion.base import FusionResult

logger = logging.getLogger(__name__)


class ProductionDecisionEngine:
    """Production decision layer fusing Chai internal forensics with external reference providers."""

    def __init__(self, config: PipelineConfig | None = None) -> None:
        self._config = config or PipelineConfig()

    @property
    def config(self) -> PipelineConfig:
        return self._config

    def decide(
        self,
        *,
        chai_fusion: FusionResult,
        chai_heatmap: HeatmapResult | None = None,
        chai_evidence: list[str] | None = None,
        chai_scores: list[ScoreResult] | None = None,
        external_result: ExternalDetectionResult | None = None,
    ) -> ProductionDecisionResult:
        """Execute the weighted decision policy across internal forensics and external signals."""
        w_ext = self._config.decision_external_weight
        w_int = self._config.decision_internal_weight
        th_ai = self._config.decision_ai_generated_threshold
        th_edit = self._config.decision_ai_edited_threshold

        evidence = list(chai_evidence or [])

        # 1. Derive Chai internal AI generation probability [0.0, 1.0]
        chai_verdict = chai_fusion.verdict
        chai_conf = float(chai_fusion.confidence)

        if chai_verdict == Verdict.AI_GENERATED:
            p_chai_ai = 0.50 + (0.50 * chai_conf)
        elif chai_verdict == Verdict.ORIGINAL:
            p_chai_ai = 0.50 * (1.0 - chai_conf)
        elif chai_verdict == Verdict.AI_EDITED:
            p_chai_ai = 0.20
        else:
            p_chai_ai = 0.50
        p_chai_ai = max(0.0, min(1.0, p_chai_ai))

        # 2. Derive Chai internal Edit / Tampering score [0.0, 1.0]
        if chai_verdict == Verdict.AI_EDITED:
            s_chai_edit = max(0.50, chai_conf)
        elif chai_heatmap and chai_heatmap.overall_manipulation > 0.0:
            s_chai_edit = float(chai_heatmap.overall_manipulation)
        else:
            # Check localized tampering indicators from scores (e.g. ELA, Texture)
            ela_score = 0.0
            if chai_scores:
                for sc in chai_scores:
                    if getattr(sc.category, "value", str(sc.category)) in {
                        "ela",
                        "texture",
                    }:
                        ela_score = max(ela_score, sc.value)
            s_chai_edit = ela_score if ela_score > 0.40 else 0.10
        s_chai_edit = max(0.0, min(1.0, s_chai_edit))

        # 3. Process External (Sightengine) Signal
        ext_available = False
        p_ext_ai: float | None = None
        ext_status = "unconfigured"

        if external_result is not None:
            ext_status = external_result.status
            if (
                external_result.status == "success"
                and external_result.detected_as_ai is not None
            ):
                ext_available = True
                ext_conf = (
                    external_result.confidence
                    if external_result.confidence is not None
                    else 0.50
                )
                if external_result.detected_as_ai:
                    p_ext_ai = max(0.50, min(1.0, float(ext_conf)))
                else:
                    p_ext_ai = min(0.49, max(0.0, float(ext_conf)))

        # 4. Compute Fused AI Probability
        if ext_available and p_ext_ai is not None:
            total_w = w_ext + w_int
            p_fused_ai = (w_ext * p_ext_ai + w_int * p_chai_ai) / total_w
            eff_w_ext = w_ext
            eff_w_int = w_int
        else:
            p_fused_ai = p_chai_ai
            eff_w_ext = 0.0
            eff_w_int = 1.0

        p_fused_ai = max(0.0, min(1.0, p_fused_ai))

        # 5. Execute 3-Class Decision Policy & Conflict Resolution
        if ext_available and p_ext_ai is not None:
            if p_fused_ai >= th_ai:
                final_verdict = Verdict.AI_GENERATED
                # Higher confidence when both systems agree on AI
                if p_ext_ai >= 0.60 and p_chai_ai >= 0.50:
                    final_conf = min(0.98, max(p_fused_ai, 0.85))
                    reason = "Sightengine strongly indicates AI generation and Chai forensic evidence agrees."
                elif p_ext_ai >= 0.60:
                    final_conf = min(0.92, max(p_fused_ai, 0.75))
                    reason = "Sightengine indicates AI generation, while Chai forensic evidence is weak."
                else:
                    final_conf = min(0.85, max(p_fused_ai, 0.65))
                    reason = "Chai forensic evidence detects strong synthetic frequency lattice despite lower external score."
            elif s_chai_edit >= th_edit or chai_verdict == Verdict.AI_EDITED:
                final_verdict = Verdict.AI_EDITED
                final_conf = max(0.60, min(0.92, s_chai_edit))
                reason = "Sightengine indicates authentic baseline content, but Chai forensic analysis detects localized editing/tampering artifacts."
                evidence.append(
                    "Localized forensic inconsistency detected across spatial frequency and error level analysis."
                )
            else:
                final_verdict = Verdict.ORIGINAL
                auth_conf = 1.0 - max(p_fused_ai, s_chai_edit)
                final_conf = max(0.60, min(0.96, auth_conf))
                if p_ext_ai < 0.20 and p_chai_ai < 0.30:
                    reason = "Both Sightengine and Chai forensic analysis indicate authentic/unmodified original content."
                else:
                    reason = "Sightengine indicates authentic content, overriding weak internal forensic generation markers."
        else:
            # Fallback when external provider is unavailable / unconfigured / timed out
            if chai_verdict == Verdict.AI_GENERATED:
                final_verdict = Verdict.AI_GENERATED
                final_conf = chai_conf
                reason = f"Sightengine {ext_status}; classified as AI-generated based on Chai forensic analysis only."
            elif chai_verdict == Verdict.AI_EDITED or s_chai_edit >= th_edit:
                final_verdict = Verdict.AI_EDITED
                final_conf = s_chai_edit if s_chai_edit >= th_edit else chai_conf
                reason = f"Sightengine {ext_status}; classified as AI-edited based on Chai forensic analysis only."
            else:
                final_verdict = Verdict.ORIGINAL
                final_conf = chai_conf
                reason = f"Sightengine {ext_status}; classified as authentic based on Chai forensic analysis only."

        # Risk level derivation
        risk_level = self._config.risk_for(final_verdict, final_conf)

        # Build provenance
        provenance = DecisionProvenance(
            final_classification=final_verdict,
            final_confidence=round(final_conf, 4),
            chai_classification=chai_verdict,
            chai_confidence=round(chai_conf, 4),
            chai_ai_probability=round(p_chai_ai, 4),
            chai_edit_score=round(s_chai_edit, 4),
            sightengine_status=ext_status,
            sightengine_ai_probability=round(p_ext_ai, 4)
            if p_ext_ai is not None
            else None,
            fusion_weight_chai=round(eff_w_int, 2),
            fusion_weight_sightengine=round(eff_w_ext, 2),
            final_fused_probability=round(p_fused_ai, 4),
            decision_reason=reason,
            evidence=evidence,
        )

        return ProductionDecisionResult(
            verdict=final_verdict,
            confidence=round(final_conf, 4),
            risk_level=risk_level,
            explanation=reason,
            provenance=provenance,
        )

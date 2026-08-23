"""DTO mapping helpers: ORM entities and repo pages → API DTOs.

These pure functions are the only place ORM models are translated into response
DTOs. Repositories return ORM entities; services call these mappers so that no
ORM object ever leaves the service layer. Naming, ISO-8601 formatting and the
image-path convention are centralized here.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.core import constants
from app.core.enums import IndicatorSeverity, Verdict
from app.models.analysis import Analysis
from app.models.comparison import Comparison
from app.schemas.analysis import (
    AnalysisResultDTO,
    DecisionProvenanceDTO,
    DetectedIndicatorDTO,
    ForensicScoreDTO,
    HeatmapDataDTO,
    HeatmapRegionDTO,
)
from app.schemas.compare import CompareResultDTO
from app.schemas.history import HistoryItemDTO

_SEVERITY_LABELS = {
    IndicatorSeverity.LOW: "Low",
    IndicatorSeverity.MODERATE: "Moderate",
    IndicatorSeverity.STRONG: "Strong",
}

_VERDICT_LABELS = {
    Verdict.ORIGINAL: "Original",
    Verdict.AI_EDITED: "AI Edited",
    Verdict.AI_GENERATED: "AI Generated",
}


def format_utc_timestamp(value: datetime | None) -> str:
    """Format a timestamp as an ISO-8601 UTC string (``YYYY-MM-DDTHH:MM:SSZ``)."""
    if value is None:
        return ""
    return (
        value.astimezone(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def format_duration_iso(duration_ms: int) -> str:
    """Format a millisecond duration as an ISO-8601 duration (``PT2.1S``)."""
    return f"PT{duration_ms / 1000:.1f}S"


def analysis_image_path(public_id: str) -> str:
    """Return the API path serving an analysis's original image bytes."""
    return f"{constants.API_V1_PREFIX}/analyses/{public_id}/original"


def analysis_to_result_dto(analysis: Analysis) -> AnalysisResultDTO:
    """Map an ``Analysis`` (with loaded children) to the full result DTO."""
    heatmap_dto: HeatmapDataDTO | None = None
    if analysis.heatmap is not None:
        heatmap_dto = HeatmapDataDTO(
            regions=[
                HeatmapRegionDTO(
                    x=region.x,
                    y=region.y,
                    width=region.width,
                    height=region.height,
                    intensity=region.intensity,
                    label=region.label,
                )
                for region in sorted(analysis.heatmap.regions, key=lambda r: r.id)
            ],
            overallManipulation=analysis.heatmap.overall_manipulation,
        )

    meta_dict = {item.key: item.value for item in analysis.metadata_items}

    prov_dto: DecisionProvenanceDTO | None = None
    if "prov:decision_reason" in meta_dict or "decision_reason" in meta_dict:
        reason = meta_dict.get("prov:decision_reason") or meta_dict.get(
            "decision_reason", ""
        )
        se_status = meta_dict.get("prov:sightengine_status") or meta_dict.get(
            "sightengine_status", "unconfigured"
        )
        se_prob_str = meta_dict.get("prov:sightengine_ai_probability") or meta_dict.get(
            "sightengine_ai_probability"
        )
        se_prob = (
            float(se_prob_str)
            if se_prob_str is not None and se_prob_str != ""
            else None
        )
        chai_cls_str = meta_dict.get("prov:chai_classification") or meta_dict.get(
            "chai_classification",
            analysis.verdict.value if analysis.verdict else "original",
        )
        try:
            chai_verdict = Verdict(chai_cls_str)
        except Exception:
            chai_verdict = analysis.verdict or Verdict.ORIGINAL

        chai_conf = float(
            meta_dict.get(
                "prov:chai_confidence",
                meta_dict.get("chai_confidence", analysis.confidence or 0.5),
            )
        )
        chai_ai_p = float(
            meta_dict.get(
                "prov:chai_ai_probability", meta_dict.get("chai_ai_probability", 0.5)
            )
        )
        chai_edit_s = float(
            meta_dict.get("prov:chai_edit_score", meta_dict.get("chai_edit_score", 0.0))
        )
        w_chai = float(
            meta_dict.get(
                "prov:fusion_weight_chai", meta_dict.get("fusion_weight_chai", 0.3)
            )
        )
        w_se = float(
            meta_dict.get(
                "prov:fusion_weight_sightengine",
                meta_dict.get("fusion_weight_sightengine", 0.7),
            )
        )
        fused_p = float(
            meta_dict.get(
                "prov:final_fused_probability",
                meta_dict.get("final_fused_probability", chai_ai_p),
            )
        )

        prov_dto = DecisionProvenanceDTO(
            finalClassification=analysis.verdict or Verdict.ORIGINAL,
            finalConfidence=analysis.confidence or 0.0,
            chaiClassification=chai_verdict,
            chaiConfidence=chai_conf,
            chaiAiProbability=chai_ai_p,
            chaiEditScore=chai_edit_s,
            sightengineStatus=se_status,
            sightengineAiProbability=se_prob,
            fusionWeightChai=w_chai,
            fusionWeightSightengine=w_se,
            finalFusedProbability=fused_p,
            decisionReason=reason,
            evidence=[
                line.text
                for line in sorted(analysis.evidence, key=lambda line: line.position)
            ],
        )

    return AnalysisResultDTO(
        id=analysis.public_id,
        imagePath=analysis_image_path(analysis.public_id),
        fileName=analysis.file_name,
        verdict=analysis.verdict,
        confidence=analysis.confidence,
        riskLevel=analysis.risk_level,
        explanation=analysis.explanation or "",
        analysisDuration=format_duration_iso(analysis.duration_ms or 0),
        timestamp=format_utc_timestamp(analysis.created_at),
        scores=[
            ForensicScoreDTO(category=score.category, value=score.value)
            for score in analysis.forensic_scores
        ],
        indicators=[
            DetectedIndicatorDTO(
                type=indicator.indicator_type.value,
                confidence=indicator.confidence,
                severity=_SEVERITY_LABELS[indicator.severity],
                description=indicator.description,
            )
            for indicator in analysis.detected_indicators
        ],
        heatmap=heatmap_dto,
        evidence=[
            line.text
            for line in sorted(analysis.evidence, key=lambda line: line.position)
        ],
        metadata=meta_dict,
        provenance=prov_dto,
    )


def analysis_to_history_item(analysis: Analysis) -> HistoryItemDTO:
    """Map an ``Analysis`` to its lightweight history summary."""
    return HistoryItemDTO(
        id=analysis.public_id,
        imagePath=analysis_image_path(analysis.public_id),
        fileName=analysis.file_name,
        verdict=analysis.verdict,
        confidence=analysis.confidence,
        riskLevel=analysis.risk_level,
        timestamp=format_utc_timestamp(analysis.created_at),
        isFavorite=False,
    )


def comparison_to_result_dto(comparison: Comparison) -> CompareResultDTO:
    """Map a ``Comparison`` (with loaded children) to the result DTO."""
    ordered_findings = sorted(comparison.findings, key=lambda finding: finding.position)
    return CompareResultDTO(
        labelA=comparison.label_a,
        labelB=comparison.label_b,
        similarity=comparison.similarity,
        aiProbability=comparison.ai_probability,
        similarities=[f.text for f in ordered_findings if f.is_similarity],
        differences=[f.text for f in ordered_findings if not f.is_similarity],
        manipulatedRegions=[
            HeatmapRegionDTO(
                x=region.x,
                y=region.y,
                width=region.width,
                height=region.height,
                intensity=region.intensity,
                label=region.label,
            )
            for region in sorted(comparison.regions, key=lambda region: region.id)
        ],
    )


def verdict_label(verdict: Verdict) -> str:
    """Return the human-readable label for a verdict enum."""
    return _VERDICT_LABELS.get(
        verdict, verdict.value if hasattr(verdict, "value") else str(verdict)
    )

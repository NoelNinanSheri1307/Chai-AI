"""Comparison and benchmarking engine for external AI detector validation.

Evaluates agreements and disagreements between Chai's internal seven-detector
three-class forensic verdict (Original, AI Edited, AI Generated) and external
providers' normalized results (binary or multi-class).
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.clients.external_detection.base import ExternalDetectionResult


class ExternalBenchmarkItem(BaseModel):
    """Comparison item for a single external provider against Chai's verdict."""

    provider: str
    provider_version: str
    status: str
    detected_as_ai: bool | None = None
    confidence: float | None = None
    classification_label: str | None = None
    agreement: bool | None = None
    compatibility_note: str
    confidence_delta: float | None = None


class ExternalBenchmarkResult(BaseModel):
    """Aggregated benchmark report comparing Chai's verdict against external providers."""

    analysis_id: str
    chai_verdict: str
    chai_confidence: float
    chai_risk_level: str
    external_results: list[ExternalDetectionResult] = Field(default_factory=list)
    benchmark_items: list[ExternalBenchmarkItem] = Field(default_factory=list)
    overall_agreement_ratio: float | None = None
    summary: str


def _normalize_chai_verdict(verdict: str) -> str:
    v = verdict.strip()
    if v in {"original", "Original", "real"}:
        return "original"
    if v in {"aiEdited", "ai_edited", "AI Edited"}:
        return "ai_edited"
    if v in {"aiGenerated", "ai_generated", "AI Generated"}:
        return "ai_generated"
    return v.lower()


def compare_verdict(
    chai_verdict: str,
    chai_confidence: float,
    external: ExternalDetectionResult,
) -> ExternalBenchmarkItem:
    """Compare Chai's three-class verdict with an external provider result.

    Preserves classification granularity: binary 'AI Detected' from an external
    provider is compatible with Chai's 'ai_edited' or 'ai_generated'.
    """
    normalized_chai = _normalize_chai_verdict(chai_verdict)

    if not external.is_configured or external.status != "success":
        return ExternalBenchmarkItem(
            provider=external.provider,
            provider_version=external.provider_version,
            status=external.status,
            detected_as_ai=external.detected_as_ai,
            confidence=external.confidence,
            classification_label=external.classification_label,
            agreement=None,
            compatibility_note=(
                f"Provider '{external.provider}' is {external.status}."
                if external.error_message is None
                else f"Provider '{external.provider}' error: {external.error_message}"
            ),
            confidence_delta=None,
        )

    ext_ai = external.detected_as_ai
    ext_conf = external.confidence

    confidence_delta = (
        abs(round(chai_confidence - ext_conf, 4))
        if ext_conf is not None
        else None
    )

    if ext_ai is None:
        return ExternalBenchmarkItem(
            provider=external.provider,
            provider_version=external.provider_version,
            status=external.status,
            detected_as_ai=None,
            confidence=ext_conf,
            classification_label=external.classification_label,
            agreement=None,
            compatibility_note="External provider returned inconclusive AI detection state.",
            confidence_delta=confidence_delta,
        )

    # Classification compatibility matrix:
    # Chai: original | ai_edited | ai_generated
    # External: detected_as_ai=True | False
    if normalized_chai == "original":
        if not ext_ai:
            agree = True
            note = "Both Chai and external provider classified the image as authentic/original."
        else:
            agree = False
            note = "Disagreement: Chai classified image as Original, but external provider detected AI content."
    elif normalized_chai == "ai_generated":
        if ext_ai:
            agree = True
            note = "Both Chai and external provider detected AI synthetic content."
        else:
            agree = False
            note = "Disagreement: Chai classified image as AI Generated, but external provider classified as authentic."
    elif normalized_chai == "ai_edited":
        if ext_ai:
            agree = True
            note = "Chai detected AI editing; external provider detected AI involvement (compatible classification)."
        else:
            agree = False
            note = "Disagreement: Chai detected AI editing, but external provider classified image as authentic."
    else:
        agree = (normalized_chai != "original") == ext_ai
        note = f"Comparison evaluated for custom Chai verdict '{chai_verdict}'."

    return ExternalBenchmarkItem(
        provider=external.provider,
        provider_version=external.provider_version,
        status=external.status,
        detected_as_ai=ext_ai,
        confidence=ext_conf,
        classification_label=external.classification_label,
        agreement=agree,
        compatibility_note=note,
        confidence_delta=confidence_delta,
    )


def compute_benchmark_report(
    analysis_id: str,
    chai_verdict: str,
    chai_confidence: float,
    chai_risk_level: str,
    external_results: list[ExternalDetectionResult],
) -> ExternalBenchmarkResult:
    """Build a complete benchmark report from external provider results."""
    items = [
        compare_verdict(chai_verdict, chai_confidence, res)
        for res in external_results
    ]

    valid_agreements = [
        item.agreement for item in items if item.agreement is not None
    ]

    if valid_agreements:
        agreement_ratio = round(
            sum(1 for a in valid_agreements if a) / len(valid_agreements), 4
        )
    else:
        agreement_ratio = None

    if agreement_ratio is None:
        summary = "No active external providers were available for comparison."
    elif agreement_ratio == 1.0:
        summary = "Full agreement: external providers corroborate Chai's forensic verdict."
    elif agreement_ratio == 0.0:
        summary = "Disagreement: external providers contradict Chai's forensic verdict."
    else:
        summary = f"Partial agreement: {int(agreement_ratio * 100)}% of external providers corroborate Chai's verdict."

    return ExternalBenchmarkResult(
        analysis_id=analysis_id,
        chai_verdict=chai_verdict,
        chai_confidence=chai_confidence,
        chai_risk_level=chai_risk_level,
        external_results=external_results,
        benchmark_items=items,
        overall_agreement_ratio=agreement_ratio,
        summary=summary,
    )

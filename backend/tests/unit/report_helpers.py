"""Shared helpers for the forensic report tests.

Seed a persisted ``Analysis`` reachable by the report builder/service without
running the (slow, sensor-dependent) pipeline. Everything is deterministic.
"""

from __future__ import annotations

from app.core.enums import (
    AnalysisStatus,
    IndicatorSeverity,
    IndicatorType,
    RiskLevel,
    ScoreCategory,
    Verdict,
)
from app.models.analysis import (
    Analysis,
    AnalysisContribution,
    DetectedIndicator,
    Evidence,
    ForensicScore,
    Heatmap,
    HeatmapRegion,
    MetadataItem,
)


def vt_analysis(
    public_id: str = "ana_report_1",
    *,
    verdict: Verdict = Verdict.AI_GENERATED,
    confidence: float = 0.85,
    risk: RiskLevel = RiskLevel.HIGH,
    margin: float | None = 0.50,
    runner_up: Verdict | None = Verdict.ORIGINAL,
    hypothesis: tuple[float, float] = (0.15, 0.85),
    duration_ms: int = 2100,
) -> Analysis:
    """Build a completed analysis stamped with classification results."""
    analysis = Analysis(
        public_id=public_id,
        original_key="testing/orig/sample.png",
        file_name="sample.png",
        mime_type="image/png",
        verdict=verdict,
        confidence=confidence,
        risk_level=risk,
        explanation="Deterministic report fixture explanation.",
        duration_ms=duration_ms,
        status=AnalysisStatus.COMPLETED,
        hypothesis_original=hypothesis[0],
        hypothesis_edited=0.0,
        hypothesis_generated=hypothesis[1],
        runner_up_verdict=runner_up,
        classification_margin=margin,
    )
    analysis.forensic_scores = [
        ForensicScore(category=ScoreCategory.FREQUENCY, value=0.77),
        ForensicScore(category=ScoreCategory.TEXTURE, value=0.83),
    ]
    analysis.analysis_contributions = []
    analysis.evidence = []
    analysis.detected_indicators = []
    analysis.metadata_items = []
    return analysis


def add_contribution(
    analysis: Analysis,
    *,
    detector: str,
    normalized_score: float,
    confidence: float = 0.9,
    reliability: float = 0.1,
    contribution: float = 0.1,
    weights: tuple[float, float] = (0.0, 1.0),
    preferred: str = "AI Generated",
    processing_time_ms: int = 100,
    category: str = "frequency",
    position: int = 0,
) -> None:
    """Attach a single detector contribution to ``analysis``."""
    analysis.analysis_contributions.append(
        AnalysisContribution(
            position=position,
            detector=detector,
            detector_version="0.1.0",
            category=category,
            normalized_score=normalized_score,
            detector_confidence=confidence,
            reliability=reliability,
            weight_share=reliability,
            contribution=contribution,
            direction=(
                "supports:manipulation"
                if normalized_score >= 0.5
                else "supports:original"
            ),
            hypothesis_original=weights[0],
            hypothesis_edited=0.0,
            hypothesis_generated=weights[1],
            preferred_hypothesis=preferred,
            processing_time_ms=processing_time_ms,
        )
    )


def add_evidence(analysis: Analysis, detector: str, text: str) -> None:
    """Add a detector evidence line in the ``<detector> — <text>`` shape."""
    analysis.evidence.append(
        Evidence(text=f"{detector} — {text}", position=len(analysis.evidence))
    )


def add_metadata_items(analysis: Analysis, items: dict[str, str]) -> None:
    """Add key/value metadata items to ``analysis``."""
    analysis.metadata_items.extend(
        MetadataItem(key=key, value=value) for key, value in items.items()
    )


def add_indicator(
    analysis: Analysis,
    *,
    indicator_type: IndicatorType = IndicatorType.DIFFUSION,
    confidence: float = 0.94,
    severity: IndicatorSeverity = IndicatorSeverity.STRONG,
    description: str = (
        "Soft watercolor-like artifacts consistent with diffusion synthesis."
    ),
) -> None:
    """Add a detected indicator to ``analysis``."""
    analysis.detected_indicators.append(
        DetectedIndicator(
            indicator_type=indicator_type,
            confidence=confidence,
            severity=severity,
            description=description,
        )
    )


def set_heatmap(
    analysis: Analysis,
    *,
    overall: float = 0.71,
    region: tuple[float, float, float, float, float, str] | None = None,
) -> None:
    """Attach a heatmap (plus one optional region) to ``analysis``.

    ``region`` is ``(x, y, width, height, intensity, label)``.
    """
    heatmap = Heatmap(overall_manipulation=overall)
    if region:
        heatmap.regions = [
            HeatmapRegion(
                x=region[0],
                y=region[1],
                width=region[2],
                height=region[3],
                intensity=region[4],
                label=region[5],
            )
        ]
    analysis.heatmap = heatmap


def commit_analysis(db_session, analysis: Analysis) -> Analysis:
    """Persist ``analysis`` and its children, returning the stored instance."""
    db_session.add(analysis)
    db_session.commit()
    db_session.refresh(analysis)
    return analysis


def ai_generated_report_fixture(db_session) -> Analysis:
    """A canonical AI Generated analysis with mixed evidence."""
    analysis = vt_analysis(public_id="ana_gen_report")
    add_contribution(
        analysis,
        detector="frequency",
        normalized_score=0.83,
        contribution=0.30,
        weights=(0.15, 0.85),
        preferred="AI Generated",
        position=0,
    )
    add_contribution(
        analysis,
        detector="texture",
        normalized_score=0.78,
        contribution=0.24,
        weights=(0.20, 0.80),
        preferred="AI Generated",
        position=1,
    )
    add_contribution(
        analysis,
        detector="metadata",
        normalized_score=0.05,
        contribution=0.15,
        weights=(0.95, 0.05),
        preferred="Original",
        position=2,
        confidence=0.95,
    )
    add_evidence(
        analysis,
        "frequency",
        "Spectral anomalies consistent with upscaled synthetic content.",
    )
    add_evidence(
        analysis,
        "texture",
        "Unusually uniform texture characteristics are present.",
    )
    add_evidence(analysis, "metadata", "Valid camera metadata present: Sony ILCE-7M4.")
    add_indicator(
        analysis,
        indicator_type=IndicatorType.DIFFUSION,
        confidence=0.94,
        description=(
            "Soft watercolor-like artifacts consistent with diffusion synthesis."
        ),
    )
    add_metadata_items(
        analysis,
        {
            "Camera": "Sony ILCE-7M4",
            "Software": "Sony Imaging Camera Mobile",
            "Format": "JPEG",
            "File size": "3.90 MB",
        },
    )
    add_metadata_items(
        analysis,
        {
            "pipeline_version": "1.0",
            "fusion_version": "0.1.0",
            "framework_version": "0.1.0",
            "detector_versions": ("frequency@0.1.0, texture@0.1.0, metadata@0.1.0"),
        },
    )
    set_heatmap(
        analysis,
        region=(0.1, 0.2, 0.3, 0.4, 0.8, "frequency: Synthetic region (strong)"),
    )
    return commit_analysis(db_session, analysis)

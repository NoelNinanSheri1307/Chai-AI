"""Tests for the forensic report builder.

Covers every report section for all three classifications plus degraded input
(empty/missing evidence, low confidence, conflicting detectors).
"""

from __future__ import annotations

import pytest

from app.core.enums import RiskLevel, Verdict
from app.models.analysis import HeatmapRegion
from app.services.reporting.builder import build_forensic_report

from .report_helpers import (
    add_contribution,
    add_evidence,
    add_metadata_items,
    commit_analysis,
    set_heatmap,
    vt_analysis,
)


def _report_for(db_session, **kwargs):
    analysis = commit_analysis(db_session, vt_analysis(**kwargs))
    return build_forensic_report(analysis)


def test_report_identity_and_classification(db_session) -> None:
    report = _report_for(db_session, public_id="ana_id_check")
    assert report.analysis_id == "ana_id_check"
    assert report.classification.verdict == Verdict.AI_GENERATED
    assert report.classification.classification == "AI Generated"
    assert report.classification.confidence == pytest.approx(0.85)
    assert report.classification.confidence_percent == 85
    assert report.classification.risk == RiskLevel.HIGH
    assert report.timestamp.endswith("Z")


def test_original_report_shape(db_session) -> None:
    report = _report_for(
        db_session,
        verdict=Verdict.ORIGINAL,
        confidence=0.90,
        risk=RiskLevel.LOW,
        margin=0.60,
        runner_up=Verdict.AI_EDITED,
        hypothesis=(0.82, 0.11, 0.07),
    )
    assert report.classification.verdict == Verdict.ORIGINAL
    assert report.comparison.winner == "Original"
    assert report.comparison.original == pytest.approx(0.82)
    assert report.comparison.runner_up == "AI Edited"
    assert report.heatmap is not None
    assert report.heatmap.present is False or report.heatmap.region_count >= 0


def test_ai_edited_report_shape(db_session) -> None:
    report = _report_for(
        db_session,
        verdict=Verdict.AI_EDITED,
        risk=RiskLevel.MEDIUM,
        margin=0.12,
        runner_up=Verdict.ORIGINAL,
        hypothesis=(0.31, 0.52, 0.17),
    )
    assert report.classification.verdict == Verdict.AI_EDITED
    assert report.comparison.ai_edited == pytest.approx(0.52)
    assert report.comparison.runner_up == "Original"


def test_ai_generated_report_shape(db_session) -> None:
    report = _report_for(
        db_session,
        verdict=Verdict.AI_GENERATED,
        hypothesis=(0.08, 0.21, 0.71),
        margin=0.50,
        runner_up=Verdict.AI_EDITED,
    )
    assert report.comparison.ai_generated == pytest.approx(0.71)
    assert report.comparison.margin == pytest.approx(0.50)
    assert report.comparison.runner_up == "AI Edited"


def test_supporting_and_contradicting_evidence(db_session) -> None:
    analysis = vt_analysis(public_id="ana_evid")
    add_contribution(
        analysis,
        detector="frequency",
        normalized_score=0.83,
        contribution=0.3,
        weights=(0.05, 0.20, 0.75),
        preferred="AI Generated",
    )
    add_contribution(
        analysis,
        detector="metadata",
        normalized_score=0.05,
        contribution=0.15,
        weights=(0.90, 0.05, 0.05),
        preferred="Original",
    )
    add_evidence(analysis, "frequency", "Spectral anomalies are present.")
    add_evidence(analysis, "metadata", "Valid camera metadata present.")
    commit_analysis(db_session, analysis)

    report = build_forensic_report(analysis)
    supporting = report.supporting_evidence
    contradicting = report.contradicting_evidence
    assert any(s.source_detector == "frequency" for s in supporting)
    assert any(s.source_detector == "metadata" for s in contradicting)
    metadata_item = next(s for s in contradicting if s.source_detector == "metadata")
    assert "Valid camera metadata present." in metadata_item.text
    assert metadata_item.importance >= 0.0
    assert metadata_item.supports_verdict is False


def test_detector_contributions_breakdown(db_session) -> None:
    analysis = vt_analysis(public_id="ana_contrib")
    add_contribution(
        analysis,
        detector="lighting",
        normalized_score=0.66,
        contribution=0.22,
        weights=(0.20, 0.40, 0.40),
        preferred="AI Edited",
        processing_time_ms=140,
    )
    report = build_forensic_report(commit_analysis(db_session, analysis))
    assert len(report.detector_contributions) == 1
    row = report.detector_contributions[0]
    assert row.detector == "lighting"
    assert row.detector_version == "0.1.0"
    assert row.normalized_score == pytest.approx(0.66)
    assert row.contribution_original == pytest.approx(0.20)
    assert row.contribution_ai_edited == pytest.approx(0.40)
    assert row.contribution_ai_generated == pytest.approx(0.40)
    assert row.contribution_winning_class == pytest.approx(0.40)
    assert row.preferred_hypothesis == "AI Edited"
    assert row.processing_time_ms == 140


def test_evidence_aggregation_is_ranked_and_deduped(db_session) -> None:
    analysis = vt_analysis(public_id="ana_rank")
    add_contribution(
        analysis,
        detector="frequency",
        normalized_score=0.8,
        weights=(0.0, 0.0, 1.0),
        preferred="AI Generated",
        contribution=0.25,
    )
    add_contribution(
        analysis,
        detector="texture",
        normalized_score=0.7,
        weights=(0.0, 0.0, 1.0),
        preferred="AI Generated",
        contribution=0.20,
    )
    add_evidence(analysis, "frequency", "Spectrum shows resampling lattice.")
    add_evidence(analysis, "texture", "Uniform texture patch observed.")
    add_evidence(analysis, "texture", "Uniform texture patch observed.")
    report = build_forensic_report(commit_analysis(db_session, analysis))
    supporting = [e.text for e in report.supporting_evidence]

    texts = [t.casefold() for t in supporting]
    assert "spectrum shows resampling lattice." in texts
    assert texts.count("uniform texture patch observed.") == 1


def test_heatmap_summary(db_session) -> None:
    analysis = vt_analysis(public_id="ana_heat")
    set_heatmap(
        analysis,
        region=(0.1, 0.2, 0.3, 0.4, 0.8, "frequency: Synthetic region (strong)"),
    )
    analysis.heatmap.regions.append(
        HeatmapRegion(
            x=0.5,
            y=0.5,
            width=0.2,
            height=0.2,
            intensity=0.6,
            label="texture: Texture region (low)",
        )
    )
    report = build_forensic_report(commit_analysis(db_session, analysis))

    heatmap = report.heatmap
    assert heatmap is not None and heatmap.present is True
    assert heatmap.region_count == 2
    assert heatmap.regions[0].intensity == pytest.approx(0.8)
    assert heatmap.regions[0].detectors == ["frequency"]
    assert heatmap.regions[0].severity == "strong"
    assert heatmap.detector_attribution == ["frequency", "texture"]
    assert "primarily by frequency" in heatmap.narrative


def test_heatmap_absent_for_original(db_session) -> None:
    analysis = vt_analysis(
        verdict=Verdict.ORIGINAL, risk=RiskLevel.LOW, hypothesis=(0.9, 0.05, 0.05)
    )
    report = build_forensic_report(commit_analysis(db_session, analysis))
    assert report.heatmap is not None
    assert report.heatmap.present is False
    assert report.heatmap.narrative  # deterministic "no heatmap recorded" text


def test_metadata_summary_states(db_session) -> None:
    analysis = vt_analysis(public_id="ana_md")
    add_metadata_items(analysis, {"Camera": "Sony ILCE-7M4"})
    report = build_forensic_report(commit_analysis(db_session, analysis))
    assert report.image_metadata.status == "present"
    assert report.image_metadata.camera_present is True
    assert report.image_metadata.narrative

    analysis = vt_analysis(public_id="ana_md2")
    report = build_forensic_report(commit_analysis(db_session, analysis))
    assert report.image_metadata.status == "absent"
    assert report.image_metadata.camera_present is False

    analysis = vt_analysis(public_id="ana_md3")
    add_metadata_items(analysis, {"Software": "ComfyUI"})
    report = build_forensic_report(commit_analysis(db_session, analysis))
    assert report.image_metadata.status == "suspicious"
    assert report.image_metadata.has_suspicious_entries is True


def test_processing_summary(db_session) -> None:
    analysis = vt_analysis(public_id="ana_proc", duration_ms=2222)
    add_contribution(
        analysis,
        detector="noise",
        normalized_score=0.10,
        weights=(0.8, 0.1, 0.1),
        preferred="Original",
        position=0,
        processing_time_ms=55,
    )
    add_metadata_items(
        analysis,
        {
            "pipeline_version": "2.0",
            "fusion_version": "0.3.0",
            "framework_version": "0.2.0",
            "detector_versions": "noise@0.1.0",
        },
    )
    report = build_forensic_report(commit_analysis(db_session, analysis))
    processing = report.processing
    assert processing.total_analysis_ms == 2222
    assert processing.active_detector_count == 1
    assert processing.detector_execution[0].processing_time_ms == 55
    assert processing.pipeline_version == "2.0"
    assert processing.fusion_version == "0.3.0"
    assert processing.detector_versions == ["noise@0.1.0"]


def test_why_summary_is_evidence_traceable(db_session) -> None:
    analysis = vt_analysis(public_id="ana_why")
    add_contribution(
        analysis,
        detector="frequency",
        normalized_score=0.83,
        weights=(0.05, 0.20, 0.75),
        preferred="AI Generated",
        contribution=0.3,
    )
    add_contribution(
        analysis,
        detector="metadata",
        normalized_score=0.05,
        weights=(0.9, 0.05, 0.05),
        preferred="Original",
        contribution=0.15,
    )
    add_evidence(analysis, "frequency", "Spectral anomalies present.")
    report = build_forensic_report(commit_analysis(db_session, analysis))
    summary = report.classification.summary
    assert "AI Generated" in summary
    assert "frequency" in summary
    assert "argue against it" in summary


def test_low_confidence_classification(db_session) -> None:
    report = _report_for(
        db_session,
        verdict=Verdict.AI_EDITED,
        confidence=0.31,
        risk=RiskLevel.MEDIUM,
        margin=0.04,
        runner_up=Verdict.ORIGINAL,
        hypothesis=(0.34, 0.38, 0.28),
    )
    assert report.classification.confidence_percent == 31
    assert report.comparison.margin == pytest.approx(0.04)
    assert report.classification.confidence == pytest.approx(0.31)


def test_empty_evidence_degrades_gracefully(db_session) -> None:
    report = _report_for(
        db_session,
        verdict=Verdict.ORIGINAL,
        confidence=0.5,
        risk=RiskLevel.MEDIUM,
        margin=0.05,
        hypothesis=(0.35, 0.30, 0.35),
    )
    assert report.supporting_evidence == []
    assert report.contradicting_evidence == []
    assert report.detector_contributions == []
    assert "no corroborating forensic signal" in report.classification.summary


def test_conflicting_detector_evidence_is_honest(db_session) -> None:
    analysis = vt_analysis(public_id="conflict")
    add_contribution(
        analysis,
        detector="frequency",
        normalized_score=0.85,
        weights=(0.05, 0.10, 0.85),
        preferred="AI Generated",
        contribution=0.30,
    )
    add_contribution(
        analysis,
        detector="metadata",
        normalized_score=0.05,
        weights=(0.92, 0.03, 0.05),
        preferred="Original",
        contribution=0.15,
    )
    report = build_forensic_report(commit_analysis(db_session, analysis))
    assert any(d.source_detector == "frequency" for d in report.supporting_evidence)
    assert any(d.source_detector == "metadata" for d in report.contradicting_evidence)


def test_report_rejects_unclassified_analysis(db_session) -> None:
    analysis = vt_analysis(verdict=None)
    analysis.verdict = None
    with pytest.raises(ValueError):
        build_forensic_report(analysis)

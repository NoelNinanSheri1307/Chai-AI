"""Tests for the report renderers: Markdown, share text and JSON export."""

from __future__ import annotations

import json

from app.core.enums import Verdict
from app.services.reporting.builder import build_forensic_report
from app.services.reporting.renderers import (
    render_markdown,
    render_share_text,
    report_to_json,
)

from .report_helpers import ai_generated_report_fixture


def _report(db_session):
    return build_forensic_report(ai_generated_report_fixture(db_session))


def test_markdown_contains_all_sections(db_session) -> None:
    markdown = render_markdown(_report(db_session))
    for section in (
        "# Chai AI Forensic Analysis",
        "## Classification",
        "## Confidence",
        "## Why this classification?",
        "## Supporting Evidence",
        "## Contradicting Evidence",
        "## Detector Analysis",
        "## Suspicious Regions",
        "## Image Metadata",
        "## Processing Information",
        "## Methodology",
    ):
        assert section in markdown
    assert "AI Generated" in markdown
    assert "frequency" in markdown
    assert "Synthetic region" in markdown


def test_markdown_methodology_describes_actual_detectors(db_session) -> None:
    markdown = render_markdown(_report(db_session))
    assert "frequency" in markdown
    assert "texture" in markdown
    assert "Gaussian response" in markdown
    assert "Original, AI Generated" in markdown


def test_share_text_is_concise_and_deterministic(db_session) -> None:
    report = _report(db_session)
    first = render_share_text(report)
    second = render_share_text(report)
    assert first == second
    assert "Chai AI" in first
    assert "AI Generated" in first
    assert "Confidence" in first
    assert "Evidence supporting" in first
    assert "Evidence against" in first
    assert "report" in first  # analysis id


def test_share_text_contract_format(db_session) -> None:
    text = render_share_text(_report(db_session))
    assert text.startswith("Chai AI — Verdict: AI Generated.")
    assert "Verdict:" in text


def test_json_export_is_complete_and_stable(db_session) -> None:
    parsed = json.loads(report_to_json(_report(db_session)))
    assert parsed["analysis_id"] == "ana_gen_report"
    assert parsed["classification"]["verdict"] == Verdict.AI_GENERATED.value
    assert parsed["classification"]["confidence"] == 0.85
    assert "supporting_evidence" in parsed
    assert "contradicting_evidence" in parsed
    assert "detector_contributions" in parsed
    assert "heatmap" in parsed
    assert "image_metadata" in parsed
    assert "processing" in parsed
    assert parsed["processing"]["total_analysis_ms"] >= 0


def test_json_export_never_leaks_orm_objects(db_session) -> None:
    parsed = json.loads(report_to_json(_report(db_session)))
    assert not any(
        key in parsed for key in ("_sa_instance_state", "original_key", "user_id", "id")
    )

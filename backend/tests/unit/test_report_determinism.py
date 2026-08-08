"""Tests for report determinism.

The same stored analysis must always produce byte-identical reports — no
randomness, no volatile ordering, no timestamps inside reasoning text.
"""

from __future__ import annotations

import json

from app.services.reporting.builder import build_forensic_report
from app.services.reporting.renderers import (
    render_markdown,
    render_share_text,
    report_to_json,
)

from .report_helpers import ai_generated_report_fixture


def test_rebuild_from_reloaded_entity_is_identical(db_session) -> None:
    analysis = ai_generated_report_fixture(db_session)
    first = build_forensic_report(analysis)
    db_session.expire_all()
    reloaded = db_session.get(type(analysis), analysis.id)
    second = build_forensic_report(reloaded)

    assert first.model_dump() == second.model_dump()
    assert first.model_dump_json() == second.model_dump_json()


def test_markdown_and_share_text_are_byte_identical(db_session) -> None:
    analysis = ai_generated_report_fixture(db_session)
    report = build_forensic_report(analysis)

    assert render_markdown(report).encode() == render_markdown(report).encode()
    assert render_share_text(report) == render_share_text(report)
    assert report_to_json(report) == report_to_json(report)


def test_evidence_ordering_is_stable_across_builds(db_session) -> None:
    analysis = ai_generated_report_fixture(db_session)
    report_a = build_forensic_report(analysis)
    report_b = build_forensic_report(analysis)
    assert [e.text for e in report_a.supporting_evidence] == [
        e.text for e in report_b.supporting_evidence
    ]
    assert [d.detector for d in report_a.detector_contributions] == [
        d.detector for d in report_b.detector_contributions
    ]


def test_json_has_no_timestamp_inside_reasoning(db_session) -> None:
    report = build_forensic_report(ai_generated_report_fixture(db_session))
    markdown = render_markdown(report)
    # Reasoning text must not embed wall-clock timestamps.
    assert "2026-08-08" not in markdown
    # Report metadata timestamp is ISO (allowed).
    parsed = json.loads(report_to_json(report))
    assert parsed["timestamp"].endswith("Z")

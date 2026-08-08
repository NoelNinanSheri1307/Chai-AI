"""Report security tests.

Reports must never expose secrets, filesystem paths, ORM tokens, API
credentials or private configuration.
"""

from __future__ import annotations

import json

from app.services.reporting.builder import build_forensic_report
from app.services.reporting.renderers import (
    render_markdown,
    render_share_text,
    report_to_json,
)

from .report_helpers import add_metadata_items, commit_analysis, vt_analysis


def _crafted_suspicious_analysis(db_session):
    analysis = vt_analysis(public_id="ana_sec")
    add_metadata_items(
        analysis,
        {
            "archive": "4032 x 3024",
            "API_KEY": "sk-live-1234567890abcdef",
            "original_path": "C:\\Users\\secret\\storage\\orig\\x.png",
            "JWT": "eyJhbGciOiJIUzI1NiJ9.example",
            "Camera": "Sony ILCE-7M4",
        },
    )
    return commit_analysis(db_session, analysis)


def _all_renderings(db_session):
    report = build_forensic_report(_crafted_suspicious_analysis(db_session))
    return (
        render_markdown(report),
        render_share_text(report),
        report_to_json(report),
        json.dumps(report.model_dump()),
    )


def test_never_leaks_secret_values(db_session) -> None:
    markdown, share, json_text, dumped = _all_renderings(db_session)
    for blob in (markdown, share, json_text, dumped):
        assert "sk-live-1234" not in blob
        assert "eyJhbGciOiJIUzI1NiJ9" not in blob
        assert "storage\\orig" not in blob
        assert "C:\\Users" not in blob


def test_sensitive_metadata_pairs_are_stripped(db_session) -> None:
    report = build_forensic_report(_crafted_suspicious_analysis(db_session))
    items = report.image_metadata.items
    assert "API_KEY" not in items
    assert "JWT" not in items
    assert "original_path" not in items
    assert "Camera" in items
    assert "archive" in items


def test_report_uses_public_id_not_internal_values(db_session) -> None:
    report = build_forensic_report(_crafted_suspicious_analysis(db_session))
    dumped = json.dumps(report.model_dump())
    assert report.analysis_id.startswith("ana_")
    assert "original_key" not in dumped
    assert "user_id" not in dumped
    assert "_sa_instance_state" not in dumped
    assert "password_hash" not in dumped


def test_markdown_has_no_internal_paths(db_session) -> None:
    markdown = render_markdown(
        build_forensic_report(_crafted_suspicious_analysis(db_session))
    )
    assert "testing/orig" not in markdown
    assert "C:\\Users" not in markdown

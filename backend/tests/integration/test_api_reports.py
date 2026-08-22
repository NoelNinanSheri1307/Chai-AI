"""API integration tests for the reports router."""

from __future__ import annotations

import json

from fastapi.testclient import TestClient

from tests.sample_images import JPEG_BYTES


def _upload(api_client: TestClient) -> str:
    response = api_client.post(
        "/v1/analyses", files={"file": ("sample.jpg", JPEG_BYTES, "image/jpeg")}
    )
    assert response.status_code == 200
    return response.json()["id"]


def test_share_text_returns_report(api_client: TestClient) -> None:
    public_id = _upload(api_client)
    response = api_client.get(f"/v1/reports/{public_id}/share-text")
    assert response.status_code == 200
    body = response.json()
    assert "Chai AI" in body["text"]
    assert "Verdict:" in body["text"]
    assert any(
        label in body["text"] for label in ("Original", "AI Generated")
    )


def test_share_text_shortcut_path_returns_same(api_client: TestClient) -> None:
    public_id = _upload(api_client)
    full = api_client.get(f"/v1/reports/{public_id}/share-text").json()
    shortcut = api_client.get(f"/v1/reports/{public_id}").json()
    assert full["text"] == shortcut["text"]


def test_share_text_missing_analysis_returns_404(api_client: TestClient) -> None:
    response = api_client.get("/v1/reports/ana_missing/share-text")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "analysis_not_found"


def test_json_report_endpoint(api_client: TestClient) -> None:
    public_id = _upload(api_client)
    response = api_client.get(f"/v1/reports/{public_id}/json")
    assert response.status_code == 200
    report = response.json()
    assert report["analysis_id"] == public_id
    assert report["classification"]["verdict"] in (
        "original",
        "aiGenerated",
    )
    assert "supporting_evidence" in report
    assert "contradicting_evidence" in report
    assert "detector_contributions" in report
    assert "heatmap" in report
    assert "image_metadata" in report
    assert "processing" in report
    # Values are numbers, not strings claiming to be probabilities.
    assert isinstance(report["classification"]["confidence"], (int, float))


def test_json_report_is_stable_across_requests(api_client: TestClient) -> None:
    public_id = _upload(api_client)
    first = api_client.get(f"/v1/reports/{public_id}/json").json()
    second = api_client.get(f"/v1/reports/{public_id}/json").json()
    assert first == second


def test_markdown_report_endpoint(api_client: TestClient) -> None:
    public_id = _upload(api_client)
    response = api_client.get(f"/v1/reports/{public_id}/md")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/markdown")
    text = response.text
    assert text.startswith("# Chai AI Forensic Analysis")
    for section in (
        "## Classification",
        "## Why this classification?",
        "## Methodology",
    ):
        assert section in text


def test_report_json_and_markdown_missing_returns_404(api_client: TestClient) -> None:
    assert api_client.get("/v1/reports/ana_missing/json").status_code == 404
    assert api_client.get("/v1/reports/ana_missing/md").status_code == 404


def test_report_endpoints_do_not_leak_internal_state(api_client: TestClient) -> None:
    public_id = _upload(api_client)
    report = api_client.get(f"/v1/reports/{public_id}/json").json()
    dumped = json.dumps(report)
    assert "original_key" not in dumped
    assert "user_id" not in dumped
    assert "_sa_instance_state" not in dumped
    assert "accessToken" not in dumped
    assert "password" not in dumped

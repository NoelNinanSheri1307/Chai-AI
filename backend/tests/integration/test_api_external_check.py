"""API integration tests for the external check / benchmark endpoint."""

from __future__ import annotations

from fastapi.testclient import TestClient

from tests.sample_images import JPEG_BYTES


def test_external_check_returns_benchmark_result(api_client: TestClient) -> None:
    # 1. First upload an image to create an analysis record
    uploaded = api_client.post(
        "/v1/analyses", files={"file": ("sample.jpg", JPEG_BYTES, "image/jpeg")}
    ).json()
    public_id = uploaded["id"]

    # 2. Call external check endpoint
    response = api_client.post(f"/v1/analyses/{public_id}/external-check")
    assert response.status_code == 200

    body = response.json()
    assert body["analysisId"] == public_id
    assert "chaiVerdict" in body
    assert "chaiConfidence" in body
    assert "chaiRiskLevel" in body
    assert "externalResults" in body
    assert "benchmarkItems" in body
    assert "summary" in body

    # By default, external providers are disabled/unconfigured, so Chai analysis succeeded
    # and external check gracefully returned unconfigured/disabled status items.
    assert len(body["externalResults"]) >= 1
    assert body["externalResults"][0]["provider"] == "sightengine"
    assert isinstance(body["externalResults"][0]["isConfigured"], bool)
    assert body["externalResults"][0]["status"] in {
        "success",
        "disabled",
        "unconfigured",
        "error",
        "timeout",
    }


def test_external_check_missing_analysis_returns_404(api_client: TestClient) -> None:
    response = api_client.post("/v1/analyses/ana_nonexistent/external-check")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "analysis_not_found"

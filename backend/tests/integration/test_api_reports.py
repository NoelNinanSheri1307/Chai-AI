"""API integration tests for the reports router."""

from __future__ import annotations

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
    assert "AI Generated" in body["text"]


def test_share_text_shortcut_path_returns_same(api_client: TestClient) -> None:
    public_id = _upload(api_client)
    full = api_client.get(f"/v1/reports/{public_id}/share-text").json()
    shortcut = api_client.get(f"/v1/reports/{public_id}").json()
    assert full["text"] == shortcut["text"]


def test_share_text_missing_analysis_returns_404(api_client: TestClient) -> None:
    response = api_client.get("/v1/reports/ana_missing/share-text")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "analysis_not_found"

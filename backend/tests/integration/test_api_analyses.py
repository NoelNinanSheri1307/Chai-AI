"""API integration tests for the analyses router."""

from __future__ import annotations

from fastapi.testclient import TestClient

from tests.sample_images import GARBAGE_BYTES, JPEG_BYTES


def test_upload_analysis_returns_completed_result(api_client: TestClient) -> None:
    response = api_client.post(
        "/v1/analyses",
        files={"file": ("sample.jpg", JPEG_BYTES, "image/jpeg")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["id"].startswith("ana_")
    assert body["verdict"] == "aiGenerated"
    assert "scores" in body
    assert "indicators" in body
    assert body["confidence"] == 0.91


def test_upload_garbage_returns_422_invalid_image(api_client: TestClient) -> None:
    response = api_client.post(
        "/v1/analyses", files={"file": ("bad.jpg", GARBAGE_BYTES, "image/jpeg")}
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_image"


def test_upload_unsupported_media_returns_415(api_client: TestClient) -> None:
    response = api_client.post(
        "/v1/analyses", files={"file": ("x.gif", JPEG_BYTES, "image/gif")}
    )
    assert response.status_code == 415
    assert response.json()["error"]["code"] == "unsupported_media_type"


def test_upload_missing_file_returns_422(api_client: TestClient) -> None:
    response = api_client.post("/v1/analyses", files={})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_get_analysis_returns_stored_result(api_client: TestClient) -> None:
    uploaded = api_client.post(
        "/v1/analyses", files={"file": ("sample.jpg", JPEG_BYTES, "image/jpeg")}
    ).json()
    response = api_client.get(f"/v1/analyses/{uploaded['id']}")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == uploaded["id"]
    assert body["verdict"] == "aiGenerated"


def test_get_analysis_missing_returns_404(api_client: TestClient) -> None:
    response = api_client.get("/v1/analyses/ana_missing")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "analysis_not_found"

"""API integration tests for the compare router."""

from __future__ import annotations

from fastapi.testclient import TestClient

from tests.sample_images import GARBAGE_BYTES, JPEG_BYTES, PNG_BYTES


def test_compare_returns_result(api_client: TestClient) -> None:
    response = api_client.post(
        "/v1/compare",
        files={
            "file_a": ("photo_a.png", JPEG_BYTES, "image/jpeg"),
            "file_b": ("photo_b.png", PNG_BYTES, "image/png"),
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["labelA"] == "photo_a.png"
    assert body["labelB"] == "photo_b.png"
    assert body["similarity"] == 0.21
    assert body["aiProbability"] == 0.86
    assert body["differences"]
    assert "manipulatedRegions" in body


def test_compare_persists_both_analyses(api_client: TestClient) -> None:
    api_client.post(
        "/v1/compare",
        files={
            "file_a": ("a.jpg", JPEG_BYTES, "image/jpeg"),
            "file_b": ("b.jpg", PNG_BYTES, "image/png"),
        },
    )
    assert api_client.get("/v1/history").json()["total"] == 2


def test_compare_invalid_file_returns_422(api_client: TestClient) -> None:
    response = api_client.post(
        "/v1/compare",
        files={
            "file_a": ("bad.jpg", GARBAGE_BYTES, "image/jpeg"),
            "file_b": ("ok.jpg", PNG_BYTES, "image/png"),
        },
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_image"

"""API integration tests for the history router."""

from __future__ import annotations

from fastapi.testclient import TestClient

from tests.sample_images import JPEG_BYTES, PNG_BYTES


def _upload(api_client: TestClient, *, name: str, data: bytes, mime: str) -> str:
    response = api_client.post("/v1/analyses", files={"file": (name, data, mime)})
    assert response.status_code == 200
    return response.json()["id"]


def test_list_history_returns_page_envelope(api_client: TestClient) -> None:
    _upload(api_client, name="a.jpg", data=JPEG_BYTES, mime="image/jpeg")
    _upload(api_client, name="b.png", data=PNG_BYTES, mime="image/png")

    response = api_client.get("/v1/history")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert body["page"] == 1
    assert body["has_more"] is False
    assert len(body["items"]) == 2
    assert all(item["id"].startswith("ana_") for item in body["items"])
    assert body["items"][0]["isFavorite"] is False


def test_list_history_honours_pagination(api_client: TestClient) -> None:
    for index in range(3):
        _upload(api_client, name=f"{index}.jpg", data=JPEG_BYTES, mime="image/jpeg")

    response = api_client.get("/v1/history?page=1&limit=2")
    assert response.status_code == 200
    body = response.json()
    assert body["limit"] == 2
    assert len(body["items"]) == 2
    assert body["has_more"] is True


def test_history_detail_returns_full_result(api_client: TestClient) -> None:
    public_id = _upload(api_client, name="a.jpg", data=JPEG_BYTES, mime="image/jpeg")
    response = api_client.get(f"/v1/history/{public_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == public_id
    assert body["verdict"] == "aiGenerated"
    assert body["scores"]


def test_history_detail_missing_returns_404(api_client: TestClient) -> None:
    response = api_client.get("/v1/history/ana_missing")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "history_not_found"


def test_delete_history_soft_deletes(api_client: TestClient) -> None:
    public_id = _upload(api_client, name="a.jpg", data=JPEG_BYTES, mime="image/jpeg")

    response = api_client.delete(f"/v1/history/{public_id}")
    assert response.status_code == 204

    assert api_client.get("/v1/history").json()["total"] == 0
    detail = api_client.get(f"/v1/history/{public_id}")
    assert detail.status_code == 404
    assert detail.json()["error"]["code"] == "history_not_found"

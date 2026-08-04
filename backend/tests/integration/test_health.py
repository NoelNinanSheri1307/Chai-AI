"""Integration tests for health endpoints, docs and the API contract."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_health(client: TestClient) -> None:
    response = client.get("/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_reports_not_configured_checks(client: TestClient) -> None:
    response = client.get("/v1/health/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "degraded"
    assert body["checks"] == {
        "database": "not configured",
        "storage": "not configured",
        "cache": "not configured",
        "models": "not configured",
    }


def test_openapi_document_is_configured(client: TestClient) -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    info = response.json()["info"]
    assert info["title"] == "Chai AI"
    assert info["version"]
    assert "/v1/health" in response.json()["paths"]


def test_docs_and_redoc_resolve(client: TestClient) -> None:
    assert client.get("/docs").status_code == 200
    assert client.get("/redoc").status_code == 200


def test_unknown_route_returns_standard_error(client: TestClient) -> None:
    response = client.get("/v1/definitely-not-a-route")
    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "invalid_request"
    assert isinstance(body["error"]["retryable"], bool)
    assert isinstance(body["error"]["details"], dict)


def test_inbound_request_id_is_echoed(client: TestClient) -> None:
    response = client.get("/v1/health", headers={"X-Request-ID": "abc-123"})
    assert response.headers.get("x-request-id") == "abc-123"


def test_request_id_is_generated_when_absent(client: TestClient) -> None:
    response = client.get("/v1/health")
    assert response.headers.get("x-request-id")

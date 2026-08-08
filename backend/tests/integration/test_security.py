"""Security hardening tests (Milestone 10).

Covers oversized uploads, invalid MIME/magic bytes, path traversal, unsafe
storage keys, production error sanitisation, CORS/trusted-host configuration,
security headers and secret leakage in responses.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.clients.storage import LocalStorageAdapter, StorageError
from app.core.config import Settings
from app.core.exceptions import (
    ConfigurationError,
)
from app.main import create_app
from tests.sample_bytes import bomb_png
from tests.sample_images import (
    GARBAGE_BYTES,
    JPEG_BYTES,
)


def test_oversized_upload_rejected_413(api_client: TestClient) -> None:
    payload = b"\x00" * (25 * 1024 * 1024 + 1)
    response = api_client.post(
        "/v1/analyses", files={"file": ("big.jpg", payload, "image/jpeg")}
    )
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "file_too_large"


def test_decompression_bomb_upload_rejected(api_client: TestClient) -> None:
    response = api_client.post(
        "/v1/analyses", files={"file": ("bomb.png", bomb_png(), "image/png")}
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_image"


def test_invalid_magic_bytes_rejected(api_client: TestClient) -> None:
    response = api_client.post(
        "/v1/analyses", files={"file": ("fake.jpg", GARBAGE_BYTES, "image/jpeg")}
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_image"


def test_mime_mismatch_rejected(api_client: TestClient) -> None:
    response = api_client.post(
        "/v1/analyses", files={"file": ("x.png", JPEG_BYTES, "image/png")}
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_image"


def test_unsupported_mime_rejected(api_client: TestClient) -> None:
    response = api_client.post(
        "/v1/analyses", files={"file": ("x.gif", JPEG_BYTES, "image/gif")}
    )
    assert response.status_code == 415
    assert response.json()["error"]["code"] == "unsupported_media_type"


# ---------------------------------------------------------------------------
# Storage path traversal / unsafe keys
# ---------------------------------------------------------------------------


def test_storage_rejects_path_traversal(storage: LocalStorageAdapter) -> None:
    for key in [
        "../escape.txt",
        "a/../../escape.txt",
        "/etc/passwd",
        "a/./b.png",
        "a//b.png",
        "a\\..\\..\\escape.txt",
    ]:
        try:
            storage.store(key, b"x")
            raise AssertionError(f"path traversal key accepted: {key!r}")
        except StorageError:
            pass


def test_storage_rejects_oversized_key(storage: LocalStorageAdapter) -> None:
    try:
        storage.store("x" * 300, b"data")
        raise AssertionError("oversized key accepted")
    except StorageError:
        pass


def test_storage_store_is_atomic_and_readable(storage: LocalStorageAdapter) -> None:
    storage.store("dev/orig/abc123.png", b"hello", content_type="image/png")
    assert storage.fetch("dev/orig/abc123.png") == b"hello"
    assert storage.exists("dev/orig/abc123.png")


# ---------------------------------------------------------------------------
# Error sanitisation in production
# ---------------------------------------------------------------------------


def test_production_errors_do_not_leak_internals() -> None:
    app = create_app(
        Settings(
            environment="production",
            debug=False,
            database_url="sqlite://",
            cors_origins=["https://app.chai.example"],
            trusted_hosts=["api.chai.example"],
        )
    )
    client = TestClient(app)
    # Trigger an internal failure (missing route handler path) and assert the
    # response never exposes tracebacks or filesystem paths.
    response = client.get("/v1/analyses/ana_nope", headers={"Host": "api.chai.example"})
    assert response.status_code == 404
    body = response.json()
    assert "error" in body
    message = body["error"]["message"]
    assert "Traceback" not in message
    assert "app\\" not in message and "app/" not in message
    assert "C:" not in message


def test_debug_errors_are_sanitised_even_with_detail() -> None:
    app = create_app(
        Settings(environment="testing", debug=True, database_url="sqlite://")
    )
    client = TestClient(app)
    response = client.get("/v1/analyses/ana_nope")
    # Debug mode may add a hint, but never raw internals such as DB URLs.
    text = response.text
    assert "sqlite" not in text
    assert "password" not in text.lower()


# ---------------------------------------------------------------------------
# CORS and trusted hosts
# ---------------------------------------------------------------------------


def test_cors_restricted_when_configured() -> None:
    app = create_app(
        Settings(
            environment="testing",
            cors_origins=["https://app.chai.example"],
            database_url="sqlite://",
        )
    )
    client = TestClient(app)
    response = client.options(
        "/v1/health",
        headers={
            "Origin": "https://evil.example",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.headers.get("access-control-allow-origin") != "https://evil.example"
    # Allowed origin is echoed.
    response = client.options(
        "/v1/health",
        headers={
            "Origin": "https://app.chai.example",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert (
        response.headers.get("access-control-allow-origin")
        == "https://app.chai.example"
    )


def test_trusted_host_enforced_when_configured() -> None:
    app = create_app(
        Settings(
            environment="testing",
            trusted_hosts=["api.chai.example"],
            database_url="sqlite://",
        )
    )
    client = TestClient(app)
    response = client.get("/v1/health", headers={"Host": "evil.example"})
    assert response.status_code == 400  # Starlette trusted-host rejects
    response = client.get("/v1/health", headers={"Host": "api.chai.example"})
    assert response.status_code == 200


def test_production_rejects_insecure_defaults() -> None:
    for settings in [
        Settings(environment="production", debug=True),
        Settings(environment="production", cors_origins=["*"]),
        Settings(environment="production", trusted_hosts=["*"]),
        Settings(environment="production", docs_enabled=True),
    ]:
        try:
            create_app(settings)
            raise AssertionError("production app created with unsafe settings")
        except ConfigurationError:
            pass


# ---------------------------------------------------------------------------
# Security headers
# ---------------------------------------------------------------------------


def test_security_headers_present(client: TestClient) -> None:
    response = client.get("/v1/health")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"


def test_hsts_present_in_production() -> None:
    app = create_app(
        Settings(
            environment="production",
            database_url="sqlite://",
            cors_origins=["https://app.chai.example"],
            trusted_hosts=["api.chai.example"],
        )
    )
    client = TestClient(app)
    response = client.get("/v1/health", headers={"Host": "api.chai.example"})
    assert "strict-transport-security" in response.headers


# ---------------------------------------------------------------------------
# Secrets never reach the client
# ---------------------------------------------------------------------------


def test_analysis_response_contains_no_secrets(api_client: TestClient) -> None:
    response = api_client.post(
        "/v1/analyses", files={"file": ("a.jpg", JPEG_BYTES, "image/jpeg")}
    )
    assert response.status_code == 200
    text = response.text.lower()
    for token in ("password", "secret", "api_key", "token_hash", "chai_database_url"):
        assert token not in text


def test_report_contains_no_secrets(api_client: TestClient) -> None:
    uploaded = api_client.post(
        "/v1/analyses", files={"file": ("a.jpg", JPEG_BYTES, "image/jpeg")}
    ).json()
    for endpoint in (
        f"/v1/reports/{uploaded['id']}/share-text",
        f"/v1/reports/{uploaded['id']}/json",
    ):
        response = api_client.get(endpoint)
        assert response.status_code == 200
        assert "password" not in response.text.lower()
        assert "secret" not in response.text.lower()

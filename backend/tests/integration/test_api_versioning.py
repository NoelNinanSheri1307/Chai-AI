"""API integration tests: pipeline versioning flows through to the result."""

from __future__ import annotations

from fastapi.testclient import TestClient

from tests.sample_images import JPEG_BYTES


def test_version_trail_reaches_analysis_result_metadata(
    api_client: TestClient,
) -> None:
    response = api_client.post(
        "/v1/analyses", files={"file": ("sample.jpg", JPEG_BYTES, "image/jpeg")}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["metadata"]["pipeline_version"]
    assert body["metadata"]["framework_version"]
    assert body["metadata"]["fusion_version"]
    assert body["metadata"]["detector_versions"]


def test_version_trail_persists_and_is_retrievable(api_client: TestClient) -> None:
    uploaded = api_client.post(
        "/v1/analyses", files={"file": ("sample.jpg", JPEG_BYTES, "image/jpeg")}
    ).json()
    persisted = api_client.get(f"/v1/analyses/{uploaded['id']}").json()
    assert (
        persisted["metadata"]["pipeline_version"]
        == uploaded["metadata"]["pipeline_version"]
    )

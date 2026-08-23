"""Unit tests for the external AI detection & independent benchmarking layer."""

from __future__ import annotations

import httpx
import pytest

from app.clients.external_detection.base import (
    ExternalDetectionResult,
    ExternalDetectorProvider,
)
from app.clients.external_detection.benchmark import (
    compare_verdict,
    compute_benchmark_report,
)
from app.clients.external_detection.manager import ExternalDetectionManager
from app.clients.external_detection.providers.sightengine import (
    SightengineDetectorProvider,
)
from app.core.config import Settings


class MockCustomProvider(ExternalDetectorProvider):
    """Mock provider for unit testing provider contracts."""

    def __init__(
        self,
        name: str = "mock_provider",
        configured: bool = True,
        result: ExternalDetectionResult | None = None,
    ) -> None:
        self._name = name
        self._configured = configured
        self._result = result

    @property
    def provider_name(self) -> str:
        return self._name

    @property
    def provider_version(self) -> str:
        return "1.0.0"

    def is_configured(self) -> bool:
        return self._configured

    def analyze(
        self,
        image_bytes: bytes,
        filename: str = "image.jpg",
        content_type: str = "image/jpeg",
    ) -> ExternalDetectionResult:
        if not self._configured:
            return ExternalDetectionResult(
                provider=self.provider_name,
                provider_version=self.provider_version,
                is_configured=False,
                status="unconfigured",
                error_message="Provider unconfigured.",
            )
        return self._result or ExternalDetectionResult(
            provider=self.provider_name,
            provider_version=self.provider_version,
            is_configured=True,
            status="success",
            detected_as_ai=True,
            confidence=0.88,
            classification_label="ai_generated",
        )


def test_provider_contract_and_normalized_result_model() -> None:
    res = ExternalDetectionResult(
        provider="test_provider",
        provider_version="1.0",
        is_configured=True,
        status="success",
        detected_as_ai=True,
        confidence=0.92,
        classification_label="ai_generated",
        raw_category="genai",
        processing_time_ms=120,
        metadata={"request_id": "req_1"},
    )
    assert res.provider == "test_provider"
    assert res.is_configured is True
    assert res.status == "success"
    assert res.detected_as_ai is True
    assert res.confidence == 0.92
    assert res.metadata == {"request_id": "req_1"}


def test_disabled_provider_behaviour() -> None:
    settings = Settings(external_detection_enabled=False)
    provider = SightengineDetectorProvider(settings)
    assert provider.is_configured() is False

    res = provider.analyze(b"fake_image_bytes")
    assert res.provider == "sightengine"
    assert res.is_configured is False
    assert res.status == "disabled"
    assert "disabled" in (res.error_message or "").lower()


def test_unconfigured_provider_behaviour() -> None:
    settings = Settings(
        external_detection_enabled=True,
        sightengine_enabled=True,
        sightengine_api_user=None,
        sightengine_api_secret=None,
    )
    provider = SightengineDetectorProvider(settings)
    assert provider.is_configured() is False

    res = provider.analyze(b"fake_image_bytes")
    assert res.is_configured is False
    assert res.status == "unconfigured"
    assert "missing" in (res.error_message or "").lower()


def test_provider_http_failure_handling(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = Settings(
        external_detection_enabled=True,
        sightengine_enabled=True,
        sightengine_api_user="user123",
        sightengine_api_secret="secret456",
    )
    provider = SightengineDetectorProvider(settings)
    assert provider.is_configured() is True

    def mock_post(*args, **kwargs):
        class MockResponse:
            status_code = 500

            def json(self):
                return {"error": "Server error"}

        return MockResponse()

    monkeypatch.setattr(httpx.Client, "post", mock_post)

    res = provider.analyze(b"fake_image_bytes")
    assert res.is_configured is True
    assert res.status == "error"
    assert "500" in (res.error_message or "")


def test_provider_timeout_handling(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = Settings(
        external_detection_enabled=True,
        sightengine_enabled=True,
        sightengine_api_user="user123",
        sightengine_api_secret="secret456",
    )
    provider = SightengineDetectorProvider(settings)

    def mock_post_timeout(*args, **kwargs):
        raise httpx.TimeoutException("Timed out")

    monkeypatch.setattr(httpx.Client, "post", mock_post_timeout)

    res = provider.analyze(b"fake_image_bytes")
    assert res.status == "timeout"
    assert "timed out" in (res.error_message or "").lower()


def test_sightengine_successful_parsing(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = Settings(
        external_detection_enabled=True,
        sightengine_enabled=True,
        sightengine_api_user="user123",
        sightengine_api_secret="secret456",
    )
    provider = SightengineDetectorProvider(settings)

    def mock_post_success(*args, **kwargs):
        class MockResponse:
            status_code = 200

            def json(self):
                return {
                    "status": "success",
                    "request": {"id": "req_abc123"},
                    "type": {"ai_generated": 0.94},
                }

        return MockResponse()

    monkeypatch.setattr(httpx.Client, "post", mock_post_success)

    res = provider.analyze(b"fake_bytes")
    assert res.status == "success"
    assert res.detected_as_ai is True
    assert res.confidence == 0.94
    assert res.classification_label == "ai_generated"
    assert res.metadata.get("request_id") == "req_abc123"
    # Verify credentials never leak into response metadata or error messages
    assert "user123" not in str(res.model_dump())
    assert "secret456" not in str(res.model_dump())


def test_binary_vs_three_class_matching_agreements() -> None:
    # 1. Chai Original & External detected_as_ai=False -> Match
    res_orig = ExternalDetectionResult(
        provider="p1",
        provider_version="1.0",
        is_configured=True,
        status="success",
        detected_as_ai=False,
        confidence=0.10,
        classification_label="authentic",
    )
    item1 = compare_verdict("original", 0.90, res_orig)
    assert item1.agreement is True
    assert "authentic/original" in item1.compatibility_note

    # 2. Chai AI Generated & External detected_as_ai=True -> Match
    res_ai = ExternalDetectionResult(
        provider="p1",
        provider_version="1.0",
        is_configured=True,
        status="success",
        detected_as_ai=True,
        confidence=0.95,
        classification_label="ai_generated",
    )
    item2 = compare_verdict("ai_generated", 0.95, res_ai)
    assert item2.agreement is True
    assert "synthetic" in item2.compatibility_note

    # 3. Chai AI Edited & External detected_as_ai=True -> Compatible Match
    item3 = compare_verdict("ai_edited", 0.85, res_ai)
    assert item3.agreement is True
    assert "compatible classification" in item3.compatibility_note


def test_genuine_disagreement_cases() -> None:
    res_ai = ExternalDetectionResult(
        provider="p1",
        provider_version="1.0",
        is_configured=True,
        status="success",
        detected_as_ai=True,
        confidence=0.88,
        classification_label="ai_generated",
    )
    # Chai says Original, External says AI -> Disagreement
    item1 = compare_verdict("original", 0.90, res_ai)
    assert item1.agreement is False
    assert "Disagreement" in item1.compatibility_note

    res_auth = ExternalDetectionResult(
        provider="p1",
        provider_version="1.0",
        is_configured=True,
        status="success",
        detected_as_ai=False,
        confidence=0.05,
        classification_label="authentic",
    )
    # Chai says AI Generated, External says Original -> Disagreement
    item2 = compare_verdict("ai_generated", 0.92, res_auth)
    assert item2.agreement is False
    assert "Disagreement" in item2.compatibility_note


def test_multiple_providers_benchmark_aggregation() -> None:
    p1 = MockCustomProvider(
        "prov1",
        True,
        ExternalDetectionResult(
            provider="prov1",
            provider_version="1.0",
            is_configured=True,
            status="success",
            detected_as_ai=True,
            confidence=0.90,
            classification_label="ai_generated",
        ),
    )
    p2 = MockCustomProvider(
        "prov2",
        True,
        ExternalDetectionResult(
            provider="prov2",
            provider_version="1.0",
            is_configured=True,
            status="success",
            detected_as_ai=False,
            confidence=0.10,
            classification_label="authentic",
        ),
    )

    mgr = ExternalDetectionManager(providers=[p1, p2])
    results = mgr.analyze_all(b"bytes")
    assert len(results) == 2

    report = compute_benchmark_report(
        analysis_id="ana_test",
        chai_verdict="ai_generated",
        chai_confidence=0.91,
        chai_risk_level="high",
        external_results=results,
    )
    assert report.analysis_id == "ana_test"
    assert len(report.benchmark_items) == 2
    # p1 agrees (True), p2 disagrees (False) -> ratio 0.5
    assert report.overall_agreement_ratio == 0.5
    assert "Partial agreement" in report.summary

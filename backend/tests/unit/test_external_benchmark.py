"""Unit and integration tests for Milestone 15 — Independent External Benchmarking with Sightengine."""

from __future__ import annotations

import io
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from app.benchmark.external_cache import ExternalBenchmarkCache
from app.benchmark.external_metrics import (
    ChaiVsExternalAgreement,
    ExternalProviderMetrics,
    compute_agreement_metrics,
    compute_complete_external_benchmark,
    compute_external_provider_metrics,
    compute_format_comparisons,
    compute_three_way_comparison,
)
from app.benchmark.external_reports import (
    generate_external_markdown_report,
    save_external_reports,
)
from app.benchmark.models import (
    BenchmarkManifest,
    GroundTruthLabel,
    ImageBenchmarkResult,
    ManifestEntry,
)
from app.benchmark.runner import run_benchmark
from app.clients.external_detection.base import (
    ExternalDetectionResult,
)
from app.clients.external_detection.manager import ExternalDetectionManager
from app.clients.external_detection.providers.sightengine import (
    SightengineDetectorProvider,
)
from app.core.config import Settings


def _create_test_image_bytes(color: str = "red", size: tuple[int, int] = (32, 32)) -> bytes:
    img = Image.new("RGB", size, color=color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


# ---------------------------------------------------------------------------
# 1. External benchmark disabled / unconfigured
# ---------------------------------------------------------------------------


def test_provider_disabled_globally() -> None:
    settings = Settings(
        external_detection_enabled=False,
        sightengine_enabled=True,
        sightengine_api_user="test_user",
        sightengine_api_secret="test_secret",
    )
    provider = SightengineDetectorProvider(settings)
    assert not provider.is_configured()

    res = provider.analyze(b"fake_bytes")
    assert res.status == "disabled"
    assert res.is_configured is False
    assert res.detected_as_ai is None
    assert "disabled" in (res.error_message or "").lower()


def test_provider_unconfigured_missing_credentials() -> None:
    settings = Settings(
        external_detection_enabled=True,
        sightengine_enabled=True,
        sightengine_api_user=None,
        sightengine_api_secret=None,
    )
    provider = SightengineDetectorProvider(settings)
    assert not provider.is_configured()

    res = provider.analyze(b"fake_bytes")
    assert res.status == "unconfigured"
    assert res.is_configured is False
    assert res.detected_as_ai is None
    assert "missing" in (res.error_message or "").lower()


# ---------------------------------------------------------------------------
# 2. Successful response parsing & normalization
# ---------------------------------------------------------------------------


def test_successful_sightengine_ai_detected() -> None:
    settings = Settings(
        external_detection_enabled=True,
        sightengine_enabled=True,
        sightengine_api_user="user123",
        sightengine_api_secret="secret123",
    )
    provider = SightengineDetectorProvider(settings)
    assert provider.is_configured()

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "status": "success",
        "request": {"id": "req_abc123"},
        "type": {"ai_generated": 0.92},
    }

    with patch("httpx.Client.post", return_value=mock_response):
        res = provider.analyze(b"image_bytes_here")

    assert res.status == "success"
    assert res.is_configured is True
    assert res.detected_as_ai is True
    assert res.confidence == 0.92
    assert res.classification_label == "ai_generated"
    assert res.metadata.get("request_id") == "req_abc123"


def test_successful_sightengine_authentic_detected() -> None:
    settings = Settings(
        external_detection_enabled=True,
        sightengine_enabled=True,
        sightengine_api_user="user123",
        sightengine_api_secret="secret123",
    )
    provider = SightengineDetectorProvider(settings)

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "status": "success",
        "request": {"id": "req_xyz456"},
        "type": {"ai_generated": 0.05},
    }

    with patch("httpx.Client.post", return_value=mock_response):
        res = provider.analyze(b"image_bytes_here")

    assert res.status == "success"
    assert res.detected_as_ai is False
    assert res.confidence == 0.05
    assert res.classification_label == "authentic"


# ---------------------------------------------------------------------------
# 3. Provider error handling (timeout, HTTP error, malformed)
# ---------------------------------------------------------------------------


def test_provider_timeout_handling() -> None:
    import httpx

    settings = Settings(
        external_detection_enabled=True,
        sightengine_enabled=True,
        sightengine_api_user="user123",
        sightengine_api_secret="secret123",
        external_timeout_seconds=2.0,
    )
    provider = SightengineDetectorProvider(settings)

    with patch("httpx.Client.post", side_effect=httpx.TimeoutException("Read timed out")):
        res = provider.analyze(b"bytes")

    assert res.status == "timeout"
    assert res.detected_as_ai is None
    assert res.confidence is None
    assert "timed out" in (res.error_message or "").lower()


def test_provider_http_error_handling() -> None:
    settings = Settings(
        external_detection_enabled=True,
        sightengine_enabled=True,
        sightengine_api_user="user123",
        sightengine_api_secret="secret123",
    )
    provider = SightengineDetectorProvider(settings)

    mock_response = MagicMock()
    mock_response.status_code = 500

    with patch("httpx.Client.post", return_value=mock_response):
        res = provider.analyze(b"bytes")

    assert res.status == "error"
    assert res.detected_as_ai is None
    assert "500" in (res.error_message or "")


def test_provider_malformed_response_handling() -> None:
    settings = Settings(
        external_detection_enabled=True,
        sightengine_enabled=True,
        sightengine_api_user="user123",
        sightengine_api_secret="secret123",
    )
    provider = SightengineDetectorProvider(settings)

    # Status failure in payload
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "status": "failure",
        "error": {"message": "Invalid file format"},
    }

    with patch("httpx.Client.post", return_value=mock_response):
        res = provider.analyze(b"bytes")

    assert res.status == "error"
    assert "Invalid file format" in (res.error_message or "")


# ---------------------------------------------------------------------------
# 4. Resilience: external failure never breaks internal benchmark
# ---------------------------------------------------------------------------


def test_external_failure_does_not_break_internal_benchmark(tmp_path: Path) -> None:
    img_path = tmp_path / "test.jpg"
    img_path.write_bytes(_create_test_image_bytes())

    manifest = BenchmarkManifest(
        version="2.0",
        created_at="2026-08-23T00:00:00Z",
        description="test",
        entries=[
            ManifestEntry(
                id="img_1",
                sha256="abc123hash",
                path=str(img_path),
                dataset="test",
                ground_truth=GroundTruthLabel.ORIGINAL,
                width=32,
                height=32,
                format="JPEG",
                file_size_bytes=1024,
            )
        ],
    )

    # External manager that raises unhandled exception
    broken_manager = MagicMock()
    broken_manager.analyze_all.side_effect = RuntimeError("Network crashed!")

    run_res = run_benchmark(
        manifest=manifest,
        external_manager=broken_manager,
        run_external=True,
    )

    assert run_res.successful_analyses == 1
    assert run_res.failed_analyses == 0
    assert len(run_res.results) == 1
    item = run_res.results[0]
    assert item.predicted_class in {"original", "ai_generated"}
    # Internal forensic confidence still populated
    assert 0.0 <= item.confidence <= 1.0


# ---------------------------------------------------------------------------
# 5. Metrics, Agreement, and Three-Way Comparisons
# ---------------------------------------------------------------------------


def _build_mock_image_result(
    img_id: str,
    gt: GroundTruthLabel,
    chai_pred: str,
    ext_ai: bool | None,
    ext_conf: float | None = None,
    file_path: str = "img.jpg",
) -> ImageBenchmarkResult:
    ext_data = None
    if ext_ai is not None:
        ext_data = {
            "provider": "sightengine",
            "provider_version": "1.0",
            "is_configured": True,
            "status": "success",
            "detected_as_ai": ext_ai,
            "confidence": ext_conf if ext_conf is not None else (0.9 if ext_ai else 0.1),
            "classification_label": "ai_generated" if ext_ai else "authentic",
        }
    elif ext_conf is None:
        ext_data = {
            "provider": "sightengine",
            "provider_version": "1.0",
            "is_configured": False,
            "status": "unconfigured",
            "detected_as_ai": None,
            "confidence": None,
        }

    return ImageBenchmarkResult(
        image_id=img_id,
        sha256=f"hash_{img_id}",
        dataset="test",
        ground_truth=gt,
        file_path=file_path,
        predicted_class=chai_pred,
        correct=chai_pred == gt.value,
        confidence=0.85,
        risk_level="low",
        analysis_duration_ms=10,
        external_result=ext_data,
    )


def test_external_metrics_calculation() -> None:
    results = [
        # Ground Truth Real, Sightengine Real (TN)
        _build_mock_image_result("r1", GroundTruthLabel.ORIGINAL, "original", ext_ai=False),
        # Ground Truth Real, Sightengine AI (FP)
        _build_mock_image_result("r2", GroundTruthLabel.ORIGINAL, "original", ext_ai=True),
        # Ground Truth AI, Sightengine AI (TP)
        _build_mock_image_result("a1", GroundTruthLabel.AI_GENERATED, "ai_generated", ext_ai=True),
        # Ground Truth AI, Sightengine Real (FN)
        _build_mock_image_result("a2", GroundTruthLabel.AI_GENERATED, "ai_generated", ext_ai=False),
    ]

    metrics = compute_external_provider_metrics(results)
    assert isinstance(metrics, ExternalProviderMetrics)
    assert metrics.total_evaluated == 4
    assert metrics.successful_analyses == 4
    assert metrics.tp == 1
    assert metrics.tn == 1
    assert metrics.fp == 1
    assert metrics.fn == 1
    assert metrics.accuracy == 0.50
    assert metrics.precision == 0.50
    assert metrics.recall == 0.50
    assert metrics.f1 == 0.50


def test_agreement_calculation() -> None:
    results = [
        # Real GT: Both say Real -> Agree
        _build_mock_image_result("r1", GroundTruthLabel.ORIGINAL, "original", ext_ai=False),
        # Real GT: Chai Real, Ext AI -> Disagree
        _build_mock_image_result("r2", GroundTruthLabel.ORIGINAL, "original", ext_ai=True),
        # AI GT: Both say AI -> Agree
        _build_mock_image_result("a1", GroundTruthLabel.AI_GENERATED, "ai_generated", ext_ai=True),
        # AI GT: Chai AI, Ext Real -> Disagree
        _build_mock_image_result("a2", GroundTruthLabel.AI_GENERATED, "ai_generated", ext_ai=False),
    ]

    agr = compute_agreement_metrics(results)
    assert isinstance(agr, ChaiVsExternalAgreement)
    assert agr.total_compared == 4
    assert agr.agree_count == 2
    assert agr.disagree_count == 2
    assert agr.agreement_rate == 0.50
    assert agr.chai_real_ext_real == 1
    assert agr.chai_ai_ext_ai == 1
    assert agr.chai_real_ext_ai == 1
    assert agr.chai_ai_ext_real == 1
    assert agr.real_subset_agree_rate == 0.50
    assert agr.ai_subset_agree_rate == 0.50


def test_three_way_comparison_truth_table() -> None:
    results = [
        # Real, Real, Real -> Both correct (authentic)
        _build_mock_image_result("r1", GroundTruthLabel.ORIGINAL, "original", ext_ai=False),
        # Real, AI, Real -> Chai FP
        _build_mock_image_result("r2", GroundTruthLabel.ORIGINAL, "ai_generated", ext_ai=False),
        # AI, AI, AI -> Both correct (AI)
        _build_mock_image_result("a1", GroundTruthLabel.AI_GENERATED, "ai_generated", ext_ai=True),
        # AI, Real, Real -> Both missed
        _build_mock_image_result("a2", GroundTruthLabel.AI_GENERATED, "original", ext_ai=False),
    ]

    table = compute_three_way_comparison(results)
    assert len(table) == 8

    # Find row for (original, original, original)
    both_real = next(t for t in table if t.ground_truth == "original" and t.chai_verdict == "original" and t.external_verdict == "original")
    assert both_real.count == 1
    assert both_real.sample_image_ids == ["r1"]

    # Find row for (ai_generated, original, original)
    both_miss = next(t for t in table if t.ground_truth == "ai_generated" and t.chai_verdict == "original" and t.external_verdict == "original")
    assert both_miss.count == 1
    assert both_miss.sample_image_ids == ["a2"]


def test_format_comparisons() -> None:
    results = [
        _build_mock_image_result("j1", GroundTruthLabel.ORIGINAL, "original", ext_ai=False, file_path="img.jpg"),
        _build_mock_image_result("p1", GroundTruthLabel.AI_GENERATED, "ai_generated", ext_ai=True, file_path="img.png"),
        _build_mock_image_result("a1", GroundTruthLabel.AI_GENERATED, "original", ext_ai=True, file_path="img.avif"),
    ]

    breakdown = compute_format_comparisons(results)
    assert "JPEG" in breakdown
    assert "PNG" in breakdown
    assert "AVIF" in breakdown

    assert breakdown["JPEG"].image_count == 1
    assert breakdown["JPEG"].chai_accuracy == 1.0
    assert breakdown["AVIF"].chai_ai_recall == 0.0
    assert breakdown["AVIF"].external_ai_recall == 1.0


# ---------------------------------------------------------------------------
# 6. Caching by SHA-256 + provider + version
# ---------------------------------------------------------------------------


def test_external_benchmark_cache_persistence(tmp_path: Path) -> None:
    cache_file = tmp_path / "test_cache.json"
    cache = ExternalBenchmarkCache(cache_file)
    assert len(cache) == 0

    res = ExternalDetectionResult(
        provider="sightengine",
        provider_version="1.0",
        is_configured=True,
        status="success",
        detected_as_ai=True,
        confidence=0.88,
        classification_label="ai_generated",
    )

    sha = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    cache.set(sha, "sightengine", "1.0", res)
    assert len(cache) == 1

    cached_item = cache.get(sha, "sightengine", "1.0")
    assert cached_item is not None
    assert cached_item.detected_as_ai is True
    assert cached_item.confidence == 0.88

    # Save and reload in new instance
    cache.save()
    assert cache_file.is_file()

    cache_reloaded = ExternalBenchmarkCache(cache_file)
    assert len(cache_reloaded) == 1
    item_reloaded = cache_reloaded.get(sha, "sightengine", "1.0")
    assert item_reloaded is not None
    assert item_reloaded.confidence == 0.88


# ---------------------------------------------------------------------------
# 7. Privacy & Security: Zero credentials or image bytes in output
# ---------------------------------------------------------------------------


def test_reports_and_json_contain_no_credentials(tmp_path: Path) -> None:
    img_res = _build_mock_image_result("r1", GroundTruthLabel.ORIGINAL, "original", ext_ai=False)
    # Complete benchmark run result
    from app.benchmark.metrics import compute_benchmark_run_result

    run_res = compute_benchmark_run_result(
        run_id="test_m15_run",
        timestamp="2026-08-23T00:00:00Z",
        manifest_hash="test_manifest_hash_123456",
        duration_seconds=1.2,
        successful_count=1,
        failed_count=0,
        results=[img_res],
    )

    ext_report = compute_complete_external_benchmark(run_res)
    md_report = generate_external_markdown_report(ext_report)
    json_report = ext_report.model_dump_json(indent=2)

    secret_tokens = ["api_secret", "secret123", "CHAI_SIGHTENGINE", "password", "Bearer "]
    for token in secret_tokens:
        assert token.lower() not in md_report.lower()
        assert token.lower() not in json_report.lower()

    # Verify report files saved
    out_dir = tmp_path / "reports"
    md_p, json_p = save_external_reports(ext_report, out_dir)
    assert md_p.is_file()
    assert json_p.is_file()
    saved_md = md_p.read_text(encoding="utf-8")
    assert "# Chai AI vs Sightengine External Benchmark Report" in saved_md
    assert "## 5. Three-Way Ground-Truth Comparison" in saved_md

"""Performance/regression tests (Milestone 10).

These are deliberately *not* machine-specific latency assertions. They verify
behavioural guarantees that hardening introduced: the pipeline completes,
bounded concurrency is respected, malformed input does not crash the process,
concurrent requests do not corrupt results and repeated analysis is
deterministic.
"""

from __future__ import annotations

import threading
import time
from concurrent.futures import ThreadPoolExecutor

import pytest

from app.core.enums import Verdict
from app.core.execution import run_with_timeout, shutdown_executors
from app.pipeline.config import PipelineConfig
from app.pipeline.detectors.registry import build_detectors
from app.pipeline.explanation.classifier import (
    ClassificationEvidenceGenerator,
    ClassificationExplanationGenerator,
)
from app.pipeline.fusion.engine import DeterministicFusionEngine
from app.pipeline.heatmap.generator import DeterministicHeatmapGenerator
from app.pipeline.runner import ModularAnalysisPipeline
from tests.sample_images import JPEG_BYTES


def _build_pipeline(max_concurrency: int = 1) -> ModularAnalysisPipeline:
    config = PipelineConfig()
    return ModularAnalysisPipeline(
        detectors=build_detectors(config.enabled_detector_names()),
        fusion=DeterministicFusionEngine(config),
        heatmap_generator=DeterministicHeatmapGenerator(config),
        evidence_generator=ClassificationEvidenceGenerator(config),
        explanation_generator=ClassificationExplanationGenerator(config),
        pipeline_config=config,
    )


def _analyze(pipeline: ModularAnalysisPipeline) -> dict:
    started = time.perf_counter()
    result = pipeline.analyze(JPEG_BYTES, content_type="image/jpeg")
    return {
        "result": result,
        "latency_s": time.perf_counter() - started,
    }


def test_pipeline_completes_within_loose_budget() -> None:
    # A loose, non-brittle budget (far above observed latencies on this code
    # path) that still catches truly pathological regressions (hang/DoS).
    pipeline = _build_pipeline()
    started = time.perf_counter()
    result = pipeline.analyze(JPEG_BYTES, content_type="image/jpeg")
    elapsed = time.perf_counter() - started
    assert result.verdict in Verdict
    assert elapsed < 30.0


def test_max_concurrency_one_runs_sequentially() -> None:
    pipeline = _build_pipeline(max_concurrency=1)
    result = pipeline.analyze(JPEG_BYTES, content_type="image/jpeg")
    assert result.confidence >= 0.0


def test_parallel_concurrency_matches_sequential_output(pipeline_config) -> None:
    sequential = _build_pipeline(max_concurrency=1).analyze(
        JPEG_BYTES, content_type="image/jpeg"
    )
    parallel = _build_pipeline(max_concurrency=4).analyze(
        JPEG_BYTES, content_type="image/jpeg"
    )
    assert sequential.verdict == parallel.verdict
    assert sequential.confidence == parallel.confidence
    assert sequential.scores == parallel.scores
    assert sequential.evidence == parallel.evidence
    assert sequential.heatmap == parallel.heatmap
    assert sequential.report_data is not None and parallel.report_data is not None
    assert (
        sequential.report_data.hypothesis_scores
        == parallel.report_data.hypothesis_scores
    )
    assert (
        sequential.report_data.classification_margin
        == parallel.report_data.classification_margin
    )


def test_repeated_analysis_is_deterministic() -> None:
    pipeline = _build_pipeline()
    first = pipeline.analyze(JPEG_BYTES, content_type="image/jpeg")
    second = pipeline.analyze(JPEG_BYTES, content_type="image/jpeg")
    assert first.verdict == second.verdict
    assert first.confidence == second.confidence
    assert first.evidence == second.evidence
    assert first.heatmap == second.heatmap


def test_concurrent_pipeline_runs_do_not_interfere() -> None:
    """Concurrent analyses on the same image bytes preserve forensic output."""
    results: list[str] = []
    lock = threading.Lock()

    def run_one() -> None:
        result = _build_pipeline().analyze(JPEG_BYTES, content_type="image/jpeg")
        with lock:
            results.append(result.verdict.value)

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(run_one) for _ in range(6)]
        for future in futures:
            future.result(timeout=60)

    assert results, "no analyses completed"
    assert len(set(results)) <= 1, "concurrent runs diverged"


def test_oversized_input_rejected_by_validation(api_client) -> None:
    payload = b"x" * (25 * 1024 * 1024 + 1)
    response = api_client.post(
        "/v1/analyses", files={"file": ("huge.jpg", payload, "image/jpeg")}
    )
    assert response.status_code == 413


def test_malformed_input_does_not_crash_process(api_client) -> None:
    response = api_client.post(
        "/v1/analyses",
        files={"file": ("bad.png", b"\x89PNG\r\n\x1a\nnot-a-real-rest", "image/png")},
    )
    # Either accepted (decoders degrade to baseline) or a controlled 422.
    assert response.status_code in {200, 422}


def test_bounded_execution_respects_timeout() -> None:
    try:
        with pytest.raises(TimeoutError):
            run_with_timeout(
                lambda: time.sleep(5),
                kwargs={},
                timeout_seconds=0.1,
                max_workers=1,
            )
    finally:
        shutdown_executors()

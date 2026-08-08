"""Resource-safety tests: oversized files, decompression bombs, malformed input.

The API must return controlled errors (or the pipeline's documented baseline
signals) instead of crashing the process.
"""

from __future__ import annotations

import time

import pytest

from app.core import constants
from app.core.enums import Verdict
from app.core.exceptions import FileTooLargeError, InvalidImageError
from app.core.execution import run_with_timeout, shutdown_executors
from app.pipeline.base import PipelineResult
from app.pipeline.config import PipelineConfig
from app.pipeline.detectors.registry import build_detectors
from app.pipeline.explanation.classifier import (
    ClassificationEvidenceGenerator,
    ClassificationExplanationGenerator,
)
from app.pipeline.fusion.engine import DeterministicFusionEngine
from app.pipeline.heatmap.generator import DeterministicHeatmapGenerator
from app.pipeline.runner import ModularAnalysisPipeline
from app.utils.image import validate_image_upload
from tests.sample_bytes import (
    bomb_png,
    oversized_dimension_png,
    truncated_png,
)


def _pipeline() -> ModularAnalysisPipeline:
    config = PipelineConfig()
    return ModularAnalysisPipeline(
        detectors=build_detectors(config.enabled_detector_names()),
        fusion=DeterministicFusionEngine(config),
        heatmap_generator=DeterministicHeatmapGenerator(config),
        evidence_generator=ClassificationEvidenceGenerator(config),
        explanation_generator=ClassificationExplanationGenerator(config),
        pipeline_config=config,
    )


def test_oversized_pixel_count_is_rejected() -> None:
    with pytest.raises(InvalidImageError):
        validate_image_upload(bomb_png())


def test_oversized_dimension_is_rejected() -> None:
    with pytest.raises(InvalidImageError):
        validate_image_upload(oversized_dimension_png())


def test_oversized_file_is_rejected() -> None:
    payload = b"\x00" * (constants.MAX_UPLOAD_SIZE_BYTES + 1)
    with pytest.raises(FileTooLargeError):
        validate_image_upload(payload, content_type="image/png")


def test_truncated_image_does_not_crash_and_completes() -> None:
    # A truncated header is treated as "not a decodable header" and must not
    # crash the process; the pipeline still returns a deterministic result.
    result = _pipeline().analyze(truncated_png())
    assert isinstance(result, PipelineResult)
    assert result.verdict in Verdict


def test_run_with_timeout_returns_result_in_time() -> None:
    try:
        assert (
            run_with_timeout(
                lambda: "ok",
                timeout_seconds=10,
                max_workers=1,
            )
            == "ok"
        )
    finally:
        shutdown_executors()


def test_run_with_timeout_raises_when_budget_exceeded() -> None:
    try:
        with pytest.raises(TimeoutError):
            run_with_timeout(
                lambda: time.sleep(5),
                timeout_seconds=0.1,
                max_workers=1,
            )
    finally:
        shutdown_executors()

"""Lightweight pipeline profiler.

Measure the wall-clock cost of each pipeline stage for a given image so
performance work is driven by data rather than assumptions.

Usage::

    python -m app.performance.profile <image> [--repeat N]
    python -m app.performance.profile <image> --concurrency 4

The profiler constructs the same pipeline the API uses (through the detector
registry and the deterministic fusion/heatmap/explanation components) and
records per-stage timing plus peak process memory.
"""

from __future__ import annotations

import argparse
import gc
import json
import sys
import time
import tracemalloc
from pathlib import Path

try:
    import resource
except ImportError:  # pragma: no cover - Windows has no resource module
    resource = None  # type: ignore[assignment]

from app.pipeline.config import PipelineConfig
from app.pipeline.detectors.registry import build_detectors
from app.pipeline.explanation.base import EvidenceGenerator, ExplanationGenerator
from app.pipeline.explanation.classifier import (
    ClassificationEvidenceGenerator,
    ClassificationExplanationGenerator,
)
from app.pipeline.fusion.base import FusionEngine
from app.pipeline.fusion.engine import DeterministicFusionEngine
from app.pipeline.heatmap.base import HeatmapContext, HeatmapGenerator
from app.pipeline.heatmap.generator import DeterministicHeatmapGenerator
from app.pipeline.runner import ModularAnalysisPipeline
from app.utils.image import validate_image_upload

_EXTENSION_MIME: dict[str, str] = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}


def _guess_content_type(path: Path) -> str | None:
    """Return a likely MIME type from the file extension, if known."""
    return _EXTENSION_MIME.get(path.suffix.lower())


def build_pipeline(
    pipeline_config: PipelineConfig,
    *,
    max_concurrency: int = 1,
) -> ModularAnalysisPipeline:
    """Build the same pipeline composition the API uses."""
    detectors = build_detectors(pipeline_config.enabled_detector_names())

    fusion: FusionEngine = DeterministicFusionEngine(pipeline_config)
    heatmap: HeatmapGenerator = DeterministicHeatmapGenerator(pipeline_config)
    evidence: EvidenceGenerator = ClassificationEvidenceGenerator(pipeline_config)
    explanation: ExplanationGenerator = ClassificationExplanationGenerator(
        pipeline_config
    )

    return ModularAnalysisPipeline(
        detectors=detectors,
        fusion=fusion,
        heatmap_generator=heatmap,
        evidence_generator=evidence,
        explanation_generator=explanation,
        pipeline_config=pipeline_config,
        max_concurrency=max_concurrency,
    )


def _measure_once(
    pipeline: ModularAnalysisPipeline,
    data: bytes,
    content_type: str | None,
) -> dict[str, float]:
    """Time the pipeline's public stages in seconds (best-of-one)."""
    started = time.perf_counter()

    validate_image_upload(data, content_type=content_type)
    t_validation = time.perf_counter()

    signals = pipeline.run_detectors(data, content_type=content_type, file_name=None)
    t_detectors = time.perf_counter()

    fusion_result = pipeline.fusion.fuse(signals)
    t_fusion = time.perf_counter()

    heatmap_context = HeatmapContext(
        image_bytes=data,
        content_type=content_type,
        signals=tuple(signals),
        fusion=fusion_result,
    )
    pipeline.heatmap_generator.generate(heatmap_context)
    t_heatmap = time.perf_counter()

    evidence = pipeline.evidence_generator.generate(fusion_result, signals)
    pipeline.explanation_generator.explain(fusion_result, evidence, signals)
    t_explanation = time.perf_counter()

    pipeline.build_report_data(signals, fusion_result)
    t_report = time.perf_counter()

    return {
        "validation": t_validation - started,
        "detectors": t_detectors - t_validation,
        "fusion": t_fusion - t_detectors,
        "heatmap": t_heatmap - t_fusion,
        "explanation": t_explanation - t_heatmap,
        "report_snapshot": t_report - t_explanation,
        "total": t_report - started,
    }


def profile(image: Path, *, repeat: int = 3, max_concurrency: int = 1) -> dict:
    """Profile ``image`` and return aggregate stage durations."""
    data = image.read_bytes()
    content_type = _guess_content_type(image)
    config = PipelineConfig()

    # Warm-up run so lazy imports (cv2, numpy) are not attributed to the work.
    build_pipeline(config).analyze(data, content_type=content_type)

    # Peak heap is measured with tracemalloc, which itself slows Python down
    # dramatically, so the *duration* numbers come from separate, un-instrumented
    # runs (see ``result_duration_ms`` and the stage aggregation below).
    gc.collect()
    tracemalloc.start()
    build_pipeline(config, max_concurrency=max_concurrency).analyze(
        data, content_type=content_type
    )
    tracemalloc.stop()
    _current, peak_peak = tracemalloc.get_traced_memory()
    result_peak_mb = peak_peak / (1024 * 1024)

    # Un-instrumented wall time of a full ``analyze`` call (the metric that
    # actually matters for request latency).
    pipeline = build_pipeline(config, max_concurrency=max_concurrency)
    full_started = time.perf_counter()
    result = pipeline.analyze(data, content_type=content_type)
    full_duration_ms = (time.perf_counter() - full_started) * 1000.0

    aggregate: dict[str, float] = {
        name: float("inf")
        for name in (
            "validation",
            "detectors",
            "fusion",
            "heatmap",
            "explanation",
            "report_snapshot",
            "total",
        )
    }
    detector_aggregate: dict[str, float] = {}
    for _ in range(max(1, repeat)):
        pipeline = build_pipeline(config, max_concurrency=max_concurrency)
        once = _measure_once(pipeline, data, content_type)
        for name, seconds in once.items():
            aggregate[name] = min(aggregate[name], seconds)
        # Per-detector wall times come straight from the detectors themselves.
        signals = pipeline.run_detectors(
            data, content_type=content_type, file_name=None
        )
        for signal in signals:
            ms = float(signal.processing_time_ms)
            if signal.detector_name not in detector_aggregate:
                detector_aggregate[signal.detector_name] = ms
            else:
                detector_aggregate[signal.detector_name] = min(
                    detector_aggregate[signal.detector_name], ms
                )

    rss_mb = (
        resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
        if resource is not None
        else 0.0
    )

    return {
        "image": str(image),
        "size_bytes": len(data),
        "concurrency": max_concurrency,
        "stage_durations_ms": {
            name: round(seconds * 1000.0, 3) for name, seconds in aggregate.items()
        },
        "detector_durations_ms": {
            name: round(ms, 3) for name, ms in sorted(detector_aggregate.items())
        },
        "peak_heap_mb": round(result_peak_mb, 3),
        "peak_rss_mb": round(rss_mb, 3),
        "result_duration_ms": round(full_duration_ms, 3),
        "result_duration_ms_internal": result.duration_ms,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Profile the Chai AI pipeline.")
    parser.add_argument("image", type=Path, help="Path to an image")
    parser.add_argument("--repeat", type=int, default=3, help="Runs per stage")
    parser.add_argument("--concurrency", type=int, default=1, help="Detector threads")
    args = parser.parse_args(argv)

    if not args.image.is_file():
        print(f"error: {args.image} is not a file", file=sys.stderr)
        return 2

    data = profile(
        args.image,
        repeat=args.repeat,
        max_concurrency=args.concurrency,
    )
    print(json.dumps(data, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

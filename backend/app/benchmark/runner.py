"""Automated benchmark runner executing manifest entries through Chai's production pipeline."""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.benchmark.manifest import compute_manifest_hash
from app.benchmark.metrics import compute_benchmark_run_result
from app.benchmark.models import (
    BenchmarkManifest,
    BenchmarkRunResult,
    DetectorScoreRecord,
    ImageBenchmarkResult,
)
from app.pipeline.config import PipelineConfig, get_pipeline_config
from app.pipeline.detectors.registry import build_detectors
from app.pipeline.explanation.classifier import (
    ClassificationEvidenceGenerator,
    ClassificationExplanationGenerator,
)
from app.pipeline.fusion.engine import DeterministicFusionEngine
from app.pipeline.heatmap.generator import DeterministicHeatmapGenerator
from app.pipeline.runner import ModularAnalysisPipeline

logger = logging.getLogger(__name__)


def build_benchmark_pipeline(
    config: PipelineConfig | None = None,
) -> ModularAnalysisPipeline:
    """Instantiate the exact production forensic pipeline for benchmark execution."""
    cfg = config or get_pipeline_config()
    detectors = build_detectors(cfg.enabled_detector_names())
    fusion = DeterministicFusionEngine(cfg)
    heatmap_gen = DeterministicHeatmapGenerator(cfg)
    evidence_gen = ClassificationEvidenceGenerator(cfg)
    explanation_gen = ClassificationExplanationGenerator(cfg)

    return ModularAnalysisPipeline(
        detectors=detectors,
        fusion=fusion,
        heatmap_generator=heatmap_gen,
        evidence_generator=evidence_gen,
        explanation_generator=explanation_gen,
        pipeline_config=cfg,
    )


def normalize_verdict_label(verdict_val: str) -> str:
    """Normalize Chai's verdict string to a canonical benchmark class name."""
    lower = verdict_val.lower().replace("-", "_")
    if lower in {"original", "real"}:
        return "original"
    if lower in {"aigenerated", "ai_generated", "synthetic"}:
        return "ai_generated"
    return lower


def run_benchmark(
    manifest: BenchmarkManifest,
    pipeline: ModularAnalysisPipeline | None = None,
    discovery_stats: dict[str, Any] | None = None,
    external_manager: Any = None,
    run_external: bool = False,
    external_cache: Any = None,
    external_delay: float = 0.0,
) -> BenchmarkRunResult:
    """Execute all images in ``manifest`` through Chai's production pipeline and evaluate performance."""
    run_start_time = time.perf_counter()
    now_iso = datetime.now(timezone.utc).isoformat()
    manifest_hash = compute_manifest_hash(manifest)

    if pipeline is None:
        pipeline = build_benchmark_pipeline()

    image_results: list[ImageBenchmarkResult] = []
    success_count = 0
    fail_count = 0

    for entry in manifest.entries:
        path = Path(entry.path)
        if not path.is_file():
            fail_count += 1
            image_results.append(
                ImageBenchmarkResult(
                    image_id=entry.id,
                    sha256=entry.sha256,
                    dataset=entry.dataset,
                    ground_truth=entry.ground_truth,
                    file_path=str(path),
                    predicted_class="error",
                    correct=False,
                    confidence=0.0,
                    risk_level="error",
                    analysis_duration_ms=0,
                    error=f"File not found: {path}",
                )
            )
            continue

        try:
            data = path.read_bytes()
            start_single = time.perf_counter()

            # Execute through the production ModularAnalysisPipeline
            result = pipeline.analyze(data)
            duration_ms = int((time.perf_counter() - start_single) * 1000)

            # Map detector scores and details
            det_scores: dict[str, float] = {}
            det_confidences: dict[str, float] = {}
            det_details: list[DetectorScoreRecord] = []

            for s in result.scores:
                det_scores[s.category.value] = s.value

            # Extract details from fusion contributions if available
            if (
                hasattr(result, "report_data")
                and result.report_data
                and result.report_data.contributions
            ):
                for c in result.report_data.contributions:
                    det_confidences[c.category.value] = c.detector_confidence
                    det_details.append(
                        DetectorScoreRecord(
                            detector_name=c.detector,
                            raw_score=c.normalized_score,
                            normalized_score=c.normalized_score,
                            confidence=c.detector_confidence,
                            evidence=[],
                            processing_time_ms=c.processing_time_ms or 0,
                        )
                    )

            # Fallback for confidences if not populated from contributions
            for cat_val in det_scores:
                if cat_val not in det_confidences:
                    det_confidences[cat_val] = 1.0

            predicted = normalize_verdict_label(result.verdict.value)
            gt_val = entry.ground_truth.value
            is_correct = predicted == gt_val

            # External provider evaluation (isolated from Chai pipeline)
            ext_data = None
            if run_external and external_manager is not None:
                try:
                    providers = getattr(external_manager, "providers", [])
                    main_provider = providers[0] if providers else None
                    provider_name = (
                        main_provider.provider_name if main_provider else "sightengine"
                    )
                    provider_ver = (
                        main_provider.provider_version if main_provider else "1.0"
                    )

                    cached_res = None
                    if external_cache is not None:
                        cached_res = external_cache.get(
                            entry.sha256, provider_name, provider_ver
                        )

                    if cached_res is not None:
                        ext_data = cached_res.model_dump()
                    else:
                        ext_results = external_manager.analyze_all(
                            image_bytes=data,
                            filename=path.name,
                            content_type=entry.metadata.get("mime_type", "image/jpeg"),
                        )
                        if ext_results:
                            ext_res = ext_results[0]
                            ext_data = ext_res.model_dump()
                            if external_cache is not None and ext_res.status in {
                                "success",
                                "disabled",
                                "unconfigured",
                            }:
                                external_cache.set(
                                    entry.sha256,
                                    provider_name,
                                    provider_ver,
                                    ext_res,
                                )

                        if external_delay > 0.0:
                            time.sleep(external_delay)
                except Exception as ext_exc:
                    logger.warning(
                        "External evaluation failed for %s: %s", path.name, ext_exc
                    )

            img_res = ImageBenchmarkResult(
                image_id=entry.id,
                sha256=entry.sha256,
                dataset=entry.dataset,
                ground_truth=entry.ground_truth,
                file_path=str(path),
                predicted_class=predicted,
                correct=is_correct,
                confidence=result.confidence,
                risk_level=result.risk_level.value,
                analysis_duration_ms=duration_ms,
                detector_scores=det_scores,
                detector_confidences=det_confidences,
                detector_details=det_details,
                evidence=list(result.evidence),
                heatmap_region_count=len(result.heatmap.regions)
                if result.heatmap
                else 0,
                overall_manipulation_score=result.heatmap.overall_manipulation
                if result.heatmap
                else 0.0,
                external_result=ext_data,
            )
            image_results.append(img_res)
            success_count += 1

        except Exception as exc:
            logger.exception("Analysis failed for image %s: %s", path.name, exc)
            fail_count += 1
            image_results.append(
                ImageBenchmarkResult(
                    image_id=entry.id,
                    sha256=entry.sha256,
                    dataset=entry.dataset,
                    ground_truth=entry.ground_truth,
                    file_path=str(path),
                    predicted_class="error",
                    correct=False,
                    confidence=0.0,
                    risk_level="error",
                    analysis_duration_ms=0,
                    error=str(exc),
                )
            )

    if external_cache is not None:
        try:
            external_cache.save()
        except Exception as cache_exc:
            logger.warning("Failed to persist external benchmark cache: %s", cache_exc)

    total_duration = time.perf_counter() - run_start_time

    run_id = f"run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

    return compute_benchmark_run_result(
        run_id=run_id,
        timestamp=now_iso,
        manifest_hash=manifest_hash,
        duration_seconds=total_duration,
        successful_count=success_count,
        failed_count=fail_count,
        results=image_results,
        discovery_stats=discovery_stats,
    )

"""Automated benchmark runner executing manifest entries through Chai's pipeline."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path

from app.benchmark.manifest import compute_manifest_hash
from app.benchmark.metrics import compute_benchmark_run_result
from app.benchmark.models import (
    BenchmarkManifest,
    BenchmarkRunResult,
    DetectorScoreRecord,
    GroundTruthLabel,
    ImageBenchmarkResult,
)

from app.clients.external_detection.manager import ExternalDetectionManager
from app.clients.storage import StorageClient
from app.core.config import Settings
from app.pipeline.runner import ModularAnalysisPipeline
from app.repos.analysis_repo import AnalysisRepository
from app.services.analysis_service import AnalysisService


def run_benchmark(
    manifest: BenchmarkManifest,
    analysis_service: AnalysisService,
    external_manager: ExternalDetectionManager | None = None,
    run_external: bool = False,
    output_dir: Path | None = None,
) -> BenchmarkRunResult:
    """Execute all images in ``manifest`` through Chai's analysis pipeline and evaluate performance."""
    run_start_time = time.perf_counter()
    now_iso = datetime.now(timezone.utc).isoformat()
    manifest_hash = compute_manifest_hash(manifest)

    image_results: list[ImageBenchmarkResult] = []
    success_count = 0
    fail_count = 0

    for entry in manifest.entries:
        path = Path(entry.path)
        if not path.is_file():
            fail_count += 1
            continue

        try:
            data = path.read_bytes()
            start_single = time.perf_counter()

            # Execute through Chai's analysis service
            result_dto = analysis_service.analyze_upload(
                data=data,
                content_type=entry.metadata.get("mime_type", "image/jpeg"),
                file_name=path.name,
            )
            duration_ms = int((time.perf_counter() - start_single) * 1000)

            # Map detector score details
            det_scores: dict[str, float] = {}
            det_details: list[DetectorScoreRecord] = []
            for s in result_dto.scores:
                det_scores[s.category.value] = s.value
                det_details.append(
                    DetectorScoreRecord(
                        detector_name=s.category.value,
                        raw_score=s.value,
                        normalized_score=s.value,
                        confidence=s.value,
                        evidence=[],
                        processing_time_ms=0,
                    )
                )

            # Optional external provider evaluation
            ext_data = None
            if run_external and external_manager is not None:
                ext_results = external_manager.analyze_all(
                    image_bytes=data,
                    filename=path.name,
                    content_type=entry.metadata.get("mime_type", "image/jpeg"),
                )
                if ext_results:
                    ext_data = ext_results[0].model_dump()

            # Calculate match status
            verdict = result_dto.verdict.value
            gt = entry.ground_truth

            is_3_match = None
            if gt.is_three_class_compatible:
                is_3_match = (verdict == gt.value)

            is_bin_match = None
            if gt in {GroundTruthLabel.ORIGINAL, GroundTruthLabel.AI_GENERATED, GroundTruthLabel.AI_EDITED, GroundTruthLabel.REAL_MANIPULATED}:
                gt_ai = gt != GroundTruthLabel.ORIGINAL
                chai_ai = verdict != "original"
                is_bin_match = (gt_ai == chai_ai)

            img_res = ImageBenchmarkResult(
                image_id=entry.id,
                sha256=entry.sha256,
                dataset=entry.dataset,
                ground_truth=gt,
                file_path=str(path),
                chai_verdict=verdict,
                chai_confidence=result_dto.confidence,
                chai_risk_level=result_dto.risk_level.value,
                analysis_duration_ms=duration_ms,
                detector_scores=det_scores,
                detector_details=det_details,
                evidence=result_dto.evidence,
                heatmap_region_count=len(result_dto.heatmap.regions) if result_dto.heatmap else 0,
                overall_manipulation_score=result_dto.heatmap.overall_manipulation if result_dto.heatmap else 0.0,
                external_result=ext_data,
                is_binary_match=is_bin_match,
                is_three_class_match=is_3_match,
            )
            image_results.append(img_res)
            success_count += 1

        except Exception:
            fail_count += 1
            continue

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
    )

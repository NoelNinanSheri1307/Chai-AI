"""Command-line interface for running automated benchmarks and ingesting datasets."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from app.benchmark.downloader import ingest_local_directory
from app.benchmark.manifest import load_manifest, sample_manifest
from app.benchmark.models import GroundTruthLabel
from app.benchmark.reports import generate_markdown_report, save_markdown_report
from app.benchmark.runner import run_benchmark
from app.clients.external_detection.manager import ExternalDetectionManager
from app.clients.storage import create_storage_client
from app.core.config import get_settings
from app.core.db import get_database
from app.pipeline.config import get_pipeline_config
from app.pipeline.explanation.classifier import (
    ClassificationEvidenceGenerator,
    ClassificationExplanationGenerator,
)
from app.pipeline.fusion.engine import DeterministicFusionEngine
from app.pipeline.heatmap.generator import DeterministicHeatmapGenerator
from app.pipeline.runner import ModularAnalysisPipeline
from app.pipeline.detectors.registry import build_detectors
from app.repos.analysis_repo import AnalysisRepository
from app.services.analysis_service import AnalysisService


def run_cli() -> None:
    """CLI entry point for running a benchmark evaluation: ``python -m app.benchmark.run``."""
    parser = argparse.ArgumentParser(description="Chai AI Automated Benchmark Runner")
    parser.add_argument("--manifest", type=str, default="benchmark/manifest.json", help="Path to manifest JSON")
    parser.add_argument("--output-dir", type=str, default="benchmark", help="Output directory for results/reports")
    parser.add_argument("--limit", type=int, default=None, help="Maximum number of images to evaluate")
    parser.add_argument("--seed", type=int, default=42, help="Deterministic sampling random seed")
    parser.add_argument("--dataset", type=str, default=None, help="Filter manifest by dataset name")
    parser.add_argument("--external", action="store_true", help="Enable external provider benchmarking")

    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    if not manifest_path.is_file():
        print(f"Error: Manifest file not found at {manifest_path}", file=sys.stderr)
        sys.exit(1)

    # Load and sample manifest
    full_manifest = load_manifest(manifest_path)
    manifest = sample_manifest(
        full_manifest,
        limit=args.limit,
        seed=args.seed,
        dataset_filter=args.dataset,
    )

    settings = get_settings()
    pipeline_config = get_pipeline_config()

    # Wire standalone pipeline and services for benchmark execution
    detectors = build_detectors(pipeline_config.enabled_detector_names())
    fusion = DeterministicFusionEngine(pipeline_config)
    heatmap_gen = DeterministicHeatmapGenerator(pipeline_config)
    ev_gen = ClassificationEvidenceGenerator(pipeline_config)
    exp_gen = ClassificationExplanationGenerator(pipeline_config)

    pipeline = ModularAnalysisPipeline(
        detectors=detectors,
        fusion=fusion,
        heatmap_generator=heatmap_gen,
        evidence_generator=ev_gen,
        explanation_generator=exp_gen,
        pipeline_config=pipeline_config,
    )

    storage = create_storage_client(settings)

    with get_database(settings).session_scope() as session:
        analysis_repo = AnalysisRepository(session)
        analysis_service = AnalysisService(
            analysis_repo=analysis_repo,
            storage=storage,
            pipeline=pipeline,
            settings=settings,
        )

        ext_mgr = ExternalDetectionManager(settings=settings) if args.external else None

        result = run_benchmark(
            manifest=manifest,
            analysis_service=analysis_service,
            external_manager=ext_mgr,
            run_external=args.external,
        )

        out_dir = Path(args.output_dir)
        results_dir = out_dir / "results"
        reports_dir = out_dir / "reports"
        results_dir.mkdir(parents=True, exist_ok=True)
        reports_dir.mkdir(parents=True, exist_ok=True)

        res_path = results_dir / f"{result.run_id}.json"
        res_path.write_text(result.model_dump_json(indent=2), encoding="utf-8")

        report_md = generate_markdown_report(result)
        save_markdown_report(report_md, reports_dir / "latest.md")
        save_markdown_report(report_md, reports_dir / f"{result.run_id}.md")

        print(f"Benchmark completed successfully! Evaluated {result.successful_analyses} images.")
        print(f"Overall Accuracy: {result.overall_accuracy * 100:.2f}% | Macro F1: {result.macro_f1:.4f}")
        print(f"Results saved to: {res_path}")
        print(f"Report saved to:  {reports_dir / 'latest.md'}")


def ingest_cli() -> None:
    """CLI entry point for ingesting a directory of images: ``python -m app.benchmark.ingest``."""
    parser = argparse.ArgumentParser(description="Chai AI Dataset Ingestion Tool")
    parser.add_argument("--source-dir", type=str, required=True, help="Directory containing images to ingest")
    parser.add_argument("--ground-truth", type=str, required=True, choices=[e.value for e in GroundTruthLabel], help="Ground-truth label")
    parser.add_argument("--dataset-name", type=str, required=True, help="Unique dataset identifier name")
    parser.add_argument("--output", type=str, default="benchmark/manifest.json", help="Manifest output JSON file path")

    args = parser.parse_args()

    source = Path(args.source_dir)
    gt = GroundTruthLabel(args.ground_truth)
    out_path = Path(args.output)

    manifest = ingest_local_directory(
        source_dir=source,
        ground_truth=gt,
        dataset_name=args.dataset_name,
        output_manifest_path=out_path,
    )

    print(f"Successfully ingested {len(manifest.entries)} images into {out_path}")


if __name__ == "__main__":
    run_cli()

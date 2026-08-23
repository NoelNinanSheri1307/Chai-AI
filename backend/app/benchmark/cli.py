"""Command-line interface for running automated benchmarks (Real vs AI Generated)."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from app.benchmark.external_cache import ExternalBenchmarkCache
from app.benchmark.external_metrics import compute_complete_external_benchmark
from app.benchmark.external_reports import (
    generate_external_markdown_report,
    save_external_reports,
)
from app.benchmark.manifest import (
    discover_benchmark_images,
    load_manifest,
    sample_manifest,
    save_manifest,
)
from app.benchmark.reports import generate_markdown_report, save_markdown_report
from app.benchmark.runner import build_benchmark_pipeline, run_benchmark
from app.clients.external_detection.manager import ExternalDetectionManager
from app.core.config import Settings
from app.pipeline.config import PipelineConfig


def find_default_dataset_dir() -> Path:
    """Find the default benchmark dataset folder across common repository relative paths."""
    candidates = [
        Path("../chai_benchmark"),
        Path("../chai-benchmark"),
        Path("chai_benchmark"),
        Path("chai-benchmark"),
        Path("../../chai_benchmark"),
        Path("../../chai-benchmark"),
        Path("c:/Users/VICTUS/Chai-AI/chai_benchmark"),
        Path("c:/Users/VICTUS/Chai-AI/chai-benchmark"),
    ]
    for c in candidates:
        if c.is_dir():
            return c.resolve()
    return Path("../chai_benchmark").resolve()


def run_cli() -> None:
    """CLI entry point for running a benchmark evaluation: ``python -m app.benchmark.cli``."""
    parser = argparse.ArgumentParser(
        description="Chai AI Real vs AI-Generated Benchmark Harness"
    )
    parser.add_argument(
        "--dataset-dir",
        type=str,
        default=None,
        help="Path to benchmark dataset root (containing real/ and ai_generated/)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for results and reports (defaults to <dataset-dir>/results)",
    )
    parser.add_argument(
        "--manifest",
        type=str,
        default=None,
        help="Optional path to pre-built manifest JSON file",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of images to evaluate (deterministic sampling)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Deterministic sampling random seed (default: 42)",
    )
    parser.add_argument(
        "--external",
        action="store_true",
        help="Enable independent external provider benchmarking (Sightengine)",
    )
    parser.add_argument(
        "--external-delay",
        type=float,
        default=0.2,
        help="Inter-request delay in seconds for external provider calls (default: 0.2s)",
    )
    parser.add_argument(
        "--external-cache",
        type=str,
        default="reports/external_cache.json",
        help="Path to JSON cache file for external provider responses",
    )
    parser.add_argument(
        "--profile",
        type=str,
        default="m14",
        choices=["m14", "exp_4", "baseline", "exp4"],
        help="Calibration profile: 'm14' (baseline) or 'exp_4' (rebalanced)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable detailed logging output",
    )

    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level, format="%(asctime)s [%(levelname)s] %(message)s"
    )

    # Locate dataset directory
    if args.dataset_dir:
        dataset_path = Path(args.dataset_dir).resolve()
    else:
        dataset_path = find_default_dataset_dir()

    if not args.manifest and not dataset_path.is_dir():
        print(
            f"Error: Benchmark dataset directory not found at {dataset_path}.\n"
            "Please specify --dataset-dir <path>.",
            file=sys.stderr,
        )
        sys.exit(1)

    # 1. Discover or load manifest
    discovery_stats = None
    if args.manifest:
        manifest_p = Path(args.manifest)
        if not manifest_p.is_file():
            print(f"Error: Manifest file not found at {manifest_p}", file=sys.stderr)
            sys.exit(1)
        full_manifest = load_manifest(manifest_p)
        print(
            f"Loaded manifest from {manifest_p} with {len(full_manifest.entries)} entries."
        )
    else:
        print(f"Discovering benchmark images in: {dataset_path}...")
        full_manifest, discovery_stats = discover_benchmark_images(dataset_path)
        print(
            f"Discovered {discovery_stats['real_count']} real images, "
            f"{discovery_stats['ai_generated_count']} AI-generated images "
            f"({discovery_stats['duplicate_count']} duplicates skipped, "
            f"{discovery_stats['skipped_count']} invalid/unsupported skipped)."
        )

    if not full_manifest.entries:
        print("Error: No valid images found in dataset directory.", file=sys.stderr)
        sys.exit(1)

    # 2. Sample manifest if limit is requested
    manifest = sample_manifest(full_manifest, limit=args.limit, seed=args.seed)
    if args.limit:
        print(
            f"Sampled {len(manifest.entries)} images using seed {args.seed} (limit={args.limit})."
        )
    else:
        print(f"Evaluating complete dataset of {len(manifest.entries)} images...")

    # 3. Build production pipeline with requested calibration profile
    pipeline_cfg = PipelineConfig.for_profile(args.profile)
    pipeline = build_benchmark_pipeline(config=pipeline_cfg)
    print(f"Active Pipeline Profile: {pipeline_cfg.calibration_profile.upper()} ({pipeline_cfg.detector_reliability})")


    # 4. Optional external provider initialization
    external_manager = None
    external_cache = None
    if args.external:
        settings = Settings()
        external_manager = ExternalDetectionManager(settings=settings)
        external_cache = ExternalBenchmarkCache(args.external_cache)
        print(
            f"External benchmarking enabled (Sightengine). Using cache: {external_cache.cache_path}"
        )

    # 5. Execute benchmark
    print("Running production forensic pipeline...")
    result = run_benchmark(
        manifest=manifest,
        pipeline=pipeline,
        discovery_stats=discovery_stats,
        external_manager=external_manager,
        run_external=args.external,
        external_cache=external_cache,
        external_delay=args.external_delay,
    )

    # 6. Output results and reports
    if args.output_dir:
        out_dir = Path(args.output_dir).resolve()
    else:
        out_dir = dataset_path / "results"

    results_runs_dir = out_dir / "runs"
    out_dir.mkdir(parents=True, exist_ok=True)
    results_runs_dir.mkdir(parents=True, exist_ok=True)

    # Save manifest alongside results
    save_manifest(manifest, out_dir / "manifest.json")

    # JSON results
    latest_json = out_dir / "latest.json"
    run_json = results_runs_dir / f"{result.run_id}.json"
    json_content = result.model_dump_json(indent=2)
    latest_json.write_text(json_content, encoding="utf-8")
    run_json.write_text(json_content, encoding="utf-8")

    # Markdown reports
    report_md = generate_markdown_report(result)
    latest_md = out_dir / "latest.md"
    run_md = results_runs_dir / f"{result.run_id}.md"
    save_markdown_report(report_md, latest_md)
    save_markdown_report(report_md, run_md)

    # 7. External comparative report generation if requested
    ext_report_md_path = None
    ext_result_obj = None
    if args.external:
        ext_result_obj = compute_complete_external_benchmark(result)
        ext_md_path, ext_json_path = save_external_reports(ext_result_obj, out_dir)
        ext_run_md = results_runs_dir / f"{result.run_id}_external.md"
        ext_run_json = results_runs_dir / f"{result.run_id}_external.json"
        ext_run_md.write_text(
            generate_external_markdown_report(ext_result_obj), encoding="utf-8"
        )
        ext_run_json.write_text(
            ext_result_obj.model_dump_json(indent=2), encoding="utf-8"
        )
        ext_report_md_path = ext_md_path

    # 8. Terminal Summary
    print("\n" + "=" * 60)
    print(f"CHAI AI BENCHMARK SUMMARY ({result.run_id})")
    print("=" * 60)
    print(
        f"Evaluated Images:   {result.total_images} (Real: {result.real_count}, AI Generated: {result.ai_generated_count})"
    )
    print(f"Chai Overall Acc:   {result.accuracy * 100:.2f}%")
    print(f"Chai AI Precision:  {result.precision * 100:.2f}%")
    print(f"Chai AI Recall:     {result.recall * 100:.2f}%")
    print(f"Chai AI F1 Score:   {result.f1:.4f}")
    print(f"Chai Macro F1:      {result.macro_f1:.4f}")
    print(
        f"Chai Confusion Mtx: TN={result.tn}, FP={result.fp}, FN={result.fn}, TP={result.tp}"
    )

    if ext_result_obj is not None:
        em = ext_result_obj.external_metrics
        ag = ext_result_obj.agreement
        print("-" * 60)
        print("SIGHTENGINE EXTERNAL BENCHMARK COMPARISON")
        print("-" * 60)
        print(
            f"Sightengine Status: {em.successful_analyses} success, {em.failed_analyses} fail, {em.unconfigured_or_disabled} unconfigured"
        )
        print(f"Sightengine Acc:    {em.accuracy * 100:.2f}%")
        print(f"Sightengine AI Rec: {em.recall * 100:.2f}%")
        print(f"Sightengine AI Prec:{em.precision * 100:.2f}%")
        print(f"Sightengine AI F1:  {em.f1:.4f}")
        print(
            f"Sightengine Mtx:    TN={em.tn}, FP={em.fp}, FN={em.fn}, TP={em.tp}"
        )
        print(
            f"Overall Agreement:  {ag.agree_count}/{ag.total_compared} ({ag.agreement_rate * 100:.2f}%)"
        )
        print(
            f"  - Real Partition: {ag.real_subset_agree_count}/{ag.real_subset_count} ({ag.real_subset_agree_rate * 100:.2f}%)"
        )
        print(
            f"  - AI Partition:   {ag.ai_subset_agree_count}/{ag.ai_subset_count} ({ag.ai_subset_agree_rate * 100:.2f}%)"
        )

    print("=" * 60)
    print(f"Full Chai Report:       {latest_md}")
    print(f"Chai JSON Result:       {latest_json}")
    if ext_report_md_path:
        print(f"Comparative Ext Report: {ext_report_md_path}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    run_cli()

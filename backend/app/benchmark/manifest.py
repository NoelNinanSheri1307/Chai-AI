"""Manifest loading, saving, discovery, deduplication, and sampling for benchmark datasets."""

from __future__ import annotations

import json
import logging
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.benchmark.models import (
    BenchmarkManifest,
    GroundTruthLabel,
    ManifestEntry,
)
from app.benchmark.validation import (
    ImageValidationError,
    calculate_sha256,
    inspect_and_validate_image,
)

logger = logging.getLogger(__name__)

SUPPORTED_IMAGE_EXTENSIONS = frozenset({".jpg", ".jpeg", ".png", ".webp", ".avif"})


def compute_manifest_hash(manifest: BenchmarkManifest) -> str:
    """Compute a deterministic SHA-256 fingerprint for a manifest."""
    serialized = json.dumps(
        [entry.model_dump() for entry in sorted(manifest.entries, key=lambda x: x.id)],
        sort_keys=True,
    )
    return calculate_sha256(serialized.encode("utf-8"))


def load_manifest(path: Path) -> BenchmarkManifest:
    """Load a benchmark manifest from a JSON file."""
    if not path.is_file():
        raise FileNotFoundError(f"Manifest file not found: {path}")
    raw = json.loads(path.read_text(encoding="utf-8"))
    return BenchmarkManifest.model_validate(raw)


def save_manifest(manifest: BenchmarkManifest, path: Path) -> None:
    """Save a benchmark manifest to a JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(manifest.model_dump(), indent=2)
    path.write_text(content, encoding="utf-8")


def create_manifest(
    entries: list[ManifestEntry],
    description: str = "Chai AI Benchmark Dataset Manifest (Real vs AI Generated)",
    metadata: dict[str, Any] | None = None,
) -> BenchmarkManifest:
    """Create a new BenchmarkManifest object."""
    now = datetime.now(timezone.utc).isoformat()
    return BenchmarkManifest(
        version="2.0",
        created_at=now,
        description=description,
        entries=entries,
        metadata=metadata or {},
    )


def sample_manifest(
    manifest: BenchmarkManifest,
    limit: int | None = None,
    seed: int = 42,
    label_filter: GroundTruthLabel | None = None,
) -> BenchmarkManifest:
    """Return a deterministically sampled/filtered subset of a manifest."""
    filtered = list(manifest.entries)

    if label_filter:
        filtered = [e for e in filtered if e.ground_truth == label_filter]

    if limit is not None and limit > 0 and len(filtered) > limit:
        rng = random.Random(seed)
        # Stable sort before sampling
        filtered = sorted(filtered, key=lambda e: (e.ground_truth.value, e.id))
        sampled = rng.sample(filtered, limit)
        filtered = sorted(sampled, key=lambda e: (e.ground_truth.value, e.id))

    return BenchmarkManifest(
        version=manifest.version,
        created_at=manifest.created_at,
        description=f"{manifest.description} (sampled)",
        entries=filtered,
        metadata={**manifest.metadata, "sample_seed": seed, "sample_limit": limit},
    )


def discover_benchmark_images(
    dataset_dir: Path,
) -> tuple[BenchmarkManifest, dict[str, Any]]:
    """Discover, validate, and deduplicate benchmark images in ``dataset_dir``.

    Looks for subdirectories matching Real / AI_Generated (case-insensitive).
    Performs SHA-256 deduplication and cross-category collision checks.
    """
    if not dataset_dir.is_dir():
        raise FileNotFoundError(f"Benchmark dataset directory not found: {dataset_dir}")

    # Discover candidate category folders
    real_dirs: list[Path] = []
    ai_dirs: list[Path] = []

    for child in dataset_dir.iterdir():
        if child.is_dir():
            name_lower = child.name.lower().replace("-", "_")
            if name_lower in {"real", "original"}:
                real_dirs.append(child)
            elif name_lower in {"ai_generated", "aigenerated", "synthetic", "ai"}:
                ai_dirs.append(child)

    entries_by_sha: dict[str, tuple[GroundTruthLabel, ManifestEntry, Path]] = {}
    cross_category_duplicates: list[str] = []
    duplicate_count = 0
    skipped_count = 0

    def _collect_files(dir_path: Path) -> list[Path]:
        files = []
        for p in dir_path.rglob("*"):
            if p.is_file() and p.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS:
                files.append(p)
        return sorted(files)

    # Local counter helper
    counters = {"dup": 0, "skip": 0}

    def nonlocal_inc(kind: str) -> None:
        counters[kind] += 1

    all_real_files = [f for d in real_dirs for f in _collect_files(d)]
    all_ai_files = [f for d in ai_dirs for f in _collect_files(d)]

    for file_path in all_real_files:
        _process_candidate(
            file_path=file_path,
            ground_truth=GroundTruthLabel.ORIGINAL,
            dataset_name="coco_val2017"
            if "val2017" in str(file_path).lower()
            else "real",
            dataset_dir=dataset_dir,
            entries_by_sha=entries_by_sha,
            cross_category_duplicates=cross_category_duplicates,
            on_duplicate=lambda: nonlocal_inc("dup"),
            on_skip=lambda: nonlocal_inc("skip"),
        )

    for file_path in all_ai_files:
        _process_candidate(
            file_path=file_path,
            ground_truth=GroundTruthLabel.AI_GENERATED,
            dataset_name="ai_generated",
            dataset_dir=dataset_dir,
            entries_by_sha=entries_by_sha,
            cross_category_duplicates=cross_category_duplicates,
            on_duplicate=lambda: nonlocal_inc("dup"),
            on_skip=lambda: nonlocal_inc("skip"),
        )

    duplicate_count = counters["dup"]
    skipped_count = counters["skip"]

    # Exclude any cross-category duplicates from the active manifest
    valid_entries = [
        entry
        for sha, (gt, entry, _) in sorted(
            entries_by_sha.items(), key=lambda item: item[1][1].id
        )
        if sha not in cross_category_duplicates
    ]

    real_count = sum(
        1 for e in valid_entries if e.ground_truth == GroundTruthLabel.ORIGINAL
    )
    ai_count = sum(
        1 for e in valid_entries if e.ground_truth == GroundTruthLabel.AI_GENERATED
    )

    stats = {
        "real_count": real_count,
        "ai_generated_count": ai_count,
        "skipped_count": skipped_count,
        "duplicate_count": duplicate_count,
        "cross_category_duplicates": cross_category_duplicates,
    }

    manifest = create_manifest(
        entries=valid_entries,
        metadata={
            "dataset_dir": str(dataset_dir),
            "real_count": real_count,
            "ai_generated_count": ai_count,
            "skipped_count": skipped_count,
            "duplicate_count": duplicate_count,
        },
    )

    return manifest, stats


def _process_candidate(
    file_path: Path,
    ground_truth: GroundTruthLabel,
    dataset_name: str,
    dataset_dir: Path,
    entries_by_sha: dict[str, tuple[GroundTruthLabel, ManifestEntry, Path]],
    cross_category_duplicates: list[str],
    on_duplicate: Any,
    on_skip: Any,
) -> None:
    """Validate and register a candidate image file into ``entries_by_sha``."""
    try:
        data = file_path.read_bytes()
        meta = inspect_and_validate_image(data)
    except (ImageValidationError, OSError) as exc:
        logger.warning("Skipping invalid image %s: %s", file_path.name, exc)
        on_skip()
        return

    sha = calculate_sha256(data)

    if sha in entries_by_sha:
        existing_gt, _, existing_path = entries_by_sha[sha]
        if existing_gt != ground_truth:
            logger.error(
                "Cross-category duplicate detected: %s (in %s and %s)",
                sha[:12],
                existing_path,
                file_path,
            )
            if sha not in cross_category_duplicates:
                cross_category_duplicates.append(sha)
        else:
            on_duplicate()
        return

    try:
        rel_path = str(file_path.relative_to(dataset_dir)).replace("\\", "/")
    except ValueError:
        rel_path = str(file_path).replace("\\", "/")

    entry_id = f"{ground_truth.value}_{sha[:12]}"

    entry = ManifestEntry(
        id=entry_id,
        sha256=sha,
        path=str(file_path),
        dataset=dataset_name,
        ground_truth=ground_truth,
        width=int(meta["width"]),
        height=int(meta["height"]),
        format=str(meta["format"]),
        file_size_bytes=int(meta["file_size_bytes"]),
        split="benchmark",
        metadata={
            "mime_type": str(meta["mime_type"]),
            "relative_path": rel_path,
            "filename": file_path.name,
        },
    )

    entries_by_sha[sha] = (ground_truth, entry, file_path)

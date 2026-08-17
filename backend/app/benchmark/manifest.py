"""Manifest loading, saving, sampling, and hash calculation for benchmark datasets."""

from __future__ import annotations

import json
import random
from datetime import datetime, timezone
from pathlib import Path

from app.benchmark.models import (
    BenchmarkManifest,
    GroundTruthLabel,
    ManifestEntry,
)
from app.benchmark.validation import calculate_sha256


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
    description: str = "Chai AI Real-World Benchmark Dataset Manifest",
    metadata: dict | None = None,
) -> BenchmarkManifest:
    """Create a new BenchmarkManifest object."""
    now = datetime.now(timezone.utc).isoformat()
    return BenchmarkManifest(
        version="1.0",
        created_at=now,
        description=description,
        entries=entries,
        metadata=metadata or {},
    )


def sample_manifest(
    manifest: BenchmarkManifest,
    limit: int | None = None,
    seed: int = 42,
    dataset_filter: str | None = None,
    label_filter: GroundTruthLabel | None = None,
) -> BenchmarkManifest:
    """Return a deterministically sampled/filtered subset of a manifest."""
    filtered = list(manifest.entries)

    if dataset_filter:
        filtered = [e for e in filtered if e.dataset == dataset_filter]

    if label_filter:
        filtered = [e for e in filtered if e.ground_truth == label_filter]

    if limit is not None and limit > 0 and len(filtered) > limit:
        rng = random.Random(seed)
        filtered = sorted(filtered, key=lambda e: e.id)
        filtered = rng.sample(filtered, limit)

    return BenchmarkManifest(
        version=manifest.version,
        created_at=manifest.created_at,
        description=f"{manifest.description} (sampled)",
        entries=filtered,
        metadata={**manifest.metadata, "sample_seed": seed, "sample_limit": limit},
    )

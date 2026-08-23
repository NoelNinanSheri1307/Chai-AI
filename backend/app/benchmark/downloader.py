"""Automated dataset metadata catalog and ingestion downloader for the benchmark harness.

Defines metadata for trustworthy, publicly available benchmark dataset sources
and provides safe ingestion functions. No binary images are committed to Git.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.benchmark.manifest import create_manifest, save_manifest
from app.benchmark.models import (
    BenchmarkManifest,
    GroundTruthLabel,
    ManifestEntry,
)
from app.benchmark.validation import calculate_sha256, inspect_and_validate_image

DATASET_SOURCES: dict[str, dict[str, Any]] = {
    "coco_val2017": {
        "name": "MS-COCO 2017 Validation Set (Authentic Photographic Subset)",
        "source_url": "http://images.cocodataset.org/zips/val2017.zip",
        "license": "CC-BY 4.0",
        "description": "Diverse real-world photographic images captured with authentic cameras.",
        "ground_truth": GroundTruthLabel.ORIGINAL,
    },
    "ai_generated": {
        "name": "AI-Generated Benchmark Dataset",
        "source_url": None,
        "license": "CC0 / Mixed",
        "description": "Unmodified synthetic images produced by modern generative AI models.",
        "ground_truth": GroundTruthLabel.AI_GENERATED,
    },
}


def ingest_local_directory(
    source_dir: Path,
    ground_truth: GroundTruthLabel,
    dataset_name: str,
    output_manifest_path: Path,
    license_name: str = "CC-BY 4.0",
    source_url: str | None = None,
) -> BenchmarkManifest:
    """Ingest a directory of local images, validating format and SHA-256 deduplicating."""
    if not source_dir.is_dir():
        raise FileNotFoundError(f"Source directory not found: {source_dir}")

    entries: list[ManifestEntry] = []
    seen_hashes: set[str] = set()

    for file_path in sorted(source_dir.glob("**/*")):
        if not file_path.is_file() or file_path.name.startswith("."):
            continue

        try:
            data = file_path.read_bytes()
            meta = inspect_and_validate_image(data)
            sha256 = calculate_sha256(data)

            if sha256 in seen_hashes:
                continue  # Deduplicate duplicate images
            seen_hashes.add(sha256)

            entry_id = f"{dataset_name}_{file_path.stem[:16]}_{sha256[:8]}"
            entry = ManifestEntry(
                id=entry_id,
                sha256=sha256,
                path=str(file_path.resolve()),
                dataset=dataset_name,
                source_url=source_url,
                ground_truth=ground_truth,
                license=license_name,
                width=int(meta["width"]),
                height=int(meta["height"]),
                format=str(meta["format"]),
                file_size_bytes=int(meta["file_size_bytes"]),
                split="benchmark",
                metadata={"mime_type": str(meta["mime_type"])},
            )
            entries.append(entry)
        except Exception:
            continue  # Skip non-image or corrupt files gracefully

    manifest = create_manifest(
        entries=entries,
        description=f"Ingested manifest for {dataset_name} ({ground_truth.value})",
        metadata={"source_dir": str(source_dir), "entry_count": len(entries)},
    )
    save_manifest(manifest, output_manifest_path)
    return manifest

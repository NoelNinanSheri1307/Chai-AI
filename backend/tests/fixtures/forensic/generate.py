"""Deterministic forensic regression fixtures.

Generates a small set of small images (fixed content, fixed seeds) and records
the current forensic pipeline output for each. The image bytes are stable
across runs, so fingerprints can be compared before/after changes to prove the
forensic outputs are unchanged. Pipeline timings are excluded because they are
environment-dependent.
"""

from __future__ import annotations

import io
import json
from pathlib import Path

import numpy as np
from PIL import Image

from app.performance.fingerprints import pipeline_fingerprint
from app.performance.profile import build_pipeline
from app.pipeline.config import PipelineConfig

_FIXTURES_DIR = Path(__file__).parent
_IMAGES_DIR = _FIXTURES_DIR / "images"
_SNAPSHOT = _FIXTURES_DIR / "forensic_snapshot.json"


def _generate_images() -> list[str]:
    """Create the deterministic fixture images; return their names."""
    _IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    names: list[str] = []

    rng = np.random.default_rng(seed=42)
    noise = rng.normal(128, 24, (128, 256)).clip(0, 255).astype(np.uint8)
    Image.fromarray(noise, "L").save(_IMAGES_DIR / "noise.png")
    names.append("noise.png")

    gradient = np.linspace(20, 240, 256, dtype=np.float32)
    flat = np.tile(gradient.reshape(1, -1), (128, 1))
    Image.fromarray(flat.astype(np.uint8), "L").save(_IMAGES_DIR / "gradient.png")
    names.append("gradient.png")

    base = Image.fromarray(noise, "L")
    buffer = io.BytesIO()
    base.save(buffer, "JPEG", quality=60)
    buffer.seek(0)
    reencoded = Image.open(buffer).convert("RGB")
    reencoded.save(_IMAGES_DIR / "reencoded.jpg", "JPEG", quality=80)
    names.append("reencoded.jpg")

    rng_webp = np.random.default_rng(seed=7)
    rgba = rng_webp.integers(0, 255, size=(64, 64, 4), dtype=np.uint8)
    Image.fromarray(rgba, "RGBA").save(_IMAGES_DIR / "photo.webp", "WEBP")
    names.append("photo.webp")

    return sorted(names)


def _fingerprint_for(path: Path) -> dict:
    """Run the pipeline on ``path`` and fingerprint the forensic output."""
    data = path.read_bytes()
    pipeline = build_pipeline(PipelineConfig())
    result = pipeline.analyze(data)
    return {"image": path.name, "fingerprint": pipeline_fingerprint(result)}


def build_snapshot_records() -> list[dict]:
    """Return the fingerprint records for every fixture image."""
    names = _generate_images()
    return [_fingerprint_for(_IMAGES_DIR / name) for name in sorted(names)]


def write_snapshot() -> None:
    """Write the forensic snapshot for every fixture image."""
    records = build_snapshot_records()
    _SNAPSHOT.write_text(
        json.dumps(records, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )


def load_snapshot() -> list[dict]:
    """Load the committed forensic snapshot."""
    if not _SNAPSHOT.is_file():
        return []
    return json.loads(_SNAPSHOT.read_text(encoding="utf-8"))


if __name__ == "__main__":
    write_snapshot()
    print(f"Wrote {_SNAPSHOT}")

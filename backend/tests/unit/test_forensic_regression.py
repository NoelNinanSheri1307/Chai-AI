"""Forensic regression tests (Milestone 10).

The forensic behaviour is FROZEN: performance and security hardening must not
change any output (verdict, confidence, risk, hypothesis scores, margin,
detector outputs, evidence, heatmap regions). These tests compare the current
pipeline output for a fixed set of fixtures against a committed snapshot.

If a forensic result changes, the failure must be investigated, **not** fixed by
updating the snapshot.
"""

from __future__ import annotations

import json
from pathlib import Path

from tests.fixtures.forensic.generate import (
    _IMAGES_DIR,
)

_SNAPSHOT_PATH = (
    Path(__file__).parent.parent / "fixtures" / "forensic" / "forensic_snapshot.json"
)


def _current_records() -> list[dict]:
    from tests.fixtures.forensic.generate import (
        _fingerprint_for,
        _generate_images,
    )

    names = _generate_images()
    return [_fingerprint_for(_IMAGES_DIR / name) for name in sorted(names)]


def test_forensic_snapshot_exists() -> None:
    assert _SNAPSHOT_PATH.is_file(), (
        "forensic_snapshot.json is missing; run write_snapshot() from the "
        "generate module ONLY when a deliberate forensic model change is "
        "approved."
    )


def test_forensic_output_unchanged() -> None:
    expected = json.loads(_SNAPSHOT_PATH.read_text(encoding="utf-8"))
    actual = _current_records()

    by_image = {record["image"]: record["fingerprint"] for record in expected}
    errors: list[str] = []
    for record in actual:
        image = record["image"]
        if image not in by_image:
            errors.append(f"new fixture image {image!r} not present in snapshot")
            continue
        if record["fingerprint"] != by_image[image]:
            errors.append(
                f"forensic output changed for {image!r}:\n"
                f"expected={by_image[image]}\n  actual  ={record['fingerprint']}"
            )

    assert not errors, (
        "Forensic regression detected — investigate, do not re-baseline.\n"
        + "\n".join(errors)
    )


def _noop_snapshot_loader() -> None:  # pragma: no cover
    pass

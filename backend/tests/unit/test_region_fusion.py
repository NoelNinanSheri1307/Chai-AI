"""Tests for the spatial region primitives and heatmap region fusion."""

from __future__ import annotations

import numpy as np
import pytest

from app.pipeline.heatmap.fusion import merge_regions, unique_detectors
from app.pipeline.heatmap.spatial import iou, mask_to_regions, normalize_pixel_box
from app.pipeline.signals import SpatialRegion


def _region(
    x: float,
    y: float,
    w: float,
    h: float,
    conf: float = 0.5,
    detector: str = "ela",
    severity: str = "moderate",
) -> SpatialRegion:
    return SpatialRegion(
        x=x,
        y=y,
        width=w,
        height=h,
        confidence=conf,
        severity=severity,
        label="Anomaly",
        detector=detector,
    )


# ---------------------------------------------------------------------------
# Spatial primitives
# ---------------------------------------------------------------------------


def test_iou_identical_is_one() -> None:
    a = _region(0.1, 0.1, 0.2, 0.2)
    assert iou(a, _region(0.1, 0.1, 0.2, 0.2)) == pytest.approx(1.0)


def test_iou_disjoint_is_zero() -> None:
    a = _region(0.0, 0.0, 0.1, 0.1)
    b = _region(0.5, 0.5, 0.1, 0.1)
    assert iou(a, b) == 0.0


def test_normalize_pixel_box_clamps() -> None:
    # Coorstit corners out-of-bounds get clamped to the image extent.
    x, y, w, h = normalize_pixel_box(10, 20, 200, 300, 100, 100)
    assert (x, y, w, h) == (0.1, 0.2, 0.9, 0.8)


def test_mask_to_regions() -> None:
    mask = np.zeros((100, 100), dtype=np.uint8)
    mask[30:60, 40:70] = 255
    regions = mask_to_regions(
        mask, detector="x", severity="strong", label="Box", confidence=0.9
    )
    assert len(regions) == 1
    region = regions[0]
    assert region.x == pytest.approx(0.4)
    assert region.y == pytest.approx(0.3)
    assert region.width == pytest.approx(0.3)
    assert region.height == pytest.approx(0.3)
    assert region.detector == "x"


# ---------------------------------------------------------------------------
# Region fusion
# ---------------------------------------------------------------------------


def test_overlapping_regions_merge_and_attribute() -> None:
    regions = [
        _region(0.15, 0.15, 0.4, 0.4, conf=0.7, detector="ela"),
        # Overlaps the first region (shared area).
        _region(0.2, 0.2, 0.4, 0.4, conf=0.6, detector="compression"),
    ]
    merged = merge_regions(regions)
    assert len(merged) == 1
    m = merged[0]
    assert "ela" in m.detectors
    assert "compression" in m.detectors
    # Accumulated confidence exceeds the strongest single contributor.
    assert m.confidence > 0.7
    # Union bounding box encloses both inputs.
    assert m.width >= 0.4
    assert m.height >= 0.4


def test_non_overlapping_regions_stay_separate() -> None:
    regions = [
        _region(0.0, 0.0, 0.1, 0.1, conf=0.9),
        _region(0.7, 0.7, 0.1, 0.1, conf=0.5),
    ]
    merged = merge_regions(regions)
    assert len(merged) == 2
    # Strongest first.
    assert merged[0].confidence > merged[1].confidence


def test_duplicate_suppression() -> None:
    # Two identical regions from the same detector must collapse to one.
    regions = [
        _region(0.1, 0.1, 0.2, 0.2, detector="texture"),
        _region(0.12, 0.1, 0.2, 0.2, detector="texture"),
    ]
    merged = merge_regions(regions)
    assert len(merged) == 1


def test_unique_detectors_ordered() -> None:
    regions = [
        _region(0, 0, 0.1, 0.1, detector="b"),
        _region(0.5, 0.5, 0.1, 0.1, detector="a"),
        _region(0.2, 0.2, 0.1, 0.1, detector="a"),
    ]
    assert unique_detectors(regions) == ("b", "a")


def test_tiny_regions_dropped() -> None:
    regions = [_region(0.1, 0.1, 0.001, 0.001)]
    merged = merge_regions(regions, min_area=0.001)
    assert merged == []


def test_worst_severity_used() -> None:
    regions = [
        _region(0.1, 0.1, 0.4, 0.4, severity="low", detector="a"),
        _region(0.12, 0.12, 0.4, 0.4, severity="strong", detector="b"),
    ]
    merged = merge_regions(regions)
    assert merged[0].severity == "strong"

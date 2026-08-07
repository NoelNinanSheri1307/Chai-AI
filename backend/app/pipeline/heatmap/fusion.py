"""Detector region fusion.

Multiple detectors may flag overlapping areas of the same image. This module
merges those regions into a single, non-redundant manipulation map:

* overlapping regions are greedily grouped using an intersection-over-union
  threshold;
* the merged confidence **accumulates** across contributing detectors
  (``1 - prod(1 - c_i)``), so agreement between detectors strengthens a region;
* detector **attribution** is preserved as the ordered set of sources;
* tiny regions are dropped and the result is returned strongest-first.

Fusion is fully deterministic — ordering is fixed by confidence — and depends
only on the input regions.
"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, field

from app.pipeline.signals import SpatialRegion

from .spatial import _max_size, clamp01, drop_duplicates, iou

_SEVERITY_RANK = {"low": 0, "moderate": 1, "strong": 2}
_SEVERITY_NAMES = ("low", "moderate", "strong")


@dataclass(frozen=True)
class MergedRegion:
    """A fused manipulation region with attribution and accumulated confidence."""

    x: float
    y: float
    width: float
    height: float
    confidence: float
    severity: str
    label: str
    detectors: tuple[str, ...] = field(default_factory=tuple)

    @property
    def area(self) -> float:
        """Return the normalized area of the merged region."""
        return self.width * self.height


def _accumulated_confidence(regions: list[SpatialRegion]) -> float:
    """Combine region confidences as independent-evidence accumulation."""
    score = 0.0
    for region in regions:
        score = 1.0 - (1.0 - score) * (1.0 - clamp01(region.confidence))
    return clamp01(score)


def _worst_severity(regions: list[SpatialRegion]) -> str:
    """Return the strongest severity among the contributing regions."""
    rank = max(_SEVERITY_RANK.get(r.severity, 0) for r in regions)
    return _SEVERITY_NAMES[rank]


def _build_merged(regions: list[SpatialRegion]) -> MergedRegion:
    """Build a single ``MergedRegion`` from a grouped cluster."""
    xs = [r.x for r in regions]
    ys = [r.y for r in regions]
    x = min(xs)
    y = min(ys)
    x2 = max(r.x + r.width for r in regions)
    y2 = max(r.y + r.height for r in regions)
    primary = max(regions, key=lambda r: r.confidence)
    detectors = tuple(sorted({r.detector for r in regions}))
    return MergedRegion(
        x=x,
        y=y,
        width=_max_size(x2 - x),
        height=_max_size(y2 - y),
        confidence=_accumulated_confidence(regions),
        severity=_worst_severity(regions),
        label=primary.label,
        detectors=detectors,
    )


def merge_regions(
    regions: list[SpatialRegion],
    *,
    iou_threshold: float = 0.4,
    min_area: float = 0.0005,
) -> list[MergedRegion]:
    """Merge overlapping regions into a deduplicated, ordered manipulation map.

    ``iou_threshold`` controls when two regions are considered the same area;
    ``min_area`` (normalized) drops trivial regions. The result is sorted by
    descending confidence.
    """
    prepared = drop_duplicates(regions)
    clusters: list[list[SpatialRegion]] = []
    for region in sorted(prepared, key=lambda r: -r.confidence):
        target: int | None = None
        for index, cluster in enumerate(clusters):
            if any(iou(member, region) >= iou_threshold for member in cluster):
                target = index
                break
        if target is None:
            clusters.append([region])
        else:
            clusters[target].append(region)

    merged = [_build_merged(cluster) for cluster in clusters]
    merged = [m for m in merged if m.area >= min_area]
    merged.sort(key=lambda m: -m.confidence)
    return merged


def unique_detectors(regions: list[SpatialRegion]) -> tuple[str, ...]:
    """Return the ordered set of detector names contributing regions."""
    return tuple(OrderedDict((r.detector, None) for r in regions).keys())

"""Spatial primitives shared by detectors and the heatmap generator.

These small, pure functions normalize pixel-space evidence into the normalized
:class:`SpatialRegion` vocabulary used across the pipeline, compute intersection
over union for overlap detection, and convert binary masks into bounding boxes.
Everything here is deterministic: the same mask always yields the same boxes.
"""

from __future__ import annotations

from collections.abc import Sequence

import cv2
import numpy as np

from app.pipeline.signals import SpatialRegion

#: Clamp margin applied when normalizing so regions never exceed the image and
#: never collapse to a zero-size box.
_EPSILON = 1e-4


def clamp01(value: float) -> float:
    """Clamp ``value`` into the closed unit interval ``[0, 1]``."""
    return max(0.0, min(1.0, value))


def normalize_pixel_box(
    x: float,
    y: float,
    width: float,
    height: float,
    image_width: int,
    image_height: int,
) -> tuple[float, float, float, float]:
    """Convert a pixel-space box to clamped normalized coordinates."""
    if image_width <= 0 or image_height <= 0:
        return 0.0, 0.0, 0.0, 0.0
    n_x = clamp01(x / image_width)
    n_y = clamp01(y / image_height)
    right = clamp01((x + width) / image_width)
    bottom = clamp01((y + height) / image_height)
    n_w = max(0.0, right - n_x)
    n_h = max(0.0, bottom - n_y)
    return n_x, n_y, _max_size(n_w), _max_size(n_h)


def _max_size(size: float) -> float:
    """Constrain a normalized box dimension to at least the epsilon margin."""
    return max(_EPSILON, size)


def iou(a: SpatialRegion, b: SpatialRegion) -> float:
    """Return the intersection-over-union overlap between two regions."""
    a_x2 = a.x + a.width
    a_y2 = a.y + a.height
    b_x2 = b.x + b.width
    b_y2 = b.y + b.height

    inter_x = max(0.0, min(a_x2, b_x2) - max(a.x, b.x))
    inter_y = max(0.0, min(a_y2, b_y2) - max(a.y, b.y))
    inter = inter_x * inter_y
    union = a.area + b.area - inter
    if union <= 0.0:
        return 0.0
    return inter / union


def mask_to_regions(
    mask: np.ndarray,
    *,
    detector: str,
    severity: str,
    label: str,
    confidence: float,
    min_area: int = 8,
) -> list[SpatialRegion]:
    """Convert a binary pixel ``mask`` into normalized bounding-box regions.

    ``confidence``, ``severity`` and ``label`` are copied onto every region and
    ``detector`` records the source. ``min_area`` drops spuriously tiny blobs.
    """
    if mask.size == 0:
        return []
    binary = (mask > 0).astype(np.uint8) * 255
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    image_height, image_width = mask.shape[:2]

    regions: list[SpatialRegion] = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if w * h < min_area:
            continue
        nx, ny, nw, nh = normalize_pixel_box(x, y, w, h, image_width, image_height)
        # Keep tightly clustered boxes small; skip boxes that are essentially
        # the whole frame (not a localized signal).
        if nw * nh >= 0.99:
            continue
        regions.append(
            SpatialRegion(
                x=nx,
                y=ny,
                width=nw,
                height=nh,
                confidence=confidence,
                severity=severity,
                label=label,
                detector=detector,
            )
        )
    return regions


def merge_boxes(regions: Sequence[SpatialRegion]) -> SpatialRegion:
    """Return a single region tightly bounding ``regions`` (union geometry).

    The merged ``confidence`` is the mean of the inputs and ``label``/``detector``
    come from the first (highest-confidence) contributor.
    """
    xs = [r.x for r in regions]
    ys = [r.y for r in regions]
    x = min(xs)
    y = min(ys)
    x2 = max(r.x + r.width for r in regions)
    y2 = max(r.y + r.height for r in regions)
    confidence = sum(r.confidence for r in regions) / len(regions)
    primary = max(regions, key=lambda r: r.confidence)
    return SpatialRegion(
        x=x,
        y=y,
        width=_max_size(x2 - x),
        height=_max_size(y2 - y),
        confidence=clamp01(confidence),
        severity=primary.severity,
        label=primary.label,
        detector="/".join(sorted({r.detector for r in regions})),
    )


def drop_duplicates(
    regions: Sequence[SpatialRegion], iou_threshold: float = 0.6
) -> list[SpatialRegion]:
    """Remove near-duplicate regions (same source, above-overlap) greedily."""
    kept: list[SpatialRegion] = []
    for region in sorted(regions, key=lambda r: (r.detector, r.x, r.y, -r.confidence)):
        duplicate = any(
            kept_region.detector == region.detector
            and iou(kept_region, region) > iou_threshold
            for kept_region in kept
        )
        if not duplicate:
            kept.append(region)
    return kept

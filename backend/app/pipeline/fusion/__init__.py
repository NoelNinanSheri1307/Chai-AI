"""Fusion engine framework.

The fusion engine turns the collected detector signals into a single decision:
the final verdict, a confidence score, a risk level, the aggregated per-category
scores and the detected indicators. It is deliberately isolated behind the
:class:`FusionEngine` interface so the deterministic placeholder shipped here can
be replaced by the real weighting model without touching the pipeline or the
services.
"""

from app.pipeline.fusion.base import FusionEngine, FusionResult
from app.pipeline.fusion.placeholder import PlaceholderFusionEngine

__all__ = ["FusionEngine", "FusionResult", "PlaceholderFusionEngine"]

"""Fusion engine framework.

The fusion engine turns the collected detector signals into a single decision:
the final verdict, a confidence score, a risk level, the aggregated per-category
scores, the detected indicators, per-detector contributions and a deduplicated,
ranked evidence list. It is deliberately isolated behind the
:class:`FusionEngine` interface so the deterministic engine shipped here can be
tuned or swapped without touching the pipeline or the services.
"""

from app.pipeline.fusion.base import DetectorContribution, FusionEngine, FusionResult
from app.pipeline.fusion.classify import (
    ClassificationResult,
    DetectorHypothesisContribution,
    compute_classification,
)
from app.pipeline.fusion.engine import DeterministicFusionEngine
from app.pipeline.fusion.hypotheses import HYPOTHESES, Hypothesis, HypothesisScores

__all__ = [
    "ClassificationResult",
    "DetectorContribution",
    "DetectorHypothesisContribution",
    "DeterministicFusionEngine",
    "FusionEngine",
    "FusionResult",
    "HYPOTHESES",
    "Hypothesis",
    "HypothesisScores",
    "compute_classification",
]

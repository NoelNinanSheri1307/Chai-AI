"""Forensic pipeline.

Pure computation on an image file: detector execution, signal collection,
fusion, confidence, evidence, explanation and heatmap generation. The pipeline
is isolated from HTTP and the database so it can be unit-tested and swapped
independently.

The framework (Milestone 4) ships the modular :class:`ModularAnalysisPipeline`
runner, the abstract :class:`AnalysisPipeline` contract, the detector/fusion/
heatmap/explainability frameworks and deterministic placeholder implementations.
The real forensic detectors arrive in a later milestone and plug into these
interfaces without pipeline changes.
"""

from app.pipeline.base import (
    AnalysisPipeline,
    HeatmapRegionResult,
    HeatmapResult,
    IndicatorResult,
    PipelineResult,
    ScoreResult,
)
from app.pipeline.config import PipelineConfig, get_pipeline_config
from app.pipeline.detectors import Detector
from app.pipeline.explanation import EvidenceGenerator, ExplanationGenerator
from app.pipeline.fusion import FusionEngine, FusionResult
from app.pipeline.heatmap import HeatmapContext, HeatmapGenerator
from app.pipeline.placeholder import PlaceholderAnalysisPipeline
from app.pipeline.runner import ModularAnalysisPipeline
from app.pipeline.signals import DetectorHealth, DetectorSignal
from app.pipeline.versioning import ComponentVersion, PipelineRunVersion

__all__ = [
    "AnalysisPipeline",
    "ComponentVersion",
    "Detector",
    "DetectorHealth",
    "DetectorSignal",
    "EvidenceGenerator",
    "ExplanationGenerator",
    "FusionEngine",
    "FusionResult",
    "HeatmapContext",
    "HeatmapGenerator",
    "HeatmapRegionResult",
    "HeatmapResult",
    "IndicatorResult",
    "ModularAnalysisPipeline",
    "PipelineConfig",
    "PipelineResult",
    "PipelineRunVersion",
    "PlaceholderAnalysisPipeline",
    "ScoreResult",
    "get_pipeline_config",
]

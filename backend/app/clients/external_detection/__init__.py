"""External AI detection & independent benchmarking package."""

from app.clients.external_detection.base import (
    ExternalDetectionResult,
    ExternalDetectorProvider,
)
from app.clients.external_detection.benchmark import (
    ExternalBenchmarkItem,
    ExternalBenchmarkResult,
    compare_verdict,
    compute_benchmark_report,
)
from app.clients.external_detection.manager import ExternalDetectionManager

__all__ = [
    "ExternalDetectionResult",
    "ExternalDetectorProvider",
    "ExternalBenchmarkItem",
    "ExternalBenchmarkResult",
    "compare_verdict",
    "compute_benchmark_report",
    "ExternalDetectionManager",
]

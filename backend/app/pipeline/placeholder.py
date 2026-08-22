"""Deterministic placeholder pipeline used to validate the request lifecycle.

This implementation deliberately does **not** inspect image content. It returns
a fixed, contract-shaped :class:`PipelineResult` so every layer of the
application (upload → pipeline → persistence → DTO) is exercised end to end.

The placeholder exists only to validate application flow. A later milestone
replaces it with the real forensic pipeline while keeping the rest of the
application unchanged.
"""

from __future__ import annotations

from app.core.enums import (
    IndicatorSeverity,
    IndicatorType,
    RiskLevel,
    ScoreCategory,
    Verdict,
)
from app.pipeline.base import (
    AnalysisPipeline,
    HeatmapResult,
    IndicatorResult,
    PipelineReportData,
    PipelineResult,
    ReportContribution,
    ScoreResult,
)

_FORMAT_BY_MIME: dict[str | None, str] = {
    "image/jpeg": "JPEG",
    "image/png": "PNG",
    "image/webp": "WebP",
}


class PlaceholderAnalysisPipeline(AnalysisPipeline):
    """Return a fixed, deterministic mock analysis result."""

    def analyze(
        self,
        image_bytes: bytes,
        *,
        content_type: str | None = None,
        file_name: str | None = None,
    ) -> PipelineResult:
        """Build a deterministic placeholder result for ``image_bytes``.

        ``content_type`` and ``file_name`` are ignored except for the derived
        metadata entries; nothing about the bytes themselves is analyzed.
        """
        metadata = self._derive_metadata(image_bytes, content_type)
        return PipelineResult(
            verdict=Verdict.AI_GENERATED,
            confidence=0.91,
            risk_level=RiskLevel.HIGH,
            explanation=(
                "Image appears to be fully or largely AI-generated. Strongest "
                "signal: soft, watercolor-like artifacts consistent with "
                "diffusion synthesis."
            ),
            duration_ms=2100,
            scores=self._placeholder_scores(),
            indicators=self._placeholder_indicators(),
            evidence=["Sensor and frequency analyses returned clean profiles."],
            metadata=metadata,
            heatmap=HeatmapResult(overall_manipulation=0.78, regions=[]),
            report_data=_placeholder_report_data(),
        )

    @staticmethod
    def _placeholder_scores() -> list[ScoreResult]:
        """Return a fixed per-category confidence breakdown."""
        return [
            ScoreResult(ScoreCategory.TEXTURE, 0.83),
            ScoreResult(ScoreCategory.METADATA, 0.64),
            ScoreResult(ScoreCategory.LIGHTING, 0.55),
            ScoreResult(ScoreCategory.FREQUENCY, 0.77),
            ScoreResult(ScoreCategory.NOISE_PATTERN, 0.12),
            ScoreResult(ScoreCategory.COMPRESSION, 0.71),
            ScoreResult(ScoreCategory.EDGE_CONSISTENCY, 0.68),
            ScoreResult(ScoreCategory.COLOR_DISTRIBUTION, 0.58),
        ]

    @staticmethod
    def _placeholder_indicators() -> list[IndicatorResult]:
        """Return fixed detected-indicator signals."""
        return [
            IndicatorResult(
                type=IndicatorType.DIFFUSION,
                confidence=0.94,
                severity=IndicatorSeverity.STRONG,
                description=(
                    "Soft, watercolor-like artifacts consistent with diffusion "
                    "synthesis."
                ),
            ),
            IndicatorResult(
                type=IndicatorType.FREQUENCY,
                confidence=0.72,
                severity=IndicatorSeverity.MODERATE,
                description=(
                    "Spectral anomalies consistent with upscaled synthetic content."
                ),
            ),
        ]

    @staticmethod
    def _derive_metadata(
        image_bytes: bytes, content_type: str | None
    ) -> dict[str, str]:
        """Return placeholder metadata derived only from upload context."""
        return {
            "Format": _FORMAT_BY_MIME.get(content_type, "Unknown"),
            "File size": f"{len(image_bytes):,} bytes",
        }


def _placeholder_report_data() -> PipelineReportData:
    """A deterministic report snapshot mirroring the placeholder result."""
    contributions = (
        ReportContribution(
            detector="frequency",
            detector_version="0.1.0",
            category=ScoreCategory.FREQUENCY,
            normalized_score=0.77,
            detector_confidence=0.90,
            reliability=0.18,
            weight_share=18 / 100,
            contribution=0.20,
            direction="supports:manipulation",
            hypothesis_weights=(0.15, 0.85),
            preferred_hypothesis="AI Generated",
            processing_time_ms=180,
        ),
        ReportContribution(
            detector="texture",
            detector_version="0.1.0",
            category=ScoreCategory.TEXTURE,
            normalized_score=0.83,
            detector_confidence=0.85,
            reliability=0.15,
            weight_share=15 / 100,
            contribution=0.22,
            direction="supports:manipulation",
            hypothesis_weights=(0.18, 0.82),
            preferred_hypothesis="AI Generated",
            processing_time_ms=160,
        ),
        ReportContribution(
            detector="metadata",
            detector_version="0.1.0",
            category=ScoreCategory.METADATA,
            normalized_score=0.64,
            detector_confidence=0.90,
            reliability=0.10,
            weight_share=10 / 100,
            contribution=0.12,
            direction="supports:manipulation",
            hypothesis_weights=(0.80, 0.20),
            preferred_hypothesis="Original",
            processing_time_ms=90,
        ),
    )
    return PipelineReportData(
        hypothesis_scores=(0.15, 0.85),
        runner_up_verdict=Verdict.ORIGINAL,
        classification_margin=0.70,
        contributions=contributions,
    )

"""External detection & benchmarking DTOs.

Response schema for the ``POST /v1/analyses/{public_id}/external-check`` endpoint.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ExternalDetectionResultDTO(BaseModel):
    """Normalized response from an external AI detection provider."""

    model_config = ConfigDict(extra="forbid")

    provider: str
    providerVersion: str
    isConfigured: bool
    status: str
    detectedAsAi: bool | None = None
    confidence: float | None = None
    classificationLabel: str | None = None
    rawCategory: str | None = None
    processingTimeMs: int = 0
    errorMessage: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)


class ExternalBenchmarkItemDTO(BaseModel):
    """Comparison item for a single external provider against Chai's verdict."""

    model_config = ConfigDict(extra="forbid")

    provider: str
    providerVersion: str
    status: str
    detectedAsAi: bool | None = None
    confidence: float | None = None
    classificationLabel: str | None = None
    agreement: bool | None = None
    compatibilityNote: str
    confidenceDelta: float | None = None


class ExternalBenchmarkResponseDTO(BaseModel):
    """API response contract for the external benchmark / check endpoint."""

    model_config = ConfigDict(extra="forbid")

    analysisId: str
    chaiVerdict: str
    chaiConfidence: float
    chaiRiskLevel: str
    externalResults: list[ExternalDetectionResultDTO] = Field(default_factory=list)
    benchmarkItems: list[ExternalBenchmarkItemDTO] = Field(default_factory=list)
    overallAgreementRatio: float | None = None
    summary: str

"""Abstract provider contract and normalized result models for external AI detectors.

External providers (such as Sightengine, Hive, or other third-party services)
implement :class:`ExternalDetectorProvider` and return normalized
:class:`ExternalDetectionResult` objects. External results are kept completely
isolated from Chai's internal seven-detector forensic fusion engine and are
used exclusively for independent validation and benchmarking.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from pydantic import BaseModel, Field


class ExternalDetectionResult(BaseModel):
    """Normalized output from an external AI-image detection provider."""

    provider: str
    provider_version: str = "1.0"
    is_configured: bool
    status: str = Field(
        description="One of: success, disabled, unconfigured, error, timeout"
    )
    detected_as_ai: bool | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    classification_label: str | None = None
    raw_category: str | None = None
    processing_time_ms: int = 0
    error_message: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)


class ExternalDetectorProvider(ABC):
    """Abstract interface for external AI detection service adapters."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Unique identifier for this provider adapter (for example 'sightengine')."""

    @property
    @abstractmethod
    def provider_version(self) -> str:
        """Adapter version string."""

    @abstractmethod
    def is_configured(self) -> bool:
        """Return True when the provider is enabled and all credentials exist."""

    @abstractmethod
    def analyze(
        self,
        image_bytes: bytes,
        filename: str = "image.jpg",
        content_type: str = "image/jpeg",
    ) -> ExternalDetectionResult:
        """Query the external provider and return a normalized result.

        Must handle all exceptions and timeouts internally, returning a result
        with appropriate status rather than raising unhandled errors.
        """

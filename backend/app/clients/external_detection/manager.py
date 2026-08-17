"""External detection manager: aggregates registered external detector providers."""

from __future__ import annotations

from app.clients.external_detection.base import (
    ExternalDetectionResult,
    ExternalDetectorProvider,
)
from app.clients.external_detection.providers.sightengine import (
    SightengineDetectorProvider,
)
from app.core.config import Settings


class ExternalDetectionManager:
    """Orchestrates registered external AI detection providers."""

    def __init__(
        self,
        providers: list[ExternalDetectorProvider] | None = None,
        settings: Settings | None = None,
    ) -> None:
        if providers is not None:
            self._providers = providers
        else:
            resolved_settings = settings or Settings()
            self._providers = [SightengineDetectorProvider(resolved_settings)]

    @property
    def providers(self) -> list[ExternalDetectorProvider]:
        return list(self._providers)

    def analyze_all(
        self,
        image_bytes: bytes,
        filename: str = "image.jpg",
        content_type: str = "image/jpeg",
    ) -> list[ExternalDetectionResult]:
        """Run all registered external detector providers and return results."""
        results: list[ExternalDetectionResult] = []
        for provider in self._providers:
            try:
                res = provider.analyze(
                    image_bytes=image_bytes,
                    filename=filename,
                    content_type=content_type,
                )
                results.append(res)
            except Exception as exc:
                results.append(
                    ExternalDetectionResult(
                        provider=provider.provider_name,
                        provider_version=provider.provider_version,
                        is_configured=provider.is_configured(),
                        status="error",
                        error_message=f"Unhandled provider error: {exc!s}",
                    )
                )
        return results

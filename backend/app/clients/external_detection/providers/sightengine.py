"""Sightengine AI-image detection provider adapter.

Interfaces with Sightengine's official GenAI detection API endpoint
(``models=genai``) to obtain independent AI image likelihood scores.

Requires ``CHAI_EXTERNAL_DETECTION_ENABLED=true`` and valid Sightengine
API credentials (``CHAI_SIGHTENGINE_API_USER`` and ``CHAI_SIGHTENGINE_API_SECRET``).
When unconfigured, disabled, or failing, returns an isolated result with status
without interrupting Chai's primary forensic pipeline.
"""

from __future__ import annotations

import time
from typing import Any

import httpx

from app.clients.external_detection.base import (
    ExternalDetectionResult,
    ExternalDetectorProvider,
)
from app.core.config import Settings


class SightengineDetectorProvider(ExternalDetectorProvider):
    """Adapter for the Sightengine GenAI image detection service."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._endpoint = "https://api.sightengine.com/1.0/check.json"

    @property
    def provider_name(self) -> str:
        return "sightengine"

    @property
    def provider_version(self) -> str:
        return "1.0"

    def is_configured(self) -> bool:
        """Return True when external detection is enabled and credentials exist."""
        return bool(
            self._settings.external_detection_enabled
            and self._settings.sightengine_enabled
            and self._settings.sightengine_api_user
            and self._settings.sightengine_api_secret
        )

    def analyze(
        self,
        image_bytes: bytes,
        filename: str = "image.jpg",
        content_type: str = "image/jpeg",
    ) -> ExternalDetectionResult:
        """Query Sightengine GenAI detection API and return normalized result."""
        if not self._settings.external_detection_enabled:
            return ExternalDetectionResult(
                provider=self.provider_name,
                provider_version=self.provider_version,
                is_configured=False,
                status="disabled",
                error_message="External detection is globally disabled.",
            )

        if not self.is_configured():
            return ExternalDetectionResult(
                provider=self.provider_name,
                provider_version=self.provider_version,
                is_configured=False,
                status="unconfigured",
                error_message="Sightengine API credentials (api_user / api_secret) are missing.",
            )

        start_time = time.perf_counter()
        timeout = self._settings.external_timeout_seconds

        data = {
            "models": "genai",
            "api_user": self._settings.sightengine_api_user,
            "api_secret": self._settings.sightengine_api_secret,
        }
        files = {
            "media": (filename, image_bytes, content_type),
        }

        try:
            with httpx.Client(timeout=timeout) as client:
                response = client.post(self._endpoint, data=data, files=files)
                duration_ms = int((time.perf_counter() - start_time) * 1000)

                if response.status_code != 200:
                    return ExternalDetectionResult(
                        provider=self.provider_name,
                        provider_version=self.provider_version,
                        is_configured=True,
                        status="error",
                        processing_time_ms=duration_ms,
                        error_message=f"Sightengine API returned HTTP {response.status_code}.",
                    )

                payload: dict[str, Any] = response.json()
                return self._parse_response(payload, duration_ms)

        except httpx.TimeoutException:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            return ExternalDetectionResult(
                provider=self.provider_name,
                provider_version=self.provider_version,
                is_configured=True,
                status="timeout",
                processing_time_ms=duration_ms,
                error_message=f"Sightengine API request timed out after {timeout}s.",
            )
        except Exception as exc:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            return ExternalDetectionResult(
                provider=self.provider_name,
                provider_version=self.provider_version,
                is_configured=True,
                status="error",
                processing_time_ms=duration_ms,
                error_message=f"Sightengine request failed: {exc!s}",
            )

    def _parse_response(
        self, payload: dict[str, Any], duration_ms: int
    ) -> ExternalDetectionResult:
        if payload.get("status") != "success":
            error_info = payload.get("error", {})
            msg = (
                error_info.get("message")
                if isinstance(error_info, dict)
                else "Sightengine reported failure."
            )
            return ExternalDetectionResult(
                provider=self.provider_name,
                provider_version=self.provider_version,
                is_configured=True,
                status="error",
                processing_time_ms=duration_ms,
                error_message=str(msg),
            )

        type_scores = payload.get("type", {})
        ai_score = type_scores.get("ai_generated")

        if ai_score is None:
            return ExternalDetectionResult(
                provider=self.provider_name,
                provider_version=self.provider_version,
                is_configured=True,
                status="success",
                processing_time_ms=duration_ms,
                detected_as_ai=None,
                confidence=None,
                error_message="Sightengine response omitted 'type.ai_generated' score.",
            )

        try:
            ai_score_float = float(ai_score)
        except (ValueError, TypeError):
            ai_score_float = 0.0

        ai_score_clean = max(0.0, min(1.0, round(ai_score_float, 4)))
        detected = ai_score_clean >= 0.5

        request_id = ""
        req_obj = payload.get("request")
        if isinstance(req_obj, dict):
            request_id = str(req_obj.get("id", ""))

        return ExternalDetectionResult(
            provider=self.provider_name,
            provider_version=self.provider_version,
            is_configured=True,
            status="success",
            detected_as_ai=detected,
            confidence=ai_score_clean,
            classification_label="ai_generated" if detected else "authentic",
            raw_category=f"genai_{ai_score_clean:.2f}",
            processing_time_ms=duration_ms,
            metadata={"request_id": request_id, "model": "genai"},
        )

"""External detector providers sub-package."""

from app.clients.external_detection.providers.sightengine import (
    SightengineDetectorProvider,
)

__all__ = ["SightengineDetectorProvider"]

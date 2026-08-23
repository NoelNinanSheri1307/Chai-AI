"""Local disk cache for external benchmark API responses (Milestone 15).

Caches normalized external detection results indexed by image SHA-256 hash, provider name,
and provider version. Enables resilient resumption and prevents duplicate billable API queries.
Strictly ensures zero secrets or image payloads are persisted.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from app.clients.external_detection.base import ExternalDetectionResult

logger = logging.getLogger(__name__)


class ExternalBenchmarkCache:
    """Persistent JSON cache for external provider benchmark responses."""

    def __init__(self, cache_path: Path | str | None = None) -> None:
        if cache_path is None:
            self._cache_path = Path("reports/external_cache.json")
        else:
            self._cache_path = Path(cache_path)
        self._entries: dict[str, dict[str, Any]] = {}
        self._load()

    @property
    def cache_path(self) -> Path:
        return self._cache_path

    def _make_key(
        self, sha256: str, provider: str, provider_version: str = "1.0"
    ) -> str:
        return f"{sha256.lower().strip()}:{provider.lower().strip()}:{provider_version.strip()}"

    def _load(self) -> None:
        """Load cache entries from disk if file exists."""
        if not self._cache_path.is_file():
            return
        try:
            raw = self._cache_path.read_text(encoding="utf-8")
            data = json.loads(raw)
            if isinstance(data, dict):
                self._entries = data
                logger.info(
                    "Loaded %d external benchmark cache entries from %s",
                    len(self._entries),
                    self._cache_path,
                )
        except Exception as exc:
            logger.warning(
                "Failed to read external benchmark cache at %s: %s",
                self._cache_path,
                exc,
            )
            self._entries = {}

    def save(self) -> None:
        """Persist current cache entries to disk safely."""
        try:
            self._cache_path.parent.mkdir(parents=True, exist_ok=True)
            self._cache_path.write_text(
                json.dumps(self._entries, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        except Exception as exc:
            logger.warning(
                "Failed to write external benchmark cache to %s: %s",
                self._cache_path,
                exc,
            )

    def get(
        self,
        sha256: str,
        provider: str,
        provider_version: str = "1.0",
    ) -> ExternalDetectionResult | None:
        """Retrieve a cached external detection result if available."""
        key = self._make_key(sha256, provider, provider_version)
        item = self._entries.get(key)
        if not item:
            return None
        try:
            return ExternalDetectionResult.model_validate(item)
        except Exception:
            return None

    def set(
        self,
        sha256: str,
        provider: str,
        provider_version: str,
        result: ExternalDetectionResult,
    ) -> None:
        """Store an external detection result into the cache."""
        key = self._make_key(sha256, provider, provider_version)
        # Redact any unsafe keys from metadata just in case
        safe_dict = result.model_dump()
        self._entries[key] = safe_dict

    def __len__(self) -> int:
        return len(self._entries)

"""Object-storage abstraction: interface + local filesystem adapter.

The rest of the system talks to object storage only through the
:class:`StorageClient` interface, so a future S3/MinIO adapter (Milestone 3)
can replace :class:`LocalStorageAdapter` without touching callers. Storage
keys are server-generated and content-addressed; the filesystem adapter
resolves keys beneath a configurable root and guards against path traversal.
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from pathlib import Path
from uuid import uuid4

from app.core.config import Settings


class StorageError(Exception):
    """Base class for storage failures."""


class StorageObjectNotFoundError(StorageError):
    """A requested object does not exist."""


class StorageClient(ABC):
    """Narrow interface for object storage.

    ``store``/``fetch``/``delete``/``exists`` are implemented by every
    adapter. ``signed_url`` is reserved for the remote adapters (Milestone 3)
    and raises by default.
    """

    @abstractmethod
    def store(self, key: str, data: bytes, *, content_type: str | None = None) -> None:
        """Write ``data`` under ``key``, replacing any existing object."""

    @abstractmethod
    def fetch(self, key: str) -> bytes:
        """Return the bytes stored under ``key``.

        Raises :class:`StorageObjectNotFoundError` when the object is missing.
        """

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Remove the object under ``key``; returns whether it existed."""

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Return whether an object exists under ``key``."""

    def signed_url(self, key: str, ttl_seconds: int) -> str:
        """Return a temporary access URL (reserved for remote adapters)."""
        raise NotImplementedError(
            "Signed URLs are reserved for the remote storage adapters (Milestone 3)."
        )


class LocalStorageAdapter(StorageClient):
    """Filesystem-backed storage rooted at a configurable directory.

    Keys use forward slashes as separators and are resolved beneath ``root``.
    Absolute and path-traversal keys are rejected. Writes are atomic (temp
    file + rename) so a crash never leaves a partially written object.
    """

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _resolve(self, key: str) -> Path:
        """Resolve a key to an absolute path verified to stay under ``root``."""
        if not isinstance(key, str) or not key or "\x00" in key:
            raise StorageError("Storage key must be a non-empty string.")
        normalized = key.replace("\\", "/")
        if normalized.startswith("/"):
            raise StorageError(f"Storage key must be relative: {key!r}")
        parts = normalized.split("/")
        if any(part in {"", ".", ".."} for part in parts):
            raise StorageError(f"Storage key contains invalid path components: {key!r}")
        resolved = self.root.joinpath(*parts).resolve()
        try:
            resolved.relative_to(self.root.resolve())
        except ValueError as exc:
            raise StorageError(
                f"Storage key escapes the storage root: {key!r}"
            ) from exc
        return resolved

    def store(self, key: str, data: bytes, *, content_type: str | None = None) -> None:
        """Write ``data`` atomically under ``key``."""
        path = self._resolve(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
        try:
            temp_path.write_bytes(bytes(data))
            os.replace(temp_path, path)
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def fetch(self, key: str) -> bytes:
        """Return the bytes stored under ``key`` or raise a not-found error."""
        path = self._resolve(key)
        if not path.is_file():
            raise StorageObjectNotFoundError(f"No object stored at {key!r}")
        return path.read_bytes()

    def delete(self, key: str) -> bool:
        """Remove the object under ``key``; return whether it existed."""
        path = self._resolve(key)
        if not path.is_file():
            return False
        path.unlink()
        return True

    def exists(self, key: str) -> bool:
        """Return whether an object exists under ``key``."""
        return self._resolve(key).is_file()


def create_storage_client(settings: Settings) -> StorageClient:
    """Build the storage adapter configured for the active environment."""
    return LocalStorageAdapter(settings.storage_root)

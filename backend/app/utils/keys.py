"""Server-generated object-storage keys and public resource ids.

Original image blobs are stored under a content-addressed, partitionable key
(architecture spec §9.2): ``{environment}/orig/{sha256-16}.{ext}``. Public
resource ids are opaque strings with a type prefix (``ana_...``, ``cm_...``).
All identifiers are generated server side so client input never forms part of a
filesystem path.
"""

from __future__ import annotations

import hashlib
import uuid

_EXTENSION_BY_MIME: dict[str, str] = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}


def new_public_id(prefix: str) -> str:
    """Return an opaque, collision-resistant public id with ``prefix``."""
    return f"{prefix}{uuid.uuid4().hex}"


def original_storage_key(environment: str, data: bytes, mime: str) -> str:
    """Return the content-addressed storage key for an original image."""
    digest = hashlib.sha256(data).hexdigest()
    extension = _EXTENSION_BY_MIME.get(mime, "bin")
    return f"{environment}/orig/{digest[:16]}.{extension}"

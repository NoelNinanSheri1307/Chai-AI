"""Report DTOs.

``ShareTextResponse`` wraps the human-readable report text returned by the
reports endpoints. PDF generation is deferred to the reports milestone.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ShareTextResponse(BaseModel):
    """Shareable plain-text summary of an analysis."""

    model_config = ConfigDict(extra="forbid")

    text: str

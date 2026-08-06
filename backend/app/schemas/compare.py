"""Comparison DTOs mirroring the Flutter frontend model.

``CompareResultDTO`` is returned synchronously by ``POST /v1/compare`` (and
would back the async result retrieval once job orchestration arrives).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.analysis import HeatmapRegionDTO


class CompareResultDTO(BaseModel):
    """Result of a two-image comparison."""

    model_config = ConfigDict(extra="forbid")

    labelA: str
    labelB: str
    similarity: float = Field(ge=0.0, le=1.0)
    aiProbability: float = Field(ge=0.0, le=1.0)
    similarities: list[str] = Field(default_factory=list)
    differences: list[str] = Field(default_factory=list)
    manipulatedRegions: list[HeatmapRegionDTO] = Field(default_factory=list)

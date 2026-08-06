"""History DTOs mirroring the Flutter frontend model.

``HistoryItemDTO`` is the lightweight summary returned by ``GET /v1/history``;
the full detail is served by the ``AnalysisResult`` DTO.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import RiskLevel, Verdict


class HistoryItemDTO(BaseModel):
    """A paginated history summary row."""

    model_config = ConfigDict(extra="forbid")

    id: str
    imagePath: str | None = None
    fileName: str | None = None
    verdict: Verdict
    confidence: float = Field(ge=0.0, le=1.0)
    riskLevel: RiskLevel
    timestamp: str
    isFavorite: bool = False

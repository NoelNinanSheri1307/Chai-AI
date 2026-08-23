"""Models and data structures for Milestone 19 external-assisted production classification."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.core.enums import RiskLevel, Verdict


@dataclass(frozen=True)
class DecisionProvenance:
    """Audit trail and provenance for the external-assisted classification decision."""

    final_classification: Verdict
    final_confidence: float
    chai_classification: Verdict
    chai_confidence: float
    chai_ai_probability: float
    chai_edit_score: float
    sightengine_status: str  # "success", "timeout", "error", "disabled", "unconfigured"
    sightengine_ai_probability: float | None
    fusion_weight_chai: float
    fusion_weight_sightengine: float
    decision_reason: str
    evidence: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ProductionDecisionResult:
    """The final production decision output after multi-source fusion and conflict resolution."""

    verdict: Verdict
    confidence: float
    risk_level: RiskLevel
    explanation: str
    provenance: DecisionProvenance

"""Explainability framework.

Distinguishes two concerns: :class:`EvidenceGenerator` emits machine-readable
facts (the recovered evidence lines persisted with the analysis), while
:class:`ExplanationGenerator` composes a single human-readable narrative. Both
are deterministic here: the shipped generators produce a full three-class
forensic report from the classified fusion result — no LLM, no external
providers. A later milestone may wire an LLM-assisted explanation behind the
same interfaces.
"""

from app.pipeline.explanation.base import EvidenceGenerator, ExplanationGenerator
from app.pipeline.explanation.classifier import (
    ClassificationEvidenceGenerator,
    ClassificationExplanationGenerator,
)
from app.pipeline.explanation.placeholder import (
    PlaceholderEvidenceGenerator,
    PlaceholderExplanationGenerator,
)

__all__ = [
    "ClassificationEvidenceGenerator",
    "ClassificationExplanationGenerator",
    "EvidenceGenerator",
    "ExplanationGenerator",
    "PlaceholderEvidenceGenerator",
    "PlaceholderExplanationGenerator",
]

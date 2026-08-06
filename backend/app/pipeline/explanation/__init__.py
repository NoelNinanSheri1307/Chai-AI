"""Explainability framework.

Distinguishes two concerns: :class:`EvidenceGenerator` emits machine-readable
facts (the recovered evidence lines persisted with the analysis), while
:class:`ExplanationGenerator` composes a single human-readable narrative. Both
are deterministic here and produce placeholder content; a later milestone wires
the LLM-assisted explanation behind the same interfaces.
"""

from app.pipeline.explanation.base import EvidenceGenerator, ExplanationGenerator
from app.pipeline.explanation.placeholder import (
    PlaceholderEvidenceGenerator,
    PlaceholderExplanationGenerator,
)

__all__ = [
    "EvidenceGenerator",
    "ExplanationGenerator",
    "PlaceholderEvidenceGenerator",
    "PlaceholderExplanationGenerator",
]

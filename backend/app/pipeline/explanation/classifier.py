"""Deterministic three-class evidence and explanation generators.

Replaces the placeholder generators with a real, deterministic explainer driven
entirely by the classified :class:`FusionResult` and configuration templates.
No LLM, no OpenRouter, no randomness: the same result always yields the same
report.

* :class:`ClassificationEvidenceGenerator` emits machine-readable evidence lines
  (facts) drawn from the winning and runner-up hypothesis, the most influential
  detectors, and the detectors that most opposed the winning class.
* :class:`ClassificationExplanationGenerator` composes the human-readable
  narrative: the classification, its confidence, the top supporting evidence,
  the top contradicting evidence, the most influential detectors, per-detector
  contribution percentages and a reasoning summary.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence

from app.core.enums import Verdict
from app.pipeline.config import PipelineConfig
from app.pipeline.explanation.base import EvidenceGenerator, ExplanationGenerator
from app.pipeline.fusion.base import DetectorContribution, FusionResult
from app.pipeline.signals import DetectorSignal

logger = logging.getLogger(__name__)

_VERDICT_LABELS = {
    Verdict.ORIGINAL: "Original",
    Verdict.AI_EDITED: "AI Edited",
    Verdict.AI_GENERATED: "AI Generated",
}


def _sort_contributions(
    contributions: list[DetectorContribution],
) -> list[DetectorContribution]:
    """Return contributions ordered by descending influence (stable)."""
    return sorted(
        contributions,
        key=lambda c: (abs(c.hypothesis_weights[1]), abs(c.normalized_score)),
        reverse=True,
    )


class ClassificationEvidenceGenerator(EvidenceGenerator):
    """Deterministic, classification-driven evidence lines."""

    def __init__(self, config: PipelineConfig) -> None:
        self._config = config

    def generate(
        self,
        fusion: FusionResult,
        signals: Sequence[DetectorSignal],
    ) -> list[str]:
        """Return the evidence lines recovered from ``fusion`` and ``signals``."""
        lines = list(fusion.evidence)
        if fusion.decision_reason:
            lines.append(fusion.decision_reason)
        # Class-aware per-detector agreement lines.
        lines.extend(self._detector_agreement_lines(fusion))
        return self._dedupe(lines)

    @staticmethod
    def _dedupe(lines: list[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for line in lines:
            text = line.strip()
            if not text or text.casefold() in seen:
                continue
            seen.add(text.casefold())
            result.append(text)
        return result

    def _detector_agreement_lines(self, fusion: FusionResult) -> list[str]:
        """Lines noting which detectors agreed with the winning hypothesis."""
        winner = _VERDICT_LABELS.get(fusion.verdict, fusion.verdict.value)
        lines: list[str] = []
        for contribution in fusion.contributions:
            template = self._config.reasoning_support_line
            lines.append(
                template.format(
                    detector=contribution.detector,
                    hypothesis_label=contribution.preferred_hypothesis or winner,
                )
            )
        return lines


class ClassificationExplanationGenerator(ExplanationGenerator):
    """Compose a deterministic, fully explainable classification report."""

    def __init__(self, config: PipelineConfig) -> None:
        self._config = config

    def explain(
        self,
        fusion: FusionResult,
        evidence: Sequence[str],
        signals: Sequence[DetectorSignal],
    ) -> str:
        """Return the narrative explanation for the given classification."""
        blocks: list[str] = []

        header = self._header(fusion)
        blocks.append(header)
        blocks.append(self._summary(fusion))
        blocks.append(self._supporting(fusion))
        blocks.append(self._contradicting(fusion))
        blocks.append(self._influential(fusion))
        blocks.append(self._percentages(fusion))
        blocks.append(self._reasoning_detail(fusion))

        return "\n\n".join(block for block in blocks if block)

    def _header(self, fusion: FusionResult) -> str:
        label = _VERDICT_LABELS.get(fusion.verdict, fusion.verdict.value)
        runner = (
            _VERDICT_LABELS.get(fusion.runner_up_verdict, "n/a")
            if fusion.runner_up_verdict
            else "n/a"
        )
        return (
            f"Classification: {label} (confidence {fusion.confidence:.0%}; "
            f"runner-up {runner}; margin {fusion.classification_margin:.0%})."
        )

    def _summary(self, fusion: FusionResult) -> str:
        return fusion.decision_reason or "No classification rationale available."

    def _supporting(self, fusion: FusionResult) -> str:
        lines = self._top_supporting(fusion)
        if not lines:
            return ""
        return "Top supporting evidence:\n- " + "\n- ".join(lines)

    def _contradicting(self, fusion: FusionResult) -> str:
        lines = self._top_contradicting(fusion)
        if not lines:
            return ""
        return "Top contradicting evidence:\n- " + "\n- ".join(lines)

    def _influential(self, fusion: FusionResult) -> str:
        names = [c.detector for c in self._most_influential(fusion)]
        if not names:
            return ""
        return "Most influential detectors: " + ", ".join(names) + "."

    def _percentages(self, fusion: FusionResult) -> str:
        row = fusion.hypothesis_scores
        return (
            "Detector contribution percentages: "
            f"{row[0]:.0%} Original, {row[1]:.0%} AI Edited, "
            f"{row[2]:.0%} AI Generated."
        )

    def _reasoning_detail(self, fusion: FusionResult) -> str:
        winner = _VERDICT_LABELS.get(fusion.verdict, fusion.verdict.value)
        lines: list[str] = []
        for contribution in fusion.contributions:
            w = contribution.hypothesis_weights
            lines.append(
                self._config.reasoning_detailed_line.format(
                    detector=contribution.detector,
                    original=max(0.0, w[0]),
                    edited=max(0.0, w[1]),
                    generated=max(0.0, w[2]),
                    original_label="Original",
                    edited_label="AI Edited",
                    generated_label="AI Generated",
                )
            )
        detail = "Per-detector reasoning:\n- " + "\n- ".join(lines)
        detail += (
            f"\nSummarized by the winning hypothesis ({winner}) and the margin "
            "between it and the runner-up."
        )
        return detail

    # ------------------------------------------------------------------
    # Selection helpers (all purely derived from the frozen fusion result)
    # ------------------------------------------------------------------
    @staticmethod
    def _top_supporting(fusion: FusionResult) -> list[str]:
        winner_probs = fusion.hypothesis_scores
        winner_index = max(range(3), key=lambda i: winner_probs[i])
        ranked = sorted(
            fusion.contributions,
            key=lambda c: c.hypothesis_weights[winner_index],
            reverse=True,
        )
        return [
            f"{c.detector} (support {c.hypothesis_weights[winner_index]:.0%})"
            for c in ranked[:3]
            if c.hypothesis_weights[winner_index] > 0.0
        ]

    @staticmethod
    def _top_contradicting(fusion: FusionResult) -> list[str]:
        winner_label = _VERDICT_LABELS.get(fusion.verdict, "")
        opposing = [
            c
            for c in fusion.contributions
            if c.preferred_hypothesis and c.preferred_hypothesis != winner_label
        ]
        ranked = sorted(
            opposing,
            key=lambda c: c.hypothesis_weights[1],
            reverse=True,
        )
        return [f"{c.detector} favoured {c.preferred_hypothesis}" for c in ranked[:3]]

    @staticmethod
    def _most_influential(fusion: FusionResult) -> list[DetectorContribution]:
        # Reliance on the fused manipulation share (largest first), bounded.
        return sorted(
            fusion.contributions,
            key=lambda c: c.contribution,
            reverse=True,
        )[:3]

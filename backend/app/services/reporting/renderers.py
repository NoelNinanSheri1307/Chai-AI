"""Deterministic report renderers.

These functions turn a typed :class:`ForensicReportDTO` into human-readable
representations (Markdown report, share text) and a JSON-safe string. They
contain no randomness, no timestamps inside reasoning text, and never include
secrets or filesystem paths.
"""

from __future__ import annotations

from app.schemas.report import ForensicReportDTO


def _percent(value: float) -> str:
    """Render a ``[0, 1]`` ratio as a whole-number percentage string."""
    return f"{int(round(max(0.0, min(1.0, value)) * 100))}%"


def _severity_capitalized(value: str | None) -> str | None:
    """Capitalize a lowercase severity label (``low`` -> ``Low``)."""
    if not value:
        return None
    return f"{value[0].upper()}{value[1:]}"


def _methodology(report: ForensicReportDTO) -> str:
    """Accurately describe the detectors and decision process actually used."""
    rows = report.detector_contributions
    if rows:
        detector_line = ", ".join(
            f"{row.detector} ({row.detector_version})" for row in rows
        )
    else:
        detector_line = "no active detectors"
    return (
        "The analysis ran the configured forensic detectors: "
        f"{detector_line}. Each detector produces a normalized manipulation "
        "score and a self-confidence on the unit interval. The deterministic "
        "fusion engine maps every detector score onto the three competing "
        "hypotheses (Original, AI Edited, AI Generated) through a fixed "
        "contribution matrix and Gaussian response curves, then ranks them and "
        "derives a confidence from the classification margin, detector "
        "agreement, winning-hypothesis separation, active-detector coverage "
        "and detector reliability. Risk is derived from the classification and "
        "confidence. Suspicious regions are localized by the detectors that "
        "report spatial evidence and are merged into a manipulation heatmap. "
        "No external models, LLMs or probabilistic sampling are involved."
    )


def render_markdown(report: ForensicReportDTO) -> str:
    """Render the complete, human-readable Markdown forensic report."""
    classification = report.classification
    sections: list[str] = [
        "# Chai AI Forensic Analysis",
        f"Analysis id: `{report.analysis_id}`",
        f"Pipeline version: `{report.pipeline_version or 'n/a'}`",
        "",
        "## Classification",
        classification.classification,
        "",
        "## Confidence",
        f"{classification.confidence_percent}% confidence "
        f"(risk level: {classification.risk})",
    ]
    if classification.margin is not None:
        sections.append(
            f"Classification margin over the runner-up: "
            f"{_percent(classification.margin)}"
        )
    sections.append("")

    sections.append("## Why this classification?")
    sections.append(classification.summary)
    sections.append("")

    sections.append("## Supporting Evidence")
    if report.supporting_evidence:
        for item in report.supporting_evidence:
            header = item.source_detector or "image-level evidence"
            sections.append(f"- **{header}**: {item.text}")
    else:
        sections.append("- None.")
    sections.append("")

    sections.append("## Contradicting Evidence")
    if report.contradicting_evidence:
        for item in report.contradicting_evidence:
            header = item.source_detector or "image-level evidence"
            sections.append(f"- **{header}**: {item.text}")
    else:
        sections.append("- None.")
    sections.append("")

    sections.append("## Detector Analysis")
    if report.detector_contributions:
        for row in report.detector_contributions:
            sections.append(
                f"- **{row.detector}** (v{row.detector_version}): "
                f"normalized score {row.normalized_score:.2f}, "
                f"contribution {_percent(row.contribution)} of fused evidence, "
                f"prefers {row.preferred_hypothesis or 'n/a'}."
            )
    else:
        sections.append("- No detector contributions were recorded.")
    sections.append("")

    sections.append("## Suspicious Regions")
    if report.heatmap is not None and report.heatmap.present:
        sections.append(report.heatmap.narrative)
        for region in report.heatmap.regions:
            severity = _severity_capitalized(region.severity)
            attribution = ", ".join(region.detectors) or "unknown detector"
            sections.append(
                f"- ({region.x:.2f}, {region.y:.2f}, "
                f"{region.width:.2f} x {region.height:.2f}) "
                f"intensity {_percent(region.intensity)}"
                f"{', ' + severity if severity else ''} "
                f"[{attribution}]: {region.label}"
            )
        sections.append(
            "Overall manipulation indicator: "
            f"{_percent(report.heatmap.overall_manipulation)}"
        )
    else:
        sections.append("No localized suspicious regions were recorded.")
    sections.append("")

    sections.append("## Image Metadata")
    metadata = report.image_metadata
    sections.append(f"Status: {metadata.status}")
    sections.append(metadata.narrative)
    for key, value in metadata.items.items():
        sections.append(f"- {key}: {value}")
    sections.append("")

    sections.append("## Processing Information")
    sections.append(f"Analysis duration: {report.processing.total_analysis_ms} ms")
    sections.append(f"Active detectors: {report.processing.active_detector_count}")
    for execution in report.processing.detector_execution:
        sections.append(f"- {execution.detector}: {execution.processing_time_ms} ms")
    sections.append(f"Pipeline version: {report.pipeline_version or 'n/a'}")
    sections.append(f"Fusion version: {report.processing.fusion_version or 'n/a'}")
    sections.append("")

    sections.append("## Methodology")
    sections.append(_methodology(report))
    sections.append("")

    return "\n".join(sections).strip() + "\n"


def render_share_text(report: ForensicReportDTO) -> str:
    """Render the concise, deterministic shareable text."""
    classification = report.classification
    lines: list[str] = [
        f"Chai AI — Verdict: {classification.classification}.",
        f"Confidence: {classification.confidence_percent}%.",
        f"Risk level: {classification.risk}.",
        classification.summary,
    ]
    major = report.supporting_evidence[:3]
    if major:
        lines.append("Evidence supporting:")
        lines.extend(f"- {item.text}" for item in major)
    minority = report.contradicting_evidence[:2]
    if minority:
        lines.append("Evidence against:")
        lines.extend(f"- {item.text}" for item in minority)
    lines.append(f"Analysis: {report.analysis_id}")
    lines.append(f"Pipeline version: {report.pipeline_version or 'n/a'}")
    return "\n".join(lines)


def report_to_json(report: ForensicReportDTO) -> str:
    """Serialize the complete report as stable, structured JSON."""
    return report.model_dump_json(indent=2)

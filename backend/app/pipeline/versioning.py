"""Pipeline versioning metadata.

Every pipeline run is version-stamped so results remain reproducible and
auditable: the framework version, the pipeline (stage) version, the fusion
engine version and the version of every detector that contributed. The
``PipelineRunVersion`` value object is attached to each ``PipelineResult`` via
its ``metadata`` map so the version trail flows through to the persisted
analysis and the API result.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ComponentVersion:
    """The version of a single pipeline component (for example a detector)."""

    name: str
    version: str

    def as_metadata(self) -> str:
        """Render as ``name@version`` for the version trail."""
        return f"{self.name}@{self.version}"


@dataclass(frozen=True)
class PipelineRunVersion:
    """Version stamp recorded for one pipeline execution."""

    framework_version: str
    pipeline_version: str
    fusion_version: str
    detector_versions: tuple[ComponentVersion, ...] = ()

    def as_metadata(self) -> dict[str, str]:
        """Return the version trail as metadata entries.

        Entries are named so they flow into ``PipelineResult.metadata`` and from
        there into the API ``AnalysisResult.metadata`` map unchanged.
        """
        entries: dict[str, str] = {
            "framework_version": self.framework_version,
            "pipeline_version": self.pipeline_version,
            "fusion_version": self.fusion_version,
        }
        if self.detector_versions:
            entries["detector_versions"] = ", ".join(
                component.as_metadata() for component in self.detector_versions
            )
        return entries

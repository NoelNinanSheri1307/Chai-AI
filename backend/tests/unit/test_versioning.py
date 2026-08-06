"""Tests for the pipeline versioning framework."""

from __future__ import annotations

from app.pipeline.config import PipelineConfig
from app.pipeline.runner import ModularAnalysisPipeline
from app.pipeline.versioning import ComponentVersion, PipelineRunVersion
from tests.sample_images import JPEG_BYTES


def test_component_version_renders_metadata() -> None:
    component = ComponentVersion(name="noise", version="1.2.0")
    assert component.as_metadata() == "noise@1.2.0"


def test_run_version_builds_metadata_map() -> None:
    version = PipelineRunVersion(
        framework_version="0.1.0",
        pipeline_version="1.0",
        fusion_version="0.1.0",
        detector_versions=(ComponentVersion("noise", "1.0.0"),),
    )
    metadata = version.as_metadata()
    assert metadata["framework_version"] == "0.1.0"
    assert metadata["pipeline_version"] == "1.0"
    assert metadata["fusion_version"] == "0.1.0"
    assert metadata["detector_versions"] == "noise@1.0.0"


def test_version_info_reflects_configured_pipeline(
    pipeline: ModularAnalysisPipeline,
    pipeline_config: PipelineConfig,
) -> None:
    info = pipeline.version_info
    assert info.pipeline_version == pipeline_config.pipeline_version
    assert info.framework_version == pipeline_config.framework_version
    assert info.fusion_version == pipeline_config.fusion_version
    assert len(info.detector_versions) == len(pipeline_config.enabled_detector_names())


def test_version_trail_flows_into_result_metadata(
    pipeline: ModularAnalysisPipeline,
    pipeline_config: PipelineConfig,
) -> None:
    result = pipeline.analyze(JPEG_BYTES, content_type="image/jpeg")
    assert result.metadata["pipeline_version"] == pipeline_config.pipeline_version
    assert result.metadata["framework_version"] == pipeline_config.framework_version
    assert result.metadata["fusion_version"] == pipeline_config.fusion_version
    assert "metadata@0.1.0" in result.metadata["detector_versions"]

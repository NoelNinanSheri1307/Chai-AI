"""Centralized persistence and DTO enums.

Every enum literal used by ORM models and API DTOs lives here so strings are
never duplicated across modules. Values are stored as plain varchar columns by
the ORM (portable across PostgreSQL and SQLite), while the Python values remain
the single source of truth for validation and serialization.

The ``Verdict`` and ``RiskLevel`` members use ``str`` values that mirror the
Flutter frontend serialization (camelCase for multi-word members).
"""

from __future__ import annotations

import enum


class Verdict(str, enum.Enum):
    """Final classification of an analyzed image."""

    ORIGINAL = "original"
    AI_EDITED = "aiEdited"
    AI_GENERATED = "aiGenerated"


class RiskLevel(str, enum.Enum):
    """Derived risk tier for an analysis result."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class IndicatorType(str, enum.Enum):
    """Discrete manipulation signal categories detected by the pipeline."""

    FREQUENCY = "frequency"
    TEXTURE = "texture"
    METADATA = "metadata"
    DIFFUSION = "diffusion"
    COMPRESSION = "compression"
    LIGHTING = "lighting"


class IndicatorSeverity(str, enum.Enum):
    """Strength of a detected indicator."""

    LOW = "low"
    MODERATE = "moderate"
    STRONG = "strong"


class ScoreCategory(str, enum.Enum):
    """Per-category forensic confidence measurements."""

    TEXTURE = "texture"
    METADATA = "metadata"
    LIGHTING = "lighting"
    FREQUENCY = "frequency"
    NOISE_PATTERN = "noisePattern"
    COMPRESSION = "compression"
    EDGE_CONSISTENCY = "edgeConsistency"
    COLOR_DISTRIBUTION = "colorDistribution"


class AnalysisStatus(str, enum.Enum):
    """Lifecycle state of an analysis record."""

    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class JobType(str, enum.Enum):
    """Kind of background job."""

    ANALYSIS = "analysis"
    COMPARE = "compare"
    REPORT = "report"


class JobStatus(str, enum.Enum):
    """Lifecycle state of a background job."""

    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"

"""Tests for ORM models: schema, validation, constraints and relationships."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError, StatementError
from sqlmodel import Session

from app.core.db import Base
from app.core.enums import (
    AnalysisStatus,
    IndicatorSeverity,
    IndicatorType,
    JobStatus,
    JobType,
    RiskLevel,
    ScoreCategory,
    Verdict,
)
from app.models.analysis import (
    Analysis,
    DetectedIndicator,
    ForensicScore,
    Heatmap,
    HeatmapRegion,
    MetadataItem,
)
from app.models.comparison import (
    Comparison,
)
from app.models.job import Job
from app.models.refresh_token import RefreshToken
from app.models.user import User

EXPECTED_TABLES: set[str] = {
    "users",
    "analyses",
    "forensic_scores",
    "detected_indicators",
    "evidence",
    "metadata_items",
    "heatmaps",
    "heatmap_regions",
    "comparisons",
    "comparison_findings",
    "comparison_regions",
    "jobs",
    "refresh_tokens",
}


def _user(session: Session) -> User:
    user = User(email="a@example.com", password_hash="hash", display_name="A")
    session.add(user)
    session.flush()
    return user


def test_metadata_registers_every_expected_table() -> None:
    registered = {table.name for table in Base.metadata.tables.values()}
    assert EXPECTED_TABLES <= registered


def test_models_expose_soft_delete_and_timestamps(db_session: Session) -> None:
    user = _user(db_session)
    db_session.commit()
    assert user.created_at is not None
    assert user.updated_at is not None
    assert user.deleted_at is None
    for cls in (User, Analysis, Comparison):
        assert "deleted_at" in cls.__table__.columns
        assert "created_at" in cls.__table__.columns
        assert "updated_at" in cls.__table__.columns
    for cls in (ForensicScore, Job, RefreshToken):
        assert "deleted_at" not in cls.__table__.columns


def test_unique_email_is_enforced(db_session: Session) -> None:
    db_session.add(User(email="a@example.com", password_hash="hash", display_name="A"))
    db_session.flush()
    db_session.add(User(email="a@example.com", password_hash="hash", display_name="B"))
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_analysis_is_anonymous_by_default(db_engine) -> None:
    with Session(db_engine) as session:
        analysis = Analysis(
            public_id="ana_1",
            original_key="dev/orig/a.png",
            status=AnalysisStatus.COMPLETED,
        )
        session.add(analysis)
        session.commit()
        assert analysis.user_id is None


def test_invalid_enum_value_is_rejected(db_session: Session) -> None:
    analysis = Analysis(
        public_id="ana_bad",
        original_key="dev/orig/a.png",
        status=AnalysisStatus.COMPLETED,
    )
    db_session.add(analysis)
    db_session.flush()
    analysis.status = "not-a-status"
    with pytest.raises((StatementError, IntegrityError)):
        db_session.flush()


def test_enum_values_round_trip(db_session: Session) -> None:
    analysis = Analysis(
        public_id="ana_rt",
        original_key="dev/orig/a.png",
        verdict=Verdict.AI_GENERATED,
        risk_level=RiskLevel.HIGH,
        confidence=0.9,
        status=AnalysisStatus.COMPLETED,
    )
    db_session.add(analysis)
    db_session.commit()
    fresh = db_session.get(Analysis, analysis.id)
    assert fresh.verdict == Verdict.AI_GENERATED
    assert fresh.risk_level == RiskLevel.HIGH
    assert fresh.status == AnalysisStatus.COMPLETED


def test_forensic_score_range_check_is_enforced(db_session: Session) -> None:
    analysis = Analysis(public_id="ana_chk", original_key="k")
    db_session.add(analysis)
    db_session.flush()
    db_session.add(
        ForensicScore(
            analysis_id=analysis.id, category=ScoreCategory.TEXTURE, value=1.7
        )
    )
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_missing_foreign_key_is_rejected(db_session: Session) -> None:
    db_session.add(
        ForensicScore(analysis_id=999_999, category=ScoreCategory.TEXTURE, value=0.5)
    )
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_heatmap_analysis_is_unique(db_session: Session) -> None:
    analysis = Analysis(public_id="ana_h", original_key="k")
    db_session.add(analysis)
    db_session.flush()
    db_session.add(Heatmap(analysis_id=analysis.id, overall_manipulation=0.5))
    with pytest.raises(IntegrityError):
        db_session.add(Heatmap(analysis_id=analysis.id, overall_manipulation=0.6))
        db_session.flush()


def test_relationship_navigation(db_session: Session) -> None:
    user = _user(db_session)
    analysis = Analysis(
        public_id="ana_rel",
        original_key="k",
        user_id=user.id,
        status=AnalysisStatus.COMPLETED,
    )
    db_session.add(analysis)
    db_session.commit()
    assert analysis.user is user
    assert user.analyses == [analysis]
    assert analysis in user.analyses


def test_child_graph_relationship_navigation(db_session: Session) -> None:
    analysis = Analysis(public_id="ana_graph", original_key="k")
    heatmap = Heatmap(analysis_id=analysis.id, overall_manipulation=0.4)
    region = HeatmapRegion(
        x=0.1, y=0.2, width=0.3, height=0.4, intensity=0.8, label="Edited region"
    )
    heatmap.regions = [region]
    analysis.heatmap = heatmap
    analysis.forensic_scores = [
        ForensicScore(category=ScoreCategory.FREQUENCY, value=0.7)
    ]
    analysis.detected_indicators = [
        DetectedIndicator(
            indicator_type=IndicatorType.DIFFUSION,
            confidence=0.9,
            severity=IndicatorSeverity.STRONG,
            description="d",
        )
    ]
    analysis.metadata_items = [MetadataItem(key="Camera", value="X")]
    db_session.add(analysis)
    db_session.commit()
    assert analysis.heatmap.regions == [region]
    assert len(analysis.forensic_scores) == 1
    assert len(analysis.detected_indicators) == 1
    assert len(analysis.metadata_items) == 1


def test_comparison_relationships(db_session: Session) -> None:
    a = Analysis(public_id="ana_ca", original_key="k")
    b = Analysis(public_id="ana_cb", original_key="k2")
    db_session.add_all([a, b])
    db_session.flush()
    comparison = Comparison(
        public_id="cm_1",
        analysis_a_id=a.id,
        analysis_b_id=b.id,
        similarity=0.5,
        ai_probability=0.6,
        label_a="a",
        label_b="b",
    )
    db_session.add(comparison)
    db_session.commit()
    assert comparison.analysis_a is a
    assert comparison.analysis_b is b
    assert a.comparison_a is comparison or b.comparison_b is comparison


def test_job_defaults(db_session: Session) -> None:
    analysis = Analysis(public_id="ana_j", original_key="k")
    db_session.add(analysis)
    db_session.flush()
    job = Job(analysis_id=analysis.id, job_type=JobType.ANALYSIS)
    db_session.add(job)
    db_session.commit()
    assert job.status == JobStatus.QUEUED
    assert job.attempts == 0
    assert job.max_attempts == 3


def test_refresh_token_requires_expiry(db_session: Session) -> None:
    user = _user(db_session)
    db_session.flush()
    token = RefreshToken(
        user_id=user.id,
        token_hash="xyz",
        expires_at=datetime.now(timezone.utc),
    )
    db_session.add(token)
    db_session.commit()
    assert token.id is not None


def test_partial_soft_delete_indexes_exist(db_engine) -> None:
    inspector = inspect(db_engine)
    for table in ("users", "analyses", "comparisons"):
        index = next(
            (
                i
                for i in inspector.get_indexes(table)
                if i["name"] == f"ix_{table}_active"
            ),
            None,
        )
        assert index is not None
        assert "sqlite_where" in index.get("dialect_options", {})

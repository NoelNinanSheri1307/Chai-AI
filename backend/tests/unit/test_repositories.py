"""Tests for the repository layer: CRUD, pagination, filters, transactions."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from app.core.enums import (
    AnalysisStatus,
    JobStatus,
    JobType,
    RiskLevel,
    ScoreCategory,
    Verdict,
)
from app.models.analysis import (
    Analysis,
    Evidence,
    ForensicScore,
    Heatmap,
    MetadataItem,
)
from app.models.comparison import Comparison
from app.models.job import Job
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.repos import (
    AnalysisRepository,
    ComparisonRepository,
    HistoryRepository,
    JobRepository,
    PageParams,
    TokenRepository,
    UserRepository,
)


def _user(db_session: Session, email: str = "u@example.com") -> User:
    return UserRepository(db_session).create_user(
        email=email,
        password_hash="hash",
        display_name="User",
    )


def _analysis(
    db_session: Session,
    public_id: str = "ana_1",
    user_id: int | None = None,
    status: AnalysisStatus = AnalysisStatus.COMPLETED,
) -> Analysis:
    analysis = Analysis(
        public_id=public_id,
        user_id=user_id,
        original_key=f"dev/orig/{public_id}.png",
        status=status,
    )
    AnalysisRepository(db_session).create(analysis)
    return analysis


# ---------------------------------------------------------------------------
# BaseRepository
# ---------------------------------------------------------------------------


def test_base_create_get_exists_update_delete(db_session: Session) -> None:
    repo = UserRepository(db_session)
    user = repo.create(User(email="x@example.com", password_hash="h", display_name="X"))
    assert user.id is not None
    assert repo.exists(user.id)
    assert repo.get(user.id) is user

    user.display_name = "Renamed"
    updated = repo.update(user)
    assert repo.get(user.id).display_name == "Renamed"
    assert updated.id == user.id

    repo.delete(user.id)
    assert not repo.exists(user.id, include_deleted=True)


def test_base_create_many(db_session: Session) -> None:
    repo = UserRepository(db_session)
    users = repo.create_many(
        User(email=f"u{i}@example.com", password_hash="h", display_name=f"U{i}")
        for i in range(3)
    )
    assert len(users) == 3
    assert repo.count(filters={"display_name": "U0"}) == 1


def test_base_list_pagination(db_session: Session) -> None:
    repo = UserRepository(db_session)
    repo.create_many(
        User(email=f"p{i}@example.com", password_hash="h", display_name=f"P{i}")
        for i in range(10)
    )
    page = repo.list(page=PageParams(limit=3, offset=0, sort="+id"))
    assert len(page.items) == 3
    assert page.total == 10
    assert page.has_more is True
    assert [u.id for u in page.items] == [1, 2, 3]

    last = repo.list(page=PageParams(limit=5, offset=5, sort="+id"))
    assert [u.id for u in last.items] == [6, 7, 8, 9, 10]
    assert last.has_more is False


def test_base_list_filtering(db_session: Session) -> None:
    repo = UserRepository(db_session)
    repo.create_many(
        User(email=f"f{i}@example.com", password_hash="h", display_name=f"F{i}")
        for i in range(5)
    )
    page = repo.list(filters={"display_name": "F2"})
    assert page.total == 1
    assert page.items[0].email == "f2@example.com"


def test_base_list_sorting(db_session: Session) -> None:
    repo = UserRepository(db_session)
    repo.create_many(
        User(email=f"s{i}@example.com", password_hash="h", display_name=f"S{i}")
        for i in range(3)
    )
    asc = [u.id for u in repo.list(page=PageParams(sort="+id")).items]
    desc = [u.id for u in repo.list(page=PageParams(sort="-id")).items]
    assert asc == [1, 2, 3]
    assert desc == [3, 2, 1]


def test_base_list_rejects_unknown_sort_column(db_session: Session) -> None:
    repo = UserRepository(db_session)
    with pytest.raises(ValueError):
        repo.list(page=PageParams(sort="-no_such_column"))


def test_base_soft_delete(db_session: Session) -> None:
    repo = UserRepository(db_session)
    user = repo.create_user(
        email="sd@example.com", password_hash="h", display_name="SD"
    )
    assert repo.soft_delete(user.id) is True
    assert repo.get(user.id) is None
    assert repo.get(user.id, include_deleted=True) is not None
    assert repo.soft_delete(user.id) is False


def test_base_count_excludes_deleted(db_session: Session) -> None:
    repo = UserRepository(db_session)
    first = repo.create_user(email="c@example.com", password_hash="h", display_name="C")
    repo.create_user(email="c2@example.com", password_hash="h", display_name="C")
    repo.soft_delete(first.id)
    assert repo.count() == 1
    assert repo.count(include_deleted=True) == 2


def test_transaction_commits_on_success(db_session: Session) -> None:
    repo = UserRepository(db_session)
    with repo.transaction():
        repo.create_user(email="t1@example.com", password_hash="h", display_name="T")
        repo.create_user(email="t2@example.com", password_hash="h", display_name="T")
    assert repo.count() == 2


def test_transaction_rolls_back_on_error(db_session: Session) -> None:
    repo = UserRepository(db_session)
    with pytest.raises(RuntimeError):
        with repo.transaction():
            repo.create_user(email="t@example.com", password_hash="h", display_name="T")
            raise RuntimeError("boom")
    assert repo.count() == 0


def test_soft_delete_not_supported_on_hard_only_model(db_session: Session) -> None:
    repo = JobRepository(db_session)
    with pytest.raises(TypeError):
        repo.soft_delete(1)


# ---------------------------------------------------------------------------
# UserRepository
# ---------------------------------------------------------------------------


def test_create_user_normalizes_email(db_session: Session) -> None:
    repo = UserRepository(db_session)
    user = repo.create_user(
        email="  MiXeD@EXAMPLE.com ",
        password_hash="h",
        display_name="Mix",
    )
    assert user.email == "mixed@example.com"


def test_get_by_email_is_case_insensitive(db_session: Session) -> None:
    repo = UserRepository(db_session)
    repo.create_user(email="Look@Example.com", password_hash="h", display_name="L")
    assert repo.get_by_email("lOOK@example.COM") is not None
    assert repo.get_by_email("missing@example.com") is None
    assert repo.email_exists("look@example.com") is True


# ---------------------------------------------------------------------------
# AnalysisRepository
# ---------------------------------------------------------------------------


def test_analysis_get_by_public_id(db_session: Session) -> None:
    repo = AnalysisRepository(db_session)
    analysis = _analysis(db_session, public_id="ana_pk")
    assert repo.get_by_public_id("ana_pk") is analysis
    assert repo.public_id_exists("ana_pk") is True
    assert repo.get_by_public_id("nope") is None


def test_analysis_list_for_user(db_session: Session) -> None:
    user = _user(db_session, email="anaowner@example.com")
    db_session.commit()
    repo = AnalysisRepository(db_session)
    for i in range(4):
        _analysis(db_session, public_id=f"ana_u{i}", user_id=user.id)
    page = repo.list_for_user(user.id, page=PageParams(sort="+public_id"))
    assert page.total == 4
    assert {a.public_id for a in page.items} == {f"ana_u{i}" for i in range(4)}


def test_metadata_key_uniqueness_helper(db_session: Session) -> None:
    repo = AnalysisRepository(db_session)
    analysis = _analysis(db_session, "ana_md")
    assert repo.metadata_key_exists(analysis.id, "Camera") is False
    analysis.metadata_items = [MetadataItem(key="Camera", value="X")]
    db_session.commit()
    assert repo.metadata_key_exists(analysis.id, "Camera") is True


# ---------------------------------------------------------------------------
# HistoryRepository
# ---------------------------------------------------------------------------


def test_history_list_filters(db_session: Session) -> None:
    user = _user(db_session, email="hist@example.com")
    db_session.commit()
    history = HistoryRepository(db_session)
    gen = Analysis(
        public_id="ana_gen",
        user_id=user.id,
        original_key="k",
        verdict=Verdict.AI_GENERATED,
        risk_level=RiskLevel.HIGH,
        status=AnalysisStatus.COMPLETED,
    )
    run = Analysis(
        public_id="ana_run",
        user_id=user.id,
        original_key="k",
        status=AnalysisStatus.RUNNING,
    )
    db_session.add_all([gen, run])
    db_session.commit()

    assert history.count_for_user(user.id) == 2
    assert history.list_for_user(user.id).total == 2
    assert history.list_for_user(user.id, verdict=Verdict.AI_GENERATED).total == 1
    assert history.list_for_user(user.id, risk_level=RiskLevel.HIGH).total == 1
    assert history.list_for_user(user.id, status=AnalysisStatus.RUNNING).total == 1


def test_history_get_and_soft_delete_for_user(db_session: Session) -> None:
    user = _user(db_session, email="h@example.com")
    db_session.commit()
    history = HistoryRepository(db_session)
    analysis = _analysis(db_session, "ana_hd", user_id=user.id)
    assert history.get_for_user(user.id, "ana_hd") is analysis
    assert history.get_for_user(user.id, "other") is None

    assert history.soft_delete_for_user(user.id, "ana_hd") is True
    assert history.soft_delete_for_user(user.id, "ana_hd") is False
    assert history.get_for_user(user.id, "ana_hd") is None
    assert history.count_for_user(user.id) == 0


def test_history_clear_for_user(db_session: Session) -> None:
    user = _user(db_session, email="clear@example.com")
    db_session.commit()
    history = HistoryRepository(db_session)
    for i in range(3):
        _analysis(db_session, f"ana_c{i}", user_id=user.id)
    cleared = history.clear_for_user(user.id)
    assert cleared == 3
    assert history.count_for_user(user.id) == 0
    assert history.count_for_user(user.id) == 0


# ---------------------------------------------------------------------------
# ComparisonRepository
# ---------------------------------------------------------------------------


def test_comparison_repository_round_trip(db_session: Session) -> None:
    user = _user(db_session, email="cmp@example.com")
    a = _analysis(db_session, "ana_ca")
    b = _analysis(db_session, "ana_cb")
    db_session.commit()
    repo = ComparisonRepository(db_session)
    comparison = Comparison(
        public_id="cm_1",
        user_id=user.id,
        analysis_a_id=a.id,
        analysis_b_id=b.id,
        similarity=0.3,
        ai_probability=0.8,
        label_a="a",
        label_b="b",
    )
    repo.create(comparison)
    db_session.commit()
    assert repo.get_by_public_id("cm_1") is comparison
    assert repo.public_id_exists("cm_1") is True
    assert repo.list_for_user(user.id).total == 1
    assert repo.get_for_user(user.id, "cm_1") is comparison


# ---------------------------------------------------------------------------
# JobRepository
# ---------------------------------------------------------------------------


def test_job_repository_queries_and_retries(db_session: Session) -> None:
    repo = JobRepository(db_session)
    analysis = _analysis(db_session, "ana_job")
    db_session.commit()
    job = Job(analysis_id=analysis.id, job_type=JobType.ANALYSIS)
    repo.create(job)
    db_session.commit()

    assert repo.list_for_analysis(analysis.id) == [job]
    assert repo.latest_for_analysis(analysis.id) is job
    assert repo.list_queued() == [job]
    assert repo.list_by_status(JobStatus.QUEUED, limit=5) == [job]

    repo.increment_attempts(job)
    repo.set_status(job, JobStatus.RUNNING)
    db_session.commit()
    assert job.attempts == 1
    assert job.status == JobStatus.RUNNING
    assert repo.list_by_status(JobStatus.QUEUED, limit=5) == []


# ---------------------------------------------------------------------------
# TokenRepository
# ---------------------------------------------------------------------------


def test_token_repository_lifecycle(db_session: Session) -> None:
    repo = TokenRepository(db_session)
    user = _user(db_session, email="tok@example.com")
    db_session.commit()
    token = RefreshToken(
        user_id=user.id,
        token_hash="abcdef",
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )
    repo.create(token)
    db_session.commit()

    assert repo.get_by_token_hash("abcdef") is token
    assert repo.list_active_for_user(user.id) == [token]

    repo.revoke(token, replaced_by_hash="newhash")
    db_session.commit()
    assert token.revoked_at is not None
    assert token.replaced_by_hash == "newhash"
    assert repo.get_by_token_hash("abcdef") is token
    assert repo.get_by_token_hash("abcdef", include_revoked=False) is None
    assert repo.list_active_for_user(user.id) == []


def test_token_revoke_all_for_user(db_session: Session) -> None:
    repo = TokenRepository(db_session)
    user = _user(db_session, email="tok2@example.com")
    db_session.commit()
    repo.create_many(
        RefreshToken(
            user_id=user.id,
            token_hash=f"hash{i}",
            expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        )
        for i in range(3)
    )
    db_session.commit()
    assert repo.revoke_all_for_user(user.id) == 3
    assert repo.list_active_for_user(user.id) == []


# ---------------------------------------------------------------------------
# Cascade delete
# ---------------------------------------------------------------------------


def test_cascade_delete_removes_children(db_session: Session) -> None:
    analysis = Analysis(public_id="ana_cas", original_key="k")
    analysis.forensic_scores = [
        ForensicScore(category=ScoreCategory.TEXTURE, value=0.5)
    ]
    analysis.evidence = [Evidence(text="line", position=0)]
    analysis.metadata_items = [MetadataItem(key="K", value="V")]
    analysis.heatmap = Heatmap(overall_manipulation=0.2)
    db_session.add(analysis)
    db_session.commit()
    analysis_id = analysis.id

    AnalysisRepository(db_session).delete(analysis_id)
    db_session.commit()
    assert db_session.get(Analysis, analysis_id) is None
    assert (
        db_session.scalars(
            select(ForensicScore).where(ForensicScore.analysis_id == analysis_id)
        ).first()
        is None
    )
    assert (
        db_session.scalars(
            select(Evidence).where(Evidence.analysis_id == analysis_id)
        ).first()
        is None
    )
    assert (
        db_session.scalars(
            select(MetadataItem).where(MetadataItem.analysis_id == analysis_id)
        ).first()
        is None
    )
    assert (
        db_session.scalars(
            select(Heatmap).where(Heatmap.analysis_id == analysis_id)
        ).first()
        is None
    )


def test_unique_email_violation_is_integrity_error(db_session: Session) -> None:
    repo = UserRepository(db_session)
    repo.create_user(email="dup@example.com", password_hash="h", display_name="D")
    db_session.commit()
    with pytest.raises(IntegrityError):
        repo.create_user(email="dup@example.com", password_hash="h", display_name="D")
        db_session.commit()

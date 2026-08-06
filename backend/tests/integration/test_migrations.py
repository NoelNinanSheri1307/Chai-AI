"""Integration tests: Alembic migration smoke tests against a clean database."""

from __future__ import annotations

from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from alembic import command

BACKEND_DIR = Path(__file__).resolve().parents[2]

EXPECTED_TABLES: list[str] = [
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
]


@pytest.fixture()
def alembic_config(tmp_path: Path) -> Config:
    """An Alembic config pointed at a fresh file-backed SQLite database."""
    database_path = tmp_path / "migration.db"
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{database_path}")
    config.attributes["database_path"] = database_path
    return config


def _db_engine(config: Config):
    return create_engine(config.get_main_option("sqlalchemy.url"))


def test_clean_database_has_no_tables(alembic_config: Config) -> None:
    with _db_engine(alembic_config).connect() as connection:
        assert inspect(connection).get_table_names() == []


def test_upgrade_head_creates_full_schema(alembic_config: Config) -> None:
    command.upgrade(alembic_config, "head")
    with _db_engine(alembic_config).connect() as connection:
        inspector = inspect(connection)
        table_names = set(inspector.get_table_names())
        assert set(EXPECTED_TABLES) <= table_names

        # Spot-check representative columns.
        analysis_columns = {c["name"] for c in inspector.get_columns("analyses")}
        assert {
            "public_id",
            "user_id",
            "original_key",
            "verdict",
            "confidence",
            "risk_level",
            "status",
            "created_at",
            "deleted_at",
        } <= analysis_columns

        # Unique constraints enforced as unique indexes.
        user_indexes = {i["name"] for i in inspector.get_indexes("users")}
        assert "ix_users_email" in user_indexes
        analysis_indexes = {i["name"] for i in inspector.get_indexes("analyses")}
        assert "ix_analyses_public_id" in analysis_indexes

        # Partial soft-delete indexes carry a WHERE clause.
        users_active = next(
            i for i in inspector.get_indexes("users") if i["name"] == "ix_users_active"
        )
        assert "sqlite_where" in users_active.get("dialect_options", {})

        # Check constraints are present.
        checks = {c["name"] for c in inspector.get_check_constraints("forensic_scores")}
        assert "ck_forensic_scores_value" in checks
        job_checks = {c["name"] for c in inspector.get_check_constraints("jobs")}
        assert "ck_jobs_attempts" in job_checks

        # Foreign keys reference the expected tables.
        analysis_fks = {
            fk["referred_table"] for fk in inspector.get_foreign_keys("analyses")
        }
        assert analysis_fks == {"users"}
        comparison_fks = {
            fk["referred_table"] for fk in inspector.get_foreign_keys("comparisons")
        }
        assert comparison_fks == {"users", "analyses"}


def test_schema_matches_orm_metadata(alembic_config: Config) -> None:
    """The migrated schema and the ORM metadata describe the same tables."""
    import app.models  # noqa: F401  (register models on Base.metadata)
    from app.core.db import Base

    command.upgrade(alembic_config, "head")
    with _db_engine(alembic_config).connect() as connection:
        migrated = set(inspect(connection).get_table_names())
        modeled = {table.name for table in Base.metadata.tables.values()}
        assert modeled <= migrated


def test_downgrade_base_removes_all_tables(alembic_config: Config) -> None:
    command.upgrade(alembic_config, "head")
    command.downgrade(alembic_config, "base")
    with _db_engine(alembic_config).connect() as connection:
        # Alembic keeps its own version table after a full downgrade.
        assert inspect(connection).get_table_names() == ["alembic_version"]


def test_migrated_schema_supports_inserts(alembic_config: Config) -> None:
    from sqlmodel import Session

    from app.models.user import User

    command.upgrade(alembic_config, "head")
    engine = _db_engine(alembic_config)
    with Session(engine) as session:
        user = User(email="migrated@example.com", password_hash="h", display_name="M")
        session.add(user)
        session.commit()
        assert user.id is not None
        assert session.get(User, user.id) is not None

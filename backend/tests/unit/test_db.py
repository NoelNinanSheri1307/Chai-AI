"""Tests for database infrastructure: engines, sessions, and lifecycle."""

from __future__ import annotations

import pytest
from sqlalchemy import Engine, inspect
from sqlalchemy.pool import StaticPool

from app.core.config import Settings
from app.core.db import (
    Database,
    create_all_and_init,
    create_db_engine,
    create_session_factory,
    get_database,
    get_session,
)
from app.models.user import User


def test_in_memory_sqlite_uses_static_pool() -> None:
    engine = create_db_engine(Settings(environment="testing", database_url="sqlite://"))
    assert isinstance(engine.pool, StaticPool)


def test_file_sqlite_uses_pre_ping_not_static_pool(tmp_path) -> None:
    url = f"sqlite:///{tmp_path / 'db.sqlite'}"
    engine = create_db_engine(Settings(environment="testing", database_url=url))
    assert engine.pool._pre_ping is True
    assert not isinstance(engine.pool, StaticPool)


def test_postgres_url_uses_configured_pool_size() -> None:
    settings = Settings(
        environment="production",
        database_url="postgresql+psycopg://u:p@localhost:5432/chai",
        database_pool_size=3,
        database_max_overflow=7,
    )
    engine = create_db_engine(settings)
    assert engine.pool._pre_ping is True
    assert engine.pool.size() == 3
    assert engine.pool._max_overflow == 7


def test_create_session_factory_yields_working_session(db_engine: Engine) -> None:
    factory = create_session_factory(db_engine)
    with factory() as session:
        user = User(email="a@example.com", password_hash="h", display_name="A")
        session.add(user)
        session.commit()
        assert user.id is not None


def test_database_create_all_and_drop_all() -> None:
    database = Database(Settings(environment="testing", database_url="sqlite://"))
    database.create_all()
    assert set(inspect(database.engine).get_table_names()) >= {"users", "analyses"}
    database.drop_all()
    assert "users" not in inspect(database.engine).get_table_names()


def test_get_database_is_cached_per_configuration() -> None:
    settings = Settings(environment="testing", database_url="sqlite://")
    assert get_database(settings) is get_database(settings)


def test_get_database_differs_for_distinct_configuration() -> None:
    a = get_database(Settings(environment="testing", database_url="sqlite://"))
    b = get_database(
        Settings(environment="testing", database_url="sqlite://", database_pool_size=2)
    )
    assert a is not b


def test_get_session_yields_and_commits() -> None:
    from sqlalchemy import select

    settings = Settings(environment="testing", database_url="sqlite://")
    database = get_database(settings)
    database.create_all()
    generator = get_session(settings)
    session = next(generator)
    session.add(User(email="di@example.com", password_hash="h", display_name="DI"))
    with pytest.raises(StopIteration):
        next(generator)  # resumes the generator, which commits on success
    with database.session() as check:
        assert (
            check.scalars(select(User).where(User.email == "di@example.com")).first()
            is not None
        )


def test_get_session_rolls_back_on_error() -> None:
    from sqlalchemy import select

    settings = Settings(environment="testing", database_url="sqlite://")
    database = get_database(settings)
    database.create_all()
    generator = get_session(settings)
    session = next(generator)
    session.add(User(email="rb@example.com", password_hash="h", display_name="RB"))
    with pytest.raises(RuntimeError):
        generator.throw(RuntimeError("boom"))
    with database.session() as check:
        assert check.scalars(select(User)).first() is None


def test_session_scope_commits_on_success() -> None:
    database = Database(Settings(environment="testing", database_url="sqlite://"))
    database.create_all()
    with database.session_scope() as session:
        session.add(User(email="sc@example.com", password_hash="h", display_name="SC"))
    with database.session() as check:
        assert check.get(User, 1) is not None


def test_create_all_and_init_returns_session() -> None:
    settings = Settings(environment="testing", database_url="sqlite://")
    session = create_all_and_init(settings)
    try:
        session.add(
            User(email="cai@example.com", password_hash="h", display_name="CAI")
        )
        session.commit()
        assert session.get(User, 1) is not None
    finally:
        session.close()

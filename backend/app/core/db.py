"""Database infrastructure: engine, sessions, and the declarative base.

This module is the only place that creates engines. It is fully
configuration-driven: the resolved URL and pool sizing come from
:class:`Settings` for the active environment (PostgreSQL in production, SQLite
for development and testing).

A cached :class:`Database` owns one engine and session factory per distinct
configuration, so dependency injection reuses the same connection pool across
requests instead of constructing a new engine every time. The rest of the
application consumes sessions through the :func:`get_session` dependency.
"""

from __future__ import annotations

from collections.abc import Generator, Iterator
from contextlib import contextmanager
from functools import lru_cache
from typing import Any

from sqlalchemy import Engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.core.config import Settings

#: Shared SQLModel metadata. All ORM models register on this metadata so that
#: Alembic can build migrations and ``create_all`` can be used in tests.
Base = SQLModel


def _engine_kwargs(url: str, settings: Settings) -> dict[str, Any]:
    """Sensible per-dialect engine arguments derived from the URL.

    In-memory SQLite needs a single shared :class:`StaticPool` connection so
    that every session observes the same in-memory database instance.
    Server-backed databases (PostgreSQL) get a configured pool plus a
    ``pre_ping`` check that evicts stale pooled connections.
    """
    parsed = make_url(url)
    kwargs: dict[str, Any] = {}
    if parsed.get_backend_name() in {"sqlite", "sqlite+pysqlite"}:
        kwargs["connect_args"] = {"check_same_thread": False}
        if (
            parsed.database is None
            or parsed.database == ""
            or ":memory:" in parsed.database
        ):
            kwargs["poolclass"] = StaticPool
        else:
            kwargs["pool_pre_ping"] = True
    else:
        kwargs["pool_pre_ping"] = True
        kwargs["pool_size"] = settings.database_pool_size
        kwargs["max_overflow"] = settings.database_max_overflow
    return kwargs


def create_db_engine(settings: Settings) -> Engine:
    """Create an SQLAlchemy :class:`Engine` for the resolved database URL.

    ``settings`` supplies the URL and (for server-backed databases) the
    connection-pool sizing.
    """
    url = settings.effective_database_url
    return create_engine(url, **_engine_kwargs(url, settings))


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Return a SQLModel ``sessionmaker`` bound to ``engine``.

    ``autocommit`` and ``autoflush`` are disabled so callers control when
    writes reach the database.
    """
    return sessionmaker(bind=engine, class_=Session, autocommit=False, autoflush=False)


class Database:
    """Lazily owns an engine and its session factory for one configuration.

    Instantiate through :func:`get_database`, which caches one instance per
    distinct configuration so the connection pool is shared across the
    application.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._engine: Engine | None = None
        self._session_factory: sessionmaker[Session] | None = None

    @property
    def engine(self) -> Engine:
        """The configured engine, created once on first access."""
        if self._engine is None:
            self._engine = create_db_engine(self._settings)
        return self._engine

    @property
    def session_factory(self) -> sessionmaker[Session]:
        """The session factory bound to the owned engine."""
        if self._session_factory is None:
            self._session_factory = create_session_factory(self.engine)
        return self._session_factory

    def session(self) -> Session:
        """Open a new :class:`Session` from the owned factory."""
        return self.session_factory()

    def create_all(self) -> None:
        """Create every registered table on the owned engine.

        Intended for isolated tests and throwaway local runs only; production
        schema is managed exclusively by Alembic migrations.
        """
        Base.metadata.create_all(self.engine)

    def drop_all(self) -> None:
        """Drop every registered table on the owned engine (tests only)."""
        Base.metadata.drop_all(self.engine)

    def dispose(self) -> None:
        """Dispose the engine's connection pool, if an engine was created."""
        if self._engine is not None:
            self._engine.dispose()

    @contextmanager
    def session_scope(self) -> Iterator[Session]:
        """Yield a session that commits on success and rolls back on error.

        The session is always closed, so callers never leak connections.
        """
        with self.session() as session:
            try:
                yield session
                session.commit()
            except Exception:
                session.rollback()
                raise


@lru_cache(maxsize=16)
def _database_for(key: tuple[str, int, int]) -> Database:
    """Build a :class:`Database` for a normalized configuration key."""
    url, pool_size, max_overflow = key
    return Database(
        Settings(
            environment="production",
            database_url=url,
            database_pool_size=pool_size,
            database_max_overflow=max_overflow,
        )
    )


def get_database(settings: Settings) -> Database:
    """Return the cached :class:`Database` matching the given settings.

    The engine and pool are keyed by the resolved URL and pool sizing, so a
    single process reuses one engine per configuration while tests remain
    isolated (each distinct URL gets its own engine).
    """
    key = (
        settings.effective_database_url,
        settings.database_pool_size,
        settings.database_max_overflow,
    )
    return _database_for(key)


def clear_database_cache() -> None:
    """Discard cached :class:`Database` instances (used by the test suite)."""
    _database_for.cache_clear()


def get_session(settings: Settings) -> Generator[Session, None, None]:
    """FastAPI dependency: yield a transactional database session.

    Commits on success and rolls back on exception so callers never leak
    partial writes. The session is always closed after the request.
    """
    with get_database(settings).session() as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise


def create_all_and_init(settings: Settings) -> Session:
    """Create every table and return a session to the initialized database.

    Intended for isolated tests and throwaway local runs only; production
    schema is managed exclusively by Alembic migrations.
    """
    database = Database(settings)
    database.create_all()
    return database.session()

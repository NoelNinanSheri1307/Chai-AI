"""Generic repository base: CRUD, pagination, filtering, sorting, soft delete.

Repositories are the persistence layer. They accept a plain SQLModel
:class:`Session`, return ORM entities, and contain no HTTP, FastAPI or
business-logic knowledge. Future services orchestrate them.

``BaseRepository`` provides the shared persistence surface; concrete
repositories set ``model`` and add entity-specific queries.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Generic, TypeVar

from sqlalchemy import Select, func, select
from sqlmodel import Session, SQLModel

from app.core import constants

ModelT = TypeVar("ModelT", bound=SQLModel)


@dataclass(frozen=True)
class PageParams:
    """Pagination/sorting parameters for repository list queries."""

    limit: int = constants.DEFAULT_PAGE_SIZE
    offset: int = 0
    sort: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "limit", max(1, min(self.limit, constants.MAX_PAGE_SIZE))
        )
        object.__setattr__(self, "offset", max(0, self.offset))


@dataclass(frozen=True)
class Page(Generic[ModelT]):
    """A page of repository results with the total matching count."""

    items: list[ModelT]
    total: int
    limit: int
    offset: int
    has_more: bool = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "has_more", self.offset + len(self.items) < self.total)


class BaseRepository(Generic[ModelT]):
    """Persistence operations for a single ORM model.

    ``model`` must be set on concrete subclasses. Reads on models with a
    ``deleted_at`` column exclude soft-deleted rows unless ``include_deleted``
    is explicitly requested.
    """

    model: type[ModelT]

    def __init__(self, session: Session) -> None:
        self.session = session

    # ------------------------------------------------------------------
    # Session helpers
    # ------------------------------------------------------------------
    def commit(self) -> None:
        """Commit the current transaction."""
        self.session.commit()

    def rollback(self) -> None:
        """Roll back the current transaction."""
        self.session.rollback()

    def flush(self) -> None:
        """Flush pending changes to the database without committing."""
        self.session.flush()

    @contextmanager
    def transaction(self) -> Iterator[Session]:
        """Run a unit of work that commits on success and rolls back on error.

        Example::

            with repo.transaction():
                user = repo.create(User(...))
                repo.create(Analysis(..., user_id=user.id))
        """
        try:
            yield self.session
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

    # ------------------------------------------------------------------
    # Query building
    # ------------------------------------------------------------------
    def _has_column(self, name: str) -> bool:
        return name in self.model.__table__.c

    def _resolve_column(self, name: str) -> Any:
        """Resolve a column by name, rejecting unknown columns.

        Filtering/sorting keys are validated against the model's table so
        callers cannot inject arbitrary SQL fragments.
        """
        try:
            return self.model.__table__.c[name]
        except KeyError as exc:
            raise ValueError(
                f"Unknown column {name!r} for {self.model.__tablename__}"
            ) from exc

    def _base_select(self, *, include_deleted: bool = False) -> Select[tuple[ModelT]]:
        statement: Select[tuple[ModelT]] = select(self.model)
        if not include_deleted and self._has_column("deleted_at"):
            statement = statement.where(self.model.deleted_at.is_(None))
        return statement

    def _apply_filters(
        self,
        statement: Select[tuple[ModelT]],
        filters: dict[str, Any],
    ) -> Select[tuple[ModelT]]:
        for name, value in filters.items():
            statement = statement.where(self._resolve_column(name) == value)
        return statement

    def _sort_clause(self, sort: str | None) -> Any | None:
        if not sort:
            return None
        direction = "asc"
        field_name = sort
        if field_name.startswith("-"):
            direction, field_name = "desc", field_name[1:]
        elif field_name.startswith("+"):
            field_name = field_name[1:]
        column = self._resolve_column(field_name)
        return column.desc() if direction == "desc" else column.asc()

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------
    def get(self, id: int, *, include_deleted: bool = False) -> ModelT | None:
        """Return the row with the given surrogate id, or ``None``."""
        statement = self._base_select(include_deleted=include_deleted).where(
            self.model.id == id  # type: ignore[attr-defined]
        )
        return self.session.scalars(statement).first()

    def exists(self, id: int, *, include_deleted: bool = False) -> bool:
        """Return whether a row with the given surrogate id exists."""
        return self.get(id, include_deleted=include_deleted) is not None

    def find_one(self, **filters: Any) -> ModelT | None:
        """Return the first row matching the given equality filters, or ``None``."""
        statement = self._apply_filters(self._base_select(), filters)
        return self.session.scalars(statement).first()

    def count(
        self,
        *,
        include_deleted: bool = False,
        filters: dict[str, Any] | None = None,
    ) -> int:
        """Count rows matching the given filters (soft-deleted excluded)."""
        statement = self._apply_filters(
            self._base_select(include_deleted=include_deleted), filters or {}
        )
        count_statement = select(func.count()).select_from(statement.subquery())
        return int(self.session.scalars(count_statement).one())

    def list(
        self,
        *,
        page: PageParams | None = None,
        filters: dict[str, Any] | None = None,
        include_deleted: bool = False,
    ) -> Page[ModelT]:
        """Return a :class:`Page` of rows matching filters with pagination.

        ``page.sort`` accepts ``"+field"`` (ascending, default) or ``"-field"``
        (descending) where ``field`` is a real column of the model.
        """
        resolved_page = page or PageParams()
        statement = self._apply_filters(
            self._base_select(include_deleted=include_deleted),
            filters or {},
        )
        total = int(
            self.session.scalars(
                select(func.count()).select_from(statement.subquery())
            ).one()
        )
        sort_clause = self._sort_clause(resolved_page.sort)
        if sort_clause is not None:
            statement = statement.order_by(sort_clause)
        statement = statement.offset(resolved_page.offset).limit(resolved_page.limit)
        items = list(self.session.scalars(statement).all())
        return Page(
            items=items,
            total=total,
            limit=resolved_page.limit,
            offset=resolved_page.offset,
        )

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------
    def create(self, entity: ModelT) -> ModelT:
        """Persist a new row and return it with its generated identity."""
        self.session.add(entity)
        self.session.flush()
        return entity

    def create_many(self, entities: Iterable[ModelT]) -> list[ModelT]:
        """Persist many rows in a single flush and return them."""
        materialized = list(entities)
        for entity in materialized:
            self.session.add(entity)
        self.session.flush()
        return materialized

    def update(self, entity: ModelT) -> ModelT:
        """Persist changes to an existing row.

        ``entity`` may be session-bound or detached; its state is merged into
        the session and flushed.
        """
        merged = self.session.merge(entity)
        self.session.flush()
        return merged

    def delete(self, entity_or_id: ModelT | int) -> None:
        """Hard-delete a row (and, via ORM cascade, its cascade children)."""
        entity = (
            entity_or_id
            if isinstance(entity_or_id, self.model)
            else self.get(entity_or_id, include_deleted=True)
        )
        if entity is None:
            return
        self.session.delete(entity)
        self.session.flush()

    def soft_delete(self, entity_or_id: ModelT | int) -> bool:
        """Soft-delete a row by stamping ``deleted_at``.

        Returns ``False`` when the row is missing or already deleted. Only
        models with a ``deleted_at`` column support this operation.
        """
        if not self._has_column("deleted_at"):
            raise TypeError(f"{self.model.__name__} does not support soft delete")
        entity = (
            entity_or_id
            if isinstance(entity_or_id, self.model)
            else self.get(entity_or_id, include_deleted=True)
        )
        if entity is None or entity.deleted_at is not None:  # type: ignore[union-attr]
            return False
        entity.deleted_at = datetime.now(timezone.utc)  # type: ignore[union-attr]
        self.session.flush()
        return True

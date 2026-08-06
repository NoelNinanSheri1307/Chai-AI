"""ORM mixins and shared column helpers.

Mixins are plain (non-table) SQLModel classes whose columns are inherited by
concrete table models. They carry persistence-only concerns: audit timestamps
and soft-delete state. No business logic.

Shared mixin columns must be declared with an inferred ``sa_type`` (plus
``sa_column_kwargs``) rather than a bare ``sa_column=Column(...)``: SQLModel
0.0.39 reuses a shared ``sa_column`` Column across every inheriting table,
which breaks multi-table models.
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import Any

from sqlalchemy import Column, DateTime, Enum, Index, func, text
from sqlmodel import Field, SQLModel

from app.core import constants


def enum_values(enum_cls: type[enum.Enum]) -> list[str]:
    """Return the ``.value`` strings of a ``str``-backed enum type."""
    return [member.value for member in enum_cls]


def enum_column(
    enum_cls: type[enum.Enum],
    *,
    nullable: bool = False,
    server_default: str | None = None,
) -> Column:
    """Build a portable VARCHAR-backed column for a ``str`` enum.

    Stores the enum ``.value`` strings (not member names) so the persisted
    values match the domain literals defined in ``app.core.enums``, and
    validates on bind so invalid values are rejected by the ORM. Uses
    ``native_enum=False`` for portability across SQLite and PostgreSQL.

    The returned :class:`Column` is intended to be passed to
    ``Field(sa_column=...)``.
    """
    column_kwargs: dict[str, Any] = {"nullable": nullable}
    if server_default is not None:
        column_kwargs["server_default"] = server_default
    return Column(
        Enum(
            enum_cls,
            native_enum=False,
            length=constants.ENUM_LABEL_MAX_LENGTH,
            values_callable=enum_values,
            validate_strings=True,
        ),
        **column_kwargs,
    )


def soft_delete_index(table_name: str) -> Index:
    """Partial index over ``deleted_at`` for active-row queries.

    A row is "live" while ``deleted_at IS NULL``; the partial index keeps the
    index small and mirrors the read paths repositories use.
    """
    predicate = text("deleted_at IS NULL")
    return Index(
        f"ix_{table_name}_active",
        "deleted_at",
        sqlite_where=predicate,
        postgresql_where=predicate,
    )


class CreatedAtMixin(SQLModel):
    """Adds a non-nullable ``created_at`` audit timestamp."""

    created_at: datetime | None = Field(
        default=None,
        nullable=False,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"server_default": func.now()},
    )


class TimestampMixin(CreatedAtMixin):
    """Adds ``created_at`` / ``updated_at`` audit timestamps.

    ``created_at`` is set once at insert; ``updated_at`` is refreshed
    automatically on update via ``onupdate``.
    """

    updated_at: datetime | None = Field(
        default=None,
        nullable=False,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={
            "server_default": func.now(),
            "onupdate": func.now(),
        },
    )


class SoftDeleteMixin(SQLModel):
    """Adds a nullable ``deleted_at`` column for soft deletion.

    A row is active while ``deleted_at`` is NULL. Repositories apply this
    filter on reads and set the timestamp on delete. Concrete tables add a
    partial index over this column via :func:`soft_delete_index`.
    """

    deleted_at: datetime | None = Field(
        default=None,
        nullable=True,
        sa_type=DateTime(timezone=True),
    )

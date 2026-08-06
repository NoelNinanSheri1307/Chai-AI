"""Pagination helpers: page/limit parsing, sorting and the page envelope.

Converts 1-based ``page``/``limit`` query parameters into the repository's
offset-based :class:`PageParams` and rebuilds the API page envelope from a
repository page. Sorting fields are normalized from the camelCase forms used in
the API contract (for example ``-createdAt``) to the snake_case column names the
repositories validate against.
"""

from __future__ import annotations

import re

from app.core import constants
from app.repos.base import PageParams

_camel_boundary = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")


def normalize_sort_field(sort: str | None) -> str | None:
    """Convert a camelCase sort field to snake_case.

    For example ``-createdAt`` becomes ``-created_at`` so repository column
    validation accepts it.
    """
    if not sort:
        return None
    direction = ""
    field = sort
    if field.startswith("-"):
        direction, field = "-", field[1:]
    elif field.startswith("+"):
        field = field[1:]
    normalized = _camel_boundary.sub("_", field).lower()
    return f"{direction}{normalized}"


def resolve_page_params(
    *,
    page: int,
    limit: int,
    sort: str | None = None,
) -> PageParams:
    """Build offset-based repository pagination params from API query values.

    ``page`` is 1-based and is clamped to at least 1; ``limit`` is clamped to
    the configured ``MAX_PAGE_SIZE`` so the returned envelope stays consistent
    with what the repository actually executes.
    """
    effective_limit = min(max(int(limit), 1), constants.MAX_PAGE_SIZE)
    effective_page = max(int(page), 1)
    offset = (effective_page - 1) * effective_limit
    return PageParams(
        limit=effective_limit,
        offset=offset,
        sort=normalize_sort_field(sort),
    )


def build_page_envelope(
    items: list[object],
    *,
    total: int,
    page: int,
    limit: int,
) -> dict[str, object]:
    """Build the API page envelope payload from mapped items."""
    has_more = (max(int(page), 1) - 1) * int(limit) + len(items) < total
    return {
        "items": items,
        "total": total,
        "page": max(int(page), 1),
        "limit": int(limit),
        "has_more": has_more,
    }

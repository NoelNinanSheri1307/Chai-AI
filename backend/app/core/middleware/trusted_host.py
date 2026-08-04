"""Trusted host middleware (placeholder).

Wraps Starlette's ``TrustedHostMiddleware``. The set of allowed Host values is
taken from configuration. A value of ``"*"`` (the development default)
disables host filtering entirely, so this middleware is wired but inert
outside a production profile.
"""

from __future__ import annotations

from starlette.middleware.trustedhost import (
    TrustedHostMiddleware as _TrustedHostMiddleware,
)
from starlette.types import ASGIApp, Receive, Scope, Send


class TrustedHostMiddleware:
    """Config-driven wrapper around Starlette's trusted-host enforcement."""

    def __init__(self, app: ASGIApp, allowed_hosts: list[str]) -> None:
        self._delegate = _TrustedHostMiddleware(app, allowed_hosts=allowed_hosts)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        await self._delegate(scope, receive, send)

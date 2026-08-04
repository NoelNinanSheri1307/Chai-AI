"""Timing middleware.

Measures the wall-clock duration of every HTTP request and emits a single
structured log line per request containing method, path, status, latency and
request id. The request id is read from the context variable set by
:class:`app.core.middleware.request_id.RequestIDMiddleware`.
"""

from __future__ import annotations

import logging
import time

from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.logging import get_request_id

logger = logging.getLogger(__name__)


class TimingMiddleware:
    """Emit one structured request-completion log line per HTTP request."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start = time.perf_counter()
        status_code = 500

        async def send_wrapper(message: dict) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            latency_ms = (time.perf_counter() - start) * 1000.0
            logger.info(
                "request.completed",
                extra={
                    "event": "request.completed",
                    "method": scope.get("method"),
                    "path": scope.get("path"),
                    "status": status_code,
                    "latency_ms": round(latency_ms, 3),
                    "request_id": get_request_id(),
                },
            )

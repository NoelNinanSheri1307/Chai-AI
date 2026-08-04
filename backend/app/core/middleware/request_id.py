"""Request id middleware.

Assigns a unique id to every HTTP request, reusing an inbound
``X-Request-ID`` header when one is provided. The id is bound to the request
context (so logging can attach it) and echoed on the response so clients can
correlate logs across services.
"""

from __future__ import annotations

import uuid

from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.logging import request_id_context


class RequestIDMiddleware:
    """Propagate or generate a per-request id and echo it on responses."""

    def __init__(self, app: ASGIApp, header_name: str) -> None:
        self.app = app
        self.header_name = header_name

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = Headers(scope=scope)
        request_id = headers.get(self.header_name) or uuid.uuid4().hex
        token = request_id_context.set(request_id)

        async def send_wrapper(message: dict) -> None:
            if message["type"] == "http.response.start":
                response_headers = MutableHeaders(scope=message)
                response_headers[self.header_name] = request_id
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            request_id_context.reset(token)

"""Request-size limiting middleware.

Rejects requests whose declared ``Content-Length`` exceeds the configured bound
*before* the body is read/parsed, returning the standard 413 envelope. This is a
coarse HTTP-level guard: uploads are additionally validated against the more
specific image upload limit in the analyses/compare services.
"""

from __future__ import annotations

from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.errors import ErrorCode, error_response_payload


class RequestSizeLimitMiddleware:
    """Reject requests that declare a body larger than ``max_bytes``."""

    def __init__(self, app: ASGIApp, max_bytes: int) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = scope.get("headers") or []
        content_length = None
        for name, value in headers:
            if name == b"content-length":
                try:
                    content_length = int(value)
                except ValueError:
                    content_length = None
                break

        if content_length is not None and content_length > self.max_bytes:
            payload = error_response_payload(
                ErrorCode.FILE_TOO_LARGE,
                f"Request body exceeds the {self.max_bytes} byte limit.",
            )
            from starlette.responses import JSONResponse

            response = JSONResponse(status_code=413, content=payload)
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)

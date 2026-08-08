"""Security headers middleware.

Adds hardening response headers to every HTTP response. Headers are safe by
default for an API and can be adjusted through configuration for deployments
that embed the Swagger docs in iframes etc. The implementation follows the
OWASP Secure Headers guidance for a JSON API.
"""

from __future__ import annotations

from typing import Any

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Receive, Scope, Send

_DEFAULT_HEADERS: dict[str, str] = {
    # Prevent MIME-sniffing downgrade attacks on binary responses.
    "X-Content-Type-Options": "nosniff",
    # Refuse being framed; clickjacking protection.
    "X-Frame-Options": "DENY",
    # Do not leak the referring URL across origins.
    "Referrer-Policy": "no-referrer",
    # Narrow browser features this site permits.
    "Permissions-Policy": "camera=(), microphone=(), geolocation=(), usb=()",
}


class SecurityHeadersMiddleware:
    """Attach baseline security headers to every HTTP response."""

    def __init__(
        self,
        app: ASGIApp,
        *,
        extra_headers: dict[str, str] | None = None,
        hsts_enabled: bool = False,
    ) -> None:
        self.app = app
        self._headers: dict[str, str] = dict(_DEFAULT_HEADERS)
        if extra_headers:
            self._headers.update(extra_headers)
        if hsts_enabled:
            self._headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_wrapper(message: dict[str, Any]) -> None:
            if message["type"] == "http.response.start":
                response_headers = MutableHeaders(scope=message)
                for name, value in self._headers.items():
                    response_headers[name] = value
            await send(message)

        await self.app(scope, receive, send_wrapper)

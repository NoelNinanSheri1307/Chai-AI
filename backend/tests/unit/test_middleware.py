"""Tests for the global middleware."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from starlette.types import Receive, Scope, Send

from app.core.logging import request_id_context
from app.core.middleware.request_id import RequestIDMiddleware
from app.core.middleware.timing import TimingMiddleware


def _stub_scope(headers: list[tuple[bytes, bytes]] | None = None) -> Scope:
    return {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/v1/health",
        "raw_path": b"/v1/health",
        "query_string": b"",
        "root_path": "",
        "headers": headers or [],
        "client": None,
        "server": None,
        "state": {},
    }


async def _stub_app(scope: Scope, receive: Receive, send: Send) -> None:
    await send(
        {
            "type": "http.response.start",
            "status": 200,
            "headers": [(b"content-type", b"text/plain")],
        }
    )
    await send({"type": "http.response.body", "body": b"ok"})


def _run(middleware: Any, scope: Scope) -> list[dict]:
    received: list[dict] = []

    async def receive() -> dict:
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message: dict) -> None:
        received.append(message)

    asyncio.run(middleware(scope, receive, send))
    return received


def _response_headers(messages: list[dict]) -> dict[bytes, bytes]:
    start = next(m for m in messages if m["type"] == "http.response.start")
    return dict(start["headers"])


def test_request_id_generated_and_echoed() -> None:
    scope = _stub_scope()
    middleware = RequestIDMiddleware(_stub_app, header_name="X-Request-ID")

    messages = _run(middleware, scope)

    assert _response_headers(messages)[b"x-request-id"]
    assert request_id_context.get() == ""


def test_request_id_respects_inbound_value() -> None:
    scope = _stub_scope([(b"x-request-id", b"client-picked")])
    middleware = RequestIDMiddleware(_stub_app, header_name="X-Request-ID")

    messages = _run(middleware, scope)

    assert _response_headers(messages)[b"x-request-id"] == b"client-picked"
    assert request_id_context.get() == ""


def test_timing_middleware_logs_request_metadata(caplog: Any) -> None:
    scope = _stub_scope()
    middleware = TimingMiddleware(_stub_app)

    with caplog.at_level(logging.INFO):
        _run(middleware, scope)

    completed = [r for r in caplog.records if r.event == "request.completed"]
    assert completed, "expected a request.completed log record"
    record = completed[0]
    assert record.method == "GET"
    assert record.path == "/v1/health"
    assert record.status == 200
    assert record.latency_ms >= 0

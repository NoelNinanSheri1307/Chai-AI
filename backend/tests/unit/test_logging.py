"""Tests for structured logging."""

from __future__ import annotations

import io
import json
import logging

from app.core.logging import JsonFormatter, request_id_context


def test_json_formatter_includes_request_id_and_extra() -> None:
    logger = logging.getLogger("tests.json")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    try:
        token = request_id_context.set("req-123")
        try:
            logger.info("hello world", extra={"event": "request.completed"})
        finally:
            request_id_context.reset(token)
    finally:
        logger.removeHandler(handler)

    payload = json.loads(stream.getvalue())
    assert payload["message"] == "hello world"
    assert payload["request_id"] == "req-123"
    assert payload["event"] == "request.completed"
    assert payload["level"] == "INFO"


def test_json_formatter_omits_request_id_when_absent() -> None:
    logger = logging.getLogger("tests.json.plain")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    try:
        logger.info("no context")
    finally:
        logger.removeHandler(handler)

    payload = json.loads(stream.getvalue())
    assert "request_id" not in payload
    assert payload["message"] == "no context"

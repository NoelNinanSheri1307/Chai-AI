"""Structured JSON logging with per-request context.

The root logger is configured once through :func:`setup_logging`. A
``contextvars.ContextVar`` carries the active request id so that every log
line emitted while handling a request includes it, without threading it
through every call site.
"""

from __future__ import annotations

import contextvars
import json
import logging
import sys
import time
from typing import Any

from app.core.config import Settings

request_id_context: contextvars.ContextVar[str] = contextvars.ContextVar(
    "request_id", default=""
)


def get_request_id() -> str:
    """Return the request id bound to the current context (or ``""``)."""
    return request_id_context.get()


_EXCLUDED_RECORD_ATTRS = frozenset(
    {
        "args",
        "asctime",
        "created",
        "exc_info",
        "exc_text",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "message",
        "module",
        "msecs",
        "msg",
        "name",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "thread",
        "threadName",
        "taskName",
    }
)


class JsonFormatter(logging.Formatter):
    """Format log records as single-line JSON.

    Standard record attributes are mapped to well-known keys; any additional
    ``extra`` attributes are spread onto the payload verbatim.
    """

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": self._timestamp(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        request_id = request_id_context.get() or getattr(record, "request_id", "")
        if request_id:
            payload["request_id"] = request_id
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        for key, value in record.__dict__.items():
            if key in _EXCLUDED_RECORD_ATTRS or key in payload:
                continue
            payload[key] = value
        return json.dumps(payload, default=str)

    @staticmethod
    def _timestamp(record: logging.LogRecord) -> str:
        base = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(record.created))
        return f"{base}.{int(record.msecs):03d}Z"


def setup_logging(settings: Settings) -> None:
    """Configure the root logger for the application.

    Removes any pre-existing handlers and attaches a single stream handler to
    stdout. Intended to be called once, from the application factory.
    """
    root = logging.getLogger()
    for handler in root.handlers[:]:
        root.removeHandler(handler)

    if settings.json_logging:
        formatter: logging.Formatter = JsonFormatter()
    else:
        formatter = logging.Formatter("%(levelname)s %(name)s %(message)s")

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    root.addHandler(handler)
    root.setLevel(settings.log_level)

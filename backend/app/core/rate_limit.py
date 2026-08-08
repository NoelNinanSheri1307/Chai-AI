"""Rate limiting: a narrow, replaceable abstraction.

Design notes (Milestone 10):

* Chai does **not** ship a distributed rate limiter by default. Production rate
  limiting must be backed by a shared store (e.g. Redis) so limits are accurate
  across multiple worker processes. This module therefore only defines the
  interface plus two implementations:

  * :class:`NullRateLimiter` — the default; performs no limiting. Safe for
    development and single-deployment testing, and is the advised production
    baseline *until* a shared backend is deployed.
  * :class:`InMemorySlidingWindowLimiter` — a per-process, fixed-window limiter
    suitable **only** for single-process development/testing. Because it is
    process-local it is deliberately **not** wired by default in production,
    where it would double-count across replicas or silently under-count.
* The abstraction is dependency-injected, so a Redis-backed implementation can be
  dropped in later without changing callers.
"""

from __future__ import annotations

import threading
import time
from abc import ABC, abstractmethod
from collections import defaultdict, deque


class RateLimiter(ABC):
    """Abstract rate-limit check used by the API layer.

    Implementations must be safe to call concurrently (the ASGI server runs
    requests in threads/tasks) and cheap.
    """

    @abstractmethod
    def allow(self, key: str, *, now: float | None = None) -> bool:
        """Return ``True`` when ``key`` may proceed, ``False`` to rate-limit."""


class NullRateLimiter(RateLimiter):
    """A no-op limiter: every request is allowed (the default)."""

    def allow(self, key: str, *, now: float | None = None) -> bool:
        return True


class InMemorySlidingWindowLimiter(RateLimiter):
    """A process-local, thread-safe sliding-window limiter.

    Intended for single-process development and test scenarios only. State is
    kept in memory and therefore lost on restart and *not accurate across
    multiple uvicorn workers*. For production use a shared backend.
    """

    def __init__(self, limit: int, window_seconds: int = 60) -> None:
        if limit < 1:
            raise ValueError("limit must be at least 1")
        if window_seconds < 1:
            raise ValueError("window_seconds must be at least 1")
        self._limit = limit
        self._window = window_seconds
        self._lock = threading.Lock()
        self._events: defaultdict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str, *, now: float | None = None) -> bool:
        timestamp = now if now is not None else time.monotonic()
        with self._lock:
            events = self._events[key]
            cutoff = timestamp - self._window
            while events and events[0] <= cutoff:
                events.popleft()
            if len(events) >= self._limit:
                return False
            events.append(timestamp)
            return True


def build_rate_limiter(
    kind: str, *, limit: int = 100, window_seconds: int = 60
) -> RateLimiter:
    """Construct a limiter from a configuration name.

    ``"none"`` (default) yields a no-op; ``"memory"`` yields the in-memory
    sliding-window limiter (development/testing only).
    """
    normalized = (kind or "none").strip().lower()
    if normalized in {"", "none", "null", "off"}:
        return NullRateLimiter()
    if normalized == "memory":
        return InMemorySlidingWindowLimiter(limit=limit, window_seconds=window_seconds)
    raise ValueError(f"Unknown rate limiter backend {kind!r}")

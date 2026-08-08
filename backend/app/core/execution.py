"""Bounded execution helpers.

Python's GIL and thread model forbid forcibly killing a worker thread, so true
pre-emption of a single detector is impossible in-process. What we *can* do
safely is bound how long the caller waits and return a controlled timeout error
while letting the stray work finish and discard itself (detectors are pure over
image bytes; the abandoned future performs no persistence, so nothing can be
corrupted).

This module exposes a small set of bounded executors for exactly that use,
cached by worker count so threads are reused across requests rather than
spun up per request.
"""

from __future__ import annotations

import concurrent.futures
import logging
import threading
from collections.abc import Callable
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")

_executors: dict[int, concurrent.futures.ThreadPoolExecutor] = {}
_executors_lock = threading.Lock()


def _executor(max_workers: int) -> concurrent.futures.ThreadPoolExecutor:
    """Return the cached bounded executor for ``max_workers``.

    Bounded by the configured cap (configuration is system-wide, so at most two
    or three pools exist in practice) and thread-safe to call concurrently.
    """
    with _executors_lock:
        executor = _executors.get(max_workers)
        if executor is None:
            executor = concurrent.futures.ThreadPoolExecutor(
                max_workers=max_workers,
                thread_name_prefix="chai-bounded",
            )
            _executors[max_workers] = executor
        return executor


def run_with_timeout(
    fn: Callable[..., T],
    *,
    args: tuple[Any, ...] = (),
    kwargs: dict[str, Any] | None = None,
    timeout_seconds: float | int | None,
    max_workers: int = 1,
) -> T:
    """Run ``fn`` in a bounded pool, raising ``TimeoutError`` past the budget.

    Returns the function result when it completes in time. Threads are reused
    across calls and the pool is capped at ``max_workers``. A timed-out call
    keeps running in the background (Python cannot kill threads), but because
    the performed work is pure, discarding its result is safe and cannot
    corrupt persistence.
    """
    if timeout_seconds is None or timeout_seconds <= 0:
        return fn(*args, **(kwargs or {}))
    workers = max(1, min(int(max_workers), 64))

    future = _executor(workers).submit(fn, *args, **(kwargs or {}))
    try:
        return future.result(timeout=timeout_seconds)
    except concurrent.futures.TimeoutError as exc:
        logger.warning(
            "Bounded execution timed out after %.3fs; work continues in the "
            "background and its result will be discarded.",
            float(timeout_seconds),
        )
        raise TimeoutError(
            f"Operation did not complete within {timeout_seconds:g}s"
        ) from exc


def shutdown_executors() -> None:
    """Shut down and drop cached executors (used by the test suite)."""
    with _executors_lock:
        for executor in _executors.values():
            executor.shutdown(wait=False, cancel_futures=False)
        _executors.clear()

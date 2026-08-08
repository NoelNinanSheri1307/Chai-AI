"""Deterministic forensic fingerprinting.

These helpers execute the *already built* forensic pipeline and reduce its output
to a machine-comparable fingerprint. They are used to lock the forensic
behaviour of the system so performance/security work can be verified not to
change results.

Two caveats are handled deliberately:

* Wall-clock measurements (``processing_time_ms``, ``duration_ms``) are
  excluded because they are environment-dependent.
* The fingerprint is a fully JSON-serialisable, deterministic serialisation of
  the forensic *outputs only* (verdict, scores, indicators, evidence, heatmap,
  report snapshot) so it can be compared across runs and stored as a fixture.
  Enums collapse to their ``.value`` string and dataclasses to plain dicts.
"""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from enum import Enum
from typing import Any

_FORENSIC_FIELDS = (
    "verdict",
    "confidence",
    "risk_level",
    "explanation",
    "heatmap",
    "scores",
    "indicators",
    "evidence",
    "report_data",
)

#: Field names that are never part of the forensic fingerprint.
_NON_FORENSIC_FIELDS = frozenset(
    {"processing_time_ms", "duration_ms", "request_id", "timestamp"}
)


def _to_jsonable(value: Any) -> Any:
    """Recursively convert a value into plain JSON-compatible primitives."""
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {
            field.name: _to_jsonable(getattr(value, field.name))
            for field in fields(value)
            if field.name not in _NON_FORENSIC_FIELDS
        }
    if isinstance(value, dict):
        return {
            str(key): _to_jsonable(item)
            for key, item in value.items()
            if key not in _NON_FORENSIC_FIELDS
        }
    if isinstance(value, (list, tuple)):
        return [_to_jsonable(item) for item in value]
    if isinstance(value, set):
        return [_to_jsonable(item) for item in sorted(value, key=repr)]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return repr(value)


def pipeline_fingerprint(result: Any) -> dict[str, Any]:
    """Return a deterministic, JSON-ready fingerprint of a pipeline result.

    Only forensic outputs are included: never timings, never image bytes, never
    secrets. The returned dict compares for equality across runs (``==``).
    """
    fingerprint: dict[str, Any] = {}
    for name in _FORENSIC_FIELDS:
        value = getattr(result, name, None)
        fingerprint[name] = _to_jsonable(value)
    return fingerprint

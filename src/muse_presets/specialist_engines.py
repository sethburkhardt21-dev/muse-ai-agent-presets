"""Four bounded, deterministic offline specialist exercises.

This is library code for fictional supplied data, not an autonomous Muse
model, a database operator, an infrastructure probe or a browser audit.
"""
from __future__ import annotations
from decimal import (Decimal, Context, localcontext, ROUND_HALF_EVEN,
                     InvalidOperation, DivisionByZero, Overflow)
import heapq
import json
import re

SLUG = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
FIELD = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,63}$")
ROLES = frozenset({
    "data-engineering-architect", "infrastructure-reliability-engineer",
    "automation-engineer", "product-interface-designer",
})
MAX_INPUT_BYTES = 128_000


def _dict(value, name):
    if type(value) is not dict:
        raise ValueError("INVALID_" + name.upper())
    return value


def _named(value, field, *, slug=True):
    if type(value) is not str or not (SLUG if slug else FIELD).fullmatch(value):
        raise ValueError("INVALID_" + field.upper())
    return value


def _rows(value, max_rows=10000):
    if type(value) is not list or not 1 <= len(value) <= max_rows:
        raise ValueError("INVALID_ROW_COUNT")
    return value


def _common(role):
    return {"role": role, "grade": "OFFLINE_FIXTURE_ONLY",
            "native_registered": False, "external_effect_authorized": False,
            "production_effect_verified": False}


def _data(payload):
    if set(payload) != {"rows", "key"}:
        raise ValueError("INVALID_DATA_FIELDS")
    key = _named(payload["key"], "key", slug=False)
    rows = _rows(payload["rows"])
    keys = set()
    duplicates = 0
    counts = {}
    for row in rows:
        _dict(row, "row")
        if not row or len(row) > 100:
            raise ValueError("INVALID_ROW_FIELDS")
        if any(type(k) is not str or not FIELD.fullmatch(k) for k in row):
            raise ValueError("INVALID_COLUMN")
        if key not in row:
            raise ValueError("MISSING_KEY")
        value = row[key]
        if type(value) not in (str, int, bool) or value == "":
            raise ValueError("INVALID_KEY_VALUE")
        identity = (type(value).__name__, str(value))
        if identity in keys:
            duplicates += 1
        keys.add(identity)
        for name, cell in row.items():
            if type(cell) not in (str, int, bool, float, type(None)):
                raise ValueError("UNSUPPORTED_CELL_VALUE")
            if type(cell) is float and (cell != cell or abs(cell) == float("inf")):
                raise ValueError("NONFINITE_CELL")
            counts[name] = counts.get(name, 0) + int(cell is None)
    return {"rows": len(rows), "key": key, "duplicate_count": duplicates,
            "nulls_by_column": dict(sorted(counts.items())),
            "columns": sorted({k for row in rows for k in row}),
            "claim": "OBSERVED_SUPPLIED_ROWS_ONLY_NO_EXTERNAL_DATABASE"}


def _reliability(payload):
    if set(payload) != {"events", "target"}:
        raise ValueError("INVALID_RELIABILITY_FIELDS")
    rows = _rows(payload["events"], max_rows=100000)
    if any(type(v) is not bool for v in rows):
        raise ValueError("INVALID_BOOLEAN_EVENT")
    value = payload["target"]
    if (type(value) is not str or len(value) > 64
            or re.fullmatch(r"[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]{1,3})?", value) is None):
        raise ValueError("INVALID_TARGET")
    # A caller's thread-local Decimal precision/traps must not change this result.
    arithmetic = Context(prec=50, rounding=ROUND_HALF_EVEN, Emin=-100,
                         Emax=100, capitals=1, clamp=0, flags=[],
                         traps=[InvalidOperation, DivisionByZero, Overflow])
    with localcontext(arithmetic):
        try:
            target = Decimal(value)
        except InvalidOperation as exc:
            raise ValueError("INVALID_TARGET") from exc
        if (not target.is_finite() or not Decimal("0") < target < Decimal("1")
                or len(target.as_tuple().digits) > 30
                or not -30 <= target.as_tuple().exponent <= 0):
            raise ValueError("INVALID_TARGET")
        failures = sum(not v for v in rows)
        rate = Decimal(failures) / Decimal(len(rows))
        allowance = Decimal("1") - target
        budget = rate / allowance
        return {"observations": len(rows), "failures": failures,
                "failure_rate": str(rate), "objective": str(target),
                "error_budget_multiple": str(budget),
                "within_objective": Decimal(failures) <= allowance * Decimal(len(rows)),
                "claim": "SUPPLIED_SYNTHETIC_EVENTS_NOT_LIVE_SLO_PROOF"}


def _automation(payload):
    if set(payload) != {"steps"}:
        raise ValueError("INVALID_AUTOMATION_FIELDS")
    steps = _rows(payload["steps"], max_rows=5000)
    graph = {}
    for row in steps:
        _dict(row, "step")
        if set(row) != {"id", "deps"}:
            raise ValueError("INVALID_STEP_FIELDS")
        sid = _named(row["id"], "step_id")
        deps = row["deps"]
        if type(deps) is not list or len(deps) > len(steps):
            raise ValueError("INVALID_DEPENDENCIES")
        if any(type(x) is not str or not SLUG.fullmatch(x) for x in deps):
            raise ValueError("INVALID_DEPENDENCIES")
        if sid in graph or len(deps) != len(set(deps)):
            raise ValueError("DUPLICATE_ACTION_ID_OR_DEPENDENCY")
        graph[sid] = set(deps)
    for sid, deps in graph.items():
        if sid in deps or not deps.issubset(graph):
            raise ValueError("UNKNOWN_OR_SELF_DEPENDENCY")
    ready = [sid for sid, deps in graph.items() if not deps]
    heapq.heapify(ready)
    children = {sid: set() for sid in graph}
    for sid, deps in graph.items():
        for dep in deps:
            children[dep].add(sid)
    todo = {sid: set(deps) for sid, deps in graph.items()}
    order = []
    while ready:
        sid = heapq.heappop(ready)
        order.append(sid)
        for downstream in sorted(children[sid]):
            todo[downstream].remove(sid)
            if not todo[downstream]:
                heapq.heappush(ready, downstream)
    if len(order) != len(graph):
        raise ValueError("DEPENDENCY_CYCLE")
    return {"order": order, "step_count": len(steps),
            "all_effects_disabled": True,
            "claim": "VALIDATED_GRAPH_NOT_EXECUTED_SCHEDULE"}


def _designer(payload):
    if set(payload) != {"screens"}:
        raise ValueError("INVALID_INTERFACE_FIELDS")
    screens = _rows(payload["screens"], max_rows=100)
    known = set()
    findings = []
    for screen in screens:
        _dict(screen, "screen")
        if set(screen) != {"id", "controls"}:
            raise ValueError("INVALID_SCREEN_FIELDS")
        sid = _named(screen["id"], "screen_id")
        if sid in known:
            raise ValueError("DUPLICATE_SCREEN")
        known.add(sid)
        controls = screen["controls"]
        if type(controls) is not list or len(controls) > 200:
            raise ValueError("INVALID_CONTROLS")
        observed = set()
        for c in controls:
            _dict(c, "control")
            if set(c) != {"id", "label"}:
                raise ValueError("INVALID_CONTROL_FIELDS")
            cid = _named(c["id"], "control_id")
            if cid in observed:
                raise ValueError("DUPLICATE_CONTROL_ID")
            observed.add(cid)
            if type(c["label"]) is not str:
                raise ValueError("INVALID_CONTROL_LABEL")
            if not c["label"].strip():
                findings.append({"screen": sid, "control": cid,
                                 "finding": "MISSING_ACCESSIBLE_NAME_IN_SUPPLIED_DESCRIPTION"})
    return {"screen_count": len(screens), "missing_control_labels": len(findings),
            "findings": findings, "actual_browser_test": "NOT_RUN",
            "claim": "STATIC_SUPPLIED_SCREEN_DESCRIPTION_ONLY"}


def run_fixture(role: str, payload: dict) -> dict:
    """Pure calculation: never touch a filesystem, provider, subprocess or credential."""
    if type(role) is not str or role not in ROLES:
        raise ValueError("UNKNOWN_SPECIALIST")
    _dict(payload, "payload")
    try:
        raw = json.dumps(payload, allow_nan=False, sort_keys=True,
                         ensure_ascii=False).encode("utf-8")
    except (TypeError, ValueError, OverflowError, RecursionError) as exc:
        raise ValueError("UNSUPPORTED_OR_NONFINITE_INPUT") from exc
    if len(raw) > MAX_INPUT_BYTES:
        raise ValueError("INPUT_SIZE_LIMIT")
    work = {
        "data-engineering-architect": _data,
        "infrastructure-reliability-engineer": _reliability,
        "automation-engineer": _automation,
        "product-interface-designer": _designer,
    }[role](payload)
    return {**_common(role), **work}

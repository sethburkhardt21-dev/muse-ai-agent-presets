"""Source-only Coordinator graph and evidence assertion reviewer.

Consumes an already proposed workgraph. It is NOT a mission compiler,
scheduler, allocator, grant issuer, provider receipt service or remote sender.
No effects, mutations, network access, or owner identities are created.
"""
from __future__ import annotations

import hashlib
import heapq
import json
import re
from pathlib import Path

SCHEMA = "r33/coordinator-workgraph-v1"
REPORT_SCHEMA = "r33/coordinator-assertions-v1"
IDENT = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
SHA = re.compile(r"^[a-f0-9]{64}$")
TOP_KEYS = frozenset({"schema", "workspace", "budget_units", "tasks"})
TASK_KEYS = frozenset({"id", "role", "reviewer", "requires", "estimated_units",
                       "effect_class", "source_sha256", "acceptance"})
ASSERTION_KEYS = frozenset({"task_id", "actor_role", "reviewer_role",
                            "source_sha256", "actor_claim", "reviewer_claim"})
MAX_TASKS = 32
MAX_BUDGET = 64


def _hold(reason: str) -> dict:
    return {
        "schema": "r33/coordinator-review-result-v1",
        "status": "REVIEW_REQUIRED",
        "reason": reason,
        "provider_authenticated": False,
        "native_execution_verified": False,
        "recipient_readback_verified": False,
        "external_effect_authorized": False,
    }


def _digest(value: dict) -> str:
    # Caller supplied labels are untrusted; deterministic content ID, NOT a
    # publisher signature or proof of actor/recipient identity.
    content = json.dumps(value, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=True, allow_nan=False).encode("utf-8")
    return hashlib.sha256(content).hexdigest()


def _role_ids() -> set[str]:
    """Repository catalog or explicitly packed neutral role catalog, never donor state."""
    packaged = Path(__file__).with_name("coordinator_roles.json")
    if packaged.exists() or packaged.is_symlink():
        if packaged.is_symlink() or not packaged.is_file() or packaged.stat().st_size > 4096:
            raise ValueError("UNTRUSTED_ROLE_CATALOG")
        def pairs_unique(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError("DUPLICATE_ROLE_CATALOG_KEY")
                result[key] = value
            return result
        parsed = json.loads(packaged.read_bytes(), object_pairs_hook=pairs_unique)
        if (type(parsed) is not dict or set(parsed) != {"schema", "roles"} or
            parsed["schema"] != "r33/generic-role-catalog-v1" or
            type(parsed["roles"]) is not list or len(parsed["roles"]) != 11 or
            any(type(n) is not str or IDENT.fullmatch(n) is None for n in parsed["roles"]) or
            len(set(parsed["roles"])) != 11 or "coordinator" not in parsed["roles"]):
            raise ValueError("INVALID_ROLE_CATALOG")
        return set(parsed["roles"]) - {"coordinator"}
    from .catalog import load_registry
    return set(load_registry()["presets"]) - {"coordinator"}


def _bounded(value: object, *, limit: int = 200) -> bool:
    return (type(value) is str and 1 <= len(value) <= limit and
            value.strip() == value and
            all(ch.isprintable() and ch not in "\r\n" for ch in value))


def _valid_graph(graph: object):
    """Return (reason, ordering) with no mutation and no dispatch decisions."""
    if type(graph) is not dict or set(graph) != TOP_KEYS:
        return "GRAPH_FIELDS", []
    if graph["schema"] != SCHEMA or not _bounded(graph["workspace"], limit=64):
        return "GRAPH_SCHEMA_OR_WORKSPACE", []
    if IDENT.fullmatch(graph["workspace"]) is None:
        return "INVALID_WORKSPACE_ID", []
    budget = graph["budget_units"]
    if type(budget) is not int or not 1 <= budget <= MAX_BUDGET:
        return "INVALID_BUDGET", []
    tasks = graph["tasks"]
    if type(tasks) is not list or not 1 <= len(tasks) <= MAX_TASKS:
        return "INVALID_TASK_COUNT", []
    try:
        roles = _role_ids()
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return "ROLE_CATALOG_UNVERIFIED", []
    ids: set[str] = set()
    used = 0
    for task in tasks:
        if type(task) is not dict or set(task) != TASK_KEYS:
            return "TASK_FIELDS", []
        task_id = task["id"]
        if type(task_id) is not str or IDENT.fullmatch(task_id) is None or task_id in ids:
            return "TASK_ID_DUPLICATE_OR_INVALID", []
        ids.add(task_id)
        if type(task["role"]) is not str or type(task["reviewer"]) is not str:
            return "INVALID_ROLE_TYPE", []
        if (task["role"] not in roles or task["reviewer"] not in roles
                or task["role"] == task["reviewer"]):
            return "ROLE_OR_INDEPENDENT_REVIEWER_REFUSED", []
        if type(task["requires"]) is not list or len(task["requires"]) > MAX_TASKS:
            return "DEPENDENCIES_INVALID", []
        if any(type(dep) is not str or IDENT.fullmatch(dep) is None for dep in task["requires"]):
            return "DEPENDENCIES_INVALID", []
        if len(set(task["requires"])) != len(task["requires"]):
            return "DUPLICATE_DEPENDENCY", []
        units = task["estimated_units"]
        if type(units) is not int or not 1 <= units <= MAX_BUDGET:
            return "INVALID_ESTIMATE", []
        used += units
        if task["effect_class"] not in ("none", "external"):
            return "UNKNOWN_EFFECT_CLASS", []
        if type(task["source_sha256"]) is not str or SHA.fullmatch(task["source_sha256"]) is None:
            return "INVALID_SOURCE_DIGEST", []
        evidence = task["acceptance"]
        if (type(evidence) is not list or not 1 <= len(evidence) <= 4 or
                any(not _bounded(value) for value in evidence) or
                len(set(evidence)) != len(evidence)):
            return "ACCEPTANCE_INVALID", []
    if used > budget:
        return "BUDGET_EXCEEDED", []
    parents: dict[str, set[str]] = {}
    descendants: dict[str, set[str]] = {name: set() for name in ids}
    for item in tasks:
        name = item["id"]
        deps = set(item["requires"])
        if name in deps or not deps <= ids:
            return "MISSING_OR_SELF_DEPENDENCY", []
        parents[name] = deps
        for dep in deps:
            descendants[dep].add(name)
    ready = [name for name, reqs in parents.items() if not reqs]
    heapq.heapify(ready)
    order = []
    while ready:
        node = heapq.heappop(ready)
        order.append(node)
        for nxt in sorted(descendants[node]):
            parents[nxt].discard(node)
            if not parents[nxt]:
                heapq.heappush(ready, nxt)
    if len(order) != len(tasks):
        return "DEPENDENCY_CYCLE", []
    return None, order


def review_workgraph(graph: object) -> dict:
    """Assess an existing proposal; do not plan, allocate or execute work."""
    reason, order = _valid_graph(graph)
    if reason is not None:
        return _hold(reason)
    assert isinstance(graph, dict)
    return {
        "schema": "r33/coordinator-review-result-v1",
        "status": "LOCAL_PLAN_REVIEW_ONLY",
        "workgraph_sha256": _digest(graph),
        "workspace": graph["workspace"],
        "task_count": len(order),
        "budget_units": graph["budget_units"],
        "execution_order": order,  # advisory topo order, NEVER dispatch.
        "held_effect_tasks": sorted(t["id"] for t in graph["tasks"]
                                     if t["effect_class"] == "external"),
        "native_execution_verified": False,
        "provider_authenticated": False,
        "recipient_readback_verified": False,
        "effect_authorized": False,
        "external_effect_authorized": False,
    }


def review_assertions(graph: object, reported: object) -> dict:
    """Check source consistency; neither self-authored PASS nor mock recipient is proof."""
    preflight = review_workgraph(graph)
    if preflight["status"] != "LOCAL_PLAN_REVIEW_ONLY":
        return _hold("WORKGRAPH_NOT_ADMITTED")
    if (type(reported) is not dict or set(reported) !=
            {"schema", "workgraph_sha256", "items"} or
            reported["schema"] != REPORT_SCHEMA or
            reported["workgraph_sha256"] != preflight["workgraph_sha256"]):
        return _hold("ASSERTION_SCHEMA_OR_SOURCE_MISMATCH")
    rows = reported["items"]
    assert isinstance(graph, dict)
    if type(rows) is not list or len(rows) != len(graph["tasks"]):
        return _hold("ASSERTION_COUNT_MISMATCH")
    planned = {task["id"]: task for task in graph["tasks"]}
    observed = set()
    held = []
    for row in rows:
        if type(row) is not dict or set(row) != ASSERTION_KEYS:
            return _hold("ASSERTION_FIELDS")
        task_id = row["task_id"]
        if type(task_id) is not str or task_id not in planned or task_id in observed:
            return _hold("ASSERTION_TASK_DUPLICATE_OR_UNKNOWN")
        observed.add(task_id)
        task = planned[task_id]
        if (row["actor_role"] != task["role"] or
            row["reviewer_role"] != task["reviewer"] or
            row["source_sha256"] != task["source_sha256"]):
            return _hold("ASSERTION_ROLE_OR_SOURCE_MISMATCH")
        actor, reviewer = row["actor_claim"], row["reviewer_claim"]
        if (type(actor) is not str or type(reviewer) is not str or
            actor not in ("completed", "unknown_effect", "failed", "not_started") or
            reviewer not in ("pass", "hold", "fail")):
            return _hold("INVALID_ASSERTION_STATUS")
        if actor == "completed" and reviewer != "pass":
            return _hold("COMPLETION_NOT_REVIEWED")
        if actor == "unknown_effect" and reviewer != "hold":
            return _hold("UNKNOWN_EFFECT_MUST_BE_HELD")
        if actor == "not_started" and reviewer != "hold":
            return _hold("NOT_STARTED_MUST_BE_HELD")
        if actor == "failed" and reviewer != "fail":
            return _hold("FAILURE_ASSERTION_MISMATCH")
        if task["effect_class"] == "external" or actor != "completed":
            held.append(task_id)
    return {
        "schema": "r33/coordinator-evidence-review-v1",
        "status": "UNATTESTED_ASSERTIONS_ONLY",
        "workgraph_sha256": preflight["workgraph_sha256"],
        "assertion_count": len(rows),
        "held_task_ids": sorted(set(held)),
        "native_execution_verified": False,
        "provider_authenticated": False,
        "recipient_readback_verified": False,
        "external_effect_authorized": False,
        "reason": "CALLER_ASSERTIONS_CANNOT_REPLACE_PROVIDER_OR_RECIPIENT_EVIDENCE",
    }

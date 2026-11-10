"""Pure offline Continuum resume verifier over existing Coordinator review source.

No second planner, task database, dispatcher, provider, allocator, scheduler or
native Omnium mission compiler. Caller-supplied actor/reviewer assertions are
UNATTESTED; a local SHA-256 is not an authenticated signer or effect grant.
"""
from __future__ import annotations

import hashlib
import json
import re

from .coordinator_review import review_assertions, review_workgraph

SCHEMA="r65/continuum-checkpoint-v1"
REVIEWED="UNATTESTED_LOCAL_CHECKPOINT"
_SHA=re.compile(r"^[a-f0-9]{64}$")
FIELDS=frozenset({
    "schema","status","workgraph_sha256","assertions_sha256",
    "review_sha256","advisory_order","held_task_ids",
    "provider_authenticated","native_execution_verified",
    "recipient_readback_verified","effect_authorized"
})


def _wire(payload: object) -> bytes:
    """Portable, deterministic, bounded checked JSON encoding."""
    try:
        data=json.dumps(payload,sort_keys=True,separators=(",",":"),
                        ensure_ascii=True,allow_nan=False).encode("utf-8")
    except (TypeError,ValueError,UnicodeError,RecursionError) as exc:
        raise ValueError("OFFLINE_CHECKPOINT_NOT_SERIALIZABLE") from exc
    if len(data)>131_072:
        raise ValueError("OFFLINE_CHECKPOINT_TOO_LARGE")
    return data


def _digest(payload: object) -> str:
    return hashlib.sha256(_wire(payload)).hexdigest()


def checkpoint_sha256(checkpoint: object) -> str:
    """Digest exact deterministic checkpoint content; NOT a signature."""
    if type(checkpoint) is not dict:
        raise ValueError("OFFLINE_CHECKPOINT_NOT_OBJECT")
    return _digest(checkpoint)


def capture_offline_checkpoint(graph: object, assertions: object) -> dict:
    """Review an existing graph and assertions, then derive an advisory pin.

    Does not inspect real providers, persist task state or mark any external
    work completed. The original Coordinator source owns plan validation.
    """
    plan=review_workgraph(graph)
    if plan.get("status")!="LOCAL_PLAN_REVIEW_ONLY":
        raise ValueError("WORKGRAPH_NOT_ADMITTED")
    reviewed=review_assertions(graph,assertions)
    if reviewed.get("status")!="UNATTESTED_ASSERTIONS_ONLY":
        raise ValueError("ASSERTIONS_NOT_ADMITTED")
    if (reviewed.get("workgraph_sha256")!=plan["workgraph_sha256"] or
        reviewed.get("recipient_readback_verified") is not False or
        reviewed.get("external_effect_authorized") is not False or
        reviewed.get("native_execution_verified") is not False or
        plan.get("effect_authorized") is not False or
        plan.get("provider_authenticated") is not False):
        raise ValueError("WORKGRAPH_AUTHORITY_NOT_ADMITTED")
    return {
        "schema":SCHEMA,
        "status":REVIEWED,
        "workgraph_sha256":plan["workgraph_sha256"],
        "assertions_sha256":_digest(assertions),
        "review_sha256":_digest({"plan":plan,"assertions_review":reviewed}),
        "advisory_order":list(plan["execution_order"]),
        "held_task_ids":list(reviewed["held_task_ids"]),
        "provider_authenticated":False,
        "native_execution_verified":False,
        "recipient_readback_verified":False,
        "effect_authorized":False,
    }


def resume_offline_checkpoint(checkpoint: object,graph: object,
                              assertions: object,expected_sha256: str) -> dict:
    """Fail-closed resume *advice* from an out-of-band pinned local snapshot.

    The host must independently authenticate the expected SHA and any actual
    source/actor/recipient; this method cannot grant or execute anything.
    """
    if type(expected_sha256) is not str or _SHA.fullmatch(expected_sha256) is None:
        raise ValueError("OUT_OF_BAND_CHECKPOINT_PIN_REQUIRED")
    if type(checkpoint) is not dict or set(checkpoint)!=FIELDS:
        raise ValueError("CHECKPOINT_FIELDS_NOT_ADMITTED")
    if (checkpoint["schema"]!=SCHEMA or checkpoint["status"]!=REVIEWED or
        any(checkpoint[field] is not False for field in (
            "provider_authenticated","native_execution_verified",
            "recipient_readback_verified","effect_authorized"))):
        raise ValueError("CHECKPOINT_AUTHORITY_NOT_ADMITTED")
    if checkpoint_sha256(checkpoint)!=expected_sha256:
        raise ValueError("CHECKPOINT_SHA_MISMATCH")
    canonical=capture_offline_checkpoint(graph,assertions)
    if checkpoint!=canonical:
        raise ValueError("CHECKPOINT_SOURCE_OR_REVIEW_DRIFT")
    return {
        "schema":"r65/continuum-local-resume-advice-v1",
        "status":"LOCAL_REVIEW_ONLY_RESUME",
        "checkpoint_sha256":expected_sha256,
        "workgraph_sha256":canonical["workgraph_sha256"],
        "advisory_order":list(canonical["advisory_order"]),
        "held_task_ids":list(canonical["held_task_ids"]),
        "checkpoint_authenticated_externally":False,
        "independent_review_authenticated":False,
        "native_execution_verified":False,
        "provider_authenticated":False,
        "recipient_readback_verified":False,
        "effect_authorized":False,
        "external_effect_authorized":False,
    }

"""Neutral Iron Ledger consumer of the existing Evidence Finder receipt chain.

Ported *behavioral contract*, not private donor code: read-only derived
receipt indexing, explicit head-staleness refusal, no duplicated persistence,
no task claim, and no implicit host authority.

The caller supplies an already opened EvidenceLedger-like read interface.
Its trust/identity is NOT independently authenticated by this module.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any

_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,79}$")
_SHA = re.compile(r"^[0-9a-f]{64}$")
_MAX_IDS = 32
_MAX_RECORDS = 512

_HEAD_KEYS = {
    "status", "scope", "receipt_count", "head_chain_sha256",
    "chain_verified_locally", "chain_externally_anchored",
    "source_owner_authenticated", "independent_truth_verified",
    "effect_authorized", "recipient_acknowledged", "native_muse_status",
}
_READ_KEYS = {
    "status", "scope", "finding", "receipt", "source_text_persisted_locally",
    "source_owner_authenticated", "independent_truth_verified",
    "effect_authorized", "recipient_acknowledged", "chain_externally_anchored",
    "native_muse_status",
}
_NO_AUTHORITY = {
    "native_muse_bound": False,
    "host_authority_authenticated": False,
    "source_owner_authenticated": False,
    "recipient_acknowledged": False,
    "external_effect_authorized": False,
    "redistribution_rights_verified": False,
    "independent_truth_verified": False,
}
_INDEX_BASE_KEYS = {
    "schema", "status", "scope", "head_chain_sha256", "receipt_count",
    "indexed_operations", "entries", *_NO_AUTHORITY.keys(),
}


class IronLedgerRefused(ValueError):
    """A local verified receipt index could not safely be established."""


def _digest(value: object) -> str:
    try:
        raw = json.dumps(value, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=True, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, UnicodeError, OverflowError) as exc:
        raise IronLedgerRefused("IRON_NONCANONICAL_PAYLOAD") from exc
    return hashlib.sha256(raw).hexdigest()


def _ids(value: object) -> list[str]:
    if (type(value) is not list or not 1 <= len(value) <= _MAX_IDS
        or any(type(item) is not str or _ID.fullmatch(item) is None
               for item in value)
        or len(set(value)) != len(value)):
        raise IronLedgerRefused("IRON_INVALID_OR_DUPLICATE_OPERATION_IDS")
    return sorted(value)


def _scope(value: object) -> dict[str, str]:
    expected = {"owner_id", "workspace_id", "role_id", "actor_id"}
    if (type(value) is not dict or set(value) != expected
        or any(type(v) is not str or _ID.fullmatch(v) is None
               for v in value.values())):
        raise IronLedgerRefused("IRON_INVALID_SCOPE")
    return dict(value)


def _head(value: object) -> dict:
    if (type(value) is not dict or set(value) != _HEAD_KEYS or
        value.get("status") != "LOCAL_EVIDENCE_CHAIN_VERIFIED" or
        value.get("chain_verified_locally") is not True or
        value.get("native_muse_status") != "NOT_INVOKED" or
        any(value.get(flag) is not False for flag in (
            "chain_externally_anchored", "source_owner_authenticated",
            "independent_truth_verified", "effect_authorized",
            "recipient_acknowledged"))):
        raise IronLedgerRefused("IRON_UNVERIFIED_EVIDENCE_HEAD")
    count = value["receipt_count"]
    digest = value["head_chain_sha256"]
    if (type(count) is not int or not 1 <= count <= _MAX_RECORDS or
        type(digest) is not str or _SHA.fullmatch(digest) is None):
        raise IronLedgerRefused("IRON_INVALID_HEAD")
    return {
        "scope": _scope(value["scope"]),
        "receipt_count": count,
        "head_chain_sha256": digest,
    }


def _read_record(value: object, *, operation_id: str, head: dict) -> dict:
    if (type(value) is not dict or set(value) != _READ_KEYS or
        value.get("status") != "LOCAL_EVIDENCE_REOPENED" or
        value.get("native_muse_status") != "NOT_INVOKED" or
        any(value.get(flag) is not False for flag in (
            "source_owner_authenticated", "independent_truth_verified",
            "effect_authorized", "recipient_acknowledged",
            "chain_externally_anchored"))):
        raise IronLedgerRefused("IRON_UNVERIFIED_READ_RESPONSE")
    if _scope(value["scope"]) != head["scope"]:
        raise IronLedgerRefused("IRON_SCOPE_MISMATCH")
    receipt = value["receipt"]
    finding = value["finding"]
    if (type(receipt) is not dict or
        set(receipt) != {"operation_id", "sequence", "record_sha256",
                         "previous_chain_sha256", "chain_sha256"} or
        receipt.get("operation_id") != operation_id or
        type(receipt.get("sequence")) is not int or
        not 1 <= receipt["sequence"] <= head["receipt_count"] or
        any(type(receipt.get(k)) is not str or
            _SHA.fullmatch(receipt[k]) is None
            for k in ("record_sha256", "previous_chain_sha256", "chain_sha256"))):
        raise IronLedgerRefused("IRON_INVALID_RECEIPT")
    if (type(finding) is not dict or
        set(finding) != {"source_uri", "source_sha256", "observation", "result"} or
        type(finding["source_sha256"]) is not str or
        _SHA.fullmatch(finding["source_sha256"]) is None or
        type(finding["source_uri"]) is not str or
        not finding["source_uri"] or
        type(finding["observation"]) is not str or
        finding["result"] not in ("FOUND", "NOT_FOUND")):
        raise IronLedgerRefused("IRON_INVALID_FINDING")
    found = finding["result"] == "FOUND"
    if (value["source_text_persisted_locally"] is not found or
        (found and hashlib.sha256(finding["observation"].encode("utf-8")).hexdigest()
         != finding["source_sha256"]) or
        (not found and finding["observation"] != "")):
        raise IronLedgerRefused("IRON_FINDING_SOURCE_MISMATCH")
    return {
        "operation_id": operation_id,
        "sequence": receipt["sequence"],
        "record_sha256": receipt["record_sha256"],
        "previous_chain_sha256": receipt["previous_chain_sha256"],
        "chain_sha256": receipt["chain_sha256"],
        "source_sha256": finding["source_sha256"],
        "outcome": finding["result"],
    }


def _interface(reader: object) -> None:
    if (not callable(getattr(reader, "verify", None)) or
        not callable(getattr(reader, "read", None))):
        raise IronLedgerRefused("IRON_LEDGER_READER_UNBOUND")


def build_local_receipt_index(reader: Any, operation_ids: object) -> dict:
    """Return a finite non-persistent receipt index, pinned to a live head.

    Read-only operations invoke the injected reader's existing authority
    resolver. A separate, authenticated host-side principal is still needed
    before this evidence can trigger an effect.
    """
    ids = _ids(operation_ids)
    _interface(reader)
    try:
        head = _head(reader.verify())
        entries = [_read_record(reader.read(op), operation_id=op, head=head)
                   for op in ids]
        latest = _head(reader.verify())
    except IronLedgerRefused:
        raise
    except Exception as exc:
        raise IronLedgerRefused("IRON_LEDGER_READ_OR_VERIFY_FAILED") from exc
    if latest != head:
        raise IronLedgerRefused("IRON_STALE_EVIDENCE_HEAD")
    if len({entry["sequence"] for entry in entries}) != len(entries):
        raise IronLedgerRefused("IRON_DUPLICATE_RECEIPT_SEQUENCE")
    body = {
        "schema": "software-engineer/iron-ledger-consumer-index-v1",
        "status": "LOCAL_RECEIPTS_INDEXED_ONLY",
        **head,
        "indexed_operations": len(entries),
        "entries": sorted(entries, key=lambda x: x["operation_id"]),
        **_NO_AUTHORITY,
    }
    return {**body, "index_sha256": _digest(body)}


def verify_local_receipt_index(reader: Any, index: object) -> dict:
    """Reopen and reweigh the exact selected operations and current head.

    Any head growth, source receipt alteration or forged index field refuses
    instead of silently serving a stale or user-edited sidecar snapshot.
    """
    if (type(index) is not dict or
        set(index) != _INDEX_BASE_KEYS | {"index_sha256"} or
        index.get("schema") != "software-engineer/iron-ledger-consumer-index-v1" or
        index.get("status") != "LOCAL_RECEIPTS_INDEXED_ONLY" or
        any(index.get(key) is not False for key in _NO_AUTHORITY) or
        type(index.get("entries")) is not list or
        type(index.get("index_sha256")) is not str or
        _SHA.fullmatch(index["index_sha256"]) is None):
        raise IronLedgerRefused("IRON_INVALID_INDEX")
    body = {key: value for key, value in index.items() if key != "index_sha256"}
    if _digest(body) != index["index_sha256"]:
        raise IronLedgerRefused("IRON_INDEX_TAMPERED")
    if (type(index["indexed_operations"]) is not int or
        index["indexed_operations"] != len(index["entries"])):
        raise IronLedgerRefused("IRON_INVALID_INDEX_COUNT")
    operations = []
    for entry in index["entries"]:
        if type(entry) is not dict or type(entry.get("operation_id")) is not str:
            raise IronLedgerRefused("IRON_INVALID_INDEX_ENTRY")
        operations.append(entry["operation_id"])
    _ids(operations)
    _interface(reader)
    try:
        head = _head(reader.verify())
    except IronLedgerRefused:
        raise
    except Exception as exc:
        raise IronLedgerRefused("IRON_LEDGER_VERIFY_FAILED") from exc
    if (head["scope"] != _scope(index["scope"]) or
        head["receipt_count"] != index["receipt_count"] or
        head["head_chain_sha256"] != index["head_chain_sha256"]):
        raise IronLedgerRefused("IRON_STALE_EVIDENCE_HEAD")
    refreshed = build_local_receipt_index(reader, operations)
    if refreshed != index:
        raise IronLedgerRefused("IRON_INDEX_READBACK_MISMATCH")
    return {
        "status": "LOCAL_INDEX_VERIFIED",
        "indexed_operations": len(operations),
        "head_chain_sha256": head["head_chain_sha256"],
        "index_sha256": index["index_sha256"],
        **_NO_AUTHORITY,
    }



# R32.2b — LOCAL READ-ONLY TaskGuard compatibility layer. Claim Gate remains
# the only idempotency writer; original donor claim/release methods are NEVER
# copied. Nothing here grants a new claim, resumes an effect or deletes state.
_TASK_RUN_PREFIX = "tg_"
_TASK_RUN_MAX = 32
_TASK_RECORD_STATES = {"CLAIMED", "EFFECT_DONE", "UNKNOWN", "CANCELLED"}
_TASK_DENIED_AUTHORITY = (
    "native_muse_bound", "source_owner_authenticated",
    "external_effect_authorized", "recipient_acknowledged",
    "host_authority_authenticated",
)


def task_run_claim_id(task_id: str, run_id: str) -> str:
    """Deterministically bind an explicit task and run to one Claim Gate ID."""
    if (type(task_id) is not str or _ID.fullmatch(task_id) is None
            or type(run_id) is not str or _ID.fullmatch(run_id) is None):
        raise IronLedgerRefused("TASK_GUARD_INVALID_TASK_RUN_ID")
    return _TASK_RUN_PREFIX + _digest({
        "schema": "software-engineer/task-run-identity-v1",
        "task_id": task_id, "run_id": run_id,
    })[:48]


def review_local_task_run(
    reader: Any, *, scope: str, task_id: str, run_id: str,
    expected_payload_sha256: str,
) -> dict:
    """Classify an existing Claim Gate identity without mutating its state.

    A missing, incomplete, expired, corrupted or UNKNOWN local claim is NEVER
    permission to start. A locally completed claim is not a real recipient
    ACK. The true host must verify authority and effect outcome separately.
    """
    if type(scope) is not str or _ID.fullmatch(scope) is None:
        raise IronLedgerRefused("TASK_GUARD_SCOPE_INVALID")
    claim_id = task_run_claim_id(task_id, run_id)
    if (type(expected_payload_sha256) is not str or
            _SHA.fullmatch(expected_payload_sha256) is None):
        raise IronLedgerRefused("TASK_GUARD_PAYLOAD_PIN_REQUIRED")
    read=getattr(reader, "reconcile_unknown", None)
    if not callable(read):
        raise IronLedgerRefused("TASK_GUARD_READER_UNBOUND")

    def report(status: str, terminal: bool = False) -> dict:
        return {
            "schema": "software-engineer/task-run-local-review-v1",
            "scope": scope,
            "claim_id": claim_id,
            "task_id": task_id,
            "run_id": run_id,
            "expected_payload_sha256": expected_payload_sha256,
            "status": status,
            "hold_required": True,
            "local_terminal_observed": terminal,
            "safe_to_claim": False,
            "safe_to_resume": False,
            "safe_to_retry": False,
            "safe_to_release": False,
            "claim_registry_modified": False,
            "native_muse_bound": False,
            "source_owner_authenticated": False,
            "host_authority_authenticated": False,
            "recipient_acknowledged": False,
            "independent_recipient_acknowledged": False,
            "external_effect_authorized": False,
            "external_effect_performed": False,
            "redistribution_rights_verified": False,
        }
    try:
        record = read(scope, claim_id)
    except Exception:
        # Do not serialize an underlying private path/claim error message.
        return report("LOCAL_UNREADABLE_HELD")
    if record is None:
        # Another caller may have executed an effect whose receipt was lost.
        # Absence cannot rearm the run or mint a new attempt.
        return report("LOCAL_UNVERIFIED_ABSENCE_HELD")
    if (type(record) is not dict or
        any(record.get(field) is True for field in _TASK_DENIED_AUTHORITY)
        or (record.get("pruned") is not None and
            record.get("pruned") is not True)
        or type(record.get("state")) is not str or
        record["state"] not in _TASK_RECORD_STATES):
        return report("LOCAL_UNTRUSTED_RECORD_HELD")
    if (record.get("scope") != scope or
            record.get("claim_id") != claim_id):
        return report("LOCAL_IDENTITY_MISMATCH_HELD")
    if (type(record.get("payload_digest")) is not str or
        _SHA.fullmatch(record["payload_digest"]) is None):
        return report("LOCAL_UNTRUSTED_RECORD_HELD")
    if record["payload_digest"] != expected_payload_sha256:
        return report("LOCAL_PAYLOAD_MISMATCH_HELD")
    state=record["state"]
    if state == "UNKNOWN":
        return report("LOCAL_UNKNOWN_HELD")
    if state == "CLAIMED":
        return report("LOCAL_IN_FLIGHT_HELD")
    if state == "CANCELLED":
        return report("LOCAL_CANCELLED_HELD", terminal=True)
    if state == "EFFECT_DONE":
        return report("LOCAL_TERMINAL_UNVERIFIED", terminal=True)
    return report("LOCAL_UNTRUSTED_RECORD_HELD")


def review_local_task_runs(
    reader: Any, *, scope: str, entries: object,
) -> dict:
    """Bounded multi-run local classification, never a scheduler/claim owner."""
    if type(entries) is not list or not 1 <= len(entries) <= _TASK_RUN_MAX:
        raise IronLedgerRefused("TASK_GUARD_BATCH_UNBOUNDED")
    expected={"task_id", "run_id", "expected_payload_sha256"}
    checked=[]
    seen=set()
    for entry in entries:
        if type(entry) is not dict or set(entry) != expected:
            raise IronLedgerRefused("TASK_GUARD_INVALID_BATCH_ENTRY")
        claim_id=task_run_claim_id(entry["task_id"],entry["run_id"])
        if claim_id in seen:
            raise IronLedgerRefused("TASK_GUARD_DUPLICATE_RUN")
        seen.add(claim_id)
        checked.append((claim_id,entry))
    assessments=[
        review_local_task_run(reader,scope=scope,**entry)
        for _,entry in sorted(checked)
    ]
    return {
        "schema": "software-engineer/task-run-local-batch-v1",
        "status": "LOCAL_HOLDS_REQUIRE_REVIEW",
        "assessments": assessments,
        "hold_count": len(assessments),
        "claim_registry_modified": False,
        "native_muse_bound": False,
        "source_owner_authenticated": False,
        "host_authority_authenticated": False,
        "external_effect_authorized": False,
        "independent_recipient_acknowledged": False,
        "safe_to_claim": False,
        "safe_to_resume": False,
        "safe_to_retry": False,
        "safe_to_release": False,
    }



# R32.2c — LOCAL cross-reader observation only. The native Muse host and a
# real target MUST independently authenticate their own callers/receipts.
# This adapter never interprets caller-supplied assertions as authority.
_OBSERVED_ACTOR_FIELDS = {
    "schema", "scope", "owner_id", "actor_id", "session_id",
    "status", "host_authenticated", "effect_authorized",
}
_OBSERVED_TARGET_FIELDS = {
    "schema", "recipient_id", "claim_id", "payload_sha256",
    "status", "recipient_authenticated", "external_effect_verified",
}
_OBSERVED_OUTCOMES = {"SUCCESS", "FAILED", "NOT_FOUND", "UNKNOWN"}
_OBSERVATION_MAX_BYTES = 131072
_NO_CLAIM_PRIVILEGE = (
    *_TASK_DENIED_AUTHORITY,
    "safe_to_claim", "safe_to_resume", "safe_to_retry", "safe_to_release",
    "recipient_authenticated", "independent_recipient_acknowledged",
)


def _local_claim_snapshot(value: object, *, scope: str, claim_id: str,
                          payload_sha256: str) -> str | None:
    """Conservative readback fingerprint, never an authenticated claim."""
    if (type(value) is not dict or value.get("scope") != scope or
            value.get("claim_id") != claim_id or
            value.get("payload_digest") != payload_sha256 or
            value.get("state") not in _TASK_RECORD_STATES or
            any(name in value and value[name] is not False
                for name in _NO_CLAIM_PRIVILEGE)):
        return None
    if (value.get("pruned") is not None and value["pruned"] is not True):
        return None
    token=value.get("fencing_token")
    if token is not None and (type(token) is not int or token < 0):
        return None
    lease_owner=value.get("lease_owner")
    if lease_owner is not None and (
            type(lease_owner) is not str or _ID.fullmatch(lease_owner) is None):
        return None
    state=value["state"]
    outcome=value.get("outcome")
    if (state=="EFFECT_DONE" and outcome not in ("SUCCESS", "FAILED")) or (
            state in ("CLAIMED", "UNKNOWN", "CANCELLED") and outcome is not None):
        return None
    try:
        # An existing local claim may include bounded history. Avoid hashing
        # arbitrary giant host-returned objects or emitting their content.
        raw=json.dumps(value,sort_keys=True,separators=(",",":"),
                       ensure_ascii=True,allow_nan=False)
        if len(raw.encode("utf-8")) > _OBSERVATION_MAX_BYTES:
            return None
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()
    except (TypeError, ValueError, UnicodeError, OverflowError):
        return None


def review_local_task_observations(
    claim_reader: Any, actor_reader: Any, recipient_reader: Any, *,
    scope: str, task_id: str, run_id: str, expected_payload_sha256: str,
    owner_id: str, actor_id: str, session_id: str, recipient_id: str,
) -> dict:
    """Compare three *injected* local observations without creating authority.

    Read order: local Claim Gate -> host assertion -> recipient assertion ->
    local Claim Gate again. Any mismatch, incomplete evidence, disagreement,
    changed claim or adapter error is HELD. Even a complete match remains
    LOCAL_ASSERTION_ONLY and NEVER gives permission to retry, release, claim
    or perform an external effect. Injected readers can be mocked, so this
    implementation is not native authentication or recipient verification.
    """
    identifiers = {
        "scope": scope, "owner_id": owner_id, "actor_id": actor_id,
        "session_id": session_id, "recipient_id": recipient_id,
    }
    if (any(type(v) is not str or _ID.fullmatch(v) is None
            for v in identifiers.values()) or
        type(expected_payload_sha256) is not str or
            _SHA.fullmatch(expected_payload_sha256) is None):
        raise IronLedgerRefused("OBSERVATION_INVALID_ID_OR_SOURCE_PIN")
    claim_id=task_run_claim_id(task_id,run_id)
    if actor_reader is recipient_reader:
        raise IronLedgerRefused("OBSERVATION_INDEPENDENCE_REQUIRED")
    claims_read=getattr(claim_reader,"reconcile_unknown",None)
    actor_read=getattr(actor_reader,"inspect_actor",None)
    recipient_read=getattr(recipient_reader,"inspect_receipt",None)
    if not all(callable(x) for x in (claims_read,actor_read,recipient_read)):
        raise IronLedgerRefused("OBSERVATION_READERS_UNBOUND")

    def report(status: str, *, actor_match: bool=False,
               target_match: bool=False, outcome_match: bool=False) -> dict:
        return {
            "schema": "software-engineer/local-task-observation-v1",
            "status": status,
            "proof_grade": "LOCAL_ASSERTION_ONLY",
            "claim_id": claim_id,
            "expected_payload_sha256": expected_payload_sha256,
            "hold_required": True,
            "actor_binding_matches": actor_match,
            "recipient_binding_matches": target_match,
            "reported_outcome_consistent": outcome_match,
            "safe_to_claim": False,
            "safe_to_retry": False,
            "safe_to_release": False,
            "safe_to_resume": False,
            "claim_registry_modified": False,
            "native_muse_bound": False,
            "host_owner_authenticated": False,
            "source_owner_authenticated": False,
            "recipient_acknowledged": False,
            "independent_recipient_acknowledged": False,
            "external_effect_authorized": False,
            "external_effect_performed": False,
            "redistribution_rights_verified": False,
        }

    try:
        before=claims_read(scope,claim_id)
    except Exception:
        return report("LOCAL_CLAIM_NOT_ADMITTED_HELD")
    baseline=_local_claim_snapshot(
        before,scope=scope,claim_id=claim_id,
        payload_sha256=expected_payload_sha256)
    if baseline is None:
        return report("LOCAL_CLAIM_NOT_ADMITTED_HELD")

    try:
        actor=actor_read(scope,owner_id,actor_id,session_id)
    except Exception:
        return report("LOCAL_ACTOR_READ_FAILED_HELD")
    if (type(actor) is not dict or set(actor)!=_OBSERVED_ACTOR_FIELDS or
            actor.get("schema")!="software-engineer/local-actor-observation-v1" or
            actor.get("status")!="CALLER_SUPPLIED_ASSERTION" or
            actor.get("host_authenticated") is not False or
            actor.get("effect_authorized") is not False):
        return report("LOCAL_UNTRUSTED_ACTOR_ASSERTION_HELD")
    if any(actor.get(k)!=v for k,v in (
            ("scope",scope),("owner_id",owner_id),("actor_id",actor_id),
            ("session_id",session_id))):
        return report("LOCAL_ACTOR_BINDING_MISMATCH_HELD")

    try:
        target=recipient_read(recipient_id,claim_id)
    except Exception:
        return report("LOCAL_TARGET_READ_FAILED_HELD",actor_match=True)
    if (type(target) is not dict or set(target)!=_OBSERVED_TARGET_FIELDS or
            target.get("schema")!="software-engineer/local-recipient-observation-v1" or
            type(target.get("status")) is not str or
            target["status"] not in _OBSERVED_OUTCOMES or
            target.get("recipient_authenticated") is not False or
            target.get("external_effect_verified") is not False):
        return report("LOCAL_UNTRUSTED_TARGET_ASSERTION_HELD",actor_match=True)
    if (target.get("recipient_id")!=recipient_id or
        target.get("claim_id")!=claim_id or
        target.get("payload_sha256")!=expected_payload_sha256):
        return report("LOCAL_TARGET_BINDING_MISMATCH_HELD",actor_match=True)

    try:
        after=claims_read(scope,claim_id)
    except Exception:
        return report("LOCAL_CLAIM_CHANGED_DURING_REVIEW_HELD")
    ending=_local_claim_snapshot(
        after,scope=scope,claim_id=claim_id,
        payload_sha256=expected_payload_sha256)
    if ending is None or ending!=baseline:
        return report("LOCAL_CLAIM_CHANGED_DURING_REVIEW_HELD")

    state=before["state"]
    target_state=target["status"]
    if target_state in ("UNKNOWN","NOT_FOUND"):
        return report("LOCAL_TARGET_UNRESOLVED_HELD",actor_match=True,
                      target_match=True)
    if state=="UNKNOWN":
        return report("LOCAL_UNKNOWN_WITH_TARGET_ASSERTION_HELD",
                      actor_match=True,target_match=True)
    if state=="CLAIMED":
        return report("LOCAL_IN_FLIGHT_WITH_TARGET_ASSERTION_HELD",
                      actor_match=True,target_match=True)
    if state=="CANCELLED":
        return report("LOCAL_CANCELLED_WITH_TARGET_ASSERTION_HELD",
                      actor_match=True,target_match=True)
    if before.get("outcome")!=target_state:
        return report("LOCAL_TARGET_OUTCOME_MISMATCH_HELD",
                      actor_match=True,target_match=True)
    return report("LOCAL_CONSISTENT_UNAUTHENTICATED_HELD",
                  actor_match=True,target_match=True,outcome_match=True)

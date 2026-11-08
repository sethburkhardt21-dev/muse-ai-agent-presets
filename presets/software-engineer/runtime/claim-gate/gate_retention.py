"""Claim retention and compaction for the Claim Gate.

The gate's journal grows without bound. Two measured vectors (GATE-BUILD-004,
confirmed by Challenger C 2026-10-13):

1. Terminal claim files (EFFECT_DONE / CANCELLED) are never removed — the
   module accumulates one file per settled claim forever.
2. Every knock appends a history entry (+128 bytes/knock, linear, unbounded);
   any knocker, including a hostile one spamming a held claim, can bloat a
   claim file forever. (Bounded separately by MAX_HISTORY_ENTRIES in
   claim_gate._append_history.)

This module implements the retention policy:

- PRUNE: terminal claims (EFFECT_DONE, CANCELLED) whose claim file has not
  been touched for longer than ``older_than_days`` may be pruned by an
  explicit operator call (``ClaimGate.prune_terminal``). Pruning removes the
  claim file but first appends its essential truth to the per-scope
  append-only digest log: ``claims/<scope>/.digest-log.jsonl``.
- The digest log preserves, per pruned claim: claim_id, payload_digest,
  payload_len, state, outcome, cancel_reason, fencing_token, lease_owner,
  created_ts, pruned_ts. The full history is compacted away; the sealed
  project evidence remains the deep audit trail.
- The per-scope ``.fencing`` counter is NEVER reset by pruning. Any later
  claim of a fresh name mints a strictly larger token than every token the
  pruned claim ever held.
- A pruned name is BURNED, not freed: re-claiming the same bytes returns the
  pruned summary as an idempotent reuse (no new effect); re-claiming
  different bytes raises ReplayRefused. The gate consults the digest log on
  every claim-file miss, so idempotency survives pruning.
- NEVER pruned: CLAIMED (live), UNKNOWN (held open for reconciliation),
  corrupt records, or terminal claims touched within the retention window.
- Pruning never executes an effect, never changes a state, never re-arms a
  lease. It is crash-idempotent: a crash between log-append and file-delete
  leaves at most a duplicate log line on retry, and re-prune skips the
  append when an identical entry already exists.

Charter note: this is an explicit, bounded exception to the charter's
"a claim file is never deleted" (see GATE-CHARTER.md, Retention Amendment
2026-10-13). The rite of erasure exists now, but only for settled claims,
only after the retention window, only with the digest preserved, and only
by an explicit operator hand — never by the gate on its own.

This module never imports claim_gate at module level (one-direction
dependency: claim_gate -> gate_retention). Scope names are validated with a
local copy of the safe-component pattern.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import time

DIGEST_LOG_NAME = ".digest-log.jsonl"
RETENTION_ANCHOR_NAME = ".digest-log.anchor.json"
MAX_RETENTION_LOG_BYTES = 8_388_608
DEFAULT_RETENTION_DAYS = 30

_COMPONENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


def _check_scope_component(scope: str) -> str:
    if not isinstance(scope, str) or not _COMPONENT.fullmatch(scope):
        raise ValueError("unsafe scope component: %r" % (scope,))
    return scope


def _utcnow() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def digest_log_path(state_dir: str, scope: str) -> str:
    """Path of the per-scope append-only digest log."""
    _check_scope_component(scope)
    return os.path.join(state_dir, "claims", scope, DIGEST_LOG_NAME)


class RetentionIntegrityError(ValueError):
    """History unreadable or inconsistent: never treat it as no prior effect."""


def _checked_retention(state_dir: str, scope: str) -> tuple[list[dict], bytes]:
    """Validate all retained tombstones and the local per-scope log checksum.

    A missing log AND anchor is allowed only as a not-yet-pruned scope.
    Once pruning has occurred, this anchor makes missing/empty/truncated
    logs fail closed. It is local integrity, NOT an independently signed
    witness against an adversary who can rewrite *both* files.
    """
    log=digest_log_path(state_dir,scope)
    anchor=os.path.join(os.path.dirname(log),RETENTION_ANCHOR_NAME)
    log_present=os.path.lexists(log)
    anchor_present=os.path.lexists(anchor)
    if not log_present and not anchor_present:
        return [],b""
    if not log_present or not anchor_present:
        raise RetentionIntegrityError("RETENTION_HISTORY_OR_ANCHOR_MISSING")
    if (os.path.islink(log) or os.path.islink(anchor) or
            not os.path.isfile(log) or not os.path.isfile(anchor)):
        raise RetentionIntegrityError("RETENTION_HISTORY_UNSAFE_PATH")
    try:
        with open(log,"rb") as handle:
            raw=handle.read(MAX_RETENTION_LOG_BYTES+1)
        if not raw or len(raw)>MAX_RETENTION_LOG_BYTES or not raw.endswith(b"\n"):
            raise RetentionIntegrityError("RETENTION_HISTORY_EMPTY_OR_TORN")
        records=[]
        for line in raw.splitlines():
            if not line:
                raise RetentionIntegrityError("RETENTION_HISTORY_BLANK_LINE")
            record=json.loads(line.decode("utf-8"))
            if (type(record) is not dict or
                    not all(key in record for key in (
                        "claim_id","payload_digest","state","pruned_ts")) or
                    type(record["claim_id"]) is not str or
                    type(record["payload_digest"]) is not str or
                    not re.fullmatch("[0-9a-f]{64}",record["payload_digest"]) or
                    record["state"] not in ("EFFECT_DONE","CANCELLED")):
                raise RetentionIntegrityError("RETENTION_HISTORY_INVALID_RECORD")
            records.append(record)
        with open(anchor,"r",encoding="utf-8") as handle:
            witness=json.load(handle)
        if (type(witness) is not dict or set(witness)!={
                "schema","scope","log_sha256","entry_count"} or
            witness["schema"]!="software-engineer/local-retention-anchor-v1" or
            witness["scope"]!=scope or
            type(witness["entry_count"]) is not int or
            witness["entry_count"]!=len(records) or
            witness["log_sha256"]!=hashlib.sha256(raw).hexdigest()):
            raise RetentionIntegrityError("RETENTION_ANCHOR_MISMATCH")
        return records,raw
    except RetentionIntegrityError:
        raise
    except (OSError,ValueError,TypeError,UnicodeError) as exc:
        raise RetentionIntegrityError("RETENTION_HISTORY_INVALID") from exc


def _write_retention_anchor(state_dir:str, scope:str,
                            raw:bytes, record_count:int)->None:
    directory=os.path.dirname(digest_log_path(state_dir,scope))
    body={
        "schema":"software-engineer/local-retention-anchor-v1",
        "scope":scope,
        "log_sha256":hashlib.sha256(raw).hexdigest(),
        "entry_count":record_count,
    }
    fd,temp=tempfile.mkstemp(dir=directory,prefix=".retention-",suffix=".tmp")
    target=os.path.join(directory,RETENTION_ANCHOR_NAME)
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as handle:
            json.dump(body,handle,sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp,target)
        if hasattr(os,"O_DIRECTORY"):
            parent=os.open(directory,os.O_RDONLY|os.O_DIRECTORY)
            try:os.fsync(parent)
            finally:os.close(parent)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def append_digest_entry(state_dir: str, scope: str, entry: dict) -> None:
    """Append and anchor one terminal digest before deleting the claim file.

    Must be called under ClaimGate's per-scope exclusive lock. A torn append,
    failed anchor write or older unanchored log remains held for operator
    reconciliation. No implicit migration of an unverified legacy log.
    """
    if (type(entry) is not dict or
        any(key not in entry for key in (
            "claim_id","payload_digest","state","pruned_ts")) or
        entry["state"] not in ("EFFECT_DONE","CANCELLED") or
        type(entry["payload_digest"]) is not str or
        not re.fullmatch("[0-9a-f]{64}",entry["payload_digest"])):
        raise RetentionIntegrityError("RETENTION_ENTRY_INVALID")
    path=digest_log_path(state_dir,scope)
    os.makedirs(os.path.dirname(path),exist_ok=True)
    existing,raw=_checked_retention(state_dir,scope)
    line=(json.dumps(entry,sort_keys=True,allow_nan=False)+"\n").encode("utf-8")
    if len(raw)+len(line)>MAX_RETENTION_LOG_BYTES:
        raise RetentionIntegrityError("RETENTION_HISTORY_FULL")
    flags=os.O_WRONLY|os.O_APPEND|os.O_CREAT|getattr(os,"O_NOFOLLOW",0)
    fd=os.open(path,flags,0o600)
    with os.fdopen(fd,"ab") as handle:
        handle.write(line)
        handle.flush()
        os.fsync(handle.fileno())
    # Appending before updating the anchor is intentional: a crash here
    # yields an inconsistent log and causes all future claims to HOLD.
    _write_retention_anchor(state_dir,scope,raw+line,len(existing)+1)
    checked,_=_checked_retention(state_dir,scope)
    if len(checked)!=len(existing)+1:
        raise RetentionIntegrityError("RETENTION_APPEND_READBACK_FAILED")


def lookup_pruned(state_dir: str, scope: str, claim_id: str) -> dict | None:
    """Last verified digest-log record, or None only for a genuine empty scope."""
    entries,_=_checked_retention(state_dir,scope)
    return next((entry for entry in reversed(entries)
                 if entry["claim_id"]==claim_id),None)


def has_digest_entry(state_dir: str, scope: str, claim_id: str,
                     payload_digest: str, state: str) -> bool:
    """Read-only verified dedup; damaged retention history must refuse."""
    entries,_=_checked_retention(state_dir,scope)
    return any(entry["claim_id"]==claim_id and
               entry["payload_digest"]==payload_digest and
               entry["state"]==state for entry in entries)


def pruned_summary(scope: str, claim_id: str, entry: dict) -> dict:
    """Build the gate-record-shaped summary the claim paths return for a
    pruned name. Carries ``pruned: True`` so callers can distinguish it
    from a live record. Full history was compacted away; the digest log
    is the audit remnant."""
    return {
        "scope": scope,
        "claim_id": claim_id,
        "payload_digest": entry.get("payload_digest"),
        "payload_len": entry.get("payload_len"),
        "state": entry.get("state"),
        "outcome": entry.get("outcome"),
        "receipt": None,
        "cancel_reason": entry.get("cancel_reason"),
        "created_ts": entry.get("created_ts"),
        "pruned": True,
        "pruned_ts": entry.get("pruned_ts"),
        "fencing_token": entry.get("fencing_token"),
        "lease_owner": entry.get("lease_owner"),
        "history": [],
    }

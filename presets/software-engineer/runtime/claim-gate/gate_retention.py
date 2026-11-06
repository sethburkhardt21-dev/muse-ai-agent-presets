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

import json
import os
import re
import time

DIGEST_LOG_NAME = ".digest-log.jsonl"
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


def append_digest_entry(state_dir: str, scope: str, entry: dict) -> None:
    """Append one JSON line to the digest log and fsync it.

    Entry must be a JSON-serializable dict. Raises ValueError on bad input.
    """
    if not isinstance(entry, dict):
        raise ValueError("digest entry must be a dict")
    for key in ("claim_id", "payload_digest", "state", "pruned_ts"):
        if key not in entry:
            raise ValueError("digest entry missing %r" % key)
    path = digest_log_path(state_dir, scope)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    line = json.dumps(entry, sort_keys=True) + "\n"
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(line)
        fh.flush()
        os.fsync(fh.fileno())


def lookup_pruned(state_dir: str, scope: str, claim_id: str) -> dict | None:
    """Return the LAST digest-log entry for claim_id, or None.

    Linear scan; the log is append-only and pruned claims are rare relative
    to live traffic. Returns None when the log is absent or has no entry.
    """
    path = digest_log_path(state_dir, scope)
    if not os.path.exists(path):
        return None
    found = None
    try:
        fh = open(path, "r", encoding="utf-8")
    except OSError:
        # D-D2: the log path is unreadable (e.g. a directory planted by a
        # rogue local writer). Treat as absent — consistent with a missing
        # log, and grants no new privilege: a writer who can plant the
        # directory can already delete the log outright.
        return None
    with fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except (ValueError, TypeError):
                continue  # a torn line can only come from a killed writer;
                # the fsync discipline makes this near-impossible, and a
                # skipped line fails closed (the claim file is the truth
                # while it exists).
            if isinstance(entry, dict) and entry.get("claim_id") == claim_id:
                found = entry
    return found


def has_digest_entry(state_dir: str, scope: str, claim_id: str,
                     payload_digest: str, state: str) -> bool:
    """True iff the log already records this exact pruned claim.

    Used to make prune crash-idempotent: retrying after a crash between
    log-append and file-delete must not duplicate the entry.
    """
    path = digest_log_path(state_dir, scope)
    if not os.path.exists(path):
        return False
    try:
        fh = open(path, "r", encoding="utf-8")
    except OSError:
        # D-D2: see lookup_pruned — treat an unreadable log as absent.
        return False
    with fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except (ValueError, TypeError):
                continue
            if (isinstance(entry, dict)
                    and entry.get("claim_id") == claim_id
                    and entry.get("payload_digest") == payload_digest
                    and entry.get("state") == state):
                return True
    return False


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

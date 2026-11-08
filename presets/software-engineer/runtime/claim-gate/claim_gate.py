"""Claim Gate — atomic claim/idempotency/cancellation machinery.

module 2 (Claim Gate), GATE-001 deepening. This module is the idempotency layer
beneath effect execution: one writer per scope, changed-byte replay refusal, and
UNKNOWN reconciliation that never triggers another effect.

Storage:  <state_dir>/claims/<scope>/<claim_id>.json
Locking:  one lock file per scope, <state_dir>/claims/<scope>/.lock, held with
           fcntl.flock(LOCK_EX) across every mutation. fcntl locking is
           advisory — all writers of claim state MUST go through ClaimGate.

Claim files are NEVER deleted by the claim paths — except through the explicit
retention rite in gate_retention (GATE-BUILD-004): terminal claims older than
the retention window may be pruned by an operator hand, with their digest
preserved in the per-scope digest log and the fencing counter never reset.
Cancel annotates; it does not erase.

States: CLAIMED -> EFFECT_DONE | UNKNOWN ; CLAIMED -> CANCELLED.
        A claim never moves backward and never disappears.

Usage pattern for a consumer:

    gate = ClaimGate("/var/lib/software-engineer/claim-gate")
    claimed, existing = gate.claim("payments", "inv-1001", payload_bytes)
    if claimed:
        try:
            receipt = execute_effect(payload_bytes)
        except OutcomeUnknown:
            gate.mark_unknown("payments", "inv-1001", "effect call did not confirm")
        else:
            gate.mark_effect("payments", "inv-1001", "SUCCESS", receipt=receipt)
    elif gate.verify_bytes("payments", "inv-1001", payload_bytes):
        # Identical replay: act on existing["outcome"], do NOT re-execute.
        ...
    else:
        raise ReplayRefused(existing)
"""

from __future__ import annotations

import fcntl
import hashlib
import hmac
import json
import math
import os
import re
import tempfile
import time
from contextlib import contextmanager

from gate_retention import (append_digest_entry, digest_log_path,
                            has_digest_entry, lookup_pruned, pruned_summary,
                            RetentionIntegrityError)

# ----------------------------------------------------------------------------
# Constants

CLAIMED = "CLAIMED"
EFFECT_DONE = "EFFECT_DONE"
UNKNOWN = "UNKNOWN"
CANCELLED = "CANCELLED"

# GATE-BUILD-004: bound the unbounded history growth Challenger C measured
# (+128 bytes/knock, any knocker can bloat a claim file forever). The cap
# keeps the genesis entry plus the most recent ones.
MAX_HISTORY_ENTRIES = 100

# MAL-GATE-201 (1d): the single definition of the lease ceiling. The gate
# never writes a lease_expires_epoch beyond now + MAX_LEASE_SECONDS, so a
# read-time epoch further in the future cannot be gate-written — it is
# tampered. The skew tolerance absorbs ordinary clock drift between the
# writing and reading host; massive backward clock jumps remain out of
# scope (wall-clock leases already assume a sane clock).
MAX_LEASE_SECONDS = 604800.0  # 7 days
EPOCH_SKEW_TOLERANCE_SECONDS = 300.0

_VALID_COMPONENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


class ClaimGateError(Exception):
    """Base error for Claim Gate failures."""


class ReplayRefused(ClaimGateError):
    """Same claim_id knocked with changed payload bytes.

    The existing claim record is preserved untouched; the caller's payload is
    refused. Attributes: ``existing`` (the preserved claim record).
    """

    def __init__(self, existing: dict):
        super().__init__(
            "replay refused: claim_id=%r exists with different payload bytes; "
            "original preserved" % (existing.get("claim_id"),)
        )
        self.existing = existing


class CorruptClaimRecord(ClaimGateError):
    """A claim file exists but cannot be trusted.

    Either it is not valid JSON or it fails record-shape validation. The gate
    refuses to claim over it, verify against it, or reconcile it — the record
    is preserved on disk for investigation and the path is reported. A corrupt
    record is never silently repaired or deleted.
    """

    def __init__(self, path: str, detail: str):
        super().__init__("corrupt claim record at %s: %s" % (path, detail))
        self.path = path


class InvalidClaimComponent(ClaimGateError):
    """scope or claim_id contained path separators or other unsafe characters."""


# ----------------------------------------------------------------------------
# Helpers


def _utcnow() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _digest(payload_bytes: bytes) -> str:
    return hashlib.sha256(payload_bytes).hexdigest()


def _check_component(name: str, value: str) -> str:
    if not isinstance(value, str) or not _VALID_COMPONENT.fullmatch(value):
        raise InvalidClaimComponent(
            "%s must match %s; got %r" % (name, _VALID_COMPONENT.pattern, value)
        )
    return value


def _check_receipt_serializable(receipt) -> None:
    """Fail fast on non-JSON receipts before mutating anything (D5)."""
    try:
        json.dumps(receipt)
    except (TypeError, ValueError) as exc:
        raise ClaimGateError("receipt is not JSON-serializable: %s" % exc)


# ----------------------------------------------------------------------------
# The gate


class ClaimGate:
    """Atomic idempotency gate for consequential effects."""

    def __init__(self, state_dir: str):
        self.state_dir = os.path.abspath(state_dir)
        self.claims_dir = os.path.join(self.state_dir, "claims")
        os.makedirs(self.claims_dir, exist_ok=True)

    # -- paths ---------------------------------------------------------------

    def _scope_dir(self, scope: str) -> str:
        _check_component("scope", scope)
        return os.path.join(self.claims_dir, scope)

    def _claim_path(self, scope: str, claim_id: str) -> str:
        _check_component("claim_id", claim_id)
        return os.path.join(self._scope_dir(scope), claim_id + ".json")

    def _lock_path(self, scope: str) -> str:
        _check_component("scope", scope)
        return os.path.join(self._scope_dir(scope), ".lock")

    @contextmanager
    def _scope_write_lock(self, scope: str):
        """Hold the exclusive scope lock: exactly one writer per scope."""
        scope_dir = self._scope_dir(scope)
        os.makedirs(scope_dir, exist_ok=True)
        lock_path = self._lock_path(scope)
        with open(lock_path, "a+b") as fh:
            fcntl.flock(fh, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(fh, fcntl.LOCK_UN)

    # -- atomic persistence ---------------------------------------------------

    _REQUIRED_FIELDS = ("scope", "claim_id", "payload_digest", "state")
    _KNOWN_STATES = (CLAIMED, EFFECT_DONE, UNKNOWN, CANCELLED)

    def _read_claim(self, path: str) -> dict | None:
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as fh:
                record = json.load(fh)
        except json.JSONDecodeError as exc:
            raise CorruptClaimRecord(path, "invalid JSON: %s" % exc)
        if not isinstance(record, dict):
            raise CorruptClaimRecord(path, "record is not a JSON object")
        missing = [f for f in self._REQUIRED_FIELDS if f not in record]
        if missing:
            raise CorruptClaimRecord(path, "missing fields: %s" % missing)
        if record["state"] not in self._KNOWN_STATES:
            raise CorruptClaimRecord(
                path, "unknown state %r" % (record["state"],)
            )
        # Field-type validation: a record that parses as JSON but carries
        # hostile or nonsense field types must not reach the compare/lease
        # paths, where non-ASCII digests or non-numeric epochs would raise
        # raw TypeError/ValueError instead of a clean gate refusal.
        digest = record["payload_digest"]
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise CorruptClaimRecord(
                path, "payload_digest is not a sha256 hex string"
            )
        epoch = record.get("lease_expires_epoch")
        if epoch is not None and not isinstance(epoch, (int, float)):
            raise CorruptClaimRecord(
                path, "lease_expires_epoch is not numeric"
            )
        # MAL-GATE-201 (1d): epoch tampering bound, precised. The gate only
        # ever writes epochs in [write_time, write_time + MAX_LEASE_SECONDS].
        # A boolean, non-finite, or far-future epoch cannot be gate-written:
        # it is a tampered record, and honoring it would grant a poisoned
        # lease (far-future) or a stuck comparison (NaN/inf). Fail closed.
        # Past epochs are satisfiable by natural expiry, so they read fine
        # and simply report not-live.
        if isinstance(epoch, bool):
            raise CorruptClaimRecord(
                path, "lease_expires_epoch is a boolean, not an epoch"
            )
        if isinstance(epoch, (int, float)):
            if not math.isfinite(epoch):
                raise CorruptClaimRecord(
                    path, "lease_expires_epoch is not finite"
                )
            if epoch > (time.time() + MAX_LEASE_SECONDS
                        + EPOCH_SKEW_TOLERANCE_SECONDS):
                raise CorruptClaimRecord(
                    path,
                    "lease_expires_epoch %r is beyond the gate-writable "
                    "bound (now + %r + skew) — tampered" % (
                        epoch, MAX_LEASE_SECONDS),
                )
        token = record.get("fencing_token")
        if token is not None and not isinstance(token, int):
            raise CorruptClaimRecord(path, "fencing_token is not an int")
        owner = record.get("lease_owner")
        if owner is not None and not isinstance(owner, str):
            raise CorruptClaimRecord(path, "lease_owner is not a string")
        hist = record.get("history")
        # Present-but-not-a-list (including explicit null) is corrupt;
        # a missing key is tolerated and filled by _append_history.
        if "history" in record and not isinstance(hist, list):
            raise CorruptClaimRecord(path, "history is not a list")
        return record

    def _write_claim_atomic(self, path: str, record: dict) -> None:
        """Temp file + fsync + atomic replace. Claim files are never deleted."""
        scope_dir = os.path.dirname(path)
        fd, tmp = tempfile.mkstemp(dir=scope_dir, prefix=".claim-", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(record, fh, indent=2, sort_keys=True)
                fh.write("\n")
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp, path)  # atomic on same filesystem
            # fsync the directory so the rename is durable
            dfd = os.open(scope_dir, os.O_DIRECTORY)
            try:
                os.fsync(dfd)
            finally:
                os.close(dfd)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)

    def _append_history(self, record: dict, event: str, detail: str | None = None) -> None:
        entry = {"ts": _utcnow(), "event": event}
        if detail is not None:
            entry["detail"] = detail
        hist = record.setdefault("history", [])
        hist.append(entry)
        if len(hist) > MAX_HISTORY_ENTRIES:
            # Compact: keep the genesis entry plus the most recent ones.
            # Every knock appends; without this bound a hostile knocker can
            # bloat a claim file forever (GATE-BUILD-004).
            del hist[1:len(hist) - MAX_HISTORY_ENTRIES + 1]

    def _pruned_existing(self, scope: str, claim_id: str, digest: str):
        """Consult the retention digest log for a pruned name.

        Returns (False, summary) for a pruned claim whose digest matches
        (idempotent reuse — no new effect), raises ReplayRefused when the
        digest differs (the pruned name is burned), and returns None when
        the name was never pruned (a genuinely fresh claim).
        """
        try:
            entry = lookup_pruned(self.state_dir, scope, claim_id)
        except RetentionIntegrityError as exc:
            raise ClaimGateError("RETENTION_HISTORY_UNKNOWN_HOLD") from exc
        if entry is None:
            return None
        summary = pruned_summary(scope, claim_id, entry)
        stored = entry.get("payload_digest")
        if not isinstance(stored, str) or not hmac.compare_digest(stored, digest):
            # Pruned name, different bytes (or a damaged log line): the name
            # is burned. Fail closed — the original is preserved in the log.
            raise ReplayRefused(summary)
        return False, summary

    # -- the four gate operations --------------------------------------------

    def claim(self, scope: str, claim_id: str, payload_bytes: bytes):
        """Atomically claim (scope, claim_id) for these exact payload bytes.

        Returns (claimed, existing):
          - (True, None)            → first claim; caller may now execute once.
          - (False, existing)       → already claimed. If the stored payload
            digest matches, this is an idempotent replay: use the existing
            record (it carries the outcome) and do NOT re-execute. If the
            digest differs, the replay is refused: the original is preserved
            and ReplayRefused semantics apply (see also verify_bytes()).

        Raises ReplayRefused when the bytes differ from the existing claim.
        """
        if not isinstance(payload_bytes, (bytes, bytearray)):
            raise ClaimGateError("payload_bytes must be bytes")
        payload_bytes = bytes(payload_bytes)
        digest = _digest(payload_bytes)
        path = self._claim_path(scope, claim_id)

        with self._scope_write_lock(scope):
            existing = self._read_claim(path)
            if existing is None:
                # The name may have been pruned by retention: the digest log
                # is the surviving truth. Same bytes -> idempotent reuse of
                # the pruned summary (no new effect); different bytes ->
                # ReplayRefused (the name is burned).
                pruned = self._pruned_existing(scope, claim_id, digest)
                if pruned is not None:
                    return pruned
                record = {
                    "scope": scope,
                    "claim_id": claim_id,
                    "payload_digest": digest,
                    "payload_len": len(payload_bytes),
                    "state": CLAIMED,
                    "outcome": None,
                    "receipt": None,
                    "cancel_reason": None,
                    "created_ts": _utcnow(),
                    "history": [],
                }
                self._append_history(record, "CLAIMED")
                self._write_claim_atomic(path, record)
                return True, None
            # Existing claim: idempotent hit or replay refusal.
            if existing.get("state") == CANCELLED:
                # A cancelled name stays silent. The knock is recorded so the
                # attempt is visible, but nothing may follow a cancellation.
                self._append_history(existing, "KNOCK_ON_CANCELLED")
                self._write_claim_atomic(path, existing)
                return False, existing
            if hmac.compare_digest(existing["payload_digest"], digest):
                self._append_history(existing, "REPLAY_IDENTICAL")
                self._write_claim_atomic(path, existing)
                return False, existing
            # Changed bytes under the same name: REFUSE, preserve original.
            self._append_history(
                existing,
                "REPLAY_REFUSED",
                "attempted payload_digest=%s" % digest,
            )
            self._write_claim_atomic(path, existing)
            raise ReplayRefused(existing)

    def verify_bytes(self, scope: str, claim_id: str, payload_bytes: bytes) -> bool:
        """True iff a claim exists and its payload digest matches payload_bytes.

        False when the claim is missing OR the bytes differ (replay refusal
        condition). Timing-safe comparison.
        """
        if not isinstance(payload_bytes, (bytes, bytearray)):
            raise ClaimGateError("payload_bytes must be bytes")
        try:
            path = self._claim_path(scope, claim_id)
        except InvalidClaimComponent:
            return False
        record = self._read_claim(path)
        if record is None:
            # Retention may have pruned the claim file; the digest log is
            # the surviving truth. A pruned claim verifies against its
            # recorded digest exactly like a live one.
            entry = lookup_pruned(self.state_dir, scope, claim_id)
            if entry is None:
                return False
            stored = entry.get("payload_digest")
            if not isinstance(stored, str):
                return False
            return hmac.compare_digest(stored, _digest(bytes(payload_bytes)))
        return hmac.compare_digest(
            record["payload_digest"], _digest(bytes(payload_bytes))
        )

    def _refuse_fenced_record(self, record: dict, op: str) -> None:
        """MAL-GATE-201 (1c): primitive-level FM1c enforcement.

        A claim that carries a fencing token was admitted through the lease
        path; only the fenced primitives (mark_effect_fenced /
        mark_unknown_fenced / cancel_fenced, which demand the current token)
        may settle it. The no-fence path must not silently double-apply or
        bypass the fence — settling here would let any hand record an
        outcome over a live lease without holding the token.
        """
        if record.get("fencing_token") is not None:
            raise ClaimGateError(
                "claim %s/%s carries fencing token %r: %s is the no-fence "
                "path; use the fenced primitive with the current token"
                % (record.get("scope"), record.get("claim_id"),
                   record.get("fencing_token"), op)
            )

    def mark_effect(self, scope: str, claim_id: str, outcome: str, receipt=None) -> dict:
        """Record the confirmed outcome of the claimed effect. One-way.

        outcome is "SUCCESS" or "FAILED". CLAIMED -> EFFECT_DONE.
        Raises ClaimGateError if the claim is not in CLAIMED state (a claim
        already done, unknown, or cancelled cannot be re-recorded).
        """
        if outcome not in ("SUCCESS", "FAILED"):
            raise ClaimGateError("outcome must be SUCCESS or FAILED")
        _check_receipt_serializable(receipt)
        path = self._claim_path(scope, claim_id)
        with self._scope_write_lock(scope):
            record = self._read_claim(path)
            if record is None:
                raise ClaimGateError("no such claim: %s/%s" % (scope, claim_id))
            self._refuse_fenced_record(record, "mark_effect")
            if record["state"] != CLAIMED:
                raise ClaimGateError(
                    "claim %s/%s is in state %s; cannot record effect"
                    % (scope, claim_id, record["state"])
                )
            record["state"] = EFFECT_DONE
            record["outcome"] = outcome
            record["receipt"] = receipt
            # I-D3 (GATE-BUILD-006): retention prunes on terminal-transition
            # time, not file mtime — knocks after settlement must not pin a
            # terminal claim forever.
            record["terminal_ts"] = _utcnow()
            self._append_history(record, "EFFECT_DONE", "outcome=%s" % outcome)
            self._write_claim_atomic(path, record)
            return record

    def mark_unknown(self, scope: str, claim_id: str, reason: str) -> dict:
        """Hold a claim open in UNKNOWN: effect attempted, outcome unconfirmed.

        CLAIMED -> UNKNOWN. The gate will not re-execute to resolve this;
        reconciliation is read-only (reconcile_unknown). Raises ClaimGateError
        unless the claim is in CLAIMED state.
        """
        path = self._claim_path(scope, claim_id)
        with self._scope_write_lock(scope):
            record = self._read_claim(path)
            if record is None:
                raise ClaimGateError("no such claim: %s/%s" % (scope, claim_id))
            self._refuse_fenced_record(record, "mark_unknown")
            if record["state"] != CLAIMED:
                raise ClaimGateError(
                    "claim %s/%s is in state %s; cannot mark unknown"
                    % (scope, claim_id, record["state"])
                )
            record["state"] = UNKNOWN
            record["outcome"] = None
            self._append_history(record, "UNKNOWN", reason)
            self._write_claim_atomic(path, record)
            return record

    def cancel(self, scope: str, claim_id: str, reason: str) -> dict:
        """Mark a claim CANCELLED, preserving the original. Never deletes.

        No effect may follow a cancellation: mark_effect refuses a CANCELLED
        claim, and claim() on a cancelled claim returns (False, existing) so
        the cancellation is visible to the caller.
        """
        if not reason:
            raise ClaimGateError("cancel requires a reason")
        path = self._claim_path(scope, claim_id)
        with self._scope_write_lock(scope):
            record = self._read_claim(path)
            if record is None:
                raise ClaimGateError("no such claim: %s/%s" % (scope, claim_id))
            self._refuse_fenced_record(record, "cancel")
            if record["state"] == CANCELLED:
                return record  # cancelling twice is idempotent, not an error
            if record["state"] in (EFFECT_DONE, UNKNOWN):
                # Terminal states never move backward. An EFFECT_DONE claim is
                # settled; an UNKNOWN claim is held open for read-only
                # reconciliation. Cancelling either would erase that truth.
                raise ClaimGateError(
                    "cannot cancel claim %s/%s in terminal state %s"
                    % (scope, claim_id, record["state"])
                )
            record["state"] = CANCELLED
            record["cancel_reason"] = reason
            record["terminal_ts"] = _utcnow()
            self._append_history(record, "CANCELLED", reason)
            self._write_claim_atomic(path, record)
            return record

    def reconcile_unknown(self, scope: str, claim_id: str) -> dict | None:
        """Return the current claim state WITHOUT triggering another effect.

        Purely read-only: it mutates nothing, writes nothing, and executes
        nothing. It exists so a worker that died between the effect attempt and
        its receipt can inspect the truth as it stands — and decide, by owner
        or caller policy, what to do next — without the gate re-executing
        on its behalf. A second effect attempt requires a NEW claim id and an
        explicit owner decision.
        """
        try:
            path = self._claim_path(scope, claim_id)
        except InvalidClaimComponent:
            return None
        record = self._read_claim(path)
        if record is None:
            # Retention may have pruned the claim file. Pruned claims are
            # always terminal (only EFFECT_DONE/CANCELLED are pruned), so
            # the summary is the truth as it stands.
            entry = lookup_pruned(self.state_dir, scope, claim_id)
            if entry is None:
                return None
            return pruned_summary(scope, claim_id, entry)
        return record

    # -- retention (GATE-BUILD-004) ----------------------------------------

    @staticmethod
    def _terminal_epoch(record: dict, path: str) -> float | None:
        """Epoch when the claim became terminal, for retention aging.

        Prefers the record's terminal_ts (set on every EFFECT_DONE/CANCELLED
        transition; immune to knock-pinning). Falls back to the file mtime
        for records settled before terminal_ts existed. Returns None when
        neither is available — the caller treats undatable claims as recent
        (never prune what cannot be dated).
        """
        ts = record.get("terminal_ts")
        if isinstance(ts, str):
            try:
                import calendar
                return calendar.timegm(time.strptime(ts, "%Y-%m-%dT%H:%M:%SZ"))
            except (ValueError, TypeError, OverflowError):
                pass
        try:
            return os.path.getmtime(path)
        except OSError:
            return None

    def prune_terminal(self, scope: str, older_than_days: float = 30.0,
                       dry_run: bool = False, now: float | None = None) -> dict:
        """Prune terminal claims older than the retention window.

        The explicit retention rite (see gate_retention): for each claim in
        EFFECT_DONE or CANCELLED that became terminal longer than
        ``older_than_days`` ago, append its essential truth to the per-scope
        digest log and remove the claim file. Age is measured from the
        terminal transition (terminal_ts), not the file mtime, so knocks
        after settlement cannot pin a claim forever; records settled before
        terminal_ts existed fall back to mtime. The ``.fencing`` counter is
        NEVER reset; later claims mint strictly larger tokens.

        NEVER pruned: CLAIMED (live), UNKNOWN (held open), corrupt records,
        or terminal claims touched within the window. Pruning executes no
        effect, changes no state, re-arms no lease. Crash-idempotent:
        retrying after a crash appends no duplicate log line.

        With dry_run=True, report what would be pruned without touching
        anything. Returns a report dict.
        """
        from gate_retention import DEFAULT_RETENTION_DAYS
        import math
        scope = self._check_scope(scope)
        if older_than_days is None:
            older_than_days = DEFAULT_RETENTION_DAYS
        try:
            older_than_days = float(older_than_days)
        except (TypeError, ValueError):
            raise ClaimGateError("older_than_days must be a number")
        if not math.isfinite(older_than_days) or older_than_days <= 0:
            raise ClaimGateError(
                "older_than_days must be a positive finite number")
        cutoff = (time.time() if now is None else float(now)) - older_than_days * 86400.0
        scope_dir = self._scope_dir(scope)
        report = {"scope": scope, "older_than_days": older_than_days,
                  "dry_run": bool(dry_run), "pruned": [],
                  "skipped_live": [], "skipped_recent": [],
                  "skipped_corrupt": []}
        if not os.path.isdir(scope_dir):
            return report
        with self._scope_write_lock(scope):
            for name in sorted(os.listdir(scope_dir)):
                if not name.endswith(".json") or name.startswith("."):
                    continue
                claim_id = name[:-5]
                path = os.path.join(scope_dir, name)
                try:
                    record = self._read_claim(path)
                except CorruptClaimRecord:
                    report["skipped_corrupt"].append(claim_id)
                    continue
                except OSError:
                    # D-D1: a directory (or unreadable node) disguised as a
                    # claim file. It cannot be trusted and cannot be pruned;
                    # file it as corrupt, typed, fail-closed.
                    report["skipped_corrupt"].append(claim_id)
                    continue
                if record is None:
                    continue  # vanished between listdir and read; not ours
                state = record.get("state")
                if state not in (EFFECT_DONE, CANCELLED):
                    report["skipped_live"].append(claim_id)
                    continue
                # I-D3: age is measured from the terminal transition, not the
                # file mtime — knocks after settlement refresh mtime and must
                # not pin a terminal claim forever. Records settled before
                # terminal_ts existed fall back to mtime.
                settled = self._terminal_epoch(record, path)
                if settled is None or settled >= cutoff:
                    report["skipped_recent"].append(claim_id)
                    continue
                entry = {
                    "claim_id": claim_id,
                    "payload_digest": record.get("payload_digest"),
                    "payload_len": record.get("payload_len"),
                    "state": state,
                    "outcome": record.get("outcome"),
                    "cancel_reason": record.get("cancel_reason"),
                    "fencing_token": record.get("fencing_token"),
                    "lease_owner": record.get("lease_owner"),
                    "created_ts": record.get("created_ts"),
                    "pruned_ts": _utcnow(),
                }
                report["pruned"].append(claim_id)
                if dry_run:
                    continue
                # Crash-idempotent: log-append first, then delete. A retry
                # after a crash between the two skips the duplicate append
                # but still removes the file.
                if not has_digest_entry(self.state_dir, scope, claim_id,
                                        entry["payload_digest"], state):
                    append_digest_entry(self.state_dir, scope, entry)
                try:
                    os.unlink(path)
                except FileNotFoundError:
                    pass
        return report

    def _check_scope(self, scope: str) -> str:
        if not isinstance(scope, str) or not _VALID_COMPONENT.fullmatch(scope):
            raise InvalidClaimComponent("unsafe scope component: %r" % (scope,))
        return scope

"""Distributed Claim Gate — lease-based claim coordination across processes.

Extends claim_gate.ClaimGate (GATE-001) with the Second Charter (GATE-002):

- ``claim_lease``: claim (or renew/take over) with owner id + lease duration.
- ``renew_lease``: the lease holder extends its proof of life; fenced by token.
- ``release_lease``: voluntary release; the claim becomes takeable immediately.
- ``mark_effect_fenced`` / ``mark_unknown_fenced`` / ``cancel_fenced``: writes
  that require the CURRENT fencing token — a superseded owner cannot write.
- Stale-lease takeover: an expired lease may be seized by a new owner; the new
  owner receives a strictly higher fencing token, fencing the old owner out.

Leases are measured in wall-clock seconds (time.time()). On one host the clock
is exact; across hosts the timestamp is a trigger and the FENCING TOKEN is the
truth. Lease durations must be chosen with skew + effect duration in mind.

All mutations remain serialized by the per-scope fcntl write lock, so GATE-001
semantics (first claim wins, changed bytes refused, files never deleted) hold
across processes on the same host.
"""

from __future__ import annotations

import math
import os
import time

from portable_lock import sync_directory
from claim_gate import (
    ClaimGate,
    ClaimGateError,
    ReplayRefused,
    MAX_LEASE_SECONDS,
    _check_receipt_serializable,
    _utcnow,
    CANCELLED,
    CLAIMED,
    EFFECT_DONE,
    UNKNOWN,
)

LEASE_HELD = "LEASE_HELD"
TAKEOVER = "TAKEOVER"

_DEFAULT_LEASE_SECONDS = 60.0
# Proof-of-life leases are short by design. MAX_LEASE_SECONDS is defined in
# claim_gate (single definition, MAL-GATE-201 1d): it is also the read-time
# epoch tampering bound.


class LeaseError(ClaimGateError):
    """A lease operation was refused (held, fenced, or invalid)."""


class CorruptFencingSequence(ClaimGateError):
    """The scope's fencing-token counter file is unreadable.

    The counter file is preserved on disk for investigation. No claim,
    takeover, or fenced write may proceed in this scope until the owner
    reconciles it: the sequence must be trustworthy, and a silently reset
    counter is not a decision the gate makes on its own.
    """


class DistributedClaimGate(ClaimGate):
    """ClaimGate with lease + fencing-token coordination for distant hands."""

    def __init__(self, state_dir: str, effect_receipt_lookup=None):
        """Bind an optional effect-receipt ledger for the 1c repair.

        ``effect_receipt_lookup`` is an optional callable
        ``(scope, claim_id) -> (outcome, receipt) | None`` consulted on a
        fence-begin takeover before any re-execution (MAL-GATE-201 1c
        repair, independent reviewer re-attack verdict 2026-10-20). The idempotency key
        is (scope, claim_id): it deterministically binds the exact bytes
        the claim covers. With no ledger wired, the lookup consults only
        the claim record's own receipt. The callable runs under the scope
        write lock: it must be fast and must not call back into the gate.
        """
        super().__init__(state_dir)
        if effect_receipt_lookup is not None and not callable(
                effect_receipt_lookup):
            raise ClaimGateError(
                "effect_receipt_lookup must be callable or None")
        self._effect_receipt_lookup = effect_receipt_lookup

    def _lookup_effect_receipt(self, scope: str, claim_id: str,
                               record: dict):
        """Effect-receipt lookup by idempotency key.

        Consults the claim record's own receipt first, then the injected
        effect-receipt ledger (if any). Returns ``(outcome, receipt)`` or
        ``None``. A ledger that answers with an invalid outcome or a
        non-serializable receipt fails closed — a dishonest ledger must not
        settle a claim.
        """
        if (record.get("state") == EFFECT_DONE
                and record.get("receipt") is not None
                and record.get("outcome") in ("SUCCESS", "FAILED")):
            return record["outcome"], record["receipt"]
        lookup = self._effect_receipt_lookup
        if lookup is not None:
            found = lookup(scope, claim_id)
            if found is not None:
                outcome, receipt = found
                if outcome not in ("SUCCESS", "FAILED"):
                    raise ClaimGateError(
                        "effect_receipt_lookup returned invalid outcome %r"
                        % (outcome,))
                _check_receipt_serializable(receipt)
                return outcome, receipt
        return None

    # -- fencing token sequence (one per scope) --------------------------------

    def _fencing_path(self, scope: str) -> str:
        return os.path.join(self._scope_dir(scope), ".fencing")

    def _next_fencing_token(self, scope: str) -> int:
        """Bump and return the next fencing token. Caller must hold the lock."""
        path = self._fencing_path(scope)
        current = 0
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    current = int(fh.read().strip() or "0")
            except ValueError:
                raise CorruptFencingSequence(
                    "fencing counter at %s is not numeric; preserved for "
                    "investigation, no token issued" % path
                )
        nxt = current + 1
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            fh.write(str(nxt))
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
        # Sync POSIX directory metadata; Windows power-loss durability is
        # explicitly not independently established by the local source pack.
        sync_directory(os.path.dirname(path))
        return nxt

    # -- lease helpers ----------------------------------------------------------

    @staticmethod
    def _now() -> float:
        return time.time()

    @staticmethod
    def _check_owner(owner_id: str) -> str:
        if not isinstance(owner_id, str) or not owner_id.strip():
            raise LeaseError("owner_id must be a non-empty string")
        return owner_id.strip()

    @staticmethod
    def _check_lease_seconds(lease_seconds: float) -> float:
        try:
            lease_seconds = float(lease_seconds)
        except (TypeError, ValueError):
            raise LeaseError("lease_seconds must be a number, got %r"
                             % (lease_seconds,))
        if not math.isfinite(lease_seconds):
            raise LeaseError("lease_seconds must be finite")
        if lease_seconds <= 0:
            raise LeaseError("lease_seconds must be positive")
        if lease_seconds > MAX_LEASE_SECONDS:
            raise LeaseError("lease_seconds %r exceeds maximum %r"
                             % (lease_seconds, MAX_LEASE_SECONDS))
        return lease_seconds

    @classmethod
    def is_lease_live(cls, record: dict, now: float | None = None) -> bool:
        """True iff the record holds a lease whose expiry is in the future.

        D7: defensive — a hostile dict with a non-numeric epoch answers
        False instead of raising. In-gate call sites only ever pass
        _read_claim-validated records.
        """
        if record.get("lease_owner") is None:
            return False
        expires = record.get("lease_expires_epoch")
        if expires is None:
            return False
        try:
            return (cls._now() if now is None else now) < float(expires)
        except (TypeError, ValueError):
            return False

    def _record_lease(self, record: dict, owner_id: str, lease_seconds: float,
                      fencing_token: int) -> None:
        expires = self._now() + lease_seconds
        record["lease_owner"] = owner_id
        record["lease_expires_epoch"] = expires
        record["lease_expires_ts"] = time.strftime(
            "%Y-%m-%dT%H:%M:%SZ", time.gmtime(expires)
        )
        record["fencing_token"] = fencing_token
        # MAL-GATE-201 (1b): a (re)granted lease starts a fresh fence epoch;
        # any begin_effect certificate bound to the old epoch is void.
        record["fence_begin"] = None

    def _require_current_token(self, record: dict, owner_id: str,
                               fencing_token: int) -> None:
        """Refuse unless caller is the lease owner holding the current token.

        D-CRIT-1 repair: the token is required whenever one was EVER issued
        for this claim — including after release_lease() cleared the owner.
        A record that never received a token cannot be written through the
        fenced path at all: the caller must claim_lease() first. There is no
        unleased bypass; a fabricated token never matches an issued one.
        """
        issued = record.get("fencing_token")
        if issued is None:
            raise LeaseError(
                "no fencing token issued for %s/%s; claim a lease first"
                % (record.get("scope"), record.get("claim_id"))
            )
        # MAL-GATE-201 (1b): the fence check is type-strict. Python's
        # True == 1 would let a boolean "token" pass for token 1; a fencing
        # token is a canonical int minted by _next_fencing_token, and
        # anything else is refused fail-closed.
        if (not isinstance(fencing_token, int)
                or isinstance(fencing_token, bool)):
            raise LeaseError(
                "fencing_token must be an int, got %r"
                % type(fencing_token).__name__
            )
        if record.get("lease_owner") != owner_id or issued != fencing_token:
            raise LeaseError(
                "fenced: %r does not hold the current fencing token "
                "(recorded owner=%r token=%r)" % (
                    owner_id, record.get("lease_owner"), issued,
                )
            )

    # -- MAL-GATE-201 (1b): fence-mid-execution --------------------------------
    #
    # The fence is valid when execution begins and may be revoked before the
    # effect is recorded. Before this change a refused fenced write was
    # silent: the history showed a granted lease and one recorded outcome,
    # with no trace that a second hand had raced the fence. Every refused
    # fence interaction is now durably recorded under the scope lock before
    # the refusal is raised. The gate still cannot reach into the external
    # resource — it guarantees at most one recorded outcome and a durable
    # trace of every fence race, never a silent drop.

    def _record_fence_knock(self, record: dict, event: str,
                           detail: str) -> None:
        """Append a fence knock to the record and persist it atomically.

        Caller must hold the scope lock. The knock is durable evidence; the
        caller re-raises the refusal afterwards (fail closed, never silent).
        """
        self._append_history(record, event, detail)
        path = self._claim_path(record["scope"], record["claim_id"])
        self._write_claim_atomic(path, record)

    def _refused_fence_write(self, record: dict, owner_id: str,
                             fencing_token: int, op: str) -> None:
        """Fence check that records the knock before refusing.

        On mismatch: KNOCK_FENCE_MISMATCH (attempted vs current owner/token)
        is durably recorded, then the LeaseError is re-raised.
        """
        try:
            self._require_current_token(record, owner_id, fencing_token)
        except LeaseError:
            self._record_fence_knock(
                record, "KNOCK_FENCE_MISMATCH",
                "op=%s attempted_owner=%r attempted_token=%r "
                "current_owner=%r current_token=%r" % (
                    op, owner_id, fencing_token,
                    record.get("lease_owner"), record.get("fencing_token"),
                ),
            )
            raise

    def _refused_settled_write(self, record: dict, op: str) -> None:
        """A write arriving after the claim settled is refused and recorded.

        A late mark on a settled claim is a double-application signal; it
        must be visible (KNOCK_ON_SETTLED), not silently dropped.
        """
        if record.get("state") != CLAIMED:
            self._record_fence_knock(
                record, "KNOCK_ON_SETTLED",
                "op=%s claim already in state %s" % (
                    op, record.get("state")),
            )
            raise ClaimGateError(
                "claim %s/%s is in state %s; cannot record effect"
                % (record.get("scope"), record.get("claim_id"),
                   record.get("state"))
            )

    def _verify_certificate(self, record: dict, certificate,
                            op: str) -> None:
        """Verify a begin_effect certificate against the current fence.

        A certificate binds the fence at execution start. If the fence moved
        (token bumped, payload changed, or a newer begin superseded it) the
        write is refused and the knock is recorded: the mid-execution fence
        move is provable, not merely refused.
        """
        if certificate is None:
            return
        if not isinstance(certificate, dict):
            raise ClaimGateError("certificate must be a dict")
        detail = ("op=%s certificate_token=%r current_token=%r "
                  "certificate_digest=%r record_digest=%r" % (
                      op, certificate.get("fencing_token"),
                      record.get("fencing_token"),
                      certificate.get("payload_digest"),
                      record.get("payload_digest")))
        if certificate.get("fencing_token") != record.get("fencing_token"):
            self._record_fence_knock(
                record, "KNOCK_FENCE_MISMATCH",
                "stale certificate: fence moved since begin; " + detail)
            raise LeaseError(
                "stale certificate: the fence moved since execution began")
        if certificate.get("payload_digest") != record.get("payload_digest"):
            self._record_fence_knock(
                record, "KNOCK_FENCE_MISMATCH",
                "certificate payload mismatch; " + detail)
            raise ClaimGateError(
                "certificate does not match the claimed payload bytes")
        fence_begin = record.get("fence_begin")
        if (isinstance(fence_begin, dict)
                and certificate.get("begin_epoch") != fence_begin.get("epoch")):
            self._record_fence_knock(
                record, "KNOCK_FENCE_MISMATCH",
                "stale certificate: superseded by a newer begin; " + detail)
            raise LeaseError(
                "stale certificate: superseded by a newer execution begin")

    def begin_effect(self, scope: str, claim_id: str, owner_id: str,
                     fencing_token: int) -> dict:
        """Bind the fence at execution start; return an execution certificate.

        The certificate captures (scope, claim_id, fencing token, payload
        digest, begin epoch) under the scope lock. Present it to
        mark_effect_fenced / mark_unknown_fenced / cancel_fenced: a fence
        move between begin and mark is then provable at mark time.

        Honest limit: the gate cannot reach into the external resource. The
        certificate proves the fence at begin time and makes a mid-execution
        fence move visible; it does not prevent the resource itself from
        applying an effect twice. The gate's guarantee is at most one
        recorded outcome plus a durable trace of every fence race.
        """
        owner_id = self._check_owner(owner_id)
        path = self._claim_path(scope, claim_id)
        with self._scope_write_lock(scope):
            record = self._read_claim(path)
            if record is None:
                raise LeaseError("no such claim: %s/%s" % (scope, claim_id))
            # A displaced hand cannot bind the fence: mismatch is recorded.
            self._refused_fence_write(record, owner_id, fencing_token,
                                     "begin_effect")
            self._refused_settled_write(record, "begin_effect")
            begin_epoch = self._now()
            record["fence_begin"] = {
                "token": record["fencing_token"],
                "owner": owner_id,
                "epoch": begin_epoch,
            }
            self._append_history(
                record, "FENCE_BEGIN",
                "owner=%s token=%d" % (owner_id, record["fencing_token"]),
            )
            self._write_claim_atomic(path, record)
            return {
                "scope": scope,
                "claim_id": claim_id,
                "fencing_token": record["fencing_token"],
                "begin_epoch": begin_epoch,
                "payload_digest": record["payload_digest"],
            }

    # -- the distributed operations --------------------------------------------

    def claim_lease(self, scope: str, claim_id: str, payload_bytes: bytes,
                    owner_id: str, lease_seconds: float = _DEFAULT_LEASE_SECONDS):
        """Claim with a lease: (granted, record).

        - First claim: granted, lease held by owner, fresh fencing token.
        - Same owner, live lease, same bytes: (False, existing) — call renew_lease.
        - Different owner, live lease: (False, existing) with LEASE_HELD knock.
        - Expired (or absent) lease: TAKEOVER — new owner, bumped fencing token,
          fresh expiry. The old owner is fenced out of all later writes.
        - Changed bytes under the same name: ReplayRefused (First Law still binds).
        """
        owner_id = self._check_owner(owner_id)
        lease_seconds = self._check_lease_seconds(lease_seconds)
        if not isinstance(payload_bytes, (bytes, bytearray)):
            raise ClaimGateError("payload_bytes must be bytes")
        payload_bytes = bytes(payload_bytes)
        from claim_gate import _digest
        import hmac as _hmac
        digest = _digest(payload_bytes)
        path = self._claim_path(scope, claim_id)

        with self._scope_write_lock(scope):
            existing = self._read_claim(path)
            if existing is None:
                # Retention may have pruned this name: the digest log is the
                # surviving truth. Same bytes -> idempotent reuse of the
                # pruned summary (no lease, no new effect); different bytes
                # -> ReplayRefused (the name is burned).
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
                    "created_ts": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                                time.gmtime()),
                    "history": [],
                }
                token = self._next_fencing_token(scope)
                self._record_lease(record, owner_id, lease_seconds, token)
                self._append_history(
                    record, "LEASE_GRANTED",
                    "owner=%s token=%d" % (owner_id, token),
                )
                self._write_claim_atomic(path, record)
                return True, record

            if not _hmac.compare_digest(existing["payload_digest"], digest):
                self._append_history(
                    existing, "REPLAY_REFUSED",
                    "attempted payload_digest=%s" % digest,
                )
                self._write_claim_atomic(path, existing)
                raise ReplayRefused(existing)

            if existing.get("state") == CANCELLED:
                self._append_history(existing, "KNOCK_ON_CANCELLED")
                self._write_claim_atomic(path, existing)
                return False, existing

            if existing.get("state") != CLAIMED:
                # EFFECT_DONE or UNKNOWN: the work's outcome is settled or
                # held open. No lease may be granted on a closed claim — the
                # caller reads the existing record instead.
                self._append_history(existing, "KNOCK_ON_CLOSED")
                self._write_claim_atomic(path, existing)
                return False, existing

            now = self._now()
            if self.is_lease_live(existing, now):
                if existing.get("lease_owner") == owner_id:
                    self._append_history(existing, "REPLAY_IDENTICAL")
                    self._write_claim_atomic(path, existing)
                    return False, existing
                self._append_history(
                    existing, LEASE_HELD, "owner=%s holds live lease" % owner_id
                )
                self._write_claim_atomic(path, existing)
                return False, existing

            # Expired (or never-held) lease: takeover.
            old_owner = existing.get("lease_owner")
            old_token = existing.get("fencing_token")
            prior_begin = existing.get("fence_begin")
            # MAL-GATE-201 (1c repair, independent reviewer re-attack verdict
            # 2026-10-20, probe P2): a taken-over claim whose prior
            # fence_begin shows an effect may already have run must not be
            # silently re-executed. Do the effect-receipt lookup by
            # idempotency key; absent a receipt, transfer to UNKNOWN
            # rather than re-execute. The prior fence_begin is consulted
            # BEFORE _record_lease clears it — the re-dispatch path must
            # see the old epoch's trace, not a wiped slate.
            if isinstance(prior_begin, dict) and existing.get("state") == CLAIMED:
                found = self._lookup_effect_receipt(scope, claim_id,
                                                    existing)
                if found is None:
                    existing["state"] = UNKNOWN
                    existing["outcome"] = None
                    self._append_history(
                        existing, "UNKNOWN_FENCE_BEGIN_TAKEOVER",
                        "prior fence_begin (owner=%s) showed a "
                        "possibly-executed effect; no receipt for the "
                        "idempotency key; transferred to UNKNOWN rather "
                        "than re-executed" % (prior_begin.get("owner"),),
                    )
                    self._write_claim_atomic(path, existing)
                    return False, existing
                outcome, receipt = found
                existing["state"] = EFFECT_DONE
                existing["outcome"] = outcome
                existing["receipt"] = receipt
                existing["terminal_ts"] = _utcnow()
                self._append_history(
                    existing, "EFFECT_DONE_RECEIPT_RECOVERY",
                    "effect receipt recovered from the ledger on "
                    "fence-begin takeover; outcome=%s; no re-execution"
                    % (outcome,),
                )
                self._write_claim_atomic(path, existing)
                return False, existing
            token = self._next_fencing_token(scope)
            self._record_lease(existing, owner_id, lease_seconds, token)
            self._append_history(
                existing, TAKEOVER,
                "old_owner=%r old_token=%r new_owner=%s new_token=%d"
                % (old_owner, old_token, owner_id, token),
            )
            self._write_claim_atomic(path, existing)
            return True, existing

    def renew_lease(self, scope: str, claim_id: str, owner_id: str,
                    fencing_token: int,
                    lease_seconds: float = _DEFAULT_LEASE_SECONDS) -> dict:
        """Extend the lease. Only the current token holder may renew."""
        owner_id = self._check_owner(owner_id)
        lease_seconds = self._check_lease_seconds(lease_seconds)
        path = self._claim_path(scope, claim_id)
        with self._scope_write_lock(scope):
            record = self._read_claim(path)
            if record is None:
                raise LeaseError("no such claim: %s/%s" % (scope, claim_id))
            self._require_current_token(record, owner_id, fencing_token)
            # L-A-02: renewing a lease on a settled/held claim is meaningless;
            # refuse instead of re-arming lease fields on terminal states.
            if record.get("state") != CLAIMED:
                raise LeaseError(
                    "cannot renew lease on claim %s/%s in state %s"
                    % (scope, claim_id, record.get("state")))
            # L-A-01: re-store the ISSUED token, not the caller's spelling
            # of it (e.g. True vs 1), so the stored token stays canonical.
            self._record_lease(record, owner_id, lease_seconds,
                               record["fencing_token"])
            self._append_history(
                record, "LEASE_RENEWED", "owner=%s token=%d" % (owner_id, fencing_token)
            )
            self._write_claim_atomic(path, record)
            return record

    def release_lease(self, scope: str, claim_id: str, owner_id: str,
                      fencing_token: int) -> dict:
        """Voluntarily release the lease; the claim becomes takeable at once."""
        owner_id = self._check_owner(owner_id)
        path = self._claim_path(scope, claim_id)
        with self._scope_write_lock(scope):
            record = self._read_claim(path)
            if record is None:
                raise LeaseError("no such claim: %s/%s" % (scope, claim_id))
            self._require_current_token(record, owner_id, fencing_token)
            record["lease_owner"] = None
            record["lease_expires_epoch"] = None
            record["lease_expires_ts"] = None
            # MAL-GATE-201 (1b): the fence epoch ends with the lease; any
            # begin certificate bound to it is void.
            record["fence_begin"] = None
            self._append_history(
                record, "LEASE_RELEASED", "owner=%s token=%d" % (owner_id, fencing_token)
            )
            self._write_claim_atomic(path, record)
            return record

    def mark_effect_fenced(self, scope: str, claim_id: str, owner_id: str,
                           fencing_token: int, outcome: str,
                           receipt=None, certificate: dict | None = None) -> dict:
        """Record an effect outcome only for the current token holder.

        The fencing token is the truth: a superseded (slow or dead) owner is
        refused, so a stale hand can never write an outcome over the new hand.
        Lease liveness is NOT required — a late write from the legitimate holder
        is allowed; what is refused is a write from a displaced holder.

        MAL-GATE-201 (1b): a fence mismatch (or a stale certificate) is
        durably recorded as KNOCK_FENCE_MISMATCH before the refusal is
        raised — a fence-mid-execution race leaves a trace, never silence.
        A write arriving on a settled claim is recorded as KNOCK_ON_SETTLED.
        ``certificate`` is an optional begin_effect certificate binding the
        fence at execution start.
        """
        if outcome not in ("SUCCESS", "FAILED"):
            raise ClaimGateError("outcome must be SUCCESS or FAILED")
        _check_receipt_serializable(receipt)
        owner_id = self._check_owner(owner_id)
        path = self._claim_path(scope, claim_id)
        with self._scope_write_lock(scope):
            record = self._read_claim(path)
            if record is None:
                raise ClaimGateError("no such claim: %s/%s" % (scope, claim_id))
            # D-CRIT-1: the token check is unconditional. Released and
            # never-leased records are refused here, not bypassed.
            self._refused_fence_write(record, owner_id, fencing_token,
                                     "mark_effect_fenced")
            self._verify_certificate(record, certificate, "mark_effect_fenced")
            self._refused_settled_write(record, "mark_effect_fenced")
            record["state"] = EFFECT_DONE
            record["outcome"] = outcome
            record["receipt"] = receipt
            record["terminal_ts"] = _utcnow()
            self._append_history(
                record, "EFFECT_DONE",
                "outcome=%s owner=%s token=%d" % (outcome, owner_id, fencing_token),
            )
            self._write_claim_atomic(path, record)
            return record

    def mark_unknown_fenced(self, scope: str, claim_id: str, owner_id: str,
                            fencing_token: int, reason: str,
                            certificate: dict | None = None) -> dict:
        """Hold a claim UNKNOWN; only the current token holder may do so.

        MAL-GATE-201 (1b): fence mismatches and stale certificates are
        durably recorded as KNOCK_FENCE_MISMATCH before refusal; writes on
        settled claims as KNOCK_ON_SETTLED.
        """
        owner_id = self._check_owner(owner_id)
        path = self._claim_path(scope, claim_id)
        with self._scope_write_lock(scope):
            record = self._read_claim(path)
            if record is None:
                raise ClaimGateError("no such claim: %s/%s" % (scope, claim_id))
            # D-CRIT-1: the token check is unconditional. Released and
            # never-leased records are refused here, not bypassed.
            self._refused_fence_write(record, owner_id, fencing_token,
                                     "mark_unknown_fenced")
            self._verify_certificate(record, certificate,
                                     "mark_unknown_fenced")
            self._refused_settled_write(record, "mark_unknown_fenced")
            record["state"] = UNKNOWN
            record["outcome"] = None
            self._append_history(record, "UNKNOWN", reason)
            self._write_claim_atomic(path, record)
            return record

    def cancel_fenced(self, scope: str, claim_id: str, owner_id: str,
                      fencing_token: int, reason: str,
                      certificate: dict | None = None) -> dict:
        """Cancel a lease-held claim. Only the current token holder may cancel.

        MAL-GATE-201 (1b): fence mismatches and stale certificates are
        durably recorded as KNOCK_FENCE_MISMATCH before refusal.
        """
        owner_id = self._check_owner(owner_id)
        if not reason:
            raise ClaimGateError("cancel requires a reason")
        path = self._claim_path(scope, claim_id)
        with self._scope_write_lock(scope):
            record = self._read_claim(path)
            if record is None:
                raise ClaimGateError("no such claim: %s/%s" % (scope, claim_id))
            if record.get("state") == CANCELLED:
                return record
            # D-CRIT-1: the token check is unconditional. Released and
            # never-leased records are refused here, not bypassed.
            self._refused_fence_write(record, owner_id, fencing_token,
                                     "cancel_fenced")
            self._verify_certificate(record, certificate, "cancel_fenced")
            # D-A-001: terminal states never move backward — mirror the base
            # cancel() guard. Cancelling EFFECT_DONE/UNKNOWN would erase the
            # settled outcome / the held-open unknown the sweep watches for.
            if record.get("state") in (EFFECT_DONE, UNKNOWN):
                raise ClaimGateError(
                    "cannot cancel claim %s/%s in terminal state %s"
                    % (scope, claim_id, record.get("state"))
                )
            record["state"] = CANCELLED
            record["cancel_reason"] = reason
            record["lease_owner"] = None
            record["lease_expires_epoch"] = None
            record["lease_expires_ts"] = None
            # MAL-GATE-201 (1b): cancellation ends the fence epoch.
            record["fence_begin"] = None
            record["terminal_ts"] = _utcnow()
            self._append_history(record, "CANCELLED", reason)
            self._write_claim_atomic(path, record)
            return record

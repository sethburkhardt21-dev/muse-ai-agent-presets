"""Approval-gated claims for the Claim Gate module (GATE-BUILD-016 / G1).

Composition, not modification: this module layers an approval hold over
the existing ClaimGate / DistributedClaimGate and TokenGuard without
touching their bytes. The approval layer is the Studio-facing authority
for approval-managed claims; the underlying gate only ever learns of a
claim after it has been approved.

Lifecycle:
    hold(scope, claim_id, payload, claimant_id)
        -> HELD_APPROVAL (no lease issued, no effect may execute)
    approve(scope, claim_id, approver_id, approver_token, payload)
        -> APPROVED, then admitted to the underlying gate via gate.claim()
    refuse(scope, claim_id, actor_id, reason)
        -> CANCELLED (withdraw by claimant, or refuse by authorized approver)

The approval act is fencing-bound: the approver's token must be strictly
greater than any token previously honored for an approval on that claim
(TokenGuard semantics in a dedicated approval namespace). A changed plan
presented under the same claim_id is refused (ChangedBytesRefused, a
ReplayRefused subtype — the replay-refusal machinery, reused). Approving
an already-approved claim returns the stored receipt (idempotent); it
does not re-honor the token.

Crash discipline: the approval scope lock is held across guard-honor,
gate admission, and the state transition, so concurrent approvers
serialize. If the process dies after the guard honored a token but
before the state landed, the token is consumed (TokenGuard never
forgets); the approver retries with a strictly greater token. This is
the Kleppmann discipline, and it is documented rather than hidden.

Trust boundary (stated plainly): this is a library, not a server. A
caller that bypasses the approval layer and uses the raw gate directly
on an approval-managed name is outside the approval authority — the
Studio's consumer contract (transfer standard) requires all pipeline
claims to route through ApprovalGate / the skill CLI. The raw gate
fails closed on unknown names ("no such claim"); it cannot execute a
claim the approval layer never admitted.

Identity model: approver/claimant identities are byte-exact strings.
"Op-1" and "op-1" are different identities. If the Studio's identity
source is case-insensitive (emails, directory usernames), normalize at
the identity provider — do NOT lowercase inside this layer, which would
collide identities in case-sensitive deployments.
"""

import hashlib
import hmac
import json
import os
import tempfile
import time
from contextlib import contextmanager
from portable_lock import exclusive_lock

from claim_gate import (
    ClaimGate,
    ClaimGateError,
    ReplayRefused,
    InvalidClaimComponent,
    _check_component,
    _digest,
    _utcnow,
)
from gate_token_guard import TokenGuard

# ---------------------------------------------------------------------------
# Typed errors


class ApprovalRequired(ClaimGateError):
    """An effect was attempted on a claim held for approval."""


class SelfApprovalRefused(ClaimGateError):
    """The claimant attempted to approve its own claim."""


class UnknownApprover(ClaimGateError):
    """The actor is not the claimant and not an authorized approver."""


class ChangedBytesRefused(ReplayRefused):
    """Bytes presented at approve/hold differ from the held bytes."""


class ApprovalExpired(ClaimGateError):
    """The approval hold lapsed past the scope's approval TTL."""


class StaleApprover(ClaimGateError):
    """The approver's fencing token is not greater than the last honored."""


class FencedExecutionRequired(ClaimGateError):
    """An unfenced settle was attempted on an approval-managed claim.

    Challenger J MEDIUM-2: approve() admits the claim unfenced, so the
    wrapper must not let an arbitrary hand record the effect. Execution
    on approval-managed claims goes through the lease path: claim a
    lease, then settle with owner_id/fencing_token.
    """


# ---------------------------------------------------------------------------
# Record states

HELD_APPROVAL = "HELD_APPROVAL"
APPROVED = "APPROVED"
CANCELLED = "CANCELLED"

_APPROVAL_SUBDIR = "approvals"
_GUARD_SUBDIR = "approval-fencing"

_DEFAULT_APPROVAL_TTL_SECONDS = 7 * 24 * 3600.0


def _check_token(value) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ClaimGateError(
            "fencing_token must be an int, got %r" % type(value).__name__
        )
    if value <= 0:
        raise ClaimGateError("fencing_token must be positive, got %r" % value)
    if value.bit_length() > 1024:
        # Mirror the guard's Challenger-G NEW-2 cap, but typed: an
        # oversized token must surface as a ClaimGateError (CLI contract),
        # never as the guard's bare ValueError.
        raise ClaimGateError("fencing_token exceeds 1024 bits")
    return value


def _check_payload(payload_bytes) -> bytes:
    if not isinstance(payload_bytes, (bytes, bytearray)):
        raise ClaimGateError("payload_bytes must be bytes")
    return bytes(payload_bytes)


def _check_actor(actor_id: str) -> str:
    return _check_component("actor_id", actor_id)


def _check_reason(reason: str) -> str:
    if not isinstance(reason, str) or not reason.strip():
        raise ClaimGateError("reason must be a non-empty string")
    if len(reason) > 4096:
        raise ClaimGateError("reason too long (max 4096 chars)")
    return reason


# ---------------------------------------------------------------------------
# The approval gate


class ApprovalGate:
    """Approval holds composed over a ClaimGate and a TokenGuard."""

    def __init__(self, state_dir: str, gate=None, guard=None):
        if not isinstance(state_dir, str) or not state_dir:
            raise ClaimGateError("state_dir must be a non-empty string")
        self.state_dir = state_dir
        self.approval_dir = os.path.join(state_dir, _APPROVAL_SUBDIR)
        self.gate = gate if gate is not None else ClaimGate(state_dir)
        self.guard = (
            guard
            if guard is not None
            else TokenGuard(os.path.join(state_dir, _GUARD_SUBDIR))
        )

    # -- paths and locking ------------------------------------------------

    def _scope_dir(self, scope: str) -> str:
        _check_component("scope", scope)
        return os.path.join(self.approval_dir, scope)

    def _approvers_path(self, scope: str) -> str:
        return os.path.join(self._scope_dir(scope), "approvers.json")

    def _hold_path(self, scope: str, claim_id: str) -> str:
        _check_component("scope", scope)
        _check_component("claim_id", claim_id)
        return os.path.join(self._scope_dir(scope), claim_id + ".hold.json")

    @contextmanager
    def _scope_lock(self, scope: str):
        d = self._scope_dir(scope)
        os.makedirs(d, exist_ok=True)
        lock_path = os.path.join(d, ".lock")
        with exclusive_lock(lock_path):
            yield

    def _write_atomic(self, path: str, obj: dict) -> None:
        data = json.dumps(obj, indent=2, sort_keys=True).encode("utf-8")
        d = os.path.dirname(path)
        os.makedirs(d, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=d, prefix=".tmp-")
        try:
            with os.fdopen(fd, "wb") as fh:
                fh.write(data)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp, path)
        except BaseException:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise

    # -- record validation (fail closed on corrupt state) ------------------

    @staticmethod
    def _validate_hold_record(rec: dict, path: str) -> dict:
        if not isinstance(rec, dict):
            raise ClaimGateError("corrupt hold record (not a dict): %s" % path)
        for key in ("scope", "claim_id", "claimant_id", "payload_digest",
                    "state", "held_ts", "held_epoch", "history"):
            if key not in rec:
                raise ClaimGateError(
                    "corrupt hold record (missing %r): %s" % (key, path))
        if rec["state"] not in (HELD_APPROVAL, APPROVED, CANCELLED):
            raise ClaimGateError(
                "corrupt hold record (bad state %r): %s"
                % (rec["state"], path))
        if not isinstance(rec["payload_digest"], str):
            raise ClaimGateError(
                "corrupt hold record (bad digest): %s" % path)
        if not isinstance(rec["history"], list):
            raise ClaimGateError(
                "corrupt hold record (bad history): %s" % path)
        # Challenger J LOW-3: type-check the fields approve()/sweep read
        # as numbers. A corrupt string here used to escape as an untyped
        # TypeError and break the CLI's JSON/exit-3 contract.
        epoch = rec["held_epoch"]
        if isinstance(epoch, bool) or not isinstance(epoch, (int, float)):
            raise ClaimGateError(
                "corrupt hold record (bad held_epoch): %s" % path)
        return rec

    def _read_hold(self, scope: str, claim_id: str):
        path = self._hold_path(scope, claim_id)
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as fh:
                rec = json.load(fh)
        except (OSError, ValueError) as exc:
            raise ClaimGateError(
                "corrupt hold record (unreadable): %s: %s" % (path, exc))
        return self._validate_hold_record(rec, path)

    def _append_history(self, rec: dict, event: str, detail=None) -> None:
        entry = {"ts": _utcnow(), "event": event}
        if detail is not None:
            entry["detail"] = detail
        rec["history"].append(entry)

    # -- approver registry --------------------------------------------------

    def register_approvers(self, scope: str, approver_ids,
                           approval_ttl_seconds=_DEFAULT_APPROVAL_TTL_SECONDS):
        """Authorize approvers for a scope. Replaces the scope's set."""
        _check_component("scope", scope)
        if not isinstance(approver_ids, (list, tuple)) or not approver_ids:
            raise ClaimGateError("approver_ids must be a non-empty list")
        clean = []
        for aid in approver_ids:
            _check_actor(aid)
            if aid not in clean:
                clean.append(aid)
        if not isinstance(approval_ttl_seconds, (int, float)) or isinstance(
                approval_ttl_seconds, bool):
            raise ClaimGateError("approval_ttl_seconds must be a number")
        if approval_ttl_seconds <= 0:
            raise ClaimGateError("approval_ttl_seconds must be positive")
        cfg = {
            "scope": scope,
            "approvers": clean,
            "approval_ttl_seconds": float(approval_ttl_seconds),
            "updated_ts": _utcnow(),
        }
        with self._scope_lock(scope):
            self._write_atomic(self._approvers_path(scope), cfg)
        return cfg

    def _load_approvers(self, scope: str):
        path = self._approvers_path(scope)
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as fh:
                cfg = json.load(fh)
        except (OSError, ValueError) as exc:
            raise ClaimGateError(
                "corrupt approvers config: %s: %s" % (path, exc))
        if not isinstance(cfg, dict) or not isinstance(
                cfg.get("approvers"), list):
            raise ClaimGateError("corrupt approvers config: %s" % path)
        # Challenger J LOW-3: a corrupt TTL must fail typed, not as a bare
        # ValueError from float().
        ttl = cfg.get("approval_ttl_seconds", _DEFAULT_APPROVAL_TTL_SECONDS)
        if isinstance(ttl, bool) or not isinstance(ttl, (int, float)):
            raise ClaimGateError("corrupt approvers config (bad ttl): %s"
                                 % path)
        return cfg

    def _authorized_approvers(self, scope: str):
        cfg = self._load_approvers(scope)
        if cfg is None:
            raise ClaimGateError(
                "no approvers registered for scope %r" % scope)
        return cfg["approvers"], float(
            cfg.get("approval_ttl_seconds", _DEFAULT_APPROVAL_TTL_SECONDS))

    # -- lifecycle ----------------------------------------------------------

    def hold(self, scope: str, claim_id: str, payload_bytes,
             claimant_id: str) -> dict:
        """Hold a claim for approval. No lease is issued; no effect may run.

        Idempotent: re-holding identical bytes returns the existing record.
        Changed bytes under the same name are refused (ChangedBytesRefused).
        """
        payload_bytes = _check_payload(payload_bytes)
        _check_actor(claimant_id)
        digest = _digest(payload_bytes)
        now = time.time()
        with self._scope_lock(scope):
            existing = self._read_hold(scope, claim_id)
            if existing is not None:
                if hmac.compare_digest(existing["payload_digest"], digest):
                    self._append_history(existing, "REPLAY_IDENTICAL")
                    self._write_atomic(
                        self._hold_path(scope, claim_id), existing)
                    return existing
                self._append_history(
                    existing, "REPLAY_REFUSED",
                    "attempted payload_digest=%s" % digest)
                self._write_atomic(
                    self._hold_path(scope, claim_id), existing)
                raise ChangedBytesRefused(existing)
            rec = {
                "scope": scope,
                "claim_id": claim_id,
                "claimant_id": claimant_id,
                "payload_digest": digest,
                "payload_len": len(payload_bytes),
                "state": HELD_APPROVAL,
                "held_ts": _utcnow(),
                "held_epoch": now,
                "approval": None,
                "refusal": None,
                "history": [],
            }
            self._append_history(rec, "HELD",
                                 "claimant=%s" % claimant_id)
            self._write_atomic(self._hold_path(scope, claim_id), rec)
            return rec

    def approve(self, scope: str, claim_id: str, approver_id: str,
                approver_token: int, payload_bytes) -> dict:
        """Approve a held claim and admit it to the underlying gate.

        The approver must be authorized for the scope and distinct from
        the claimant; the presented bytes must digest-match the held
        bytes; the fencing token must exceed every token previously
        honored for an approval on this claim. On success the claim is
        admitted to the underlying gate (gate.claim) and the approval
        receipt is returned. Re-approving an approved claim returns the
        stored receipt without re-honoring the token.
        """
        payload_bytes = _check_payload(payload_bytes)
        _check_actor(approver_id)
        token = _check_token(approver_token)
        digest = _digest(payload_bytes)
        now = time.time()
        with self._scope_lock(scope):
            rec = self._read_hold(scope, claim_id)
            if rec is None:
                raise ClaimGateError(
                    "no such held claim: %s/%s" % (scope, claim_id))
            if rec["state"] == APPROVED:
                out = dict(rec["approval"])
                out["replay"] = True
                return out
            if rec["state"] == CANCELLED:
                raise ClaimGateError(
                    "claim %s/%s is CANCELLED and cannot be approved"
                    % (scope, claim_id))
            approvers, ttl = self._authorized_approvers(scope)
            if now - rec["held_epoch"] > ttl:
                rec["state"] = CANCELLED
                rec["refusal"] = {
                    "actor_id": approver_id,
                    "reason": "approval expired",
                    "ts": _utcnow(),
                }
                self._append_history(rec, "EXPIRED")
                self._write_atomic(self._hold_path(scope, claim_id), rec)
                raise ApprovalExpired(
                    "approval hold for %s/%s expired" % (scope, claim_id))
            if approver_id not in approvers:
                raise UnknownApprover(
                    "%r is not an authorized approver for scope %r"
                    % (approver_id, scope))
            if approver_id == rec["claimant_id"]:
                raise SelfApprovalRefused(
                    "claimant %r cannot approve its own claim"
                    % approver_id)
            if not hmac.compare_digest(rec["payload_digest"], digest):
                self._append_history(
                    rec, "APPROVAL_REFUSED_CHANGED_BYTES",
                    "attempted payload_digest=%s" % digest)
                self._write_atomic(self._hold_path(scope, claim_id), rec)
                raise ChangedBytesRefused(rec)
            # Fencing: the approval act is ordered by token. The guard
            # honors strictly increasing tokens per claim; a stale or
            # replayed token is refused before anything is admitted.
            honored = self.guard.honor(
                scope, claim_id, token,
                effect_digest="approval:" + digest)
            if not honored:
                raise StaleApprover(
                    "token %d is not greater than the last honored approval "
                    "token for %s/%s" % (token, scope, claim_id))
            # Admit to the underlying gate. The gate has never seen this
            # claim (holds are approval-layer-only) unless a previous
            # approve crashed after admission — then the record is
            # CLAIMED with identical bytes and we proceed idempotently.
            try:
                _granted, existing = self.gate.claim(
                    scope, claim_id, payload_bytes)
            except ReplayRefused as exc:
                raise ClaimGateError(
                    "gate holds different bytes for %s/%s; refusing "
                    "approval (original preserved)" % (scope, claim_id)
                ) from exc
            if existing is not None and existing.get("state") not in (
                    "CLAIMED",):
                raise ClaimGateError(
                    "claim %s/%s already settled in gate (state=%s); "
                    "cannot approve" % (
                        scope, claim_id, existing.get("state")))
            approval = {
                "approver_id": approver_id,
                "fencing_token": token,
                "approved_ts": _utcnow(),
                "payload_digest": digest,
                "payload_len": len(payload_bytes),
            }
            rec["state"] = APPROVED
            rec["approval"] = approval
            self._append_history(
                rec, "APPROVED",
                "approver=%s token=%d" % (approver_id, token))
            self._write_atomic(self._hold_path(scope, claim_id), rec)
            out = dict(approval)
            out["approved"] = True
            return out

    def refuse(self, scope: str, claim_id: str, actor_id: str,
               reason: str) -> dict:
        """Refuse (or withdraw) a held claim -> CANCELLED.

        The actor must be the claimant (withdrawal) or an authorized
        approver (refusal). Idempotent: refusing a cancelled claim
        returns the record.
        """
        _check_actor(actor_id)
        reason = _check_reason(reason)
        with self._scope_lock(scope):
            rec = self._read_hold(scope, claim_id)
            if rec is None:
                raise ClaimGateError(
                    "no such held claim: %s/%s" % (scope, claim_id))
            if rec["state"] == CANCELLED:
                return rec
            if rec["state"] == APPROVED:
                raise ClaimGateError(
                    "claim %s/%s already approved; use cancel, not refuse"
                    % (scope, claim_id))
            approvers, _ttl = self._authorized_approvers(scope)
            if actor_id != rec["claimant_id"] and actor_id not in approvers:
                raise UnknownApprover(
                    "%r is neither the claimant nor an authorized approver "
                    "for scope %r" % (actor_id, scope))
            rec["state"] = CANCELLED
            rec["refusal"] = {
                "actor_id": actor_id,
                "reason": reason,
                "ts": _utcnow(),
            }
            self._append_history(rec, "REFUSED",
                                 "actor=%s reason=%s" % (actor_id, reason))
            self._write_atomic(self._hold_path(scope, claim_id), rec)
            return rec

    def mark_effect(self, scope: str, claim_id: str, outcome: str,
                    receipt=None, owner_id=None, fencing_token=None) -> dict:
        """Record an effect, refusing held claims with ApprovalRequired.

        Routes to the fenced primitive when owner_id/fencing_token are
        given (the lease path mints a fencing token, and the no-fence
        path must then refuse by the gate's 1c rule); otherwise uses the
        no-fence path. Either way the hold check fires first.

        Challenger J MEDIUM-2: for approval-managed (APPROVED) claims the
        no-fence path is refused with FencedExecutionRequired — the
        approval authorizes the plan, but only the lease-holding executor
        may record the effect. Challenger J LOW-5: the approval lock is
        held across the gate call so the hold check and the settle are
        atomic w.r.t. concurrent approve()/refuse() (lock ordering is
        approval -> gate everywhere; the gate never takes the approval
        lock, so no deadlock).
        """
        with self._scope_lock(scope):
            rec = self._read_hold(scope, claim_id)
            if rec is not None and rec["state"] == HELD_APPROVAL:
                raise ApprovalRequired(
                    "claim %s/%s is held for approval; approve it before "
                    "recording an effect" % (scope, claim_id))
            if (rec is not None and rec["state"] == APPROVED
                    and owner_id is None and fencing_token is None):
                raise FencedExecutionRequired(
                    "claim %s/%s is approval-managed; record the effect "
                    "through the fenced path (claim a lease, then settle "
                    "with owner_id/fencing_token)" % (scope, claim_id))
            if owner_id is not None or fencing_token is not None:
                if not hasattr(self.gate, "mark_effect_fenced"):
                    raise ClaimGateError(
                        "fenced mark_effect needs a DistributedClaimGate")
                return self.gate.mark_effect_fenced(
                    scope, claim_id, owner_id, fencing_token, outcome,
                    receipt)
            return self.gate.mark_effect(scope, claim_id, outcome, receipt)

    def mark_unknown(self, scope: str, claim_id: str, reason: str,
                     owner_id=None, fencing_token=None) -> dict:
        """Hold a claim UNKNOWN, refusing held claims with ApprovalRequired.

        Challenger J MEDIUM-1: the hold check was wired into mark_effect
        but not mark_unknown, letting any party brick a held claim by
        marking it UNKNOWN through the raw gate paths (after which
        approval could never complete). The check is now mirrored here;
        the CLI's mark-unknown / mark-unknown-fenced route through this
        wrapper.
        """
        _check_reason(reason)
        with self._scope_lock(scope):
            rec = self._read_hold(scope, claim_id)
            if rec is not None and rec["state"] == HELD_APPROVAL:
                raise ApprovalRequired(
                    "claim %s/%s is held for approval; approve or refuse it "
                    "before marking unknown" % (scope, claim_id))
            # MEDIUM-2 / LOW-5: same executor binding and the same
            # hold-the-lock-across-the-gate-call discipline as
            # mark_effect — see its docstring.
            if (rec is not None and rec["state"] == APPROVED
                    and owner_id is None and fencing_token is None):
                raise FencedExecutionRequired(
                    "claim %s/%s is approval-managed; mark unknown through "
                    "the fenced path (claim a lease, then settle with "
                    "owner_id/fencing_token)" % (scope, claim_id))
            if owner_id is not None or fencing_token is not None:
                if not hasattr(self.gate, "mark_unknown_fenced"):
                    raise ClaimGateError(
                        "fenced mark_unknown needs a DistributedClaimGate")
                return self.gate.mark_unknown_fenced(
                    scope, claim_id, owner_id, fencing_token, reason)
            return self.gate.mark_unknown(scope, claim_id, reason)

    def verify(self, scope: str, claim_id: str, payload_bytes=None) -> dict:
        """Merged view: the approval record plus gate admission state."""
        with self._scope_lock(scope):
            rec = self._read_hold(scope, claim_id)
        view = {
            "scope": scope,
            "claim_id": claim_id,
            "approval_state": rec["state"] if rec else None,
            "approval": rec.get("approval") if rec else None,
            "refusal": rec.get("refusal") if rec else None,
            # Challenger J LOW-4: this is the approval layer's own record
            # of having admitted the claim — NOT a live gate read (no
            # public read exists). The name says "recorded" on purpose.
            "admission_recorded": bool(rec) and rec["state"] == APPROVED,
            "payload_match": None,
        }
        if payload_bytes is not None and rec is not None:
            payload_bytes = _check_payload(payload_bytes)
            view["payload_match"] = hmac.compare_digest(
                rec["payload_digest"], _digest(payload_bytes))
        return view

    def sweep_expired(self) -> list:
        """Expire held claims past their scope TTL -> CANCELLED.

        Challenger J LOW-1: this used to accept an arbitrary ``now``,
        letting any library caller kill live holds. The clock is now
        always real time; there is no unauthenticated hold-killer left
        in the API.
        """
        now = time.time()
        swept = []
        if not os.path.isdir(self.approval_dir):
            return swept
        for scope in sorted(os.listdir(self.approval_dir)):
            scope_dir = os.path.join(self.approval_dir, scope)
            if not os.path.isdir(scope_dir):
                continue
            try:
                _check_component("scope", scope)
            except InvalidClaimComponent:
                continue
            cfg = self._load_approvers(scope)
            if cfg is None:
                continue
            ttl = float(cfg.get("approval_ttl_seconds",
                                _DEFAULT_APPROVAL_TTL_SECONDS))
            with self._scope_lock(scope):
                for name in sorted(os.listdir(scope_dir)):
                    if not name.endswith(".hold.json"):
                        continue
                    claim_id = name[: -len(".hold.json")]
                    rec = self._read_hold(scope, claim_id)
                    if rec is None or rec["state"] != HELD_APPROVAL:
                        continue
                    if now - rec["held_epoch"] > ttl:
                        rec["state"] = CANCELLED
                        rec["refusal"] = {
                            "actor_id": None,
                            "reason": "approval expired",
                            "ts": _utcnow(),
                        }
                        self._append_history(rec, "EXPIRED")
                        self._write_atomic(
                            self._hold_path(scope, claim_id), rec)
                        swept.append({"scope": scope, "claim_id": claim_id})
        return swept

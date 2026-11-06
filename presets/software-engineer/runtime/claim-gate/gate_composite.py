"""Composite/nested claims for the Claim Gate module (GATE-BUILD-017 / G2).

A composite is a claim tree within one scope: a parent pipeline claim
(itself approval-managed via G1) gates a set of child stage claims.

    create_composite(scope, parent_claim_id, payload, claimant_id)
        -> holds the parent plan + creates the ACTIVE composite record
    hold_child(scope, claim_id, payload, claimant_id, parent_claim_id,
               after=[...])
        -> HELD_APPROVAL child bound to the tree (atomic under the lock)
    approve_child(..., force=False, override_reason=None)
        -> per-child approval with parent/after/degraded checks
    settle_child(...)  -> mark_effect/mark_unknown + tree state update
    refuse_child(...)  -> withdraw/refuse + tree state update
    cancel_composite(...) / propagate_cancellation(...)
        -> parent cancel fans out to non-terminal children, idempotent

Composition, not modification: this module layers over ApprovalGate
(GATE-BUILD-016, challenger-clean rev3) without touching its bytes —
or any judged bytes. It reuses the approval layer's hold-record schema
(validated with ApprovalGate._validate_hold_record) and the SAME scope
lock file (approvals/<scope>/.lock), so composite critical sections are
mutually exclusive with approval-layer writers. It NEVER nests locks:
approval-layer calls (which self-lock) always happen outside the
composite lock; check-then-act races are closed by post-verification +
compensation (the LOW-5 discipline), never by lock nesting (which would
deadlock: two fds on the same flock file block each other even in one
process).

Trust boundary: same as the approval layer — library, not server.
Raw-gate paths bypass tree bookkeeping; the Studio's consumer contract
routes all pipeline claims through this layer / the skill CLI.
"""

import fcntl
import hmac
import json
import os
import tempfile
import time
from contextlib import contextmanager

from claim_gate import (
    ClaimGateError,
    ReplayRefused,
    InvalidClaimComponent,
    _check_component,
    _digest,
    _utcnow,
)
from gate_approval import (
    ApprovalGate,
    ApprovalRequired,
    ChangedBytesRefused,
    FencedExecutionRequired,
    HELD_APPROVAL,
    APPROVED,
    CANCELLED,
)

# ---------------------------------------------------------------------------
# Typed errors


class ParentNotApproved(ClaimGateError):
    """A child approval was attempted while the parent is still held."""


class ParentCancelled(ClaimGateError):
    """A child lifecycle attempt under a cancelled parent/composite."""


class ParentDegraded(ClaimGateError):
    """A sibling approval was attempted while the parent is DEGRADED
    (a child failed) without an audited force override."""


class UnknownParent(ClaimGateError):
    """Binding to a nonexistent or non-composite parent."""


class CyclicDependency(ClaimGateError):
    """The after-graph would contain a cycle."""


class ChildAlreadyBound(ClaimGateError):
    """The claim name is already held/bound and cannot be
    (re-)bound to this parent."""


# ---------------------------------------------------------------------------
# Composite states

C_ACTIVE = "ACTIVE"
C_DEGRADED = "DEGRADED"
C_CANCELLED = "CANCELLED"
C_COMPLETE = "COMPLETE"

_TERMINAL_CHILD = ("EFFECT_DONE", "UNKNOWN", CANCELLED)


def _check_actor(actor_id: str) -> str:
    return _check_component("actor_id", actor_id)


def _check_reason(reason: str) -> str:
    if not isinstance(reason, str) or not reason.strip():
        raise ClaimGateError("reason must be a non-empty string")
    if len(reason) > 4096:
        raise ClaimGateError("reason too long (max 4096 chars)")
    return reason


def _check_payload(payload_bytes) -> bytes:
    if not isinstance(payload_bytes, (bytes, bytearray)):
        raise ClaimGateError("payload_bytes must be bytes")
    return bytes(payload_bytes)


class CompositeGate:
    """Composite claim trees composed over an ApprovalGate."""

    def __init__(self, state_dir: str, approval=None):
        if not isinstance(state_dir, str) or not state_dir:
            raise ClaimGateError("state_dir must be a non-empty string")
        self.state_dir = state_dir
        self.approval_dir = os.path.join(state_dir, "approvals")
        self.approval = approval if approval is not None else ApprovalGate(
            state_dir)

    # -- paths, locking, atomic writes ------------------------------------

    def _scope_dir(self, scope: str) -> str:
        _check_component("scope", scope)
        return os.path.join(self.approval_dir, scope)

    def _composite_path(self, scope: str, parent_claim_id: str) -> str:
        _check_component("scope", scope)
        _check_component("claim_id", parent_claim_id)
        return os.path.join(
            self._scope_dir(scope), parent_claim_id + ".composite.json")

    @contextmanager
    def _composite_lock(self, scope: str):
        # SAME lock file the approval layer uses: composite critical
        # sections exclude approval-layer writers. Never nest: do not
        # call approval.* methods while holding this.
        d = self._scope_dir(scope)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, ".lock"), "a+b") as fh:
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(fh.fileno(), fcntl.LOCK_UN)

    @staticmethod
    def _write_atomic(path: str, obj: dict) -> None:
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

    # -- composite record ---------------------------------------------------

    @staticmethod
    def _validate_composite(rec: dict, path: str) -> dict:
        if not isinstance(rec, dict):
            raise ClaimGateError("corrupt composite record: %s" % path)
        for key in ("scope", "parent_claim_id", "claimant_id",
                    "payload_digest", "state", "children", "history"):
            if key not in rec:
                raise ClaimGateError(
                    "corrupt composite record (missing %r): %s" % (key, path))
        if rec["state"] not in (C_ACTIVE, C_DEGRADED, C_CANCELLED,
                                C_COMPLETE):
            raise ClaimGateError(
                "corrupt composite record (bad state): %s" % path)
        if not isinstance(rec["children"], list):
            raise ClaimGateError(
                "corrupt composite record (bad children): %s" % path)
        for child in rec["children"]:
            if not isinstance(child, dict) or "claim_id" not in child:
                raise ClaimGateError(
                    "corrupt composite record (bad child): %s" % path)
        if not isinstance(rec["history"], list):
            raise ClaimGateError(
                "corrupt composite record (bad history): %s" % path)
        return rec

    def _read_composite(self, scope: str, parent_claim_id: str):
        path = self._composite_path(scope, parent_claim_id)
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as fh:
                rec = json.load(fh)
        except (OSError, ValueError) as exc:
            raise ClaimGateError(
                "corrupt composite record (unreadable): %s: %s" % (path, exc))
        return self._validate_composite(rec, path)

    def _write_composite(self, scope: str, rec: dict) -> None:
        path = self._composite_path(scope, rec["parent_claim_id"])
        self._validate_composite(rec, path)
        self._write_atomic(path, rec)

    @staticmethod
    def _composite_history(rec: dict, event: str, detail=None) -> None:
        entry = {"ts": _utcnow(), "event": event}
        if detail is not None:
            entry["detail"] = detail
        rec["history"].append(entry)

    def _child_entry(self, comp: dict, claim_id: str):
        for child in comp["children"]:
            if child["claim_id"] == claim_id:
                return child
        return None

    def _entry_or_raise(self, comp: dict, scope: str,
                        claim_id: str) -> dict:
        """Fail closed with a typed error (never AttributeError) when the
        tree entry is missing — reachable only via manual state surgery,
        since every composite-layer transition maintains the entry."""
        entry = self._child_entry(comp, claim_id)
        if entry is None:
            raise ClaimGateError(
                "composite tree entry missing for child %s/%s "
                "(hold record exists; state surgery suspected)"
                % (scope, claim_id))
        return entry

    def _recompute_parent_state(self, comp: dict) -> None:
        """COMPLETE iff every child is terminal and none FAILED; a late
        FAILED flips COMPLETE back to DEGRADED (challenger brief item 7).
        Never clears DEGRADED or CANCELLED silently."""
        if comp["state"] == C_CANCELLED:
            return
        children = comp["children"]
        if children and all(c["state"] in _TERMINAL_CHILD for c in children):
            if any(c.get("outcome") == "FAILED" for c in children):
                if comp["state"] != C_DEGRADED:
                    comp["state"] = C_DEGRADED
                    self._composite_history(
                        comp, "DEGRADED", "child FAILED observed")
            else:
                comp["state"] = C_COMPLETE
                self._composite_history(comp, "COMPLETE")

    # -- creation -----------------------------------------------------------

    def create_composite(self, scope: str, parent_claim_id: str,
                         payload_bytes, claimant_id: str) -> dict:
        """Hold the parent plan and create the ACTIVE composite record.

        Idempotent: re-creating with identical bytes returns the existing
        record (crash between the hold and the record write repairs by
        re-invocation).
        """
        payload_bytes = _check_payload(payload_bytes)
        _check_actor(claimant_id)
        digest = _digest(payload_bytes)
        # The parent hold goes through the approval layer (self-locking;
        # no composite lock held here).
        self.approval.hold(scope, parent_claim_id, payload_bytes,
                           claimant_id)
        with self._composite_lock(scope):
            # Close the create-vs-cancel race: if the parent hold was
            # cancelled between our hold() and this critical section,
            # do not publish an ACTIVE composite over a dead parent.
            # Direct read (no lock taken by _read_hold); the composite
            # lock excludes approval-layer writers.
            parent_hold = self.approval._read_hold(scope, parent_claim_id)
            if parent_hold is not None and \
                    parent_hold.get("state") == CANCELLED:
                raise ParentCancelled(
                    "parent hold %s/%s was cancelled; composite not created"
                    % (scope, parent_claim_id))
            existing = self._read_composite(scope, parent_claim_id)
            if existing is not None:
                if hmac.compare_digest(existing["payload_digest"], digest):
                    return existing
                raise ClaimGateError(
                    "composite %s/%s exists with different bytes"
                    % (scope, parent_claim_id))
            comp = {
                "scope": scope,
                "parent_claim_id": parent_claim_id,
                "claimant_id": claimant_id,
                "payload_digest": digest,
                "payload_len": len(payload_bytes),
                "state": C_ACTIVE,
                "children": [],
                "history": [],
            }
            self._composite_history(comp, "CREATED",
                                    "claimant=%s" % claimant_id)
            self._write_composite(scope, comp)
            return comp

    # -- child binding --------------------------------------------------------

    def _check_after_acyclic(self, comp: dict, claim_id: str,
                             after: list) -> None:        # Edges point child -> after-siblings, which must already be bound
        # (older). A DFS over the existing graph plus the new edges finds
        # any cycle defensively.
        graph = {c["claim_id"]: list(c.get("after", []))
                 for c in comp["children"]}
        graph[claim_id] = list(after)
        visiting, done = set(), set()

        def visit(node, stack):
            if node in done:
                return
            if node in visiting:
                raise CyclicDependency(
                    "after-graph cycle involving %r" % node)
            visiting.add(node)
            for nxt in graph.get(node, []):
                visit(nxt, stack + [node])
            visiting.discard(node)
            done.add(node)

        for node in graph:
            visit(node, [])

    def hold_child(self, scope: str, claim_id: str, payload_bytes,
                   claimant_id: str, parent_claim_id: str,
                   after=None) -> dict:
        """Bind and hold a child claim under a composite parent.

        One critical section under the shared scope lock: the full hold
        record (including parent/after) is written atomically, so no
        approve can slip between a plain hold and the binding.
        """
        payload_bytes = _check_payload(payload_bytes)
        _check_actor(claimant_id)
        _check_component("claim_id", parent_claim_id)
        after = list(after) if after else []
        for sib in after:
            _check_component("claim_id", sib)
            if sib == claim_id:
                raise CyclicDependency("child cannot list itself in after")
        digest = _digest(payload_bytes)
        now = time.time()
        with self._composite_lock(scope):
            comp = self._read_composite(scope, parent_claim_id)
            if comp is None:
                raise UnknownParent(
                    "no composite %s/%s" % (scope, parent_claim_id))
            if comp["state"] == C_CANCELLED:
                raise ParentCancelled(
                    "composite %s/%s is CANCELLED" % (scope, parent_claim_id))
            # The parent hold itself may have been cancelled in a race
            # the composite record has not observed yet: a bound child
            # could never approve, so refuse the bind now (fail closed).
            parent_hold = self.approval._read_hold(scope, parent_claim_id)
            if parent_hold is not None and \
                    parent_hold.get("state") == CANCELLED:
                raise ParentCancelled(
                    "parent hold %s/%s is CANCELLED" % (scope, parent_claim_id))
            # after-siblings must already be bound to this parent.
            for sib in after:
                if self._child_entry(comp, sib) is None:
                    raise UnknownParent(
                        "after-sibling %r is not bound to composite %s/%s"
                        % (sib, scope, parent_claim_id))
            self._check_after_acyclic(comp, claim_id, after)
            # The name must not already be held (plain or composite).
            # Idempotent re-bind: same bytes, already ours -> return it
            # (and repair a missing tree entry from a crashed bind).
            hold_path = self.approval._hold_path(scope, claim_id)
            existing = self.approval._read_hold(scope, claim_id)
            if existing is not None:
                if hmac.compare_digest(existing["payload_digest"], digest) \
                        and existing.get("parent", {}).get("claim_id") == \
                        parent_claim_id:
                    if self._child_entry(comp, claim_id) is None:
                        # Crash-repair: the hold record is the durable
                        # truth of the bind. A re-invocation with a
                        # different `after` list must NOT silently weaken
                        # the ordering the hold was written with (LOW-1).
                        recorded_after = existing.get("after", [])
                        if not isinstance(recorded_after, list):
                            raise ClaimGateError(
                                "corrupt hold record (bad after): %s/%s"
                                % (scope, claim_id))
                        comp["children"].append({
                            "claim_id": claim_id,
                            "state": existing["state"],
                            "outcome": None,
                            "after": list(recorded_after),
                        })
                        self._composite_history(
                            comp, "CHILD_BOUND_REPAIRED", claim_id)
                        self._write_composite(scope, comp)
                    return existing
                raise ChildAlreadyBound(
                    "claim name %s/%s is already held" % (scope, claim_id))
            if self._child_entry(comp, claim_id) is not None:
                # Tree entry without a hold record: corrupt state.
                # Fail closed rather than double-binding.
                raise ClaimGateError(
                    "composite entry %s/%s has no hold record"
                    % (scope, claim_id))
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
                "parent": {"scope": scope, "claim_id": parent_claim_id},
                "after": after,
                "history": [],
            }
            self.approval._append_history(
                rec, "HELD",
                "claimant=%s composite_parent=%s after=%s"
                % (claimant_id, parent_claim_id, ",".join(after)))
            # Fail closed if the schema ever drifts from the approval
            # layer's expectations.
            ApprovalGate._validate_hold_record(rec, hold_path)
            self._write_atomic(hold_path, rec)
            comp["children"].append({
                "claim_id": claim_id,
                "state": HELD_APPROVAL,
                "outcome": None,
                "after": after,
            })
            self._composite_history(comp, "CHILD_BOUND", claim_id)
            self._write_composite(scope, comp)
            return rec

    # -- child approval --------------------------------------------------------

    def _parent_hold_state(self, scope: str, parent_claim_id: str):
        view = self.approval.verify(scope, parent_claim_id)
        return view["approval_state"]

    def approve_child(self, scope: str, claim_id: str, approver_id: str,
                      approver_token: int, payload_bytes, force=False,
                      override_reason=None) -> dict:
        """Approve a composite child with parent/after/degraded checks.

        Check-then-act across the composite lock and the approval
        layer's self-locking approve(): races are closed by
        post-verification + compensation (LOW-5 discipline), never by
        lock nesting.
        """
        payload_bytes = _check_payload(payload_bytes)
        _check_actor(approver_id)
        if force:
            _check_reason(override_reason)
        # (1) Parent hold gate — outside any composite lock.
        parent_state = self._parent_hold_state(
            scope, self._parent_of(scope, claim_id))
        if parent_state == HELD_APPROVAL:
            raise ParentNotApproved(
                "parent is still held for approval; approve the parent plan "
                "before its stages")
        if parent_state == CANCELLED:
            raise ParentCancelled("parent claim is CANCELLED")
        # (2) Composite checks under the lock.
        with self._composite_lock(scope):
            comp = self._require_composite(scope, claim_id)
            if comp["state"] == C_CANCELLED:
                raise ParentCancelled("composite is CANCELLED")
            degraded = comp["state"] == C_DEGRADED
            if degraded and not force:
                raise ParentDegraded(
                    "composite is DEGRADED (a child failed); approve with "
                    "force + override_reason, or not at all")
            if force and not degraded:
                raise ClaimGateError(
                    "force requires a DEGRADED composite")
            entry = self._entry_or_raise(comp, scope, claim_id)
            # The after-ordering is a safety invariant against ACCIDENTAL
            # misordering. An audited force override waives it along with
            # the DEGRADED fence: the approver explicitly takes
            # responsibility for the waived dependency (recorded in the
            # FORCE_APPROVED audit below), e.g. "s1's failure was a flake;
            # its artifacts are verified, s2 may proceed".
            if not force:
                for sib in entry.get("after", []):
                    sib_entry = self._child_entry(comp, sib)
                    if not (sib_entry["state"] == "EFFECT_DONE"
                            and sib_entry.get("outcome") == "SUCCESS"):
                        raise ParentNotApproved(
                            "after-sibling %r is not EFFECT_DONE/SUCCESS "
                            "(state=%s)" % (sib, sib_entry["state"]))
        # (3) The approval itself (self-locking; no composite lock held).
        receipt = self.approval.approve(scope, claim_id, approver_id,
                                        approver_token, payload_bytes)
        # (4) Post-verification + compensation. The gate record is read
        # directly (atomic file; no lock taken by _read_claim) to catch
        # what happened between the approval landing and this check:
        # a concurrent cancel, or a concurrent fenced settle by a lease
        # holder that leased immediately after step (3).
        with self._composite_lock(scope):
            comp = self._require_composite(scope, claim_id)
            entry = self._entry_or_raise(comp, scope, claim_id)
            grec = self.approval.gate._read_claim(
                self.approval.gate._claim_path(scope, claim_id))
            gstate = grec.get("state") if grec else None
            if gstate in (None, CANCELLED, "UNKNOWN"):
                self._compensate_unapprove(
                    scope, claim_id, entry, comp,
                    "gate went %s during approve" % gstate)
                raise ClaimGateError(
                    "child %s/%s reached %s in the gate during approval; "
                    "the approval was compensated" % (scope, claim_id,
                                                      gstate))
            if gstate == "EFFECT_DONE":
                # The executor settled through the fenced path between
                # step (3) and this check: legitimate, and the tree must
                # say so rather than claim APPROVED.
                entry["state"] = "EFFECT_DONE"
                entry["outcome"] = grec.get("outcome")
                self._composite_history(
                    comp, "CHILD_SETTLED",
                    "child=%s state=EFFECT_DONE outcome=%s "
                    "(settled concurrently with approval)"
                    % (claim_id, grec.get("outcome")))
                if grec.get("outcome") == "FAILED" and \
                        comp["state"] != C_DEGRADED:
                    comp["state"] = C_DEGRADED
                    self._composite_history(
                        comp, "DEGRADED", "child %s FAILED" % claim_id)
                self._recompute_parent_state(comp)
                self._write_composite(scope, comp)
                out = dict(receipt)
                out["composite_parent"] = comp["parent_claim_id"]
                out["executed_concurrently"] = True
                return out
            if comp["state"] == C_CANCELLED:
                self._compensate_unapprove(scope, claim_id, entry, comp,
                                           "parent cancelled during approve")
                raise ParentCancelled(
                    "composite was CANCELLED during approval; the approval "
                    "was compensated")
            if comp["state"] == C_DEGRADED and not force:
                self._compensate_unapprove(scope, claim_id, entry, comp,
                                           "parent degraded during approve")
                raise ParentDegraded(
                    "composite DEGRADED during approval; the approval was "
                    "compensated — re-approve with force + override_reason")
            entry["state"] = APPROVED
            if force:
                entry["forced"] = True
                waived = ",".join(entry.get("after", [])) or "none"
                self._composite_history(
                    comp, "FORCE_APPROVED",
                    "child=%s approver=%s reason=%s waived_after=[%s]"
                    % (claim_id, approver_id, override_reason, waived))
                hold_path = self.approval._hold_path(scope, claim_id)
                rec = self.approval._read_hold(scope, claim_id)
                self.approval._append_history(
                    rec, "FORCE_APPROVED",
                    "approver=%s reason=%s waived_after=[%s]"
                    % (approver_id, override_reason, waived))
                self._write_atomic(hold_path, rec)
            else:
                self._composite_history(comp, "CHILD_APPROVED", claim_id)
            self._write_composite(scope, comp)
            out = dict(receipt)
            out["composite_parent"] = comp["parent_claim_id"]
            return out

    def _parent_of(self, scope: str, claim_id: str) -> str:
        rec = self.approval._read_hold(scope, claim_id)
        if rec is None or not isinstance(rec.get("parent"), dict):
            raise ClaimGateError(
                "claim %s/%s is not a composite child" % (scope, claim_id))
        return rec["parent"]["claim_id"]

    def _require_composite(self, scope: str, claim_id: str) -> dict:
        parent_claim_id = self._parent_of(scope, claim_id)
        comp = self._read_composite(scope, parent_claim_id)
        if comp is None:
            raise UnknownParent(
                "composite %s/%s vanished" % (scope, parent_claim_id))
        return comp

    def _compensate_unapprove(self, scope: str, claim_id: str, entry: dict,
                              comp: dict, why: str) -> None:
        """Undo an approval that landed while the tree moved against it:
        cancel the claim in the gate and mark the child CANCELLED."""
        try:
            self.approval.gate.cancel(
                scope, claim_id, "composite-compensation: %s" % why)
        except ClaimGateError:
            pass  # already terminal — the marking below still applies
        entry["state"] = CANCELLED
        entry["outcome"] = None
        self._composite_history(comp, "APPROVAL_COMPENSATED",
                                "child=%s why=%s" % (claim_id, why))
        self._write_composite(scope, comp)

    # -- child settlement -------------------------------------------------------

    def settle_child(self, scope: str, claim_id: str, outcome: str,
                     receipt=None, owner_id=None, fencing_token=None,
                     unknown_reason=None) -> dict:
        """Settle a child (effect or unknown) and update tree state.

        A FAILED outcome marks the parent DEGRADED (fencing siblings
        until a forced approval). COMPLETE is recomputed; a late FAILED
        flips COMPLETE back to DEGRADED.
        """
        if unknown_reason is not None:
            record = self.approval.mark_unknown(
                scope, claim_id, unknown_reason, owner_id=owner_id,
                fencing_token=fencing_token)
        else:
            if outcome not in ("SUCCESS", "FAILED"):
                raise ClaimGateError("outcome must be SUCCESS or FAILED")
            record = self.approval.mark_effect(
                scope, claim_id, outcome, receipt, owner_id=owner_id,
                fencing_token=fencing_token)
        with self._composite_lock(scope):
            comp = self._require_composite(scope, claim_id)
            entry = self._entry_or_raise(comp, scope, claim_id)
            entry["state"] = record["state"]
            entry["outcome"] = record.get("outcome")
            self._composite_history(
                comp, "CHILD_SETTLED",
                "child=%s state=%s outcome=%s"
                % (claim_id, record["state"], record.get("outcome")))
            if record.get("outcome") == "FAILED":
                if comp["state"] != C_DEGRADED:
                    comp["state"] = C_DEGRADED
                    self._composite_history(
                        comp, "DEGRADED", "child %s FAILED" % claim_id)
            self._recompute_parent_state(comp)
            self._write_composite(scope, comp)
            return record

    def refuse_child(self, scope: str, claim_id: str, actor_id: str,
                     reason: str) -> dict:
        """Refuse/withdraw a child and update tree state."""
        record = self.approval.refuse(scope, claim_id, actor_id, reason)
        with self._composite_lock(scope):
            try:
                comp = self._require_composite(scope, claim_id)
            except ClaimGateError:
                return record  # not composite-bound; plain refuse stands
            entry = self._child_entry(comp, claim_id)
            if entry is not None:
                entry["state"] = CANCELLED
                self._composite_history(comp, "CHILD_REFUSED", claim_id)
                self._recompute_parent_state(comp)
                self._write_composite(scope, comp)
            return record

    # -- cancellation propagation -------------------------------------------------

    def _gate_state(self, scope: str, claim_id: str):
        """Direct read of the gate record state (atomic file; no lock
        taken). None when no gate record exists — the normal case for a
        child the gate never admitted."""
        rec = self.approval.gate._read_claim(
            self.approval.gate._claim_path(scope, claim_id))
        return rec.get("state") if rec else None

    def _cancel_approved_child(self, scope: str, claim_id: str,
                               reason: str) -> str:
        """Cancel an APPROVED child's gate record, including leased
        (in-flight) ones. Returns the action taken; never aborts the
        fan-out with a terminal-state surprise.

        The gate's 1c rule refuses the no-fence cancel on records
        carrying a fencing token. For a live (or expired-but-unreleased)
        lease the fenced primitive is used with the CURRENT lease
        credentials — the token is consumed, fencing the executor's
        subsequent writes out. That is the fenced path working as
        designed, not a bypass: the cancel is ordered through the fence.
        A released lease (owner cleared, token persisting per D-CRIT-1)
        cannot be cancelled without payload bytes for a fresh lease,
        which the composite layer does not retain — reported loudly.
        """
        gate = self.approval.gate
        for _attempt in range(4):
            try:
                gate.cancel(scope, claim_id, reason)
                return "gate-cancelled"
            except ClaimGateError as exc:
                msg = str(exc)
                if "terminal state" in msg:
                    return "already-terminal"
                if "fencing token" not in msg:
                    raise
            rec = gate._read_claim(gate._claim_path(scope, claim_id))
            if rec is None or rec.get("state") in (
                    CANCELLED, "EFFECT_DONE", "UNKNOWN"):
                return "already-terminal"
            owner, token = rec.get("lease_owner"), rec.get("fencing_token")
            if owner is None:
                return "uncancellable-released-lease"
            try:
                gate.cancel_fenced(scope, claim_id, owner, token, reason)
                return "gate-cancelled-fenced"
            except ClaimGateError:
                continue  # rotated/released mid-flight; re-read and retry
        return "cancel-failed-retries-exhausted"

    def _cancel_one_child(self, scope: str, comp_parent: str, cid: str,
                          actor_id: str, cancel_reason: str):
        """Cancel a single non-terminal child.

        Returns (action, done): the diagnostic action string, and whether
        the child can no longer execute through any path the composite
        layer knows (safe to mark CANCELLED in the tree). Raises only
        for unexpected failures (recorded per-child by the caller, never
        aborting the fan-out).
        """
        view = self.approval.verify(scope, cid)
        st = view["approval_state"]
        if st == HELD_APPROVAL:
            try:
                self.approval.refuse(scope, cid, actor_id, cancel_reason)
                action = "refused"
            except ClaimGateError as exc:
                if "already approved" not in str(exc):
                    raise
                gact, done = self._fence_gate_record(scope, cid,
                                                     cancel_reason)
                return ("refused-race/" + gact, done)
            # A raw-path lease may exist on the gate record even though
            # the hold never approved: leave no executable gate record
            # behind a cancelled tree.
            gact, gdone = self._fence_gate_record(scope, cid, cancel_reason)
            if gact == "no-gate-record":
                return (action, True)
            return ("%s+gate/%s" % (action, gact), gdone)
        if st == APPROVED:
            gact, done = self._fence_gate_record(scope, cid, cancel_reason)
            return (gact, done)
        if st == CANCELLED:
            return ("already-cancelled", True)
        # No hold record: still leave no executable gate record behind.
        gact, done = self._fence_gate_record(scope, cid, cancel_reason)
        return ("no-hold-record+gate/%s" % gact, done)

    def _fence_gate_record(self, scope: str, claim_id: str,
                           reason: str):
        """Ensure the gate record cannot execute: cancel it (fenced when
        leased). Returns (action, done)."""
        if self._gate_state(scope, claim_id) != "CLAIMED":
            return ("no-gate-record", True)
        action = self._cancel_approved_child(scope, claim_id, reason)
        done = action in ("gate-cancelled", "gate-cancelled-fenced",
                          "already-terminal")
        return (action, done)

    def cancel_composite(self, scope: str, parent_claim_id: str,
                         actor_id: str, reason: str) -> dict:
        """Cancel the parent and propagate to all non-terminal children.

        Crash-repairable: re-invocation (or composite-propagate) converges;
        every child ends terminal, and per-child outcomes are reported.
        """
        _check_actor(actor_id)
        reason = _check_reason(reason)
        # The parent goes through the normal paths (self-locking). An
        # approved parent may itself carry a lease (in-flight): the same
        # fenced-cancel discipline as for children applies.
        parent_view = self.approval.verify(scope, parent_claim_id)
        parent_state = parent_view["approval_state"]
        if parent_state == HELD_APPROVAL:
            self.approval.refuse(scope, parent_claim_id, actor_id, reason)
        elif parent_state == APPROVED:
            self._cancel_approved_child(
                scope, parent_claim_id, "composite-cancel: %s" % reason)
        with self._composite_lock(scope):
            comp = self._read_composite(scope, parent_claim_id)
            if comp is None:
                raise UnknownParent(
                    "no composite %s/%s" % (scope, parent_claim_id))
            comp["state"] = C_CANCELLED
            self._composite_history(
                comp, "CANCELLED", "actor=%s reason=%s" % (actor_id, reason))
            self._write_composite(scope, comp)
        swept = self.propagate_cancellation(scope, parent_claim_id,
                                            actor_id, reason)
        return {"composite": parent_claim_id, "state": C_CANCELLED,
                "swept": swept}

    def propagate_cancellation(self, scope: str, parent_claim_id: str,
                               actor_id: str, reason: str) -> list:
        """Idempotent re-run of cancellation fan-out (crash repair).

        For each non-terminal child: HELD -> refuse (reason
        parent-cancelled:<parent>); APPROVED-but-unexecuted -> gate
        cancel, fenced when the child carries a lease (the token is
        consumed, fencing the executor's later writes out); in-flight
        leases -> gate cancel (the G4 boundary: the record is cancelled;
        effects already running are the consumer's cooperative-cancel
        responsibility, documented). Terminal children are reported, not
        touched.

        The fan-out NEVER aborts on a per-child failure: every child
        gets a recorded outcome, and re-running converges over whatever
        remains.
        """
        _check_actor(actor_id)
        reason = _check_reason(reason)
        comp = self._read_composite(scope, parent_claim_id)
        if comp is None:
            raise UnknownParent(
                "no composite %s/%s" % (scope, parent_claim_id))
        cancel_reason = "parent-cancelled:%s (%s)" % (parent_claim_id, reason)
        swept = []
        for child in list(comp["children"]):
            cid = child["claim_id"]
            if child["state"] in _TERMINAL_CHILD:
                swept.append({"claim_id": cid, "action": "already-terminal",
                              "state": child["state"]})
                continue
            try:
                action, done = self._cancel_one_child(
                    scope, parent_claim_id, cid, actor_id, cancel_reason)
            except ClaimGateError as exc:
                # Unexpected per-child failure: recorded loudly, the
                # fan-out continues; a re-run retries this child.
                swept.append({"claim_id": cid,
                              "action": "cancel-failed: %s" % str(exc)[:160]})
                continue
            with self._composite_lock(scope):
                comp = self._read_composite(scope, parent_claim_id)
                entry = self._child_entry(comp, cid)
                if entry is not None and entry["state"] not in \
                        _TERMINAL_CHILD:
                    if done:
                        entry["state"] = C_CANCELLED
                        self._composite_history(
                            comp, "CHILD_CANCELLED",
                            "child=%s action=%s" % (cid, action))
                    else:
                        # Could not cancel (e.g. released lease without
                        # payload bytes for a fresh lease): recorded
                        # loudly; a re-run retries.
                        self._composite_history(
                            comp, "CHILD_CANCEL_DEFERRED",
                            "child=%s action=%s" % (cid, action))
                    self._write_composite(scope, comp)
            swept.append({"claim_id": cid, "action": action})
        return swept

    # -- status ---------------------------------------------------------------------

    def is_composite_child(self, scope: str, claim_id: str) -> bool:
        """True iff the claim is bound as a composite child. Used by the
        CLI to route settle/refuse verbs through the tree bookkeeping."""
        try:
            rec = self.approval._read_hold(scope, claim_id)
        except ClaimGateError:
            return False
        return rec is not None and isinstance(rec.get("parent"), dict)

    def composite_status(self, scope: str, parent_claim_id: str) -> dict:
        """Tree view: composite state plus per-child hold states."""
        with self._composite_lock(scope):
            comp = self._read_composite(scope, parent_claim_id)
            if comp is None:
                raise UnknownParent(
                    "no composite %s/%s" % (scope, parent_claim_id))
            view = {
                "scope": scope,
                "parent_claim_id": parent_claim_id,
                "composite_state": comp["state"],
                "children": [],
                "history_len": len(comp["history"]),
            }
            for child in comp["children"]:
                hold = self.approval._read_hold(scope, child["claim_id"])
                view["children"].append({
                    "claim_id": child["claim_id"],
                    "tree_state": child["state"],
                    "outcome": child.get("outcome"),
                    "hold_state": hold["state"] if hold else None,
                    "after": child.get("after", []),
                })
            return view

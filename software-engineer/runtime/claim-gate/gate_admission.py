"""Typed admission for the Claim Gate.

Admission answers ONE question before any claim is attempted: is this request
well-formed, well-identified, and authorized to knock? It performs no I/O and
mutates nothing — it is a pure function over the request.

Identity model (exact):
- ``task_id``: the project task identity, e.g. "GATE-COMM-20261013-001".
  Must match the safe-component pattern (no path separators, no traversal).
- ``scope``: must be REGISTERED in SCOPE_REGISTRY. Unregistered scopes are
  denied — the gate does not admit work it has no policy for.
- ``owner_id``: the worker identity that will hold the lease.
- ``authority``: typed AuthorityKind + ``authority_ref`` (the order or dispatch
  id that authorizes this work, e.g. "GATE-COMM-20261013-001" for an owner-direct
  order, or a coordinator run id for dispatched work).

Decision vocabulary for prior records mirrors the MAL-GATE-102 workpack
classifier (module-slices/claim-gate/idempotency_trace.py, worker 12b9710f,
2026-10-13), reconciled 2026-10-13: REUSE / CONFLICT / RETAIN_UNKNOWN /
PRIOR_INCOMPLETE agree exactly with this gate's idempotent-replay,
changed-byte-refusal, and read-only-UNKNOWN semantics. Implemented natively
here against gate records; the workpack file is referenced, not copied.

The local gate is NOT host-policy authority: admission checks identity and the stated
authority basis, but it does not grant effect authority. Canonical permissions
(host-policy, forward_enabled=False, protected scopes) are preserved and must be
checked by the caller at the effect layer.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from enum import Enum

from claim_gate import CANCELLED, CLAIMED, EFFECT_DONE, UNKNOWN


class AuthorityKind(Enum):
    """The typed basis on which a claim request is authorized."""
    OWNER_DIRECT = "owner_direct"          # owner direct order
    COORDINATOR_DISPATCH = "coordinator_dispatch"  # software-engineer-capability-coordinator-001
    SCOPED_WORKER = "scoped_worker"      # finite module worker delegation


_COMPONENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


@dataclass(frozen=True)
class ScopePolicy:
    description: str
    max_lease_seconds: float
    default_lease_seconds: float


SCOPE_REGISTRY: dict[str, ScopePolicy] = {}


def register_scope(scope: str, policy: ScopePolicy) -> None:
    """Register a scope the gate admits. Raises on unsafe name or dupes."""
    if not isinstance(scope, str) or not _COMPONENT.fullmatch(scope):
        raise ValueError("unsafe scope name: %r" % (scope,))
    if scope in SCOPE_REGISTRY:
        raise ValueError("scope already registered: %r" % (scope,))
    SCOPE_REGISTRY[scope] = policy


# The module's own scopes. collaboration is the communication scope proven by
# GATE-COMM-20261013-001; engineering-ops covers module-internal operations.
register_scope("collaboration", ScopePolicy(
    description="Guarded collaboration receiving (GATE-COMM hook)",
    max_lease_seconds=3600.0, default_lease_seconds=120.0))
register_scope("engineering-ops", ScopePolicy(
    description="module-internal operations (sweeps, reconciliation probes)",
    max_lease_seconds=600.0, default_lease_seconds=60.0))


class AdmissionDecision(Enum):
    ALLOW = "allow"
    DENY = "deny"


@dataclass(frozen=True)
class AdmissionRequest:
    task_id: str
    scope: str
    owner_id: str
    authority: AuthorityKind
    authority_ref: str
    payload_bytes: bytes
    lease_seconds: float = 0.0  # 0 -> scope default


@dataclass
class Admission:
    decision: AdmissionDecision
    reasons: list[str] = field(default_factory=list)
    normalized_lease_seconds: float = 0.0

    @property
    def allowed(self) -> bool:
        return self.decision == AdmissionDecision.ALLOW


def admit(request: AdmissionRequest) -> Admission:
    """Pure admission check. No I/O, no mutation."""
    reasons: list[str] = []

    # D4: admission is the trust boundary — a non-request is denied, not crashed.
    if not isinstance(request, AdmissionRequest):
        return Admission(AdmissionDecision.DENY,
                         ["request must be an AdmissionRequest, got %r"
                          % type(request).__name__])

    if not isinstance(request.task_id, str) or not _COMPONENT.fullmatch(request.task_id):
        reasons.append("task_id unsafe or missing: %r" % (request.task_id,))
    policy = SCOPE_REGISTRY.get(request.scope)
    if policy is None:
        reasons.append("scope not registered: %r" % (request.scope,))
    if not isinstance(request.owner_id, str) or not request.owner_id.strip():
        reasons.append("owner_id must be a non-empty string")
    if not isinstance(request.authority, AuthorityKind):
        reasons.append("authority must be an AuthorityKind")
    if not isinstance(request.authority_ref, str) or not request.authority_ref.strip():
        reasons.append("authority_ref must name the authorizing order/dispatch")
    if not isinstance(request.payload_bytes, (bytes, bytearray)) or len(request.payload_bytes) == 0:
        reasons.append("payload_bytes must be non-empty bytes")

    lease = 0.0
    if policy is not None:
        raw = request.lease_seconds if request.lease_seconds else 0.0
        try:
            lease = float(raw)
        except (TypeError, ValueError):
            reasons.append("lease_seconds %r is not numeric"
                           % (request.lease_seconds,))
        else:
            # D6: non-finite leases are denied — admission must not bless a
            # value its own consumer (claim_lease) will refuse.
            if not math.isfinite(lease):
                reasons.append("lease_seconds %r is not finite"
                               % (request.lease_seconds,))
            elif lease == 0:
                lease = policy.default_lease_seconds
            elif lease < 0 or lease > policy.max_lease_seconds:
                reasons.append(
                    "lease_seconds %r outside (0, %r] for scope %r"
                    % (request.lease_seconds, policy.max_lease_seconds,
                       request.scope))

    if reasons:
        return Admission(AdmissionDecision.DENY, reasons)
    return Admission(AdmissionDecision.ALLOW, [], normalized_lease_seconds=lease)


# ----------------------------------------------------------------------------
# Prior-record classification (MAL-GATE-102 vocabulary, gate-native)


class PriorDecision(Enum):
    NO_PRIOR = "no_prior"            # no record: admission may proceed to claim
    REUSE = "reuse"                  # same digest, settled or held: use it, no new effect
    CONFLICT = "conflict"            # same id, changed bytes: refuse
    RETAIN_UNKNOWN = "retain_unknown"  # outcome unconfirmed: hold, never retry
    PRIOR_INCOMPLETE = "prior_incomplete"  # record unreadable: refuse, investigate
    TAKEOVER = "takeover"            # extension: lease expired/absent, takeover permitted
    # TAKEOVER extends the MAL-GATE-102 vocabulary, which had no lease concept.
    # The workpack's four decisions are preserved verbatim above.


@dataclass(frozen=True)
class PriorClassification:
    decision: PriorDecision
    effect_allowed: bool
    detail: str = ""


def classify_against_prior(payload_bytes: bytes,
                           prior_record: dict | None,
                           owner_id: str | None = None,
                           now: float | None = None) -> PriorClassification:
    """Classify a request against an existing gate record.

    Pure function. Mirrors the MAL-GATE-102 decision vocabulary (plus TAKEOVER
    for lease expiry, which the workpack had no concept of). The gate's own
    claim/verify/reconcile operations remain the enforcement layer; this is
    the advisory pre-check with identical semantics.
    """
    import hashlib
    import hmac
    import time
    # D3: the classifier never crashes on a non-bytes payload.
    if not isinstance(payload_bytes, (bytes, bytearray)):
        return PriorClassification(PriorDecision.PRIOR_INCOMPLETE, False,
                                   "payload unreadable")
    if prior_record is None:
        return PriorClassification(PriorDecision.NO_PRIOR, True,
                                   "no prior record")
    if not isinstance(prior_record, dict) or "payload_digest" not in prior_record:
        return PriorClassification(PriorDecision.PRIOR_INCOMPLETE, False,
                                   "prior record unreadable")
    # D2: a non-string digest is the same "unreadable prior" case.
    if not isinstance(prior_record["payload_digest"], str):
        return PriorClassification(PriorDecision.PRIOR_INCOMPLETE, False,
                                   "prior digest unreadable")
    digest = hashlib.sha256(bytes(payload_bytes)).hexdigest()
    if not hmac.compare_digest(prior_record["payload_digest"], digest):
        return PriorClassification(
            PriorDecision.CONFLICT, False,
            "claim_id %r exists with different payload bytes; original preserved"
            % (prior_record.get("claim_id"),))
    state = prior_record.get("state")
    if state == UNKNOWN:
        return PriorClassification(PriorDecision.RETAIN_UNKNOWN, False,
                                   "prior outcome unconfirmed; reconcile read-only")
    if state in (EFFECT_DONE, CANCELLED):
        return PriorClassification(PriorDecision.REUSE, False,
                                   "prior %s; use recorded outcome" % state)
    if state == CLAIMED:
        ts = now if now is not None else time.time()
        expires = prior_record.get("lease_expires_epoch")
        holder = prior_record.get("lease_owner")
        try:
            live = (holder is not None and expires is not None
                    and ts < float(expires))
        except (TypeError, ValueError):
            return PriorClassification(PriorDecision.PRIOR_INCOMPLETE, False,
                                       "prior lease_expires_epoch unreadable")
        if live and holder == owner_id:
            return PriorClassification(PriorDecision.REUSE, False,
                                       "own live claim; continue it, start no new effect")
        if live:
            return PriorClassification(PriorDecision.REUSE, False,
                                       "claim held by %r until %s" % (holder, prior_record.get("lease_expires_ts")))
        return PriorClassification(PriorDecision.TAKEOVER, True,
                                   "lease expired or absent; takeover permitted")
    return PriorClassification(PriorDecision.PRIOR_INCOMPLETE, False,
                               "prior has unrecognized state %r" % (state,))

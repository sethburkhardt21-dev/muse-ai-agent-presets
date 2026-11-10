"""Bounded, purely local Family Link metadata envelope and replay-shape guard.

Not a new transport, durable replay ledger, owner auth, native recipient,
message relay, effect gate, scheduler or cross-account permission issuer.
Caller-supplied history and consent are UNTRUSTED declarations.
"""
from __future__ import annotations

from datetime import datetime,timezone
import hashlib
import json
import re

from .family import propose_handoff, verify_finding

SCHEMA="r66/family-offline-envelope-v1"
STATE="PROPOSAL_ONLY_NOT_SENT"
SHA=re.compile(r"^[a-f0-9]{64}$")
ID=re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,99}$")
BASENAME=re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
FIELDS=frozenset({
    "schema","state","sender_role","receiver_role","request_id",
    "requested_capability","finding_sha256","caller_declared_consent",
    "valid_from_utc","valid_until_utc","family_link_enabled",
    "native_receipt","recipient_acknowledged","effect_authorized",
    "sender_authenticated","recipient_authenticated",
    "consent_authenticated","replay_history_authenticated",
})
FALSE_FLAGS=(
    "family_link_enabled","native_receipt","recipient_acknowledged",
    "effect_authorized","sender_authenticated","recipient_authenticated",
    "consent_authenticated","replay_history_authenticated",
)


def _wire(value: object) -> bytes:
    try:
        raw=json.dumps(value,sort_keys=True,separators=(",",":"),
                       ensure_ascii=True,allow_nan=False).encode("utf-8")
    except (ValueError,TypeError,UnicodeError,RecursionError) as exc:
        raise ValueError("ENVELOPE_NOT_SERIALIZABLE") from exc
    if len(raw)>32_768:
        raise ValueError("ENVELOPE_TOO_LARGE")
    return raw


def _digest(value: object) -> str:
    return hashlib.sha256(_wire(value)).hexdigest()


def _finding(finding: object) -> str:
    """Review observed shape, plus exact synthetic full-source bytes when FOUND."""
    if type(finding) is not dict:
        raise ValueError("FINDING_NOT_OBJECT")
    try:
        result=verify_finding(finding)
    except ValueError as exc:
        raise ValueError("FINDING_INVALID") from exc
    if result.get("status")!="VALID_FINDING_ONLY":
        raise ValueError("FINDING_INVALID")
    uri=finding["source_uri"]
    if (type(uri) is not str or BASENAME.fullmatch(uri) is None or
        uri in (".","..") or uri.endswith(".") or ".." in uri):
        raise ValueError("SOURCE_REFERENCE_MUST_BE_NEUTRAL_BASENAME")
    observation=finding["observation"]
    if type(observation) is not str:
        raise ValueError("OBSERVATION_NOT_TEXT")
    try:
        raw=observation.encode("utf-8")
    except UnicodeError as exc:
        raise ValueError("OBSERVATION_INVALID") from exc
    if len(raw)>16_384 or b"\0" in raw:
        raise ValueError("OBSERVATION_TOO_LARGE_OR_UNSAFE")
    if finding["result"]=="FOUND":
        if not raw or hashlib.sha256(raw).hexdigest()!=finding["source_sha256"]:
            raise ValueError("OBSERVATION_SOURCE_DIGEST_MISMATCH")
    elif observation!="":
        raise ValueError("NOHIT_MUST_NOT_INVENT_OBSERVATION")
    return _digest(finding)


def finding_sha256(finding: object) -> str:
    """Metadata digest, not authenticated source ownership or truth."""
    return _finding(finding)


def envelope_sha256(envelope: object) -> str:
    if type(envelope) is not dict:
        raise ValueError("ENVELOPE_NOT_OBJECT")
    return _digest(envelope)


def _parse_utc(value: object) -> datetime:
    if type(value) is not str:
        raise ValueError("UTC_TIME_REQUIRED")
    try:
        dt=datetime.strptime(value,"%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except (ValueError,TypeError) as exc:
        raise ValueError("UTC_TIME_REQUIRED") from exc
    if dt.strftime("%Y-%m-%dT%H:%M:%SZ")!=value:
        raise ValueError("NONCANONICAL_UTC_TIME")
    return dt


def _times(start: object,end: object,now: object) -> None:
    if type(now) is not datetime or now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("AWARE_NOW_REQUIRED")
    a=_parse_utc(start)
    b=_parse_utc(end)
    if not (0<(b-a).total_seconds()<=3600):
        raise ValueError("BOUNDED_VALIDITY_REQUIRED")
    if not (a<=now.astimezone(timezone.utc)<b):
        raise ValueError("EXPIRED_OR_NOT_YET_VALID")


def _ids(value: object, label: str) -> set[str]:
    if type(value) is not list or len(value)>256:
        raise ValueError("UNTRUSTED_HISTORY_SCHEMA_"+label)
    used=set()
    for item in value:
        if type(item) is not str or ID.fullmatch(item) is None or item in used:
            raise ValueError("UNTRUSTED_HISTORY_SCHEMA_"+label)
        used.add(item)
    return used


def prepare_offline_envelope(
    sender_role: str,receiver_role: str,request_id: str,capability: str,
    finding: object,declared_consent: bool,valid_from_utc: str,
    valid_until_utc: str,now_utc: datetime,
) -> dict:
    """Make a local *preview* with no delivery, signing or durable state."""
    if declared_consent is not True:
        raise ValueError("EXPLICIT_CALLER_DECLARED_CONSENT_REQUIRED")
    if any(type(value) is not str for value in (sender_role,receiver_role,request_id,capability)):
        raise ValueError("FAMILY_ROLE_OR_REQUEST_TYPE_REFUSED")
    _times(valid_from_utc,valid_until_utc,now_utc)
    local=propose_handoff(sender_role,receiver_role,
             request_id=request_id,capability=capability)
    if local["state"]!=STATE or local["effect_authorized"] is not False:
        raise ValueError("CURRENT_FAMILY_POLICY_NOT_DISABLED")
    digest=_finding(finding)
    return {
        "schema":SCHEMA,"state":STATE,
        "sender_role":sender_role,"receiver_role":receiver_role,
        "request_id":request_id,"requested_capability":capability,
        "finding_sha256":digest,"caller_declared_consent":True,
        "valid_from_utc":valid_from_utc,"valid_until_utc":valid_until_utc,
        **{key:False for key in FALSE_FLAGS},
    }


def review_local_envelope(
    envelope: object,finding: object,expected_envelope_sha256: str,
    seen_request_ids: list[str],revoked_request_ids: list[str],
    now_utc: datetime,
    expected_receiver_role: str,
) -> dict:
    """Read-only schema guard, bound to supplied receiver-local role context."""
    if type(expected_envelope_sha256) is not str or SHA.fullmatch(expected_envelope_sha256) is None:
        raise ValueError("OUT_OF_BAND_ENVELOPE_PIN_REQUIRED")
    if type(envelope) is not dict or set(envelope)!=FIELDS:
        raise ValueError("ENVELOPE_FIELDS_NOT_ADMITTED")
    if (envelope["schema"]!=SCHEMA or envelope["state"]!=STATE or
        envelope["caller_declared_consent"] is not True or
        any(envelope[key] is not False for key in FALSE_FLAGS)):
        raise ValueError("ENVELOPE_AUTHORITY_NOT_ADMITTED")
    if envelope_sha256(envelope)!=expected_envelope_sha256:
        raise ValueError("ENVELOPE_PIN_MISMATCH")
    _times(envelope["valid_from_utc"],envelope["valid_until_utc"],now_utc)
    # An out-of-band local receiver context must match the wire receiver.
    # This is still a caller assertion, NOT native host authentication.
    if (type(expected_receiver_role) is not str or
        expected_receiver_role!=envelope["receiver_role"]):
        raise ValueError("RECEIVER_CONTEXT_ROLE_MISMATCH")
    if any(type(envelope[key]) is not str for key in (
        "sender_role","receiver_role","request_id","requested_capability")):
        raise ValueError("FAMILY_ROLE_OR_REQUEST_TYPE_REFUSED")
    proposed=propose_handoff(
        envelope["sender_role"],envelope["receiver_role"],
        request_id=envelope["request_id"],
        capability=envelope["requested_capability"])
    if proposed["state"]!=STATE or proposed["effect_authorized"] is not False:
        raise ValueError("FAMILY_PROPOSAL_NOT_DISABLED")
    if envelope["finding_sha256"]!=_finding(finding):
        raise ValueError("FINDING_PAYLOAD_DIGEST_MISMATCH")
    seen=_ids(seen_request_ids,"SEEN")
    revoked=_ids(revoked_request_ids,"REVOKED")
    if envelope["request_id"] in revoked:
        raise ValueError("DECLARED_REQUEST_REVOKED")
    if envelope["request_id"] in seen:
        raise ValueError("DECLARED_REQUEST_REPLAY")
    return {
        "schema":"r66/family-offline-shape-review-v1",
        "status":"LOCAL_HANDOFF_REVIEW_ONLY_NOT_DELIVERED",
        "request_id":envelope["request_id"],
        "sender_role":envelope["sender_role"],
        "receiver_role":envelope["receiver_role"],
        "receiver_context_authenticated":False,
        "envelope_sha256":expected_envelope_sha256,
        "finding_sha256":envelope["finding_sha256"],
        "recipient_acknowledged":False,
        "effect_authorized":False,
        "sender_authenticated":False,
        "recipient_authenticated":False,
        "consent_authenticated":False,
        "replay_history_authenticated":False,
        "durable_replay_fence_verified":False,
        "native_transport_invoked":False,
    }

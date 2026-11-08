"""Bounded local provenance checks for the neutral Software Engineer.

Original-source-guided contract: digest-qualified references and donor-manifest
admission, with stricter path refusal and no imported private profile/state.
This module grants no external, native Muse, or redistribution authority.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import stat

_REF = re.compile(r"^([A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?)@sha256:([0-9a-f]{64})$")
_HEX = re.compile(r"^[0-9a-f]{64}$")
_PIN_SUFFIXES = ("_sha256", "_digest", "_pin")
_MAX_MANIFEST_BYTES = 1_048_576
_MAX_MEMBER_BYTES = 128 * 1024 * 1024


class ProvenanceRefused(ValueError):
    """Source identity was unavailable, malformed, or unverifiable."""


def make_ref(name: str, digest: str) -> str:
    """Make a content-qualified reference without changing the file."""
    if not isinstance(name, str) or not isinstance(digest, str):
        raise ProvenanceRefused("invalid pin reference")
    ref = f"{name}@sha256:{digest.lower()}"
    if _REF.fullmatch(ref) is None:
        raise ProvenanceRefused("invalid pin reference")
    return ref


def parse_ref(ref: str) -> tuple[str, str]:
    if not isinstance(ref, str):
        raise ProvenanceRefused("malformed pin reference")
    match = _REF.fullmatch(ref.strip())
    if match is None:
        raise ProvenanceRefused("malformed pin reference")
    return match.group(1), match.group(2)


def _read_stable_regular_file(path: os.PathLike[str] | str, *, max_bytes: int) -> bytes:
    """Return bounded bytes, refusing links and changed files.

    Checks file identity before and after reading, including a no-follow open
    where supported; an attacker with arbitrary write access can still race
    this local check, so callers must use an owned, fenced work root.
    """
    item = Path(path)
    try:
        before = item.lstat()
        if stat.S_ISLNK(before.st_mode):
            raise ProvenanceRefused("source symlink refused")
        if not stat.S_ISREG(before.st_mode):
            raise ProvenanceRefused("source is not a regular file")
        if before.st_size > max_bytes:
            raise ProvenanceRefused("source too large")
        flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        fd = os.open(item, flags)
        with os.fdopen(fd, "rb") as f:
            opened = os.fstat(f.fileno())
            if (opened.st_dev, opened.st_ino, opened.st_size) != (
                    before.st_dev, before.st_ino, before.st_size):
                raise ProvenanceRefused("source changed during open")
            contents = f.read(max_bytes + 1)
            after_fd = os.fstat(f.fileno())
        if len(contents) > max_bytes:
            raise ProvenanceRefused("source too large")
        after = item.lstat()
        for observed in (after_fd, after):
            if (observed.st_dev, observed.st_ino, observed.st_size, observed.st_mtime_ns) != (
                    before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns):
                raise ProvenanceRefused("source changed during verification")
        return contents
    except ProvenanceRefused:
        raise
    except (OSError, TypeError, ValueError) as exc:
        raise ProvenanceRefused("source missing, inaccessible or changed") from exc


def verify_path_against_ref(
    path: os.PathLike[str] | str,
    ref: str,
    allow_name_mismatch: bool = False,
) -> tuple[str, str]:
    """Verify exact local bytes and expected basename; never follow a file link."""
    name, digest = parse_ref(ref)
    if not allow_name_mismatch and Path(path).name != name:
        raise ProvenanceRefused("name mismatch")
    raw = _read_stable_regular_file(path, max_bytes=_MAX_MEMBER_BYTES)
    if hashlib.sha256(raw).hexdigest() != digest:
        raise ProvenanceRefused("digest mismatch")
    return name, digest


def declared_hashes(obj: object, _path: str = "", *, _depth: int = 0) -> list[tuple[str, str]]:
    """Collect original-style pin-labelled references in a JSON document."""
    if _depth > 64:
        raise ProvenanceRefused("manifest nesting exceeds bound")
    found: list[tuple[str, str]] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            key = str(key)
            here = f"{_path}/{key}" if _path else key
            pin_label = any(h in key.lower() for h in ("sha", "digest", "pin"))
            if pin_label and isinstance(value, str) and _HEX.fullmatch(value):
                found.append((here, value))
            else:
                explicit_pin = (key.lower() in ("sha256", "digest", "pin")
                                or key.lower().endswith(_PIN_SUFFIXES))
                if explicit_pin and not isinstance(value, (dict, list)):
                    raise ProvenanceRefused("malformed explicit source digest")
                found.extend(declared_hashes(value, here, _depth=_depth + 1))
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            found.extend(declared_hashes(value, f"{_path}[{index}]", _depth=_depth + 1))
    return found


def _unique_json_pairs(pairs: list[tuple[str, object]]) -> dict:
    values = {}
    for key, value in pairs:
        if key in values:
            raise ProvenanceRefused("duplicate JSON key")
        values[key] = value
    return values


def _refuse_nonstandard_constant(value: str) -> None:
    raise ProvenanceRefused("nonstandard JSON constant")


def admit_manifest_pin(
    manifest_name: str,
    manifest_path: os.PathLike[str] | str,
    pins_registry: dict,
) -> dict:
    """Require manifest pins to resolve to *actually locally verified* donor records.

    A successful result proves a local source relationship only. It does not
    supply an account identity, software license, signer or deployment approval.
    """
    if not isinstance(manifest_name, str) or not manifest_name.strip():
        raise ProvenanceRefused("invalid manifest identity")
    try:
        raw = _read_stable_regular_file(manifest_path, max_bytes=_MAX_MANIFEST_BYTES)
    except ProvenanceRefused as exc:
        if "symlink" in str(exc):
            raise
        raise ProvenanceRefused("manifest local presence not established; never upgraded to local presence") from exc
    try:
        document = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_unique_json_pairs,
            parse_constant=_refuse_nonstandard_constant,
        )
    except ProvenanceRefused:
        raise
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise ProvenanceRefused("manifest not parseable") from exc
    if not isinstance(document, dict):
        raise ProvenanceRefused("manifest must be a JSON object")
    declarations = declared_hashes(document)
    if not declarations:
        raise ProvenanceRefused("manifest declares no pin-labeled digests")
    if not isinstance(pins_registry, dict) or not isinstance(pins_registry.get("donors", []), list):
        raise ProvenanceRefused("donor registry malformed")
    pinned = {
        item["observed_sha256"]
        for item in pins_registry.get("donors", [])
        if isinstance(item, dict)
        and item.get("status") == "pinned_verified"
        and isinstance(item.get("observed_sha256"), str)
        and _HEX.fullmatch(item["observed_sha256"])
    }
    if any(digest not in pinned for _, digest in declarations):
        raise ProvenanceRefused("declared hashes not resolving to pinned donors")
    digest = hashlib.sha256(raw).hexdigest()
    return {
        "name": manifest_name,
        "status": "pinned_verified",
        "declared_sha256": digest,
        "observed_sha256": digest,
        "declared_bytes": len(raw),
        "observed_bytes": len(raw),
        "local_path": Path(manifest_path).name,
        "note": "Manifest bytes match caller-supplied donor-pin records; no donor re-readback.",
        "evidence_grade": "LOCAL_BYTES_ONLY",
        "donor_files_reverified": False,
        "registry_authenticated": False,
        "source_owner_authenticated": False,
        "redistribution_rights_verified": False,
        "native_authority_verified": False,
    }



# R32.2: source-only inventory and a PURE seal over the existing Evidence Finder
# head. This is NOT a second append-only log, receipt writer, or host authority.
from datetime import datetime, timedelta, timezone


def _canonical_digest(value: object) -> str:
    """Stable local fingerprint; this is NOT a digital signature."""
    try:
        payload = json.dumps(value, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=True, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, UnicodeError, OverflowError) as exc:
        raise ProvenanceRefused("noncanonical provenance payload") from exc
    return hashlib.sha256(payload).hexdigest()


def inventory_tree(root: os.PathLike[str] | str, *, max_files: int = 128) -> dict:
    """Read one finite local directory, returning paths and digests but no bytes.

    Reject links and unsupported members rather than following them; no
    scanner-owned network, state database, claim controller, or filesystem
    output is created. The directory must already be owner-admitted.
    """
    if type(max_files) is not int or not 1 <= max_files <= 128:
        raise ProvenanceRefused("invalid inventory file count bound")
    base = Path(root)
    if not base.is_absolute() or ".." in base.parts:
        raise ProvenanceRefused("absolute non-traversing source root required")
    try:
        # A final-component lstat is insufficient: /allowed/link/nested would
        # otherwise cross the owner-selected source boundary through a parent.
        for component in (base, *base.parents):
            if component.is_symlink() or (
                    hasattr(component, "is_junction") and component.is_junction()):
                raise ProvenanceRefused("source symlink ancestor refused")
        stat_root = base.lstat()
    except ProvenanceRefused:
        raise
    except (OSError, TypeError, ValueError) as exc:
        raise ProvenanceRefused("inventory source directory unavailable") from exc
    if stat.S_ISLNK(stat_root.st_mode):
        raise ProvenanceRefused("source symlink refused")
    if not stat.S_ISDIR(stat_root.st_mode):
        raise ProvenanceRefused("inventory source is not a directory")

    records: list[dict] = []
    total_bytes = 0

    def walk(current: Path, depth: int) -> None:
        nonlocal total_bytes
        if depth > 12:
            raise ProvenanceRefused("inventory directory depth exceeded")
        try:
            before = current.lstat()
            if not stat.S_ISDIR(before.st_mode) or current.is_symlink():
                raise ProvenanceRefused("source symlink or invalid directory")
            members = sorted(current.iterdir(), key=lambda p: p.name)
            for item in members:
                kind = item.lstat().st_mode
                if stat.S_ISLNK(kind):
                    raise ProvenanceRefused("source symlink refused")
                if stat.S_ISDIR(kind):
                    walk(item, depth + 1)
                elif stat.S_ISREG(kind):
                    if len(records) >= max_files:
                        raise ProvenanceRefused("inventory file count exceeded")
                    raw = _read_stable_regular_file(item, max_bytes=1_048_576)
                    total_bytes += len(raw)
                    if total_bytes > 8_388_608:
                        raise ProvenanceRefused("inventory total bytes exceeded")
                    relative = item.relative_to(base).as_posix()
                    records.append({
                        "relative_path": relative,
                        "bytes": len(raw),
                        "sha256": hashlib.sha256(raw).hexdigest(),
                    })
                else:
                    raise ProvenanceRefused("unsupported source file type")
            after = current.lstat()
            if ((before.st_dev, before.st_ino, before.st_mtime_ns) !=
                    (after.st_dev, after.st_ino, after.st_mtime_ns)):
                raise ProvenanceRefused("source directory changed during scan")
        except ProvenanceRefused:
            raise
        except (OSError, ValueError) as exc:
            raise ProvenanceRefused("source directory inaccessible or changed") from exc

    walk(base, 0)
    if not records:
        raise ProvenanceRefused("empty source inventory")
    records.sort(key=lambda r: r["relative_path"])
    body = {
        "schema": "software-engineer/source-inventory-v1",
        "file_count": len(records),
        "total_bytes": total_bytes,
        "records": records,
    }
    return {**body, "inventory_sha256": _canonical_digest(body)}


def _local_finder_head(value: object) -> dict:
    """Check the shape of EvidenceLedger.verify(), not its actual issuer.

    The caller must obtain this result from the already-authorized owner
    resolver; this function does not authenticate the caller or the database.
    """
    if type(value) is not dict or value.get("status") != "LOCAL_EVIDENCE_CHAIN_VERIFIED":
        raise ProvenanceRefused("existing Evidence Finder verification required")
    if value.get("chain_verified_locally") is not True:
        raise ProvenanceRefused("Evidence Finder chain unverified")
    for field in ("chain_externally_anchored", "source_owner_authenticated",
                  "independent_truth_verified", "effect_authorized",
                  "recipient_acknowledged"):
        if value.get(field) is not False:
            raise ProvenanceRefused("unverified authority claim")
    if value.get("native_muse_status") != "NOT_INVOKED":
        raise ProvenanceRefused("native authority unverified")
    scope = value.get("scope")
    if type(scope) is not dict or set(scope) != {
        "owner_id", "workspace_id", "role_id", "actor_id"
    } or any(type(v) is not str or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", v)
             for v in scope.values()):
        raise ProvenanceRefused("invalid local Evidence Finder scope")
    count = value.get("receipt_count")
    head = value.get("head_chain_sha256")
    if type(count) is not int or not 1 <= count <= 512:
        raise ProvenanceRefused("empty or invalid Evidence Finder chain")
    if type(head) is not str or _HEX.fullmatch(head) is None:
        raise ProvenanceRefused("invalid Evidence Finder chain head")
    return {
        "evidence_scope": dict(scope),
        "receipt_count": count,
        "head_chain_sha256": head,
    }


def _utc_observation(when: datetime | None) -> datetime:
    stamp = datetime.now(timezone.utc) if when is None else when
    if not isinstance(stamp, datetime) or stamp.tzinfo is None or stamp.utcoffset() is None:
        raise ProvenanceRefused("timezone-aware clock required")
    return stamp.astimezone(timezone.utc)


def make_local_source_seal(
    root: os.PathLike[str] | str,
    evidence_verification: dict,
    *,
    version: int = 1,
    ttl_seconds: int = 86400,
    now: datetime | None = None,
) -> dict:
    """Correlate a SOURCE SNAPSHOT with the *existing* locally checked head.

    No file is written. Trust flags are hard-coded FALSE and cannot be raised
    by caller-supplied role labels. A self-hashed seal is not a signature.
    """
    if type(version) is not int or version < 1:
        raise ProvenanceRefused("invalid seal version")
    if type(ttl_seconds) is not int or not 1 <= ttl_seconds <= 30 * 86400:
        raise ProvenanceRefused("seal lifetime outside 30-day bound")
    timestamp = _utc_observation(now)
    body = {
        "schema": "software-engineer/local-source-seal-v1",
        "version": version,
        "sealed_at": timestamp.isoformat(),
        "expires_at": (timestamp + timedelta(seconds=ttl_seconds)).isoformat(),
        "inventory": inventory_tree(root),
        **_local_finder_head(evidence_verification),
        "trust": "LOCAL_SELF_HASH_NO_EXTERNAL_WITNESS",
        "chain_externally_anchored": False,
        "source_owner_authenticated": False,
        "redistribution_rights_verified": False,
        "roles_authenticated": False,
        "native_muse_bound": False,
        "effect_authorized": False,
        "recipient_acknowledged": False,
    }
    return {**body, "seal_sha256": _canonical_digest(body)}


def verify_local_source_seal(
    root: os.PathLike[str] | str,
    seal: dict,
    evidence_verification: dict,
    *,
    minimum_version: int = 1,
    now: datetime | None = None,
) -> dict:
    """Reweigh source and compare the same Evidence Finder's current head.

    No modification of the Finder, its SQLite chain, original source,
    recipient state, or an independent seal registry is performed.
    """
    if type(minimum_version) is not int or minimum_version < 1:
        raise ProvenanceRefused("invalid minimum version")
    if type(seal) is not dict or type(seal.get("seal_sha256")) is not str:
        raise ProvenanceRefused("invalid local seal")
    payload = {k: v for k, v in seal.items() if k != "seal_sha256"}
    required = {
        "schema", "version", "sealed_at", "expires_at", "inventory",
        "evidence_scope", "receipt_count", "head_chain_sha256", "trust",
        "chain_externally_anchored", "source_owner_authenticated",
        "redistribution_rights_verified", "roles_authenticated",
        "native_muse_bound", "effect_authorized", "recipient_acknowledged",
    }
    if set(payload) != required or payload.get("schema") != "software-engineer/local-source-seal-v1":
        raise ProvenanceRefused("unexpected local seal schema")
    if seal["seal_sha256"] != _canonical_digest(payload):
        raise ProvenanceRefused("seal digest mismatch")
    for field in ("chain_externally_anchored", "source_owner_authenticated",
                  "redistribution_rights_verified", "roles_authenticated",
                  "native_muse_bound", "effect_authorized", "recipient_acknowledged"):
        if payload[field] is not False:
            raise ProvenanceRefused("unverified seal authority")
    if payload["trust"] != "LOCAL_SELF_HASH_NO_EXTERNAL_WITNESS":
        raise ProvenanceRefused("unrecognized local seal trust level")
    if type(payload["version"]) is not int or payload["version"] < minimum_version:
        raise ProvenanceRefused("seal rollback refused")
    try:
        sealed_at = datetime.fromisoformat(payload["sealed_at"])
        expires_at = datetime.fromisoformat(payload["expires_at"])
        sealed_at = _utc_observation(sealed_at)
        expires_at = _utc_observation(expires_at)
    except (TypeError, ValueError, ProvenanceRefused) as exc:
        raise ProvenanceRefused("invalid seal expiry") from exc
    checked_at = _utc_observation(now)
    if checked_at < sealed_at - timedelta(minutes=5):
        raise ProvenanceRefused("seal clock moved backward")
    if checked_at > expires_at:
        raise ProvenanceRefused("seal expired")
    if expires_at <= sealed_at or expires_at - sealed_at > timedelta(days=30):
        raise ProvenanceRefused("seal lifetime invalid")
    current_inventory = inventory_tree(root)
    if current_inventory != payload["inventory"]:
        raise ProvenanceRefused("source inventory changed since sealing")
    current_head = _local_finder_head(evidence_verification)
    if current_head["evidence_scope"] != payload["evidence_scope"]:
        raise ProvenanceRefused("Evidence Finder scope changed")
    if (current_head["receipt_count"] != payload["receipt_count"] or
            current_head["head_chain_sha256"] != payload["head_chain_sha256"]):
        raise ProvenanceRefused("Evidence Finder chain head changed")
    return {
        "status": "LOCAL_SOURCE_AND_EVIDENCE_CORRELATED",
        "inventory_sha256": current_inventory["inventory_sha256"],
        "receipt_count": current_head["receipt_count"],
        "head_chain_sha256": current_head["head_chain_sha256"],
        "chain_externally_anchored": False,
        "source_owner_authenticated": False,
        "redistribution_rights_verified": False,
        "roles_authenticated": False,
        "native_muse_bound": False,
        "effect_authorized": False,
        "recipient_acknowledged": False,
    }



# R32.1b: read-only, UNAUTHENTICATED subject statements and adoption previews.
# The original private Vault used an unsigned in-toto-shaped envelope and
# writer-owned adoption registry. These helpers preserve only the verifiable
# local contracts; no DSSE signer or state-writing adoption is implemented.
from pathlib import PurePosixPath


def make_unsigned_local_statement(
    root: os.PathLike[str] | str,
    seal: dict,
    evidence_verification: dict,
    *,
    now: datetime | None = None,
) -> dict:
    """Build a strictly unsigned local subject statement over REAL source bytes.

    Source observation and Evidence Finder's existing durable head are checked
    before building the envelope. No authority, signer, publication or recipient
    claims are derived from a local checksum.
    """
    verify_local_source_seal(root, seal, evidence_verification, now=now)
    inventory = seal["inventory"]
    subjects = [
        {
            "name": member["relative_path"],
            "digest": {"sha256": member["sha256"]},
            "annotations": {"bytes": member["bytes"]},
        }
        for member in inventory["records"]
    ]
    body = {
        "_type": "https://in-toto.io/Statement/v1",
        "status": "UNSIGNED_LOCAL_OBSERVATION",
        "signature_status": "UNSIGNED_NOT_DSSE",
        "subject": subjects,
        "predicateType": "urn:muse-presets:local-source-observation:v1",
        "predicate": {
            "source_inventory_sha256": inventory["inventory_sha256"],
            "seal_sha256": seal["seal_sha256"],
            "existing_evidence_head_sha256": seal["head_chain_sha256"],
            "existing_evidence_receipt_count": seal["receipt_count"],
            "existing_evidence_scope": seal["evidence_scope"],
        },
        "issuer_authenticated": False,
        "source_owner_authenticated": False,
        "publication_authorized": False,
        "recipient_acknowledged": False,
    }
    return {**body, "statement_sha256": _canonical_digest(body)}


def verify_unsigned_local_statement(
    root: os.PathLike[str] | str,
    statement: object,
    seal: dict,
    evidence_verification: dict,
    *,
    now: datetime | None = None,
) -> dict:
    """Verify source + existing Evidence Finder head; not a signature check."""
    expected = make_unsigned_local_statement(root, seal, evidence_verification,
                                              now=now)
    if type(statement) is not dict:
        raise ProvenanceRefused("statement must be a JSON object")
    try:
        given_wire = json.dumps(statement, sort_keys=True, separators=(",", ":"),
                                allow_nan=False, ensure_ascii=True)
        expected_wire = json.dumps(expected, sort_keys=True, separators=(",", ":"),
                                   allow_nan=False, ensure_ascii=True)
    except (TypeError, ValueError, UnicodeError, OverflowError) as exc:
        raise ProvenanceRefused("statement is not canonical JSON") from exc
    if given_wire != expected_wire:
        raise ProvenanceRefused("local unsigned statement does not match verified sources")
    return {
        "status": "LOCAL_UNSIGNED_STATEMENT_MATCH",
        "subjects": len(expected["subject"]),
        "statement_sha256": expected["statement_sha256"],
        "signatures_verified": False,
        "source_owner_authenticated": False,
        "publication_authorized": False,
        "native_muse_bound": False,
        "recipient_acknowledged": False,
    }


def _adoption_member_name(name: object) -> str:
    if not isinstance(name, str) or not name or "\\" in name or ":" in name:
        raise ProvenanceRefused("invalid local adoption member")
    try:
        utf8 = name.encode("utf-8", "strict")
    except UnicodeError as exc:
        raise ProvenanceRefused("invalid local adoption member encoding") from exc
    if len(utf8) > 512 or any(ord(ch) < 32 or ord(ch) == 127 for ch in name):
        raise ProvenanceRefused("invalid local adoption member encoding or length")
    path = PurePosixPath(name)
    if (path.is_absolute() or path.as_posix() != name
            or any(part in ("", ".", "..") or part.startswith(".") for part in name.split("/"))):
        raise ProvenanceRefused("invalid local adoption member")
    return name


def preview_local_adoption(
    root: os.PathLike[str] | str,
    seal: dict,
    evidence_verification: dict,
    *,
    members: list[str],
    now: datetime | None = None,
) -> dict:
    """Build a bounded pinned membership preview; DO NOT copy or adopt files.

    This deliberately cannot write an adoption registry or quarantine. It
    neither grants permission to export bytes nor authenticates a builder.
    """
    verify_local_source_seal(root, seal, evidence_verification, now=now)
    if type(members) is not list or not 1 <= len(members) <= 128:
        raise ProvenanceRefused("invalid local adoption member list")
    normalized = [_adoption_member_name(item) for item in members]
    if len(normalized) != len(set(normalized)):
        raise ProvenanceRefused("duplicate local adoption members")
    records = {x["relative_path"]: x for x in seal["inventory"]["records"]}
    if any(name not in records for name in normalized):
        raise ProvenanceRefused("unlisted or changed local adoption source member")
    selected = [records[name] for name in sorted(normalized)]
    body = {
        "schema": "software-engineer/local-adoption-preview-v1",
        "status": "LOCAL_ADOPTION_PREVIEW_ONLY",
        "members": [{"relative_path": x["relative_path"],
                     "bytes": x["bytes"], "sha256": x["sha256"]}
                    for x in selected],
        "source_seal_sha256": seal["seal_sha256"],
        "source_inventory_sha256": seal["inventory"]["inventory_sha256"],
        "source_evidence_scope": seal["evidence_scope"],
        "source_evidence_head_sha256": seal["head_chain_sha256"],
        "source_evidence_receipt_count": seal["receipt_count"],
        "authorization_status": "HOST_APPROVAL_REQUIRED",
        "owner_authenticated": False,
        "ready_to_install": False,
        "redistribution_rights_verified": False,
        "external_effect_authorized": False,
        "native_muse_bound": False,
    }
    return {**body, "preview_sha256": _canonical_digest(body)}


def verify_local_adoption_preview(
    root: os.PathLike[str] | str,
    preview: object,
    seal: dict,
    evidence_verification: dict,
    *,
    now: datetime | None = None,
) -> dict:
    """Re-evaluate every proposed member before any separately authorized copy."""
    if type(preview) is not dict or type(preview.get("members")) is not list:
        raise ProvenanceRefused("invalid local adoption preview")
    try:
        requested = [x["relative_path"] for x in preview["members"]]
    except (TypeError, KeyError) as exc:
        raise ProvenanceRefused("invalid local adoption preview members") from exc
    expected = preview_local_adoption(root, seal, evidence_verification,
                                      members=requested, now=now)
    try:
        given_wire = json.dumps(preview, sort_keys=True, separators=(",", ":"),
                                allow_nan=False, ensure_ascii=True)
        expected_wire = json.dumps(expected, sort_keys=True, separators=(",", ":"),
                                   allow_nan=False, ensure_ascii=True)
    except (TypeError, ValueError, UnicodeError, OverflowError) as exc:
        raise ProvenanceRefused("invalid local adoption preview JSON") from exc
    if given_wire != expected_wire:
        raise ProvenanceRefused("local adoption preview does not match current source")
    return {
        "status": "LOCAL_ADOPTION_PREVIEW_MATCH",
        "members": len(expected["members"]),
        "preview_sha256": expected["preview_sha256"],
        "release_approved": False,
        "owner_authenticated": False,
        "native_muse_bound": False,
        "external_effect_authorized": False,
    }



# R32.1c: create-only LOCAL quarantine custody, never a native adoption effect.
# The caller supplies a guard for an explicitly owned disposable destination.
# A guard callback is a local assertion, NOT authenticated host-issued consent.
import re as _local_re


_LOCAL_ADOPTION_NAME = _local_re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
_LOCAL_QUARANTINE_MAX_BYTES = 8_388_608


def _quarantine_directory(path: os.PathLike[str] | str, *, label: str) -> Path:
    """Admit an absolute existing directory with no symlinked ancestor."""
    try:
        target = Path(path)
        if not target.is_absolute() or ".." in target.parts:
            raise ProvenanceRefused(f"{label} must be absolute and canonical")
        for part in (target, *target.parents):
            if part.is_symlink() or (
                    hasattr(part, "is_junction") and part.is_junction()):
                raise ProvenanceRefused(f"{label} symlink ancestor refused")
        if not target.is_dir() or not stat.S_ISDIR(target.lstat().st_mode):
            raise ProvenanceRefused(f"{label} is not an existing directory")
        if target.resolve(strict=True) != target:
            raise ProvenanceRefused(f"{label} must be owner-approved canonical path")
        return target
    except ProvenanceRefused:
        raise
    except (OSError, TypeError, ValueError) as exc:
        raise ProvenanceRefused(f"{label} unavailable or noncanonical") from exc


def _write_quarantine_file(path: Path, raw: bytes) -> None:
    """Create one new file with exclusive mode, fsync and no overwrite."""
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    flags |= getattr(os, "O_BINARY", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def _local_json_bytes(document: dict) -> bytes:
    try:
        return (json.dumps(document, indent=2, sort_keys=True,
                           ensure_ascii=True, allow_nan=False) + "\n").encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise ProvenanceRefused("quarantine metadata is not canonical") from exc


def _local_read_json(path: Path) -> dict:
    raw = _read_stable_regular_file(path, max_bytes=262144)
    try:
        document = json.loads(raw.decode("utf-8"),
                              object_pairs_hook=_unique_json_pairs,
                              parse_constant=_refuse_nonstandard_constant)
    except ProvenanceRefused:
        raise
    except (ValueError, UnicodeError, TypeError) as exc:
        raise ProvenanceRefused("quarantine metadata unreadable") from exc
    if type(document) is not dict:
        raise ProvenanceRefused("quarantine metadata invalid")
    return document


def stage_local_adoption_quarantine(
    root: os.PathLike[str] | str,
    preview: dict,
    seal: dict,
    evidence_verification: dict,
    *,
    quarantine_parent: os.PathLike[str] | str,
    adoption_name: str,
    authorize_local_write: object = None,
    now: datetime | None = None,
) -> dict:
    """Write ONLY a new, caller-owned LOCAL quarantine directory.

    The caller must first obtain a genuine host permission and pass a scoped
    guard at the action boundary; this library checks the guard's shape and
    return value, not its issuer. It never claims any effect outside LOCAL
    test storage is authorized, and does not touch adoption registry files.
    A failure after mkdir leaves STAGING_INCOMPLETE for manual reconciliation.
    """
    if (type(adoption_name) is not str
            or _LOCAL_ADOPTION_NAME.fullmatch(adoption_name) is None):
        raise ProvenanceRefused("invalid local quarantine adoption name")

    # Recompute all source/evidence links before granting any local disk write.
    verify_local_adoption_preview(root, preview, seal,
                                  evidence_verification, now=now)
    source = _quarantine_directory(root, label="source root")
    parent = _quarantine_directory(quarantine_parent, label="quarantine parent")
    if parent == source or parent.is_relative_to(source):
        raise ProvenanceRefused("quarantine parent overlaps source root")
    dest = parent / adoption_name
    if dest.exists() or dest.is_symlink():
        raise ProvenanceRefused("quarantine destination already exists")

    if not callable(authorize_local_write):
        raise ProvenanceRefused("local quarantine guard missing")
    try:
        allowed = authorize_local_write(
            source, parent, preview["preview_sha256"])
    except BaseException as exc:
        raise ProvenanceRefused("local quarantine guard refused") from exc
    if allowed is not True:
        raise ProvenanceRefused("local quarantine guard refused")

    # Prepare all exact bytes before creating the destination.
    prepared: list[tuple[dict, bytes]] = []
    total = 0
    for ordinal, member in enumerate(preview["members"], 1):
        name = _adoption_member_name(member["relative_path"])
        current = _read_stable_regular_file(
            source.joinpath(*name.split("/")), max_bytes=1_048_576)
        digest = hashlib.sha256(current).hexdigest()
        if digest != member["sha256"] or len(current) != member["bytes"]:
            raise ProvenanceRefused("quarantine source pin mismatch")
        total += len(current)
        if total > _LOCAL_QUARANTINE_MAX_BYTES:
            raise ProvenanceRefused("quarantine total bytes exceeded")
        stored = f"members/{ordinal:03d}-{hashlib.sha256(name.encode('utf-8')).hexdigest()[:16]}.bin"
        entry = {
            "relative_path": name,
            "stored_path": stored,
            "bytes": len(current),
            "sha256": digest,
        }
        prepared.append((entry, current))

    # Build only self-contained local metadata. No absolute source paths,
    # original owner's identities, secrets, signatures, or release claims.
    manifest = {
        "schema": "software-engineer/local-quarantine-manifest-v1",
        "status": "LOCAL_QUARANTINED_NOT_ADOPTED",
        "name": adoption_name,
        "source_preview_sha256": preview["preview_sha256"],
        "source_seal_sha256": seal["seal_sha256"],
        "evidence_head_sha256": seal["head_chain_sha256"],
        "evidence_receipt_count": seal["receipt_count"],
        "members": [entry for entry, _ in prepared],
        "source_owner_authenticated": False,
        "redistribution_rights_verified": False,
        "native_muse_bound": False,
        "external_effect_authorized": False,
        "ready_to_install": False,
    }
    manifest_raw = _local_json_bytes(manifest)
    manifest_sha = hashlib.sha256(manifest_raw).hexdigest()
    receipt = {
        "schema": "software-engineer/local-quarantine-receipt-v1",
        "status": "LOCAL_QUARANTINE_SELF_CHECK_ONLY",
        "name": adoption_name,
        "manifest_sha256": manifest_sha,
        "preview_sha256": preview["preview_sha256"],
        "member_count": len(prepared),
        "total_bytes": total,
        "local_guard_applied": True,
        "host_authority_authenticated": False,
        "source_owner_authenticated": False,
        "redistribution_rights_verified": False,
        "native_muse_bound": False,
        "external_effect_authorized": False,
        "release_approved": False,
        "ready_to_install": False,
    }
    receipt_raw = _local_json_bytes(receipt)

    try:
        dest.mkdir(exist_ok=False)
    except FileExistsError as exc:
        raise ProvenanceRefused("quarantine destination already exists") from exc
    except OSError as exc:
        raise ProvenanceRefused("quarantine destination could not be created") from exc

    marker = dest / "STAGING_INCOMPLETE"
    try:
        _write_quarantine_file(marker,
            b"Local quarantine staging has not completed. Reconcile; never auto-retry.\n")
        members_dir = dest / "members"
        members_dir.mkdir(exist_ok=False)
        for entry, raw in prepared:
            stored = dest / entry["stored_path"]
            _write_quarantine_file(stored, raw)
            check = _read_stable_regular_file(stored, max_bytes=1_048_576)
            if (len(check) != entry["bytes"]
                    or hashlib.sha256(check).hexdigest() != entry["sha256"]):
                raise ProvenanceRefused("quarantine member digest mismatch")
        _write_quarantine_file(dest / "ADOPTION-MANIFEST.json", manifest_raw)
        _write_quarantine_file(dest / "RECEIPT.json", receipt_raw)
        if hashlib.sha256(
            _read_stable_regular_file(dest / "ADOPTION-MANIFEST.json",
                                      max_bytes=262144)).hexdigest() != manifest_sha:
            raise ProvenanceRefused("quarantine manifest digest mismatch")
        if _read_stable_regular_file(dest / "RECEIPT.json",
                                     max_bytes=262144) != receipt_raw:
            raise ProvenanceRefused("quarantine receipt readback mismatch")
        # Only after every member and metadata file has been durably read
        # back may the marker be cleared. No automatic deletion on failure.
        marker.unlink()
    except BaseException as exc:
        raise ProvenanceRefused(
            "quarantine incomplete; existing destination preserved for reconciliation"
        ) from exc

    return {
        "status": "LOCAL_QUARANTINE_STAGED",
        "destination": str(dest),
        "members_staged": len(prepared),
        "manifest_sha256": manifest_sha,
        "local_guard_applied": True,
        "host_authority_authenticated": False,
        "source_owner_authenticated": False,
        "redistribution_rights_verified": False,
        "release_approved": False,
        "native_muse_bound": False,
        "external_effect_authorized": False,
        "ready_to_install": False,
    }


def inspect_local_adoption_quarantine(destination: os.PathLike[str] | str) -> dict:
    """Independently rehash local custody bytes; never activate or repair."""
    dest = _quarantine_directory(destination, label="quarantine destination")
    marker = dest / "STAGING_INCOMPLETE"
    if marker.is_symlink() or (hasattr(marker, "is_junction") and marker.is_junction()):
        raise ProvenanceRefused("quarantine incomplete symlink marker refused")
    if marker.exists():
        return {"status": "INCOMPLETE_STAGE", "native_muse_bound": False,
                "external_effect_authorized": False, "release_approved": False}
    observed = {item.name for item in dest.iterdir()}
    if observed != {"members", "ADOPTION-MANIFEST.json", "RECEIPT.json"}:
        raise ProvenanceRefused("unexpected quarantine contents")
    members_dir = _quarantine_directory(dest / "members", label="member store")
    manifest_path = dest / "ADOPTION-MANIFEST.json"
    receipt_path = dest / "RECEIPT.json"
    manifest_raw = _read_stable_regular_file(manifest_path, max_bytes=262144)
    manifest = _local_read_json(manifest_path)
    receipt = _local_read_json(receipt_path)
    if (set(manifest) != {
            "schema", "status", "name", "source_preview_sha256",
            "source_seal_sha256", "evidence_head_sha256",
            "evidence_receipt_count", "members", "source_owner_authenticated",
            "redistribution_rights_verified", "native_muse_bound",
            "external_effect_authorized", "ready_to_install"}
        or manifest["schema"] != "software-engineer/local-quarantine-manifest-v1"
        or manifest["status"] != "LOCAL_QUARANTINED_NOT_ADOPTED"):
        raise ProvenanceRefused("quarantine manifest invalid")
    if manifest.get("name") != dest.name:
        raise ProvenanceRefused("quarantine name does not match destination")
    if (set(receipt) != {
            "schema", "status", "name", "manifest_sha256", "preview_sha256",
            "member_count", "total_bytes", "local_guard_applied",
            "host_authority_authenticated", "source_owner_authenticated",
            "redistribution_rights_verified", "native_muse_bound",
            "external_effect_authorized", "release_approved",
            "ready_to_install"}
        or receipt["schema"] != "software-engineer/local-quarantine-receipt-v1"
        or receipt["status"] != "LOCAL_QUARANTINE_SELF_CHECK_ONLY"
        or receipt["name"] != manifest["name"]
        or receipt["preview_sha256"] != manifest["source_preview_sha256"]
        or receipt["local_guard_applied"] is not True):
        raise ProvenanceRefused("quarantine receipt invalid")
    for document in (manifest, receipt):
        for key in ("source_owner_authenticated", "redistribution_rights_verified",
                    "native_muse_bound", "external_effect_authorized",
                    "ready_to_install"):
            if document[key] is not False:
                raise ProvenanceRefused("quarantine metadata claimed unauthorized effect")
    for key in ("host_authority_authenticated", "release_approved"):
        if receipt[key] is not False:
            raise ProvenanceRefused("quarantine receipt claimed unauthorized authority")
    if hashlib.sha256(manifest_raw).hexdigest() != receipt["manifest_sha256"]:
        raise ProvenanceRefused("quarantine manifest digest mismatch")
    listed = manifest["members"]
    if (type(listed) is not list or not 1 <= len(listed) <= 128
        or type(receipt["member_count"]) is not int
        or receipt["member_count"] != len(listed)
        or type(receipt["total_bytes"]) is not int):
        raise ProvenanceRefused("quarantine member records malformed")

    observed_files = set()
    names = set()
    total = 0
    for n, entry in enumerate(listed, 1):
        if type(entry) is not dict or set(entry) != {
                "relative_path", "stored_path", "bytes", "sha256"}:
            raise ProvenanceRefused("quarantine member record invalid")
        name = _adoption_member_name(entry["relative_path"])
        if name in names:
            raise ProvenanceRefused("duplicate quarantine member")
        names.add(name)
        stored = f"members/{n:03d}-{hashlib.sha256(name.encode('utf-8')).hexdigest()[:16]}.bin"
        if entry["stored_path"] != stored:
            raise ProvenanceRefused("quarantine stored path changed")
        if (type(entry["bytes"]) is not int or not 0 <= entry["bytes"] <= 1_048_576
            or type(entry["sha256"]) is not str
            or _HEX.fullmatch(entry["sha256"]) is None):
            raise ProvenanceRefused("quarantine member pin invalid")
        raw = _read_stable_regular_file(dest / stored, max_bytes=1_048_576)
        if len(raw) != entry["bytes"] or hashlib.sha256(raw).hexdigest() != entry["sha256"]:
            raise ProvenanceRefused("quarantine member digest mismatch")
        observed_files.add(Path(stored).name)
        total += len(raw)
    actual_members = list(members_dir.iterdir())
    for file in actual_members:
        if file.is_symlink() or (
                hasattr(file, "is_junction") and file.is_junction()):
            raise ProvenanceRefused("quarantine member symlink refused")
        if not file.is_file():
            raise ProvenanceRefused("unexpected quarantine member type")
    if (total != receipt["total_bytes"] or
            observed_files != {p.name for p in actual_members}):
        raise ProvenanceRefused("unexpected quarantine member store")
    return {
        "status": "LOCAL_QUARANTINE_VERIFIED",
        "members_verified": len(listed),
        "manifest_sha256": receipt["manifest_sha256"],
        "host_authority_authenticated": False,
        "source_owner_authenticated": False,
        "redistribution_rights_verified": False,
        "release_approved": False,
        "native_muse_bound": False,
        "external_effect_authorized": False,
        "ready_to_install": False,
    }



# R32.1d: offline export and restore of the already verified local quarantine.
# Deliberately use deterministic ZIP_STORED with exact whitelist validation.
# This does NOT export a licensed/native/host-admitted agent or grant rights.
import io as _archive_io
import zipfile as _archive_zip

_LOCAL_ARCHIVE_MAX_BYTES = 10_000_000
_LOCAL_ARCHIVE_MAX_ITEMS = 131


def _archive_write_file(archive: _archive_zip.ZipFile, name: str, raw: bytes) -> None:
    """Write one regular non-compressed member, with fixed metadata."""
    if not isinstance(name, str) or not name or name.startswith("/"):
        raise ProvenanceRefused("unsafe local archive member")
    info = _archive_zip.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = _archive_zip.ZIP_STORED
    info.create_system = 3
    info.external_attr = 0o100600 << 16
    archive.writestr(info, raw)


def _archive_guard(callback: object, src: Path, parent: Path, pin: str) -> None:
    """Call action-time local guard without assigning it a host identity."""
    if not callable(callback):
        raise ProvenanceRefused("local archive guard missing")
    try:
        allowed = callback(src, parent, pin)
    except BaseException as exc:
        raise ProvenanceRefused("local archive guard refused") from exc
    if allowed is not True:
        raise ProvenanceRefused("local archive guard refused")


def export_local_quarantine_archive(
    source_quarantine: os.PathLike[str] | str,
    *,
    archive_path: os.PathLike[str] | str,
    authorize_local_export: object = None,
) -> dict:
    """Export only exact LOCAL quarantine contents to an absent offline ZIP.

    A local guard does not prove owner authentication, legal redistribution
    rights, an agent admission, or external host-effect permission. The only
    persistent effect is creation of an owner-scoped archive file. On errors
    after creation the file is preserved; no automatic cleanup or replay.
    """
    source = _quarantine_directory(source_quarantine, label="source quarantine")
    verified = inspect_local_adoption_quarantine(source)
    if verified.get("status") != "LOCAL_QUARANTINE_VERIFIED":
        raise ProvenanceRefused("unverified quarantine cannot be exported")

    target = Path(archive_path)
    if not target.is_absolute() or ".." in target.parts or target.suffix != ".zip":
        raise ProvenanceRefused("invalid offline archive destination")
    parent = _quarantine_directory(target.parent, label="archive parent")
    if (parent == source or parent.is_relative_to(source)
            or source.is_relative_to(parent)):
        raise ProvenanceRefused("archive output overlaps source quarantine")
    if target.exists() or target.is_symlink():
        raise ProvenanceRefused("offline archive destination already exists")

    manifest_raw = _read_stable_regular_file(source / "ADOPTION-MANIFEST.json",
                                             max_bytes=262144)
    receipt_raw = _read_stable_regular_file(source / "RECEIPT.json",
                                            max_bytes=262144)
    manifest = _local_read_json(source / "ADOPTION-MANIFEST.json")
    files = {
        "ADOPTION-MANIFEST.json": manifest_raw,
        "RECEIPT.json": receipt_raw,
    }
    for member in manifest["members"]:
        relative = member["stored_path"]
        if (not isinstance(relative, str) or
                relative != "members/" + Path(relative).name):
            raise ProvenanceRefused("unsafe quarantine archive member")
        files[relative] = _read_stable_regular_file(
            source / relative, max_bytes=1_048_576)
    if len(files) != len(manifest["members"]) + 2:
        raise ProvenanceRefused("duplicate quarantine archive member")
    total = sum(len(value) for value in files.values())
    if total > _LOCAL_QUARANTINE_MAX_BYTES:
        raise ProvenanceRefused("offline archive source size exceeded")

    export_manifest = {
        "schema": "software-engineer/local-quarantine-export-v1",
        "status": "LOCAL_OFFLINE_EXPORT_NOT_RELEASE",
        "name": source.name,
        "original_manifest_sha256": verified["manifest_sha256"],
        "files": [
            {"path": name, "bytes": len(raw),
             "sha256": hashlib.sha256(raw).hexdigest()}
            for name, raw in sorted(files.items())
        ],
        "host_authority_authenticated": False,
        "source_owner_authenticated": False,
        "redistribution_rights_verified": False,
        "native_muse_bound": False,
        "external_effect_authorized": False,
        "release_approved": False,
        "ready_to_install": False,
    }
    export_raw = _local_json_bytes(export_manifest)
    if len(export_raw) + total > _LOCAL_ARCHIVE_MAX_BYTES - 65536:
        raise ProvenanceRefused("offline archive too large")
    _archive_guard(authorize_local_export, source, parent,
                   verified["manifest_sha256"])

    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    flags |= getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(target, flags, 0o600)
    except FileExistsError as exc:
        raise ProvenanceRefused("offline archive destination already exists") from exc
    except OSError as exc:
        raise ProvenanceRefused("offline archive could not be created") from exc
    try:
        with os.fdopen(fd, "wb") as stream:
            with _archive_zip.ZipFile(stream, mode="w",
                                      compression=_archive_zip.ZIP_STORED,
                                      allowZip64=False) as archive:
                _archive_write_file(archive, "EXPORT-MANIFEST.json", export_raw)
                for name, raw in sorted(files.items()):
                    _archive_write_file(archive, name, raw)
            stream.flush()
            os.fsync(stream.fileno())
        actual = _read_stable_regular_file(target, max_bytes=_LOCAL_ARCHIVE_MAX_BYTES)
        archive_digest = hashlib.sha256(actual).hexdigest()
        checked = inspect_local_quarantine_archive(target,
                                                   expected_sha256=archive_digest)
        if checked["status"] != "LOCAL_ARCHIVE_VERIFIED":
            raise ProvenanceRefused("offline archive readback mismatch")
    except BaseException as exc:
        raise ProvenanceRefused(
            "offline archive incomplete; preserve and reconcile existing destination"
        ) from exc

    return {
        "status": "LOCAL_ARCHIVE_CREATED",
        "archive_sha256": archive_digest,
        "members_exported": len(manifest["members"]),
        "archive_bytes": len(actual),
        "local_guard_applied": True,
        "host_authority_authenticated": False,
        "source_owner_authenticated": False,
        "redistribution_rights_verified": False,
        "native_muse_bound": False,
        "external_effect_authorized": False,
        "release_approved": False,
        "ready_to_install": False,
    }


def _archive_member_payloads(
    archive_path: os.PathLike[str] | str,
    *,
    expected_sha256: str,
) -> tuple[dict, dict[str, bytes], str]:
    """Read finite ZIP bytes, whitelist every member, then crosscheck hashes."""
    if type(expected_sha256) is not str or _HEX.fullmatch(expected_sha256) is None:
        raise ProvenanceRefused("expected local archive digest required")
    archive = Path(archive_path)
    parent = _quarantine_directory(archive.parent, label="offline archive parent")
    if archive.parent != parent:
        raise ProvenanceRefused("offline archive path not canonical")
    raw = _read_stable_regular_file(archive, max_bytes=_LOCAL_ARCHIVE_MAX_BYTES)
    digest = hashlib.sha256(raw).hexdigest()
    if digest != expected_sha256:
        raise ProvenanceRefused("offline archive digest mismatch")
    # ZIP permits arbitrary leading/trailing garbage and archive comments.
    # Our local-only format emits neither: reject ambiguous representations
    # even when the caller supplies a checksum of those altered bytes.
    if (len(raw) < 26 or raw[:4] != b"PK\x03\x04"
            or raw[-22:-18] != b"PK\x05\x06"
            or raw[-2:] != b"\x00\x00"):
        raise ProvenanceRefused("offline archive noncanonical ZIP framing")

    try:
        with _archive_zip.ZipFile(_archive_io.BytesIO(raw), mode="r",
                                  allowZip64=False) as zf:
            members = zf.infolist()
            if not 2 <= len(members) <= _LOCAL_ARCHIVE_MAX_ITEMS:
                raise ProvenanceRefused("offline archive member count out of bounds")
            names: list[str] = []
            total = 0
            for info in members:
                name = info.filename
                if (not isinstance(name, str) or not name or
                        not name.isascii() or name.startswith("/") or
                        "\\" in name or ":" in name or
                        any(part in ("", ".", "..") for part in name.split("/"))):
                    raise ProvenanceRefused("unsafe offline archive member path")
                if name in names:
                    raise ProvenanceRefused("duplicate offline archive member")
                if (info.is_dir() or info.flag_bits & 1
                        or info.compress_type != _archive_zip.ZIP_STORED
                        or info.file_size != info.compress_size
                        or info.file_size > 1_048_576):
                    raise ProvenanceRefused("unsupported offline archive member type")
                mode = (info.external_attr >> 16) & 0o170000
                if mode not in (0, stat.S_IFREG):
                    raise ProvenanceRefused("symlink or special offline archive member")
                total += info.file_size
                if total > _LOCAL_ARCHIVE_MAX_BYTES:
                    raise ProvenanceRefused("offline archive declared bytes exceeded")
                names.append(name)
            if "EXPORT-MANIFEST.json" not in names:
                raise ProvenanceRefused("offline archive export manifest missing")
            payloads = {name: zf.read(name) for name in names}
    except ProvenanceRefused:
        raise
    except (_archive_zip.BadZipFile, _archive_zip.LargeZipFile,
            RuntimeError, OSError, KeyError, ValueError, EOFError) as exc:
        raise ProvenanceRefused("offline archive unreadable or malformed") from exc

    try:
        manifest = json.loads(payloads["EXPORT-MANIFEST.json"].decode("utf-8"),
                              object_pairs_hook=_unique_json_pairs,
                              parse_constant=_refuse_nonstandard_constant)
    except ProvenanceRefused:
        raise
    except (ValueError, UnicodeError, TypeError) as exc:
        raise ProvenanceRefused("offline export manifest invalid") from exc
    if (type(manifest) is not dict or set(manifest) != {
            "schema", "status", "name", "original_manifest_sha256", "files",
            "host_authority_authenticated", "source_owner_authenticated",
            "redistribution_rights_verified", "native_muse_bound",
            "external_effect_authorized", "release_approved", "ready_to_install"}
        or manifest["schema"] != "software-engineer/local-quarantine-export-v1"
        or manifest["status"] != "LOCAL_OFFLINE_EXPORT_NOT_RELEASE"
        or type(manifest["name"]) is not str
        or _LOCAL_ADOPTION_NAME.fullmatch(manifest["name"]) is None):
        raise ProvenanceRefused("offline export manifest invalid")
    for flag in ("host_authority_authenticated", "source_owner_authenticated",
                 "redistribution_rights_verified", "native_muse_bound",
                 "external_effect_authorized", "release_approved",
                 "ready_to_install"):
        if manifest[flag] is not False:
            raise ProvenanceRefused("offline manifest claimed unauthorized authority")
    if (type(manifest["original_manifest_sha256"]) is not str or
            _HEX.fullmatch(manifest["original_manifest_sha256"]) is None):
        raise ProvenanceRefused("offline archive original pin malformed")
    records = manifest["files"]
    if type(records) is not list or not 3 <= len(records) <= 130:
        raise ProvenanceRefused("offline archive file records invalid")
    expected = {"EXPORT-MANIFEST.json"}
    previous = ""
    for item in records:
        if type(item) is not dict or set(item) != {"path", "bytes", "sha256"}:
            raise ProvenanceRefused("offline archive file record invalid")
        name = item["path"]
        if (type(name) is not str or name <= previous or
                (name not in ("ADOPTION-MANIFEST.json", "RECEIPT.json") and
                 not name.startswith("members/"))):
            raise ProvenanceRefused("offline archive file path unexpected")
        previous = name
        if name not in payloads:
            raise ProvenanceRefused("offline archive file missing")
        if (type(item["bytes"]) is not int or not 0 <= item["bytes"] <= 1_048_576
                or type(item["sha256"]) is not str
                or _HEX.fullmatch(item["sha256"]) is None):
            raise ProvenanceRefused("offline archive file metadata invalid")
        content = payloads[name]
        if len(content) != item["bytes"] or hashlib.sha256(content).hexdigest() != item["sha256"]:
            raise ProvenanceRefused("offline archive member digest mismatch")
        expected.add(name)
    if set(payloads) != expected:
        raise ProvenanceRefused("unexpected offline archive member")
    try:
        source_manifest = json.loads(
            payloads["ADOPTION-MANIFEST.json"].decode("utf-8"),
            object_pairs_hook=_unique_json_pairs,
            parse_constant=_refuse_nonstandard_constant)
        source_receipt = json.loads(
            payloads["RECEIPT.json"].decode("utf-8"),
            object_pairs_hook=_unique_json_pairs,
            parse_constant=_refuse_nonstandard_constant)
    except ProvenanceRefused:
        raise
    except (ValueError, UnicodeError, TypeError, KeyError) as exc:
        raise ProvenanceRefused("offline archive adoption metadata invalid") from exc
    if (type(source_manifest) is not dict or type(source_receipt) is not dict or
            type(source_manifest.get("members")) is not list or
            source_manifest.get("name") != manifest["name"] or
            source_receipt.get("name") != manifest["name"] or
            hashlib.sha256(payloads["ADOPTION-MANIFEST.json"]).hexdigest() !=
            manifest["original_manifest_sha256"]):
        raise ProvenanceRefused("offline archive custody metadata mismatch")
    if (set(source_manifest) != {
            "schema", "status", "name", "source_preview_sha256",
            "source_seal_sha256", "evidence_head_sha256",
            "evidence_receipt_count", "members", "source_owner_authenticated",
            "redistribution_rights_verified", "native_muse_bound",
            "external_effect_authorized", "ready_to_install"}
        or source_manifest["schema"] != "software-engineer/local-quarantine-manifest-v1"
        or source_manifest["status"] != "LOCAL_QUARANTINED_NOT_ADOPTED"
        or set(source_receipt) != {
            "schema", "status", "name", "manifest_sha256", "preview_sha256",
            "member_count", "total_bytes", "local_guard_applied",
            "host_authority_authenticated", "source_owner_authenticated",
            "redistribution_rights_verified", "native_muse_bound",
            "external_effect_authorized", "release_approved",
            "ready_to_install"}
        or source_receipt["schema"] != "software-engineer/local-quarantine-receipt-v1"
        or source_receipt["status"] != "LOCAL_QUARANTINE_SELF_CHECK_ONLY"
        or source_receipt["manifest_sha256"] != manifest["original_manifest_sha256"]
        or source_receipt["preview_sha256"] != source_manifest["source_preview_sha256"]
        or source_receipt["local_guard_applied"] is not True):
        raise ProvenanceRefused("offline archive source custody metadata invalid")
    for record in (source_manifest, source_receipt):
        for field in ("source_owner_authenticated", "redistribution_rights_verified",
                      "native_muse_bound", "external_effect_authorized",
                      "ready_to_install"):
            if record[field] is not False:
                raise ProvenanceRefused("offline custody metadata claimed authority")
    if (source_receipt["host_authority_authenticated"] is not False or
            source_receipt["release_approved"] is not False):
        raise ProvenanceRefused("offline custody release flags forged")
    listed = source_manifest["members"]
    if (len(listed) + 3 != len(payloads) or
            type(source_receipt["member_count"]) is not int or
            source_receipt["member_count"] != len(listed) or
            type(source_receipt["total_bytes"]) is not int):
        raise ProvenanceRefused("offline archive custody member count mismatch")
    member_total = 0
    seen_names = set()
    for index, item in enumerate(listed, 1):
        if type(item) is not dict or set(item) != {
                "relative_path", "stored_path", "bytes", "sha256"}:
            raise ProvenanceRefused("offline archive custody member invalid")
        name = _adoption_member_name(item.get("relative_path"))
        if name in seen_names:
            raise ProvenanceRefused("duplicate offline custody member")
        seen_names.add(name)
        expected_member = f"members/{index:03d}-{hashlib.sha256(name.encode('utf-8')).hexdigest()[:16]}.bin"
        if item.get("stored_path") != expected_member or expected_member not in payloads:
            raise ProvenanceRefused("offline archive custody path mismatch")
        bytes_stored = payloads[expected_member]
        if (type(item["bytes"]) is not int or
                item["bytes"] != len(bytes_stored) or
                type(item["sha256"]) is not str or
                item["sha256"] != hashlib.sha256(bytes_stored).hexdigest()):
            raise ProvenanceRefused("offline custody member digest mismatch")
        member_total += len(bytes_stored)
    if member_total != source_receipt["total_bytes"]:
        raise ProvenanceRefused("offline custody total bytes mismatch")
    return manifest, payloads, digest


def inspect_local_quarantine_archive(
    archive_path: os.PathLike[str] | str,
    *,
    expected_sha256: str,
) -> dict:
    """Verify locally anchored ZIP bytes without extraction or modification."""
    manifest, payloads, digest = _archive_member_payloads(
        archive_path, expected_sha256=expected_sha256)
    return {
        "status": "LOCAL_ARCHIVE_VERIFIED",
        "archive_sha256": digest,
        "member_count": len(manifest["files"]) - 2,
        "archive_item_count": len(payloads),
        "host_authority_authenticated": False,
        "source_owner_authenticated": False,
        "redistribution_rights_verified": False,
        "native_muse_bound": False,
        "external_effect_authorized": False,
        "release_approved": False,
        "ready_to_install": False,
    }


def restore_local_quarantine_archive(
    archive_path: os.PathLike[str] | str,
    *,
    restore_parent: os.PathLike[str] | str,
    adoption_name: str,
    expected_sha256: str,
    authorize_local_restore: object = None,
) -> dict:
    """Restore only verified local custody bytes into an absent destination.

    All ZIP members and their exact bytes are checked BEFORE any restore
    directory is created. No tar extraction, path joining from archive
    metadata, external effect or native Muse install is permitted.
    """
    manifest, payloads, digest = _archive_member_payloads(
        archive_path, expected_sha256=expected_sha256)
    if type(adoption_name) is not str or adoption_name != manifest["name"]:
        raise ProvenanceRefused("offline restore adoption name mismatch")
    src = Path(archive_path)
    archive_parent = _quarantine_directory(src.parent, label="archive parent")
    parent = _quarantine_directory(restore_parent, label="restore parent")
    if (parent == archive_parent or parent.is_relative_to(archive_parent)
            or parent == src or
            any((parent / name).exists() for name in (
                "ADOPTION-MANIFEST.json", "RECEIPT.json", "STAGING_INCOMPLETE"))):
        raise ProvenanceRefused("restore parent overlaps archive source or existing custody")
    dest = parent / adoption_name
    if dest.exists() or dest.is_symlink():
        raise ProvenanceRefused("restore destination already exists")
    _archive_guard(authorize_local_restore, src, parent, digest)

    try:
        dest.mkdir(exist_ok=False)
    except FileExistsError as exc:
        raise ProvenanceRefused("restore destination already exists") from exc
    except OSError as exc:
        raise ProvenanceRefused("restore destination could not be created") from exc

    marker = dest / "STAGING_INCOMPLETE"
    try:
        _write_quarantine_file(marker,
            b"Offline restore is incomplete; reconcile and do not auto-retry.\n")
        (dest / "members").mkdir(exist_ok=False)
        for name in sorted(payloads):
            if name == "EXPORT-MANIFEST.json":
                continue
            stored = dest / name
            # Member filenames are already constrained by _archive_member_payloads.
            _write_quarantine_file(stored, payloads[name])
            if _read_stable_regular_file(stored, max_bytes=1_048_576) != payloads[name]:
                raise ProvenanceRefused("offline restore member digest mismatch")
        marker.unlink()
        observed = inspect_local_adoption_quarantine(dest)
        if observed["status"] != "LOCAL_QUARANTINE_VERIFIED":
            raise ProvenanceRefused("offline restored quarantine not verified")
    except BaseException as exc:
        raise ProvenanceRefused(
            "offline restore incomplete; preserve destination for reconciliation"
        ) from exc

    return {
        "status": "LOCAL_QUARANTINE_RESTORED",
        "archive_sha256": digest,
        "members_restored": observed["members_verified"],
        "host_authority_authenticated": False,
        "source_owner_authenticated": False,
        "redistribution_rights_verified": False,
        "native_muse_bound": False,
        "external_effect_authorized": False,
        "release_approved": False,
        "ready_to_install": False,
    }



# R32.1e: bounded READ-ONLY dependent quarantine drift assessment.
# The original donor has a registry-mutating invalidate_dependent_adoptions;
# this generic version never edits that registry or invents host authority.
def assess_local_quarantine_dependency(
    root: os.PathLike[str] | str,
    preview: object,
    seal: object,
    evidence_verification: object,
    *,
    quarantine_destination: os.PathLike[str] | str,
    now: datetime | None = None,
) -> dict:
    """Report local current/drift/hold for one source-pinned quarantine.

    Local self-hashes, caller-provided EvidenceLedger summaries, and an
    existing quarantine do NOT authenticate the donor or permit a registry
    update. A changed source yields a recommendation only after the local
    custody, preview, seal and Evidence Finder scope/head have been checked.
    Any ambiguous/corrupt/expired evidence fails closed to REVIEW_REQUIRED.
    """
    dest = Path(quarantine_destination)
    name = dest.name if _LOCAL_ADOPTION_NAME.fullmatch(dest.name) else "UNVERIFIED"
    manifest_pin = None

    def result(status: str, reason: str) -> dict:
        return {
            "schema": "software-engineer/local-dependency-assessment-v1",
            "adoption_name": name,
            "quarantine_manifest_sha256": manifest_pin,
            "status": status,
            "reason": reason,
            "invalidation_recommended": status == "LOCAL_INVALIDATION_RECOMMENDED",
            "hold_required": status != "LOCAL_DEPENDENCY_CURRENT",
            "registry_modified": False,
            "owner_authenticated": False,
            "source_owner_authenticated": False,
            "redistribution_rights_verified": False,
            "release_approved": False,
            "native_muse_bound": False,
            "external_effect_authorized": False,
            "independent_donor_identity_verified": False,
        }

    # First establish that the already-stored custody bytes themselves can be
    # read back, and that they are bound to the right local dependency.
    try:
        observed = inspect_local_adoption_quarantine(dest)
        if observed.get("status") != "LOCAL_QUARANTINE_VERIFIED":
            return result("LOCAL_REVIEW_REQUIRED", "QUARANTINE_UNVERIFIED")
        manifest_pin = observed["manifest_sha256"]
        manifest = _local_read_json(dest / "ADOPTION-MANIFEST.json")
    except (ProvenanceRefused, OSError, TypeError, ValueError):
        return result("LOCAL_REVIEW_REQUIRED", "QUARANTINE_UNVERIFIED")

    try:
        if type(seal) is not dict or type(preview) is not dict:
            return result("LOCAL_REVIEW_REQUIRED", "SEAL_UNVERIFIED")
        seal_wire = {key: value for key, value in seal.items()
                     if key != "seal_sha256"}
        if (set(seal) != {
                "schema", "version", "sealed_at", "expires_at", "inventory",
                "evidence_scope", "receipt_count", "head_chain_sha256",
                "trust", "chain_externally_anchored", "source_owner_authenticated",
                "redistribution_rights_verified", "roles_authenticated",
                "native_muse_bound", "effect_authorized", "recipient_acknowledged",
                "seal_sha256"}
            or seal.get("schema") != "software-engineer/local-source-seal-v1"
            or seal.get("trust") != "LOCAL_SELF_HASH_NO_EXTERNAL_WITNESS"
            or seal.get("seal_sha256") != _canonical_digest(seal_wire)
            or type(seal.get("version")) is not int or seal["version"] < 1
            or any(seal.get(key) is not False for key in (
                "chain_externally_anchored", "source_owner_authenticated",
                "redistribution_rights_verified", "roles_authenticated",
                "native_muse_bound", "effect_authorized", "recipient_acknowledged"))):
            return result("LOCAL_REVIEW_REQUIRED", "SEAL_UNVERIFIED")
    except (ProvenanceRefused, TypeError, ValueError):
        return result("LOCAL_REVIEW_REQUIRED", "SEAL_UNVERIFIED")

    try:
        expected_preview_keys = {
            "schema", "status", "members", "source_seal_sha256",
            "source_inventory_sha256", "source_evidence_scope",
            "source_evidence_head_sha256", "source_evidence_receipt_count",
            "authorization_status", "owner_authenticated", "ready_to_install",
            "redistribution_rights_verified", "external_effect_authorized",
            "native_muse_bound", "preview_sha256"}
        if (set(preview) != expected_preview_keys
            or preview.get("schema") != "software-engineer/local-adoption-preview-v1"
            or preview.get("status") != "LOCAL_ADOPTION_PREVIEW_ONLY"
            or preview.get("authorization_status") != "HOST_APPROVAL_REQUIRED"
            or type(preview.get("members")) is not list
            or not 1 <= len(preview["members"]) <= 128
            or preview.get("preview_sha256") != _canonical_digest({
                key: value for key, value in preview.items()
                if key != "preview_sha256"})
            or any(preview.get(key) is not False for key in (
                "owner_authenticated", "ready_to_install",
                "redistribution_rights_verified", "external_effect_authorized",
                "native_muse_bound"))):
            return result("LOCAL_REVIEW_REQUIRED", "PREVIEW_UNVERIFIED")
    except (ProvenanceRefused, TypeError, ValueError):
        return result("LOCAL_REVIEW_REQUIRED", "PREVIEW_UNVERIFIED")

    try:
        preview_names = []
        expected_members = []
        for item in preview["members"]:
            if type(item) is not dict or set(item) != {
                    "relative_path", "bytes", "sha256"}:
                return result("LOCAL_REVIEW_REQUIRED", "PREVIEW_UNVERIFIED")
            member = _adoption_member_name(item["relative_path"])
            if (type(item["bytes"]) is not int or not 0 <= item["bytes"] <= 1_048_576
                    or type(item["sha256"]) is not str or
                    _HEX.fullmatch(item["sha256"]) is None):
                return result("LOCAL_REVIEW_REQUIRED", "PREVIEW_UNVERIFIED")
            preview_names.append(member)
            expected_members.append({
                "relative_path": member,
                "bytes": item["bytes"],
                "sha256": item["sha256"],
            })
        if len(set(preview_names)) != len(preview_names):
            return result("LOCAL_REVIEW_REQUIRED", "PREVIEW_UNVERIFIED")
        stored_members = [
            {"relative_path": rec["relative_path"],
             "bytes": rec["bytes"], "sha256": rec["sha256"]}
            for rec in manifest["members"]
        ]
        if (preview_names != sorted(preview_names)
            or expected_members != stored_members
            or preview["source_seal_sha256"] != seal["seal_sha256"]
            or preview["source_inventory_sha256"] != seal["inventory"]["inventory_sha256"]
            or preview["source_evidence_scope"] != seal["evidence_scope"]
            or preview["source_evidence_head_sha256"] != seal["head_chain_sha256"]
            or preview["source_evidence_receipt_count"] != seal["receipt_count"]
            or manifest["source_preview_sha256"] != preview["preview_sha256"]
            or manifest["source_seal_sha256"] != seal["seal_sha256"]
            or manifest["evidence_head_sha256"] != seal["head_chain_sha256"]
            or manifest["evidence_receipt_count"] != seal["receipt_count"]):
            return result("LOCAL_REVIEW_REQUIRED", "QUARANTINE_DEPENDENCY_MISMATCH")
    except (ProvenanceRefused, KeyError, TypeError, ValueError):
        return result("LOCAL_REVIEW_REQUIRED", "PREVIEW_UNVERIFIED")

    try:
        # Same issuer limitations as the original Evidence Finder: local shape
        # and chain digest only. A forged caller-provided summary is not proof.
        head = _local_finder_head(evidence_verification)
    except (ProvenanceRefused, TypeError, ValueError):
        return result("LOCAL_REVIEW_REQUIRED", "EVIDENCE_UNVERIFIED")
    if head["evidence_scope"] != seal["evidence_scope"]:
        return result("LOCAL_REVIEW_REQUIRED", "EVIDENCE_SCOPE_CHANGED")
    if (head["head_chain_sha256"] != seal["head_chain_sha256"]
            or head["receipt_count"] != seal["receipt_count"]):
        return result("LOCAL_REVIEW_REQUIRED", "EVIDENCE_HEAD_CHANGED")

    try:
        checked_at = _utc_observation(now)
        created = _utc_observation(datetime.fromisoformat(seal["sealed_at"]))
        expires = _utc_observation(datetime.fromisoformat(seal["expires_at"]))
        if (checked_at < created - timedelta(minutes=5)
                or checked_at > expires or expires <= created
                or expires - created > timedelta(days=30)):
            return result("LOCAL_REVIEW_REQUIRED", "SEAL_EXPIRED_OR_INVALID")
    except (ProvenanceRefused, TypeError, ValueError):
        return result("LOCAL_REVIEW_REQUIRED", "SEAL_EXPIRED_OR_INVALID")

    try:
        latest = inventory_tree(root)
    except (ProvenanceRefused, OSError, TypeError, ValueError):
        return result("LOCAL_REVIEW_REQUIRED", "SOURCE_UNAVAILABLE_OR_UNVERIFIED")
    if latest != seal["inventory"]:
        return result("LOCAL_INVALIDATION_RECOMMENDED", "SOURCE_CONTENT_CHANGED")

    try:
        verify_local_adoption_preview(root, preview, seal,
                                      evidence_verification, now=checked_at)
    except (ProvenanceRefused, KeyError, OSError, TypeError, ValueError):
        return result("LOCAL_REVIEW_REQUIRED", "PREVIEW_UNVERIFIED")
    return result("LOCAL_DEPENDENCY_CURRENT", "CURRENT_SOURCE_AND_EVIDENCE")


def review_local_dependent_quarantines(
    dependencies: object, *, now: datetime | None = None
) -> dict:
    """Evaluate a bounded collection; return a LOCAL proposal, never mutate.

    Does not update the original donor adoption registry, claim authority,
    modify Evidence Finder, or delete quarantined bytes.
    """
    if type(dependencies) is not list or not 1 <= len(dependencies) <= 32:
        raise ProvenanceRefused("invalid bounded local dependency list")
    records = []
    seen_names: set[str] = set()
    seen_destinations: set[str] = set()
    required = {"name", "root", "seal", "preview",
                "head", "destination"}
    for item in dependencies:
        if type(item) is not dict or set(item) != required:
            raise ProvenanceRefused("invalid local dependency entry")
        name = item["name"]
        if (type(name) is not str or _LOCAL_ADOPTION_NAME.fullmatch(name) is None
            or name in seen_names):
            raise ProvenanceRefused("invalid or duplicate dependency name")
        try:
            location = Path(item["destination"])
        except (TypeError, ValueError) as exc:
            raise ProvenanceRefused("invalid dependency destination") from exc
        if (location.name != name or not location.is_absolute()
                or str(location) in seen_destinations):
            raise ProvenanceRefused("duplicate or mismatched dependency destination")
        seen_names.add(name)
        seen_destinations.add(str(location))
        records.append((name, item))
    assessments = []
    for name, item in sorted(records):
        observation = assess_local_quarantine_dependency(
            item["root"], item["preview"], item["seal"], item["head"],
            quarantine_destination=item["destination"], now=now)
        if observation["adoption_name"] != name:
            raise ProvenanceRefused("dependency name mismatch")
        assessments.append(observation)
    current = [x["adoption_name"] for x in assessments
               if x["status"] == "LOCAL_DEPENDENCY_CURRENT"]
    invalid = [x["adoption_name"] for x in assessments
               if x["status"] == "LOCAL_INVALIDATION_RECOMMENDED"]
    held = [x["adoption_name"] for x in assessments
            if x["status"] == "LOCAL_REVIEW_REQUIRED"]
    return {
        "schema": "software-engineer/local-dependency-review-v1",
        "status": "LOCAL_HOLD_REQUIRED" if invalid or held else "LOCAL_DEPENDENCIES_CURRENT",
        "assessments": assessments,
        "current": current,
        "invalidation_recommended": invalid,
        "review_required": held,
        "registry_modified": False,
        "owner_authenticated": False,
        "source_owner_authenticated": False,
        "redistribution_rights_verified": False,
        "release_approved": False,
        "native_muse_bound": False,
        "external_effect_authorized": False,
        "independent_donor_identity_verified": False,
    }

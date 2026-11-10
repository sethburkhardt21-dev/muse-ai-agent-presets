"""Create-only downloadable ZIP of an already-pinned, pristine Software Engineer pack.

The generic profile kit lacks runtime files. This source kit packages the existing
R55 engineering_pack tree without native account access, code generation, or
another Claim Gate. It has unsigned local hashes, not publisher authentication.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import stat
import tempfile
import zipfile

from . import engineering_pack as pack

SCHEMA = "t20/software-engineer-sourcekit-v1"
ROLE = "software-engineer"
PREFIX = "software-engineer/"
MANIFEST = "SOURCEKIT_MANIFEST.json"
RUNBOOK = "START_HERE.md"
EXAMPLE = "EXAMPLE_REPAIR_CASE.json"
MAX_ARCHIVE_BYTES = 8 * 1024 * 1024
MAX_UNPACKED_BYTES = 4 * 1024 * 1024
MAX_MEMBERS = 96
HEX = re.compile(r"^[0-9a-f]{64}$")

START_HERE = """# Software Engineer: independent offline source kit

Contains the actual source-pinned Python Claim Gate, RED/PATCH/GREEN
workflow, source-only profile, disabled skills and a fictional test fixture.
No native Muse agent, account connector, paid API, or deployment is installed.

Requirements: Python 3.12+ and Git. No Python package installation required.

1. Extract into a new directory. Preserve any existing user/agent files.
2. Verify downloaded ZIP SHA-256 against trusted publisher metadata, not
   just the unsigned SOURCEKIT_MANIFEST.json inside this ZIP.
3. A reviewed offline fixture is included as EXAMPLE_REPAIR_CASE.json.
   Its expected digest is in SOURCEKIT_MANIFEST.json.
4. To execute the fixture, use absolute case/output paths and a NEW output
   directory that does not exist:

   python -I -B software-engineer/runtime/claim-gate/engineering_workflow.py execute --case ABSOLUTE_CASE_PATH --case-sha256 CASE_SHA --to ABSOLUTE_NEW_WORKSPACE --reviewed-code

5. Check the RED assertion, GREEN test receipt and preserved work evidence.
   A separate reviewer can run the review verb in a distinct workspace.

IMPORTANT: --reviewed-code is an operator assertion, NOT an OS sandbox.
Python tests execute with the operating account's permissions and can reach
its files/network. Never run untrusted source without separate OS isolation.
Local hashes are not signatures. No independent human or native Muse identity
is authenticated. Real external effects and schedulers are disabled.
Windows directory-entry power-loss durability is unproven; Windows destructive
retention pruning remains disabled. This is source only.
"""


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _json(value: dict) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def _unique(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError("DUPLICATE_SOURCEKIT_MANIFEST_KEY")
        out[key] = value
    return out


def _nonfinite(value):
    raise ValueError("NONFINITE_SOURCEKIT_VALUE")


def _expected_source_members() -> set[str]:
    return {PREFIX + name for name in pack._expected_pack_members()} | {
        PREFIX + "receipts/PACK_RECEIPT.json",
    }


def _example() -> bytes:
    # Reuse the one reviewed R55 case, rather than inventing a second fixture.
    from .workflow_fixture import fixture_case
    case = fixture_case()
    return (json.dumps(case, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
            + "\n").encode("utf-8")


def _canonical_profile_pins() -> dict[str, str]:
    """Check blank profile against original trusted templates, not local receipt."""
    with tempfile.TemporaryDirectory(prefix="r56-sourcekit-neutral-profile-") as temp:
        baseline = Path(temp) / "profile"
        pack.render_preset(ROLE, baseline)
        if {p.name for p in baseline.iterdir()} != pack.PROFILE_FILES:
            raise ValueError("SOURCEKIT_CANONICAL_PROFILE_SET_DRIFT")
        return {name: _sha(pack._bytes(baseline / name))
                for name in sorted(pack.PROFILE_FILES)}


def _kit_members(pristine: Path) -> dict[str, bytes]:
    if pack.inspect_engineer_pack(pristine).get("status") != "LOCAL_MATCH":
        raise ValueError("SOURCEKIT_PRISTINE_PACK_REQUIRED")
    profile_pins = _canonical_profile_pins()
    for name, original in profile_pins.items():
        if _sha(pack._bytes(pristine / "profile" / name)) != original:
            raise ValueError("SOURCEKIT_OWNER_PROFILE_NOT_CANONICAL")
    expected = pack._expected_pack_members()
    payload = {}
    for relative in sorted(expected):
        source = pristine / relative
        if source.is_symlink() or (hasattr(source, "is_junction") and source.is_junction()):
            raise ValueError("SOURCEKIT_UNSAFE_MEMBER")
        raw = pack._bytes(source)
        if source.stat().st_nlink != 1:
            raise ValueError("SOURCEKIT_HARDLINK_REFUSED")
        if expected[relative] is not None and _sha(raw) != expected[relative]:
            raise ValueError("SOURCEKIT_SOURCE_PIN_MISMATCH")
        payload[PREFIX + relative] = raw
    receipt = PREFIX + "receipts/PACK_RECEIPT.json"
    payload[receipt] = pack._bytes(pristine / "receipts" / "PACK_RECEIPT.json")
    payload[RUNBOOK] = START_HERE.encode("utf-8")
    payload[EXAMPLE] = _example()
    for name, original in profile_pins.items():
        if _sha(payload[PREFIX + "profile/" + name]) != original:
            raise ValueError("SOURCEKIT_OWNER_PROFILE_NOT_CANONICAL")
    if len(payload) > MAX_MEMBERS or sum(len(x) for x in payload.values()) > MAX_UNPACKED_BYTES:
        raise ValueError("SOURCEKIT_MEMBER_BUDGET_EXCEEDED")
    # Freeze exact bytes before opening the destination; reject late drift.
    if pack.inspect_engineer_pack(pristine).get("status") != "LOCAL_MATCH":
        raise ValueError("SOURCEKIT_SOURCE_CHANGED_DURING_STAGE")
    for name in expected:
        if pack._bytes(pristine / name) != payload[PREFIX + name]:
            raise ValueError("SOURCEKIT_SOURCE_CHANGED_DURING_STAGE")
    if pack._bytes(pristine / "receipts" / "PACK_RECEIPT.json") != payload[receipt]:
        raise ValueError("SOURCEKIT_RECEIPT_CHANGED_DURING_STAGE")
    return payload


def _manifest(payload: dict[str, bytes]) -> dict:
    return {
        "schema": SCHEMA,
        "role_id": ROLE,
        "files_sha256": {name: _sha(data) for name, data in sorted(payload.items())},
        "source_manifest_sha256": _sha(payload[PREFIX + "runtime/claim-gate/ENGINE.json"]),
        "example_case_sha256": _sha(payload[EXAMPLE]),
        "runtime_modules": 12,
        "native_installed": False,
        "external_effect_authorized": False,
        "host_identity_authenticated": False,
        "os_sandboxed": False,
        "public_release_published": False,
    }


def _write_member(archive: zipfile.ZipFile, name: str, data: bytes) -> None:
    info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    info.create_system = 3
    info.external_attr = (stat.S_IFREG | 0o644) << 16
    info.compress_type = zipfile.ZIP_DEFLATED
    archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)


def export_engineer_sourcekit(pristine: Path, destination: Path) -> dict:
    """Export one pristine staged pack to a deterministic create-only ZIP."""
    pristine = pack._admitted_path(Path(pristine))
    frozen = _kit_members(pristine)
    members = {**frozen, MANIFEST: _json(_manifest(frozen))}
    destination = pack._require_new(Path(destination))
    with zipfile.ZipFile(destination, mode="x", allowZip64=False) as archive:
        for name, data in sorted(members.items()):
            _write_member(archive, name, data)
    digest = _sha(destination.read_bytes())
    if verify_engineer_sourcekit(destination, digest)["status"] != "LOCAL_SOURCEKIT_ARCHIVE_VERIFIED":
        raise RuntimeError("SOURCEKIT_POST_EXPORT_VERIFY_FAILED")
    return {
        "status": "LOCAL_SOURCEKIT_EXPORTED",
        "role_id": ROLE,
        "sha256": digest,
        "archive_bytes": destination.stat().st_size,
        "member_count": len(members),
        "runtime_modules": 12,
        "native_installed": False,
        "external_effect_authorized": False,
    }


def verify_engineer_sourcekit(archive_path: Path, expected_sha256: str) -> dict:
    """Inspect an archive using an expected SHA obtained separately from it."""
    archive_path = pack._admitted_path(Path(archive_path))
    if not archive_path.is_file() or archive_path.is_symlink():
        raise ValueError("SOURCEKIT_ARCHIVE_UNAVAILABLE")
    if (type(expected_sha256) is not str or HEX.fullmatch(expected_sha256) is None
            or _sha(pack._bytes(archive_path, limit=MAX_ARCHIVE_BYTES)) != expected_sha256):
        raise ValueError("SOURCEKIT_ARCHIVE_PIN_MISMATCH")
    expected = _expected_source_members() | {RUNBOOK, EXAMPLE, MANIFEST}
    with zipfile.ZipFile(archive_path, mode="r") as archive:
        infos = archive.infolist()
        if len(infos) != len(expected) or len(infos) > MAX_MEMBERS:
            raise ValueError("SOURCEKIT_ARCHIVE_FILE_SET_MISMATCH")
        seen, names_casefold = set(), set()
        total = 0
        for info in infos:
            name = info.filename
            parts = PurePosixPath(name).parts
            if (not name or name.startswith("/") or "\\" in name or
                    not parts or ":" in parts[0] or ".." in parts or
                    name in seen or name.casefold() in names_casefold or
                    info.is_dir() or name not in expected):
                raise ValueError("SOURCEKIT_ARCHIVE_UNSAFE_MEMBER")
            if stat.S_IFMT(info.external_attr >> 16) != stat.S_IFREG:
                raise ValueError("SOURCEKIT_ARCHIVE_NONREGULAR_MEMBER")
            seen.add(name)
            names_casefold.add(name.casefold())
            total += info.file_size
        if seen != expected or total > MAX_UNPACKED_BYTES or archive.testzip() is not None:
            raise ValueError("SOURCEKIT_ARCHIVE_INTEGRITY_REFUSED")
        files = {name: archive.read(name) for name in sorted(expected)}
    metadata = json.loads(files[MANIFEST].decode("utf-8"),
                          object_pairs_hook=_unique, parse_constant=_nonfinite)
    keys = {"schema", "role_id", "files_sha256", "source_manifest_sha256",
            "example_case_sha256", "runtime_modules", "native_installed",
            "external_effect_authorized", "host_identity_authenticated",
            "os_sandboxed", "public_release_published"}
    if (type(metadata) is not dict or set(metadata) != keys or
            metadata["schema"] != SCHEMA or metadata["role_id"] != ROLE or
            metadata["runtime_modules"] != 12 or
            any(metadata[k] is not False for k in (
                "native_installed", "external_effect_authorized",
                "host_identity_authenticated", "os_sandboxed",
                "public_release_published"))):
        raise ValueError("SOURCEKIT_MANIFEST_INVALID")
    pins = metadata["files_sha256"]
    if type(pins) is not dict or set(pins) != expected - {MANIFEST}:
        raise ValueError("SOURCEKIT_MANIFEST_FILE_SET_MISMATCH")
    if any(type(pins[name]) is not str or pins[name] != _sha(files[name]) for name in pins):
        raise ValueError("SOURCEKIT_ARCHIVED_MEMBER_DRIFT")
    if metadata["example_case_sha256"] != _sha(files[EXAMPLE]):
        raise ValueError("SOURCEKIT_EXAMPLE_PIN_MISMATCH")
    claim = PREFIX + "runtime/claim-gate/ENGINE.json"
    if metadata["source_manifest_sha256"] != _sha(files[claim]):
        raise ValueError("SOURCEKIT_RUNTIME_MANIFEST_DRIFT")
    engine = json.loads(files[claim].decode("utf-8"),
                        object_pairs_hook=_unique, parse_constant=_nonfinite)
    if (type(engine) is not dict or len(engine.get("files", {})) != 12 or
            engine.get("external_effects_enabled") is not False or
            engine.get("portable_windows_runtime") is not True or
            engine.get("native_muse_status") != "UNBOUND" or
            engine.get("registered_native_tools") != []):
        raise ValueError("SOURCEKIT_RUNTIME_POLICY_INVALID")
    for name, digest in engine["files"].items():
        if files.get(PREFIX+"runtime/claim-gate/"+name) is None or \
                digest != _sha(files[PREFIX+"runtime/claim-gate/"+name]):
            raise ValueError("SOURCEKIT_RUNTIME_SOURCE_PIN_MISMATCH")
    for name, digest in engine["skills"].items():
        if files.get(PREFIX+"skills/claim-gate/"+name) is None or \
                digest != _sha(files[PREFIX+"skills/claim-gate/"+name]):
            raise ValueError("SOURCEKIT_SKILL_SOURCE_PIN_MISMATCH")
    pack_receipt = json.loads(files[PREFIX+"receipts/PACK_RECEIPT.json"].decode("utf-8"),
                              object_pairs_hook=_unique, parse_constant=_nonfinite)
    receipt_keys = {
        "schema", "role_id", "source_manifest_sha256",
        "provenance_manifest_sha256", "provenance_rights_verified",
        "iron_manifest_sha256", "iron_ledger_rights_verified",
        "new_receipt_ledger_created", "files_sha256", "native_muse_status",
        "installed_native_tools", "native_installed", "external_effect_authorized",
        "schedulers_enabled", "profile_owner_memory_imported",
        "platform_execution_supported", "local_source_custody_verified",
        "evidence_grade",
    }
    if (type(pack_receipt) is not dict or set(pack_receipt) != receipt_keys or
            pack_receipt.get("schema") != "software-engineer/pack-v1" or
            pack_receipt.get("role_id") != ROLE or
            pack_receipt.get("native_muse_status") != "UNBOUND" or
            pack_receipt.get("installed_native_tools") != [] or
            pack_receipt.get("evidence_grade") != "LOCAL_FILE_STAGE_NOT_NATIVE_PROOF" or
            pack_receipt.get("local_source_custody_verified") is not True or
            type(pack_receipt.get("platform_execution_supported")) is not bool or
            any(pack_receipt.get(key) is not False for key in (
                "native_installed", "external_effect_authorized",
                "schedulers_enabled", "profile_owner_memory_imported",
                "provenance_rights_verified", "iron_ledger_rights_verified",
                "new_receipt_ledger_created")) or
            pack_receipt.get("source_manifest_sha256") != _sha(files[claim]) or
            pack_receipt.get("provenance_manifest_sha256") != _sha(
                files[PREFIX+"runtime/provenance-vault/ENGINE.json"]) or
            pack_receipt.get("iron_manifest_sha256") != _sha(
                files[PREFIX+"runtime/iron-ledger/ENGINE.json"])):
        raise ValueError("SOURCEKIT_PACK_RECEIPT_INVALID")
    expected_pack_files = pack._expected_pack_members()
    if (type(pack_receipt.get("files_sha256")) is not dict or
            set(pack_receipt["files_sha256"]) != set(expected_pack_files)):
        raise ValueError("SOURCEKIT_PACK_RECEIPT_FILE_SET_INVALID")
    for name, source_pin in expected_pack_files.items():
        if source_pin is not None and _sha(files[PREFIX+name]) != source_pin:
            raise ValueError("SOURCEKIT_PACK_SOURCE_PIN_MISMATCH")
    for relative, digest in pack_receipt["files_sha256"].items():
        if files.get(PREFIX+relative) is None or _sha(files[PREFIX+relative]) != digest:
            raise ValueError("SOURCEKIT_PACK_MEMBER_SHA_MISMATCH")
    return {
        "status": "LOCAL_SOURCEKIT_ARCHIVE_VERIFIED",
        "role_id": ROLE,
        "archive_sha256": expected_sha256,
        "member_count": len(files),
        "runtime_modules": 12,
        "native_installed": False,
        "external_effect_authorized": False,
        "host_identity_authenticated": False,
    }

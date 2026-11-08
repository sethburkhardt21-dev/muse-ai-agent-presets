"""Portable, source-pinned scoped subchat drafts for the 11 generic Muse roles.

No host IDs are discovered or minted here. This module cannot install, spawn,
grant tools, activate cron, hand off messages or modify the recipient's files.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .catalog import DISPLAY, ROOT, SLUG
from .native_canary import _no_duplicate_json, _reject_constant
from .native_skill_binding import _regular_bytes, _unsafe_source_path
from .playbooks import validate_playbook
from .system_profile import plan_system_profile

SOURCE_ROOT = ROOT
SCHEMA = "r41/subchat-scopes-v1"
ROOM_SCHEMA = "r41/subchat-v1"
MANIFEST = "SUBCHAT_RECEIPT.json"
ROOM_FILES = frozenset({
    "ROLE.md", "CONTEXT.md", "AGENTS.md", "MEMORY.md", "PREFERENCES.md",
    "TOOLS.md", "HEARTBEAT.md", "SUBCHAT.json", "skills.yaml",
})
OWNER_FILES = frozenset({"MEMORY.md", "PREFERENCES.md"})
MAX_FILE_BYTES = 131072


def _json(obj: Any) -> bytes:
    return (json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_json(data: bytes) -> Any:
    return json.loads(data.decode("utf-8"), object_pairs_hook=_no_duplicate_json,
                      parse_constant=_reject_constant)


def _source(role: str) -> tuple[dict, dict, dict[str, bytes]]:
    if not isinstance(role, str) or not SLUG.fullmatch(role):
        raise ValueError("INVALID_SUBCHAT_ROLE")
    paths = ["presets/catalog.json", f"presets/{role}/preset.json",
             f"presets/{role}/playbook.json"]
    frozen = {p: _regular_bytes(SOURCE_ROOT / p, MAX_FILE_BYTES) for p in paths}
    catalog = _read_json(frozen[paths[0]])
    if (not isinstance(catalog, dict) or type(catalog.get("presets")) is not list
            or len(catalog["presets"]) != 11 or len(set(catalog["presets"])) != 11
            or role not in catalog["presets"]):
        raise ValueError("INVALID_SUBCHAT_CATALOG")
    preset = _read_json(frozen[paths[1]])
    book = _read_json(frozen[paths[2]])
    if not isinstance(preset, dict) or preset.get("id") != role or validate_playbook(book, preset):
        raise ValueError("INVALID_SUBCHAT_PLAYBOOK")
    methods = [m["id"] for m in book["methods"]]
    if len(methods) != 3 or len(set(methods)) != 3 or any(not SLUG.fullmatch(m) for m in methods):
        raise ValueError("INVALID_SUBCHAT_METHODS")
    fam = preset.get("family_link")
    if (not isinstance(fam, dict) or fam.get("enabled") is not False
            or fam.get("transport") != "unbound" or fam.get("native_recipient") is not None):
        raise ValueError("SUBCHAT_FAMILY_POLICY_UNSAFE")
    return preset, book, frozen


def _method_files(role: str, method: dict, book: dict, display_name: str) -> dict[str, bytes]:
    mid = method["id"]
    name = f"subchats/{mid}/"
    role_name = book["purpose"]
    trigger = method["trigger"]
    instructions = "\n".join(f"{idx}. {step}" for idx, step in enumerate(method["steps"], 1))
    evidence = "\n".join(f"- {item}" for item in method["evidence"])
    metadata = {
        "schema": ROOM_SCHEMA, "role_id": role, "method_id": mid,
        "display_name": display_name,
        "handoff_to": method["handoff_to"], "handoff_mode": "PROPOSAL_ONLY",
        "owner_id": None, "agent_id": None, "native_chat_id": None,
        "provider_session_id": None, "native_installed": False,
        "native_loaded": False, "model_invocation_verified": False,
        "recipient_readback_verified": False, "external_effect_authorized": False,
        "enabled_skills": [], "scheduled_jobs": [], "connector_grants": [],
        "source_grade": "LOCAL_SUBCHAT_DRAFT_ONLY",
        "host_registration": "UNBOUND_OWNER_AND_PROVIDER_REQUIRED",
        "memory_policy": "RECEIVING_OWNER_CONTROLLED_NO_DONOR_IMPORT",
    }
    files = {
        "ROLE.md": f"# {display_name} — {mid}\n\nRole: {role}. Method: {mid}.\n\n"
                   f"Purpose: {role_name}\n\nTask trigger: {trigger}\n",
        "CONTEXT.md": f"# Scoped context: {mid}\n\n**When:** {trigger}\n\n"
                      f"**Procedure:**\n{instructions}\n\n**Evidence:**\n{evidence}\n\n"
                      f"**Stop rule:** {method['stop_rule']}\n\n"
                      f"**Possible next role:** {method['handoff_to']} — proposal only; no automatic send.\n",
        "AGENTS.md": f"# Agent instructions: {mid}\n\n"
                     "Inherit actual provider and owner policy, never inferred grants. "
                     f"Operate only this {role} method and its supplied source-bound context. "
                     "No background jobs, owner-memory transfers, impersonation or extra tools. "
                     "Every effect requires a separately authenticated owner/host grant, "
                     "and external results require independent recipient readback.\n",
        "MEMORY.md": "# Receiving-owner memory\n\n"
                     "New blank scoped memory. Nothing from the original agents is preloaded. "
                     "Keep observation, inference and owner preferences distinct. "
                     "Do not copy or synchronize to another owner without an approved native route.\n",
        "PREFERENCES.md": "# Receiving-owner preferences\n\n"
                          "This is an editable blank preference draft scoped to this method. "
                          "Preserve the owner's later changes during upgrades.\n",
        "TOOLS.md": "# Scoped tool policy\n\n"
                    "Optional capability categories from the role playbook: "
                    + ", ".join(book["optional_tool_categories"]) + ".\n\n"
                    "These are categories, not installed skills or runtime grants. "
                    "Tool discovery/registration belongs to the receiving host, not this file. "
                    "Refuse unknown tools, wrong owner and unsupported effects.\n",
        "HEARTBEAT.md": "# Heartbeat and scheduling\n\n"
                        "DISABLED by default. No callbacks, cron jobs, self-wake or model routing "
                        "are started by this draft. A later authorized host-native schedule "
                        "must be separately registered and verified.\n",
        "SUBCHAT.json": _json(metadata),
        "skills.yaml": "version: 1\nentries:\n",
    }
    result = {}
    for key, value in files.items():
        data = value if isinstance(value, bytes) else value.encode("utf-8")
        if not data or len(data) > MAX_FILE_BYTES or b"\x00" in data:
            raise ValueError("INVALID_SUBCHAT_CONTENT")
        result[name + key] = data
    return result


def _build(role: str, display_name: str | None) -> tuple[dict[str, bytes], dict, dict[str, bytes]]:
    preset, book, frozen = _source(role)
    name = role.replace("-", " ").title() if display_name is None else display_name
    if not isinstance(name, str) or not DISPLAY.fullmatch(name):
        raise ValueError("INVALID_SUBCHAT_DISPLAY_NAME")
    profile_plan = plan_system_profile(role, display_name=name)
    files = {}
    subchat_registry = []
    for method in book["methods"]:
        files.update(_method_files(role, method, book, name))
        subchat_registry.append({
            "method_id": method["id"], "folder": f"subchats/{method['id']}",
            "native_chat_id": None, "host_installed": False,
            "memory_scope": f"subchats/{method['id']}/MEMORY.md",
            "enabled_skills": [], "handoff_proposal": method["handoff_to"],
        })
    files["config/subchats.json"] = _json({
        "schema": SCHEMA, "role": role, "profile_source_sha256": profile_plan["source_sha256"],
        "owner_id": None, "provider_session_id": None,
        "native_installed": False, "model_selected_invocation": False,
        "recipient_readback_verified": False, "external_effect_authorized": False,
        "subchats": subchat_registry,
    })
    source_pins = {p: _sha(data) for p, data in frozen.items()}
    receipt = {
        "schema": SCHEMA, "role": role, "display_name": name,
        "source_pins": source_pins,
        "profile_source_sha256": profile_plan["source_sha256"],
        "files": {p: _sha(data) for p, data in files.items()},
        "owner_files": sorted(p for p in files
                              if p.rsplit("/", 1)[-1] in OWNER_FILES),
        "method_ids": [m["id"] for m in book["methods"]],
        "native_loaded": False, "provider_issued_chat_ids": False,
        "external_effect_authorized": False, "can_apply": False,
        "grade": "LOCAL_SCOPED_SUBCHATS_ONLY",
    }
    return files, receipt, frozen


def plan_subchat_scopes(role: str, *, display_name: str | None = None) -> dict:
    files, receipt, _ = _build(role, display_name)
    return {
        "status": "SOURCE_PLAN_ONLY", "role": role,
        "methods": receipt["method_ids"], "file_count": len(files),
        "profile_source_sha256": receipt["profile_source_sha256"],
        "native_loaded": False, "can_apply": False,
    }


def _require_new(path: Path) -> None:
    if _unsafe_source_path(path):
        raise ValueError("UNSAFE_SUBCHAT_DESTINATION")
    if path.exists() or path.is_symlink():
        raise FileExistsError("SUBCHAT_DESTINATION_EXISTS")
    if not path.parent.is_dir():
        raise FileNotFoundError("SUBCHAT_PARENT_REQUIRED")


def _write_new(path: Path, data: bytes) -> None:
    with path.open("xb") as stream:
        stream.write(data)


def stage_subchat_scopes(destination: Path, role: str, *, display_name: str | None = None,
                         expected_profile_source_sha256: str | None = None) -> dict:
    """Stage new source-only subchats. Any interrupted stage remains fenced."""
    dest = Path(destination)
    _require_new(dest)
    files, receipt, frozen = _build(role, display_name)
    if expected_profile_source_sha256 is not None and (
        not isinstance(expected_profile_source_sha256, str)
        or expected_profile_source_sha256 != receipt["profile_source_sha256"]):
        raise ValueError("SUBCHAT_SOURCE_PIN_MISMATCH")
    dest.mkdir(exist_ok=False)
    marker = dest / "STAGING_INCOMPLETE"
    _write_new(marker, b"LOCAL_DRAFT_STAGE_INCOMPLETE_RECONCILE_NO_RETRY\n")
    (dest / "subchats").mkdir()
    (dest / "config").mkdir()
    for relative in sorted(files):
        path = dest / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        _write_new(path, files[relative])
    # Repeat the source calculation after writes so source drift cannot be
    # acknowledged as a successful staging event.
    if _source(role)[2] != frozen or _build(role, display_name)[1] != receipt:
        raise ValueError("SUBCHAT_SOURCE_CHANGED_DURING_STAGE")
    _write_new(dest / MANIFEST, _json(receipt))
    marker.unlink()
    return {
        "status": "LOCAL_SUBCHATS_STAGED", "role": role,
        "subchat_count": len(receipt["method_ids"]),
        "file_count": len(files), "native_loaded": False,
        "external_effect_authorized": False,
    }


def _exact_tree(dest: Path, expected: set[str], methods: list[str]) -> bool:
    expected_dirs = {"subchats", "config"} | {f"subchats/{mid}" for mid in methods}
    actual_dirs, actual_files = set(), set()
    if sum(1 for _ in dest.rglob("*")) > 100:
        return False
    for child in dest.rglob("*"):
        if _unsafe_source_path(child):
            return False
        rel = child.relative_to(dest).as_posix()
        if child.is_dir():
            actual_dirs.add(rel)
        elif child.is_file():
            actual_files.add(rel)
        else:
            return False
    return actual_dirs == expected_dirs and actual_files == expected | {MANIFEST}


def inspect_subchat_scopes(destination: Path) -> dict:
    """Read-only, source-derived comparison. Unsigned receipts never grant rights."""
    dest = Path(destination)
    base = {
        "status": "REVIEW_REQUIRED", "native_loaded": False,
        "external_effect_authorized": False, "can_apply": False,
        "owner_modified": [], "policy_modified": [],
    }
    try:
        if _unsafe_source_path(dest) or not dest.is_dir():
            return base
        marker = dest / "STAGING_INCOMPLETE"
        if marker.exists() or marker.is_symlink():
            return {**base, "status": "INCOMPLETE_STAGE"}
        raw = _regular_bytes(dest / MANIFEST, MAX_FILE_BYTES)
        claim = _read_json(raw)
        if not isinstance(claim, dict) or claim.get("schema") != SCHEMA:
            return base
        files, expected, _ = _build(claim.get("role"), claim.get("display_name"))
        # A changed declared role is not an upstream source revision. The
        # original package's role-specific method roster must match first.
        if claim.get("method_ids") != expected["method_ids"]:
            return base
        if claim.get("source_pins") != expected["source_pins"] or (
            claim.get("profile_source_sha256") != expected["profile_source_sha256"]
        ):
            return {**base, "status": "SOURCE_DRIFT"}
        if raw != _json(expected) or not _exact_tree(dest, set(files), expected["method_ids"]):
            return base
        owner_modified, policy_modified = [], []
        for relative, original in files.items():
            actual = _regular_bytes(dest / relative, MAX_FILE_BYTES)
            if actual != original:
                (owner_modified if relative in expected["owner_files"] else policy_modified).append(relative)
        state = ("REVIEW_REQUIRED" if policy_modified else
                 "OWNER_CUSTOMIZED" if owner_modified else "LOCAL_SUBCHATS_MATCH")
        return {
            **base, "status": state, "role": expected["role"],
            "owner_modified": sorted(owner_modified),
            "policy_modified": sorted(policy_modified),
            "profile_source_sha256": expected["profile_source_sha256"],
            "subchat_count": len(expected["method_ids"]),
        }
    except (OSError, ValueError, TypeError, KeyError):
        return base


def preview_subchat_scopes(candidate: Path, target: Path) -> dict:
    """Diff named source files against an owner target without any application."""
    candidate, target = Path(candidate), Path(target)
    if inspect_subchat_scopes(candidate)["status"] != "LOCAL_SUBCHATS_MATCH":
        raise ValueError("UNTRUSTED_SUBCHAT_CANDIDATE")
    if _unsafe_source_path(target) or (target.exists() and not target.is_dir()):
        raise ValueError("UNSAFE_SUBCHAT_TARGET")
    changes = []
    for file in sorted(candidate.rglob("*"), key=lambda p: p.relative_to(candidate).as_posix()):
        if not file.is_file() or file.name == MANIFEST:
            continue
        relative = file.relative_to(candidate).as_posix()
        dest = target / relative
        if _unsafe_source_path(dest):
            raise ValueError("UNSAFE_SUBCHAT_TARGET_MEMBER")
        if dest.exists():
            existing = _regular_bytes(dest, MAX_FILE_BYTES)
            source = _regular_bytes(file, MAX_FILE_BYTES)
            action = ("UNCHANGED" if existing == source else
                      "PRESERVE_OWNER_EDIT" if file.name in OWNER_FILES else
                      "REVIEW_CONFLICT")
        else:
            action = "CREATE"
        changes.append({"path": relative, "action": action})
    return {
        "status": "PREVIEW_ONLY", "files": changes,
        "can_apply": False, "native_loaded": False,
        "effects_performed": False, "unlisted_owner_files": "UNTOUCHED",
    }

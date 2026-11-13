"""Create-only 15-role generic source fleet and two separate host handoffs per role.

This module never installs into or reads a personal agent. A filesystem
candidate is not a native authenticated skill, subchat, scheduler or service.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .catalog import DOCUMENTS, load_registry, render_preset
from .lifecycle import inspect_render
from .native_canary import (
    HOST_KINDS, _admitted_destination, _no_duplicate_json, _reject_constant,
    _serialized, inspect_canary, stage_canary,
)
from .native_skill_binding import _unsafe_source_path

SCHEMA = "r32/generic-fleet-v1"
ROOT_FILES = frozenset({"roles", "FLEET_RECEIPT.json"})
PROFILE_FILES = frozenset((*DOCUMENTS, "ROLE_PLAYBOOK.md",
                            "FAMILY_LINK.json", "RECEIPT.json"))
ROLE_FILES = frozenset({"profile", *HOST_KINDS})


def _sha_file(path: Path) -> str:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 131072:
        raise ValueError("FLEET_MEMBER_UNTRUSTED")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _receipt_index(root: Path, names: list[str]) -> dict:
    index = {}
    for role in names:
        p = root / "roles" / role
        index[role] = {
            "profile": _sha_file(p / "profile" / "RECEIPT.json"),
            **{host: _sha_file(p / host / "SOURCE_RECEIPT.json")
               for host in sorted(HOST_KINDS)},
        }
    return index


def _manifest(root: Path, names: list[str]) -> dict:
    return {
        "schema": SCHEMA,
        "roles": names,
        "profile_count": len(names),
        "native_canary_count": len(names) * len(HOST_KINDS),
        "source_receipts": _receipt_index(root, names),
        "maturity": "SOURCE_ONLY_UNBOUND",
        "native_installed": False,
        "host_authenticated": False,
        "external_effect_authorized": False,
        "independent_recipient_verified": False,
    }


def stage_generic_fleet(destination: Path) -> dict:
    """Never overwrite target/owner state; leave partial staging fenced."""
    dest = Path(destination)
    _admitted_destination(dest)
    roles = load_registry()["presets"]
    if (type(roles) is not list or len(roles) != len(set(roles)) or
        not roles or any(type(role) is not str for role in roles)):
        raise ValueError("INVALID_GENERIC_ROLE_CATALOG")
    dest.mkdir(exist_ok=False)
    marker = dest / "STAGING_INCOMPLETE"
    marker.write_text("LOCAL_SOURCE_STAGE_NOT_NATIVE\n", encoding="utf-8")
    roles_dir = dest / "roles"
    roles_dir.mkdir(exist_ok=False)
    for role in roles:
        item = roles_dir / role
        item.mkdir(exist_ok=False)
        # Use a neutral display label accepted by the owner-name renderer.
        render_preset(role, item / "profile", display_name=role.replace("-", " ").title())
        for host in sorted(HOST_KINDS):
            stage_canary(item / host, role, host)
    receipt = _manifest(dest, roles)
    with (dest / "FLEET_RECEIPT.json").open("xb") as handle:
        handle.write(_serialized(receipt))
    marker.unlink()
    return {
        "status": "LOCAL_FLEET_STAGED_ONLY",
        "destination": str(dest),
        "profile_count": len(roles),
        "native_canary_count": len(roles) * len(HOST_KINDS),
        "native_installed": False,
        "external_effect_authorized": False,
    }


def inspect_generic_fleet(destination: Path) -> dict:
    """Read-only, fail-closed closed-tree and current role-pin verification."""
    dest = Path(destination)
    reject = {"status": "REVIEW_REQUIRED", "native_installed": False,
              "external_effect_authorized": False}
    if _unsafe_source_path(dest) or not dest.is_dir():
        return reject
    if (dest / "STAGING_INCOMPLETE").exists() or (dest / "STAGING_INCOMPLETE").is_symlink():
        return {**reject, "status": "INCOMPLETE_STAGE"}
    try:
        if {p.name for p in dest.iterdir()} != ROOT_FILES:
            return reject
        roles_dir = dest / "roles"
        if roles_dir.is_symlink() or not roles_dir.is_dir():
            return reject
        names = load_registry()["presets"]
        if {p.name for p in roles_dir.iterdir()} != set(names):
            return reject
        for role in names:
            parent = roles_dir / role
            if (parent.is_symlink() or not parent.is_dir() or
                {p.name for p in parent.iterdir()} != ROLE_FILES):
                return reject
            profile = parent / "profile"
            if (profile.is_symlink() or not profile.is_dir() or
                {p.name for p in profile.iterdir()} != PROFILE_FILES):
                return reject
            if any(p.is_symlink() or not p.is_file() for p in profile.iterdir()):
                return reject
            if inspect_render(profile)["status"] != "LOCAL_MATCH":
                return reject
            for host in HOST_KINDS:
                if inspect_canary(parent / host)["status"] != "SOURCE_ONLY_MATCH":
                    return reject
        path = dest / "FLEET_RECEIPT.json"
        data = json.loads(path.read_bytes(), object_pairs_hook=_no_duplicate_json,
                          parse_constant=_reject_constant)
        if (type(data) is not dict or
            path.read_bytes() != _serialized(_manifest(dest, names))):
            return reject
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
        return reject
    return {
        "status": "LOCAL_FLEET_MATCH",
        "profile_count": len(names),
        "native_canary_count": len(names) * len(HOST_KINDS),
        "native_installed": False,
        "external_effect_authorized": False,
    }

"""Read-only, unauthenticated native host inventory; never a Muse grant or install."""
from __future__ import annotations

import json
from pathlib import Path
import re
import shutil
from typing import Callable

from .database_paths import _trusted_darwin_alias

KINDS = frozenset({"personal-hatch", "muse-code"})
VERSION_RE = {
    "personal-hatch": re.compile(r"^hatch\s+v?(\d+\.\d+\.\d+)(?:\s+\(([a-fA-F0-9]{7,40})\))?\s*$"),
    "muse-code": re.compile(r"^muse(?:-code)?\s+v?(\d+\.\d+\.\d+)(?:\s+\(([a-fA-F0-9]{7,40})\))?\s*$"),
}
SEMVER = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")
SHA = re.compile(r"^[a-fA-F0-9]{7,40}$")
SERVICES = frozenset({"hatch", "hatch-execd"})


def _no_duplicates(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError("DUPLICATE_JSON_KEY")
        out[key] = value
    return out


def _reject_constant(value):
    raise ValueError("NON_STANDARD_JSON_CONSTANT")


def _service_names(proc_root: Path) -> list[str]:
    """Only exact short process comm labels, never argv, environment or tokens."""
    names = set()
    if proc_root.is_symlink() or not proc_root.is_dir():
        return []
    try:
        entries = proc_root.iterdir()
        for entry in entries:
            if not entry.name.isdecimal() or entry.is_symlink():
                continue
            comm = entry / "comm"
            if comm.is_symlink():
                continue
            try:
                with comm.open("r", encoding="utf-8", errors="replace") as handle:
                    name = handle.read(80).strip()
                if name in SERVICES:
                    names.add(name)
            except (OSError, UnicodeError):
                continue
            if names == SERVICES:
                break
    except OSError:
        pass
    return sorted(names)


def _skills(skills_root: Path) -> list[str]:
    if skills_root.is_symlink() or not skills_root.is_dir():
        return []
    try:
        return sorted(p.name for p in skills_root.iterdir()
                      if p.is_dir() and not p.is_symlink()
                      and re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", p.name))[:100]
    except OSError:
        return []


def _space_sdk_version(skills_root: Path) -> str | None:
    path = skills_root / "spaces" / "ts-runtime" / "sdk" / "package.json"
    # macOS /var, /tmp and /etc may be OS-owned aliases into /private.
    # Reuse the exact root-ownership and canonical-target checks; never trust
    # arbitrary user-controlled symlinked path components.
    if skills_root.is_symlink() or any(
        p.is_symlink() and not _trusted_darwin_alias(p)
        for p in (path, *path.parents)
    ):
        return None
    try:
        if not path.is_file() or path.stat().st_size > 8192:
            return None
        data = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_no_duplicates,
                          parse_constant=_reject_constant)
    except (OSError, UnicodeError, ValueError, TypeError):
        return None
    if not isinstance(data, dict) or data.get("name") != "@hatch/space-sdk":
        return None
    version = data.get("version")
    return version if isinstance(version, str) and SEMVER.fullmatch(version) else None


def probe_host(
    host_kind: str, *,
    binary_path: Path | None = None,
    process_root: Path | None = None,
    skills_root: Path | None = None,
    version_reader: Callable[[Path], str] | None = None,
) -> dict:
    """A local snapshot, deliberately incapable of granting native authority.

    Fixture paths/runners help regression-test refusal paths. They never produce
    a host-issued signature, session principal, tool grant or recipient receipt.
    """
    if host_kind not in KINDS:
        raise ValueError("UNKNOWN_HOST_KIND")
    if binary_path is None:
        if host_kind == "personal-hatch":
            binary_path = Path("/opt/hatch/bin/hatch")
        else:
            binary_path = Path(shutil.which("muse") or "/__muse_code_not_found__")
    binary_path = Path(binary_path)
    process_root = Path(process_root) if process_root is not None else Path("/proc")
    skills_root = Path(skills_root) if skills_root is not None else Path("/opt/hatch/skills")

    binary_present = not binary_path.is_symlink() and binary_path.is_file()
    version, commit_hint = None, None
    # Passive inventory must never run a caller-supplied binary, even with --version.
    # The injected reader is for isolated unit fixtures only; production leaves
    # the version unverified until a supported host-issued metadata API exists.
    if binary_present and version_reader is not None:
        try:
            raw = version_reader(binary_path)
            if not isinstance(raw, str):
                raise ValueError("VERSION_NOT_TEXT")
            lines = raw.splitlines()
            match = VERSION_RE[host_kind].fullmatch(lines[0].strip()) if lines else None
            if match:
                version = match.group(1)
                commit_hint = match.group(2)
                for line in lines[1:5]:
                    if line.startswith("commit: "):
                        maybe = line.removeprefix("commit: ").strip()
                        if SHA.fullmatch(maybe):
                            commit_hint = maybe
        except (OSError, ValueError, TimeoutError):
            pass

    is_hatch = host_kind == "personal-hatch"
    services = _service_names(process_root) if is_hatch else []
    installed_skills = _skills(skills_root) if is_hatch else []
    sdk_hint = _space_sdk_version(skills_root) if is_hatch else None
    observed = version is not None
    capabilities = {
        "native_skill_registration": "UNVERIFIED",
        "skill_search": "UNVERIFIED",
        "model_originated_invocation": "UNVERIFIED",
        "space_agent_callback": "UNVERIFIED" if is_hatch else "NOT_APPLICABLE",
        "hooks": "UNVERIFIED",
        "cron": "UNVERIFIED",
        "subchat_identity": "UNVERIFIED",
        "memory_persistence": "UNVERIFIED",
        "owner_grants": "UNVERIFIED",
        "recipient_outcomes": "UNVERIFIED",
        "personal_hatch_agent_host": "UNVERIFIED" if is_hatch else "NOT_APPLICABLE",
    }
    return {
        "schema": "r32/native-host-local-doctor-v1",
        "host_kind": host_kind,
        "status": "HOST_RUNTIME_PRESENT_UNATTESTED" if observed else "HOST_UNVERIFIED",
        "provenance": "UNATTESTED_LOCAL_PROCESS_OBSERVATION",
        "phases": {"D0": "NOT_RUN", "D1": "PARTIAL_LOCAL_OBSERVATION" if observed else "UNVERIFIED",
                   "D2": "NOT_RUN", "D3": "NOT_RUN", "D4": "NOT_RUN"},
        "runtime": {
            "binary_present": binary_present,
            "version": version,
            "build_commit_hint": commit_hint,
            "service_names_observed": services,
            "local_skill_directories": installed_skills,
            "space_sdk_version_hint": sdk_hint,
        },
        "capabilities": capabilities,
        "authority": {
            "host_authenticated": False,
            "native_tool_registered": False,
            "native_tool_invocation_verified": False,
            "owner_grant_verified": False,
            "recipient_receipt_verified": False,
            "external_effect_authorized": False,
        },
        "next_gate": "SUPPORTED_HOST_API_AND_OWNER_SESSION_PRINCIPAL_REQUIRED",
    }

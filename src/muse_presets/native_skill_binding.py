"""Read-only local Muse custom-skill catalog reconciliation.

A skill's source and local registry are not a provider-issued skill-search hit,
model tool call, owner grant, or recipient receipt. No host writes are possible.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import re
from collections.abc import Sequence

from .database_paths import _trusted_darwin_alias

NAME = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
REG_NAME = re.compile(r"^[a-z][a-z0-9_-]{0,63}$")
MANIFEST_KEY = re.compile(r"^([a-z][a-z0-9_]*):(?: (.*))?$")
CATALOG_ENTRY = re.compile(r"^  ([a-z][a-z0-9_-]{0,63}):$")
CATALOG_STATUS = re.compile(r"^    status: (available|connected|disabled|unavailable|disconnected)$")


class SourceAdmissionError(ValueError):
    pass


def _unsafe_source_path(path: Path) -> bool:
    """Refuse owner-controlled symlink/junction ancestors and literal traversal.

    Check lexical components before absolute normalization; the only aliases
    allowed are the standard root-owned macOS paths verified by the shared
    source-only filesystem predicate. This is not an atomic openat guarantee.
    """
    if '..' in path.parts:
        return True
    absolute = Path(os.path.abspath(path))
    for part in (absolute, *absolute.parents):
        is_junction = getattr(part, 'is_junction', None)
        if (part.is_symlink() or (callable(is_junction) and is_junction())) and not _trusted_darwin_alias(part):
            return True
    return False


def _regular_bytes(path: Path, max_size: int) -> bytes:
    if _unsafe_source_path(path) or not path.is_file():
        raise SourceAdmissionError("REGULAR_FILE_REQUIRED")
    try:
        if path.stat().st_size > max_size:
            raise SourceAdmissionError("FILE_TOO_LARGE")
        data = path.read_bytes()
    except OSError as exc:
        raise SourceAdmissionError("SOURCE_READ_FAILED") from exc
    if len(data) > max_size:
        raise SourceAdmissionError("FILE_TOO_LARGE")
    return data


def _utf8(data: bytes) -> str:
    try:
        content = data.decode("utf-8")
    except UnicodeError as exc:
        raise SourceAdmissionError("INVALID_UTF8") from exc
    if "\x00" in content:
        raise SourceAdmissionError("NUL_IN_DESCRIPTOR")
    return content


def _registry(path: Path) -> tuple[dict[str, str], str]:
    """Parse the intentionally narrow, observed skills.yaml v1 status subset.

    This does not execute YAML tags, aliases or expressions and rejects
    duplicate entries/statuses. The observed version-1 registry subset
    contains only a version, entries, and exactly one status per name.
    """
    data = _regular_bytes(path, 65536)
    lines = _utf8(data).splitlines()
    if lines[:2] != ["version: 1", "entries:"]:
        raise SourceAdmissionError("REGISTRY_VERSION_OR_ROOT_INVALID")
    entries: dict[str, str | None] = {}
    name = None
    for line in lines[2:]:
        if not line.strip() or line.startswith("#"):
            continue
        m = CATALOG_ENTRY.fullmatch(line)
        if m:
            name = m.group(1)
            if name in entries:
                raise SourceAdmissionError("DUPLICATE_CATALOG_ENTRY")
            entries[name] = None
            continue
        m = CATALOG_STATUS.fullmatch(line)
        if m and name is not None and entries[name] is None:
            entries[name] = m.group(1)
            continue
        raise SourceAdmissionError("CATALOG_ENTRY_INVALID")
    if any(status is None for status in entries.values()):
        raise SourceAdmissionError("CATALOG_ENTRY_MISSING_STATUS")
    return {key: str(value) for key, value in entries.items()}, hashlib.sha256(data).hexdigest()


def _simple_scalar(raw: str | None) -> str:
    if raw is None:
        return ""
    val = raw.strip()
    if len(val) > 4096 or val.startswith(("!", "&", "*", "<<", "[", "{")):
        raise SourceAdmissionError("UNSAFE_DESCRIPTOR_SCALAR")
    if len(val) > 1 and val[0] == val[-1] and val[0] in ('"', "'"):
        val = val[1:-1]
    return val


def _descriptor(folder: Path, expected: str) -> tuple[bool, dict[str, str], dict[str, str]]:
    if _unsafe_source_path(folder) or not folder.is_dir():
        raise SourceAdmissionError("SKILL_FOLDER_INVALID")
    yaml_bytes = _regular_bytes(folder / "skill.yaml", 32768)
    md_bytes = _regular_bytes(folder / "SKILL.md", 131072)
    md = _utf8(md_bytes)
    # Native-style SKILL.md may start with bounded YAML front matter. The
    # source audit does not interpret or execute its claims; it only finds the
    # terminating delimiter and verifies there is a body after it.
    lines = md.splitlines()
    if lines and lines[0] == "---":
        try:
            last = lines.index("---", 1)
        except ValueError as exc:
            raise SourceAdmissionError("SKILL_FRONTMATTER_UNTERMINATED") from exc
        if last > 80 or sum(len(line) for line in lines[:last]) > 8192:
            raise SourceAdmissionError("SKILL_FRONTMATTER_TOO_LARGE")
        md = "\n".join(lines[last + 1:])
    if not md.lstrip().startswith("#") or not md.strip():
        raise SourceAdmissionError("SKILL_BODY_MISSING")
    values: dict[str, str] = {}
    for line in _utf8(yaml_bytes).splitlines():
        if not line or line.lstrip().startswith("#") or line.startswith(" "):
            continue
        m = MANIFEST_KEY.fullmatch(line)
        if m is None:
            raise SourceAdmissionError("INVALID_TOP_LEVEL_DESCRIPTOR")
        key = m.group(1)
        if key in values:
            raise SourceAdmissionError("DUPLICATE_DESCRIPTOR_KEY")
        values[key] = _simple_scalar(m.group(2))
    if values.get("name") != expected or not NAME.fullmatch(values.get("name", "")):
        raise SourceAdmissionError("SKILL_NAME_MISMATCH")
    for field in ("title", "description"):
        if not values.get(field) or len(values[field]) > 2048:
            raise SourceAdmissionError("MISSING_TRIGGER_METADATA")
    if values.get("include_in_prompt") not in ("true", "false"):
        raise SourceAdmissionError("INVALID_PROMPT_FLAG")
    hashes = {
        "skill_yaml_sha256": hashlib.sha256(yaml_bytes).hexdigest(),
        "skill_md_sha256": hashlib.sha256(md_bytes).hexdigest(),
    }
    bin_dir = folder / "bin"
    has_entrypoint = False
    if (folder / "run.py").is_file() and not (folder / "run.py").is_symlink():
        has_entrypoint = True
    if bin_dir.is_dir() and not bin_dir.is_symlink():
        try:
            has_entrypoint = has_entrypoint or any(
                f.is_file() and not f.is_symlink() and REG_NAME.fullmatch(f.name)
                for f in bin_dir.iterdir()
            )
        except OSError:
            pass
    return has_entrypoint, values, hashes


def _select_folder(root: Path, name: str) -> Path:
    if _unsafe_source_path(root) or not root.is_dir():
        raise SourceAdmissionError("CUSTOM_SKILLS_ROOT_INVALID")
    choices = {root / name, root / name.replace("_", "-")}
    candidates = [folder for folder in choices if folder.exists() or folder.is_symlink()]
    if len(candidates) > 1:
        raise SourceAdmissionError("AMBIGUOUS_SKILL_DIRECTORY")
    if not candidates:
        raise SourceAdmissionError("SKILL_FOLDER_MISSING")
    return candidates[0]


def inspect_skill_bindings(
    *, custom_root: Path, registry_path: Path, skill_names: Sequence[str]
) -> dict:
    """Observe only explicitly requested named skills; never enumerate private prose."""
    if not skill_names or len(skill_names) > 25:
        raise ValueError("INVALID_REQUEST_SCOPE")
    if any(type(name) is not str or NAME.fullmatch(name) is None for name in skill_names):
        raise ValueError("INVALID_SKILL_NAME")
    if len(set(skill_names)) != len(skill_names):
        raise ValueError("DUPLICATE_REQUESTED_SKILL")
    custom_root, registry_path = Path(custom_root), Path(registry_path)
    try:
        registered, registry_sha = _registry(registry_path)
        trusted_catalog = True
    except (SourceAdmissionError, OSError):
        registered, registry_sha, trusted_catalog = {}, None, False
    rows = []
    for requested in skill_names:
        descriptor = "DESCRIPTOR_REVIEW_REQUIRED"
        local_entrypoint = False
        hashes: dict[str, str] = {}
        dir_name = None
        try:
            folder = _select_folder(custom_root, requested)
            dir_name = folder.name
            local_entrypoint, values, hashes = _descriptor(folder, requested)
            descriptor = "DESCRIPTOR_VALID"
            prompt = values["include_in_prompt"] == "true"
        except (SourceAdmissionError, OSError, UnicodeError):
            prompt = None
            if (custom_root / requested).exists() or (custom_root / requested.replace("_", "-")).exists():
                descriptor = "DESCRIPTOR_REVIEW_REQUIRED"
            else:
                descriptor = "SOURCE_NOT_FOUND"
            # Duplicate alternate dirs are review-required, never treated as a match.
            if (custom_root / requested).exists() and (custom_root / requested.replace("_", "-")).exists():
                descriptor = "AMBIGUOUS_SKILL_DIRECTORY"
        if not trusted_catalog or descriptor != "DESCRIPTOR_VALID":
            catalog = "NOT_EVALUATED"
        else:
            status = registered.get(requested)
            catalog = ("DECLARED_AVAILABLE" if status == "available" else
                       "CATALOG_ENTRY_MISSING" if status is None else "NOT_ADVERTISED_AS_SKILL")
        rows.append({
            "name": requested,
            "directory": dir_name,
            "source_status": descriptor,
            "descriptor_present": descriptor == "DESCRIPTOR_VALID",
            "source_hashes": hashes,
            "include_in_prompt": prompt,
            "local_entrypoint_observed": bool(local_entrypoint),
            "catalog_status": catalog,
            "native_tool_registered": False,
            "provider_invocation_verified": False,
        })
    if not trusted_catalog:
        status = "LOCAL_CATALOG_UNTRUSTED"
    elif any(row["source_status"] != "DESCRIPTOR_VALID" for row in rows):
        status = "LOCAL_SOURCE_REVIEW_REQUIRED"
    elif any(row["catalog_status"] == "CATALOG_ENTRY_MISSING" for row in rows):
        status = "LOCAL_CATALOG_GAP"
    elif all(row["catalog_status"] == "DECLARED_AVAILABLE" for row in rows):
        status = "LOCAL_CATALOG_ADVERTISED_ONLY"
    else:
        status = "LOCAL_CATALOG_NOT_ADVERTISED"
    return {
        "schema": "r32/skill-binding-audit-v1",
        "host_kind": "personal-hatch",
        "status": status,
        "evidence_grade": "UNATTESTED_LOCAL_SOURCE_ONLY",
        "registry_sha256": registry_sha,
        "skills": rows,
        "authority": {
            "native_skill_search_verified": False,
            "model_selected_skill_verified": False,
            "provider_invocation_verified": False,
            "owner_grant_verified": False,
            "recipient_readback_verified": False,
            "external_effect_authorized": False,
        },
        "remediation": "CHECK_SUPPORTED_NATIVE_SKILL_SEARCH_IN_OWNER_CONTEXT",
    }


def propose_registry_entries(report: dict) -> dict:
    """Generate a human-reviewable text suggestion. Never open or mutate host files."""
    if report.get("schema") != "r32/skill-binding-audit-v1":
        raise ValueError("INVALID_AUDIT")
    safe = report.get("registry_sha256") is not None
    missing = sorted(row["name"] for row in report.get("skills", [])
                     if safe and row.get("source_status") == "DESCRIPTOR_VALID"
                     and row.get("catalog_status") == "CATALOG_ENTRY_MISSING")
    return {
        "schema": "r32/catalog-registration-proposal-v1",
        "base_registry_sha256": report.get("registry_sha256"),
        "missing": missing,
        "snippet": "".join(f"  {name}:\n    status: available\n" for name in missing),
        "applied": False,
        "native_installed": False,
        "owner_grant_verified": False,
        "next": "REVIEW_BASE_SHA_AND_SUPPORTED_PROVIDER_REGISTRATION_ROUTE",
    }

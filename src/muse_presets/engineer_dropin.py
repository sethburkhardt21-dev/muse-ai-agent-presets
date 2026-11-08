"""Create-only native-format Software Engineer bundle with REAL local Claim Gate.

This never authenticates a personal Muse host, registers a native skill,
spawns a chat, installs hooks or modifies an existing owner's files.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from .catalog import DOCUMENTS
from .engineering_pack import _require_new, inspect_engineer_pack, stage_engineer_pack
from .native_canary import _no_duplicate_json, _reject_constant, _serialized
from .native_skill_binding import _unsafe_source_path

SCHEMA = "r33/software-engineer-native-format-v1"
SKILLS = {
    "claim-gate": ("engineering_claim_gate", "Scoped local Claim Gate and UNKNOWN recovery"),
    "provenance-vault": ("engineering_source_provenance", "Bounded source pins and provenance review"),
    "iron-ledger": ("engineering_evidence_receipt_consumer", "Read-only existing evidence receipt review"),
}
SUBCHATS = {
    "diagnostics": {
        "purpose": "Reproduce reported behavior from exact inputs and source revision",
        "actions": "Inspect user-approved logs and source, construct an isolated failing test, record the original baseline and bounded hypotheses",
        "stop": "Do not patch or execute external effects before an observed failing case and task authority",
        "handoff": "implementation",
    },
    "implementation": {
        "purpose": "Produce the smallest maintainable engineering change with regression tests",
        "actions": "Use a disposable owned worktree, pin source, test RED then GREEN, inspect diff, enforce Claim Gate for separately approved work",
        "stop": "Changed source revision, denied owner scope or ambiguous effect means HOLD, never blind retry",
        "handoff": "verification",
    },
    "verification": {
        "purpose": "Independently scrutinize a change and original recipient result",
        "actions": "Re-run tests on source-pinned candidate, probe negative cases, inspect artifacts and actual readback; distinguish independent verifier from self-check",
        "stop": "Missing original provider receipt, rights, OS support or external witness prevents COMPLETE",
        "handoff": "diagnostics",
    },
}

README = """# Portable Software Engineer: native-format source bundle

This is a source-pinned generic engineering role with REAL local Claim Gate,
Provenance Vault and read-only Iron Ledger source. It is NOT a natively
installed Muse agent, publisher-signed release or authorized external executor.

- engine/ is the unchanged source-pinned Software Engineer runtime package.
- system-files/ is a clean neutral receiving-owner profile draft; never
  overwrite another user's system files or native memory.
- subchats/ contains three independent nonempty role/context/memory contracts.
  No provider chat IDs have been created or authenticated.
- custom-skills/ contains three native-style skill descriptor pairs. Their
  config/skills.yaml entries are DISABLED until authorized host admission.
- custom-skills/engineering_claim_gate/run.py --canary runs an ACTUAL local
  Claim Gate test on POSIX using temporary fictional state. Never a live effect.
- hooks/HOOKS.json and config/host-binding.json are explicitly disabled.
- receipts/R33_DROPIN_RECEIPT.json is a local source checksum record, not a
  publisher signature or owner-issued grant.

See engine/receipts/PACK_RECEIPT.json for source provenance and rights HOLDS.
The installed host API, subchat bindings, native discovery, model-selected
skill invocation and independent recipient readback remain unverified.
Do not install the donor's original persona, memory, secrets or system state.
"""

BINDING = {
    "schema": "r33/engineer-host-binding-v1",
    "host_profile": "personal-hatch",
    "owner_user_id": None,
    "provider_session_id": None,
    "agent_id": None,
    "registered": False,
    "installed": False,
    "model_invocation_verified": False,
    "recipient_readback_verified": False,
    "external_effect_authorized": False,
}
CAPABILITIES = {
    "schema": "r33/engineer-capabilities-v1",
    "local_claim_gate": "POSIX_ONLY_SOURCE_TESTED",
    "local_provenance_vault": "READ_ONLY_SOURCE_TESTED",
    "local_iron_ledger": "READ_ONLY_EXISTING_EVIDENCE_LEDGER_CONSUMER",
    "host_grants": "NOT_RUN",
    "native_muse": "UNVERIFIED",
    "hooks_enabled": False,
    "cron_enabled": False,
    "family_link_enabled": False,
    "model_routing_enabled": False,
    "money_required": False,
}
HOOKS = {
    "schema": "r33/hooks-proposal-v1",
    "enabled": False,
    "installed": False,
    "event_handlers": [],
    "scheduler_enabled": False,
}
EXTRA_SYSTEM = {
    "CONNECTORS.md": "# Optional connectors\n\nOnly install and grant receiving-owner-approved connectors through the actual host. No connected accounts or token secrets are included. Refuse unsupported write permissions.\n",
    "BROWSER.md": "# Browser boundaries\n\nBrowser actions require a supported authenticated receiving-host browser, explicit scope and fresh page observations. No credential extraction, unknown targets, or automatic publication.\n",
    "VOICE.md": "# Voice boundaries\n\nNo voice identity, private recordings or speech device is included. Voice is optional and off until receiving-owner configuration and supported client acceptance.\n",
}

RUNNER = r'''#!/usr/bin/env python3
"""Disposable REAL local Claim Gate canary. POSIX only; NO native host effects."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def _print(status: str, observed=None, *, success=False) -> int:
    print(json.dumps({
        "schema": "r33/engineer-local-claim-canary-v1",
        "status": status,
        "observed": observed or [],
        "native_muse_invoked": False,
        "host_authenticated": False,
        "external_effect_authorized": False,
        "recipient_readback_verified": False,
        "local_synthetic_state_only": True,
    }, sort_keys=True))
    return 0 if success else 2


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--canary", action="store_true")
    args = parser.parse_args(argv)
    if not args.canary:
        return _print("EXPLICIT_DISPOSABLE_CANARY_REQUIRED")
    if os.name != "posix":
        return _print("UNSUPPORTED_PLATFORM_POSIX_FCNTL_REQUIRED")
    root = Path(__file__).resolve().parents[2]
    cli = root / "engine" / "runtime" / "claim-gate" / "engineering_claim_gate.py"
    if not cli.is_file() or cli.is_symlink():
        return _print("SOURCE_ENGINE_MISSING")
    with tempfile.TemporaryDirectory(prefix="r33-generic-claim-canary-") as td:
        home = Path(td)
        state = home / "state"
        source = home / "source"
        state.mkdir()
        source.mkdir()
        (source / "fictional.txt").write_bytes(b"synthetic engineering repair")
        common = [sys.executable, "-I", "-B", str(cli), "--state-dir", str(state),
                  "--scope", "generic-canary", "--claim-id", "fictional-001"]
        calls = [
            ["claim", "--source-root", str(source), "--payload", "fictional.txt"],
            ["claim", "--source-root", str(source), "--payload", "fictional.txt"],
            ["hold-unknown", "--reason", "synthetic result not observed"],
            ["inspect"],
        ]
        statuses = []
        for args in calls:
            try:
                run = subprocess.run(common + args, capture_output=True,
                                     text=True, timeout=12, check=False)
                if run.returncode != 0:
                    return _print("LOCAL_CANARY_REFUSED")
                row = json.loads(run.stdout)
                if any(row.get(k) is not False for k in
                       ("native_muse_invoked", "external_effect_authorized",
                        "external_effect_performed", "recipient_acknowledged")):
                    return _print("UNEXPECTED_HOST_EFFECT_CLAIM")
                statuses.append(row["status"])
            except (OSError, ValueError, KeyError, subprocess.TimeoutExpired):
                return _print("LOCAL_CANARY_FAILED")
        expected = ["LOCAL_CLAIM_RECORDED", "LOCAL_CLAIM_REUSED",
                    "LOCAL_UNKNOWN_HELD", "LOCAL_CLAIM_OBSERVED"]
        if statuses != expected:
            return _print("LOCAL_CANARY_STATUS_MISMATCH")
        return _print("LOCAL_CLAIM_GATE_CANARY_PASSED", statuses, success=True)


if __name__ == "__main__":
    raise SystemExit(main())
'''


SCRIPT_DOCTOR = r'''#!/usr/bin/env python3
"""Standalone read-only self-hash doctor; this is NOT publisher verification."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path


def _reject_duplicate(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("DUPLICATE_RECEIPT_KEY")
        result[key] = value
    return result


def _bad_constant(_value):
    raise ValueError("NONSTANDARD_JSON_CONSTANT")


def _report(status, matched=False):
    print(json.dumps({
        "schema": "r33/engineer-offline-doctor-v1",
        "status": status,
        "local_files_matched": matched,
        "evidence_grade": "LOCAL_SELF_HASH_ONLY_NOT_PUBLISHER_ATTESTATION",
        "native_authenticated": False,
        "provider_invocation_verified": False,
        "external_effect_authorized": False,
    }, sort_keys=True))
    return 0 if matched else 2


def main():
    root = Path(__file__).resolve().parents[1]
    if (root / "STAGING_INCOMPLETE").exists():
        return _report("INCOMPLETE_STAGE")
    try:
        receipt = root / "receipts" / "R33_DROPIN_RECEIPT.json"
        if receipt.is_symlink() or not receipt.is_file() or receipt.stat().st_size > 30000:
            return _report("REVIEW_REQUIRED")
        data = json.loads(receipt.read_text(encoding="utf-8"),
                          object_pairs_hook=_reject_duplicate, parse_constant=_bad_constant)
        keys = {"schema", "role_id", "source_file_sha256", "directories",
                "native_installed", "host_authenticated", "external_effect_authorized",
                "scheduler_enabled", "license_disposition", "evidence_grade"}
        if (type(data) is not dict or set(data) != keys or
            data["schema"] != "r33/software-engineer-native-format-v1" or
            data["role_id"] != "software-engineer" or
            any(data[k] is not False for k in
                ("native_installed", "host_authenticated", "external_effect_authorized",
                 "scheduler_enabled")) or
            data["license_disposition"] != "PRIVATE_REVIEW_ONLY" or
            data["evidence_grade"] != "LOCAL_SOURCE_AND_ENGINE_ONLY"):
            return _report("REVIEW_REQUIRED")
        hashes = data["source_file_sha256"]
        if type(hashes) is not dict or len(hashes) > 200:
            return _report("REVIEW_REQUIRED")
        files = set()
        dirs = {"."}
        for parent, subdirs, entries in os.walk(root, followlinks=False):
            folder = Path(parent)
            for name in subdirs:
                child = folder / name
                if child.is_symlink() or (
                    hasattr(child, "is_junction") and child.is_junction()
                ):
                    return _report("REVIEW_REQUIRED")
                dirs.add(child.relative_to(root).as_posix())
            for name in entries:
                file = folder / name
                if file.is_symlink() or not file.is_file():
                    return _report("REVIEW_REQUIRED")
                files.add(file.relative_to(root).as_posix())
        if files != set(hashes) | {"receipts/R33_DROPIN_RECEIPT.json"}:
            return _report("REVIEW_REQUIRED")
        if dirs != set(data["directories"]):
            return _report("REVIEW_REQUIRED")
        for relative, expected in hashes.items():
            if not isinstance(relative, str) or not isinstance(expected, str):
                return _report("REVIEW_REQUIRED")
            path = Path(relative)
            if (path.is_absolute() or ".." in path.parts or
                len(expected) != 64 or any(c not in "0123456789abcdef" for c in expected)):
                return _report("REVIEW_REQUIRED")
            member = root / path
            if (member.is_symlink() or not member.is_file() or
                member.stat().st_size > 5_000_000 or
                hashlib.sha256(member.read_bytes()).hexdigest() != expected):
                return _report("REVIEW_REQUIRED")
    except (OSError, ValueError, TypeError, KeyError):
        return _report("REVIEW_REQUIRED")
    return _report("LOCAL_SELF_HASH_MATCH", True)


if __name__ == "__main__":
    raise SystemExit(main())
'''

SCRIPTS_README = """# Offline scripts

Use python -I -B scripts/doctor.py to verify local self-checksum continuity.
This is not a publisher signature; a malicious actor who can change the
manifest and all files may forge a self-consistent packet.

On POSIX Python 3.12+ you can execute an ACTUAL Claim Gate using fictional
temporary state:

    python3 -I -B custom-skills/engineering_claim_gate/run.py --canary

On native Windows the original source-derived engine must refuse. Neither
command invokes Muse, registers a skill, uses a real recipient or issues
permissions. All original user state remains untouched.
"""

def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _skill_body(source: bytes, name: str, description: str) -> bytes:
    text = source.decode("utf-8")
    if text.startswith("---\n"):
        parts = text.split("\n---\n", 1)
        if len(parts) != 2:
            raise ValueError("UNTERMINATED_SOURCE_FRONTMATTER")
        text = parts[1].lstrip("\n")
    if not text.lstrip().startswith("#"):
        raise ValueError("SKILL_SOURCE_BODY_MISSING")
    header = f"---\nname: {name}\ndescription: {description}\n---\n\n"
    notice = ("## Receiving-host binding\n\nThis is source-only. The local "
              "skills.yaml entry is disabled. No owner/native grant exists. "
              "Use only in a disposable test workspace with explicit approval. "
              "Do not interpret local receipt files as host identity.\n\n")
    if name == "engineering_claim_gate":
        notice += ("The runnable local test is python -B "
                   "custom-skills/engineering_claim_gate/run.py --canary. "
                   "It exercises the real pinned Claim Gate in temporary "
                   "fictional state on POSIX, never an external tool.\n\n")
    return (header + notice + text.rstrip() + "\n").encode("utf-8")


def _sidecars(engine: Path) -> dict[str, bytes]:
    result: dict[str, bytes] = {"README.md": README.encode("utf-8")}
    profile = engine / "profile"
    for name in (*DOCUMENTS, "ROLE_PLAYBOOK.md", "FAMILY_LINK.json"):
        path = profile / name
        if not path.is_file() or path.is_symlink():
            raise ValueError("ENGINE_PROFILE_MISSING")
        result[f"system-files/{name}"] = path.read_bytes()
    for name, text in EXTRA_SYSTEM.items():
        result[f"system-files/{name}"] = text.encode("utf-8")
    for path_component, (name, description) in sorted(SKILLS.items()):
        source_dir = engine / "skills" / path_component
        source_yaml = (source_dir / "skill.yaml").read_bytes()
        if f"name: {name}\n".encode("utf-8") not in source_yaml:
            raise ValueError("UNEXPECTED_SKILL_ID")
        prefix = f"custom-skills/{name}/"
        result[prefix + "skill.yaml"] = source_yaml
        result[prefix + "SKILL.md"] = _skill_body(
            (source_dir / "SKILL.md").read_bytes(), name, description
        )
    result["custom-skills/engineering_claim_gate/run.py"] = RUNNER.encode("utf-8")
    result["scripts/doctor.py"] = SCRIPT_DOCTOR.encode("utf-8")
    result["scripts/README.md"] = SCRIPTS_README.encode("utf-8")
    result["config/skills.yaml"] = (
        "version: 1\nentries:\n" +
        "".join(f"  {name}:\n    status: disabled\n"
                for name in sorted(name for name, _ in SKILLS.values()))
    ).encode("utf-8")
    result["config/host-binding.json"] = _serialized(BINDING)
    result["config/capabilities.json"] = _serialized(CAPABILITIES)
    manifest = {"schema": "r33/engineer-subchats-v1", "subchats": {}}
    for role, attrs in sorted(SUBCHATS.items()):
        prefix = f"subchats/{role}/"
        result[prefix + "ROLE.md"] = (
            "# " + role.title() + "\n\n" + attrs["purpose"] + "\n\n"
            "Native identity is unbound. Work only on owner-approved "
            "synthetic or source-pinned tasks.\n"
        ).encode("utf-8")
        result[prefix + "CONTEXT.md"] = (
            "# Context contract\n\n" + attrs["actions"] + "\n\n"
            "No parent transcript, donor identity, secrets or private context "
            "is imported. Source pin and permissions must be verified again "
            "at the actual host entrypoint.\n"
        ).encode("utf-8")
        result[prefix + "MEMORY.md"] = (
            "# Memory contract\n\nFresh neutral package. No personal memory "
            "records. Persist only explicitly approved, source-scoped "
            "outcomes in receiving-owner-controlled storage.\n"
        ).encode("utf-8")
        result[prefix + "TOOLS.md"] = (
            "# Tools and refusal\n\n" + attrs["stop"] + "\n\n"
            "Use provider-native tools only after discovering their "
            "schemas, real owner identity and current grants.\n"
        ).encode("utf-8")
        row = {
            "schema": "r33/unbound-subchat-v1",
            "role": role,
            "purpose": attrs["purpose"],
            "handoff_to": attrs["handoff"],
            "native_chat_id": None,
            "native_loaded": False,
            "enabled": False,
            "memory_owner_id": None,
        }
        result[prefix + "SUBCHAT.json"] = _serialized(row)
        manifest["subchats"][role] = {"path": f"subchats/{role}",
                                      "native_chat_id": None, "enabled": False}
    result["config/subchats.json"] = _serialized(manifest)
    result["hooks/HOOKS.json"] = _serialized(HOOKS)
    return result


def _tree(root: Path) -> tuple[set[str], set[str]]:
    files: set[str] = set()
    dirs: set[str] = {"."}
    for parent, subdirs, filenames in os.walk(root, followlinks=False):
        here = Path(parent)
        for name in subdirs:
            node = here / name
            if node.is_symlink() or (hasattr(node, "is_junction") and node.is_junction()):
                raise ValueError("UNTRUSTED_DIRECTORY_LINK")
            dirs.add(node.relative_to(root).as_posix())
        for name in filenames:
            node = here / name
            if not node.is_file() or node.is_symlink():
                raise ValueError("UNTRUSTED_FILE")
            files.add(node.relative_to(root).as_posix())
    return files, dirs


def _expected_manifest(root: Path, sidecars: dict[str, bytes]) -> dict:
    engine = root / "engine"
    files = {}
    for file in engine.rglob("*"):
        if file.is_file():
            if file.is_symlink():
                raise ValueError("ENGINE_SOURCE_LINK")
            files[file.relative_to(root).as_posix()] = _sha(file.read_bytes())
    for relative, contents in sidecars.items():
        files[relative] = _sha(contents)
    paths = {*files, "receipts/R33_DROPIN_RECEIPT.json"}
    directories = {"."}
    for relative in paths:
        part = Path(relative).parent
        while str(part) not in (".", ""):
            directories.add(part.as_posix())
            part = part.parent
    return {
        "schema": SCHEMA,
        "role_id": "software-engineer",
        "source_file_sha256": dict(sorted(files.items())),
        "directories": sorted(directories),
        "native_installed": False,
        "host_authenticated": False,
        "external_effect_authorized": False,
        "scheduler_enabled": False,
        "license_disposition": "PRIVATE_REVIEW_ONLY",
        "evidence_grade": "LOCAL_SOURCE_AND_ENGINE_ONLY",
    }


def stage_engineer_dropin(destination: Path) -> dict:
    """Source-pinned nested engine and isolated native-format sidecar."""
    target = _require_new(Path(destination))
    target.mkdir(exist_ok=False)
    (target / "STAGING_INCOMPLETE").write_text(
        "Do not install: source-only staging incomplete.\n", encoding="utf-8"
    )
    engine = target / "engine"
    stage_engineer_pack(engine)
    if inspect_engineer_pack(engine)["status"] != "LOCAL_MATCH":
        raise ValueError("ENGINE_PACK_NOT_MATCHED")
    sidecars = _sidecars(engine)
    for relative, body in sorted(sidecars.items()):
        file = target / relative
        file.parent.mkdir(parents=True, exist_ok=True)
        with file.open("xb") as handle:
            handle.write(body)
    receipt = _expected_manifest(target, sidecars)
    report_file = target / "receipts" / "R33_DROPIN_RECEIPT.json"
    report_file.parent.mkdir(exist_ok=False)
    with report_file.open("xb") as handle:
        handle.write(_serialized(receipt))
    (target / "STAGING_INCOMPLETE").unlink()
    if inspect_engineer_dropin(target)["status"] != "LOCAL_DROPIN_MATCH":
        raise ValueError("SOURCE_READBACK_REFUSED")
    return {
        "status": "SOURCE_ONLY_NATIVE_FORMAT_STAGED",
        "role_id": "software-engineer",
        "custom_skills": sorted(name for name, _ in SKILLS.values()),
        "subchats": sorted(SUBCHATS),
        "native_installed": False,
        "external_effect_authorized": False,
    }


def inspect_engineer_dropin(destination: Path) -> dict:
    """Require source-pinned unchanged real engine, exact sidecars and closed tree."""
    reject = {"status": "REVIEW_REQUIRED", "native_installed": False,
              "external_effect_authorized": False}
    root = Path(destination)
    if _unsafe_source_path(root) or not root.is_dir():
        return reject
    if (root / "STAGING_INCOMPLETE").exists() or (root / "STAGING_INCOMPLETE").is_symlink():
        return {**reject, "status": "INCOMPLETE_STAGE"}
    try:
        if inspect_engineer_pack(root / "engine")["status"] != "LOCAL_MATCH":
            return reject
        sidecars = _sidecars(root / "engine")
        expected = _expected_manifest(root, sidecars)
        path = root / "receipts" / "R33_DROPIN_RECEIPT.json"
        if not path.is_file() or path.is_symlink() or path.stat().st_size > 30000:
            return reject
        data = json.loads(path.read_bytes(), object_pairs_hook=_no_duplicate_json,
                          parse_constant=_reject_constant)
        if type(data) is not dict or data != expected:
            return reject
        existing, directories = _tree(root)
        expected_files = set(expected["source_file_sha256"]) | {
            "receipts/R33_DROPIN_RECEIPT.json"
        }
        if existing != expected_files or directories != set(expected["directories"]):
            return reject
        for relative, original in sidecars.items():
            if (root / relative).read_bytes() != original:
                return reject
        for relative, digest in expected["source_file_sha256"].items():
            if _sha((root / relative).read_bytes()) != digest:
                return reject
        if path.read_bytes() != _serialized(expected):
            return reject
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
        return reject
    return {
        "status": "LOCAL_DROPIN_MATCH",
        "role_id": "software-engineer",
        "native_installed": False,
        "external_effect_authorized": False,
    }

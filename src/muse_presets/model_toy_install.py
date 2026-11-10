"""Explicit opt-in staging for the bounded toy-training extension.

This module stages reviewed source only. It does not install a native agent,
train a model, start a service, modify the legacy Model Builder role, or grant
external effects. Hashes provide local continuity, not issuer authentication.
Interrupted output is retained and cannot be overwritten or retried in place.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path, PurePosixPath
import stat
import sys

if __package__:
    from . import model_toy_bundle as bundle
    from . import model_toy_math as engine
    from . import model_toy_sourcekit as kit
else:
    # A fresh extraction runs without the repository or an installed package.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import model_toy_bundle as bundle
    import model_toy_math as engine
    import model_toy_sourcekit as kit

RECEIPT = "INSTALL_RECEIPT.json"
MARKER = "STAGING_INCOMPLETE"
SCHEMA = "r61/toy-extension-stage-v1"
MARKER_BYTES = b"INCOMPLETE: inspect this run; never retry into this destination.\n"
MAX_MEMBERS = 64


def _canonical_members() -> dict[str, bytes]:
    members = kit._members()
    if type(members) is not dict or not 1 <= len(members) <= MAX_MEMBERS:
        raise engine.Refused("CANONICAL_MEMBER_SET_INVALID")
    names = set()
    total = 0
    for name, raw in members.items():
        if type(name) is not str or type(raw) is not bytes:
            raise engine.Refused("CANONICAL_MEMBER_TYPE_INVALID")
        parts = PurePosixPath(name).parts
        if (not parts or name.startswith("/") or ".." in parts or "\\" in name
                or ":" in name or name in (RECEIPT, MARKER)
                or name.casefold() in names or len(raw) > kit.MAX_FILE):
            raise engine.Refused("CANONICAL_MEMBER_PATH_INVALID")
        names.add(name.casefold())
        total += len(raw)
    if total > kit.MAX_TOTAL:
        raise engine.Refused("CANONICAL_MEMBER_SIZE_BUDGET")
    return dict(members)


def _directories(names: set[str]) -> set[str]:
    directories = {"."}
    for name in names:
        parent = PurePosixPath(name).parent
        while str(parent) != ".":
            directories.add(parent.as_posix())
            parent = parent.parent
    return directories


def _receipt(members: dict[str, bytes]) -> bytes:
    return engine.canonical_json({
        "schema": SCHEMA,
        "role_id": "model-builder",
        "scope": "OPT_IN_SYNTHETIC_TOY_EXTENSION_ONLY",
        "files_sha256": {name: engine.digest(raw) for name, raw in sorted(members.items())},
        "directories": sorted(_directories(set(members) | {RECEIPT})),
        "native_installed": False,
        "external_effect_authorized": False,
        "training_started": False,
        "training_service_authorized": False,
        "publisher_authenticated": False,
        "independent_fleet_verified": False,
        "llm_training_performed": False,
        "os_sandboxed": False,
        "legacy_role_modified": False,
    })


def _inspect_tree(root: Path, members: dict[str, bytes], receipt: bytes, *,
                  incomplete: bool = False) -> None:
    expected = set(members) | {RECEIPT}
    if incomplete:
        expected.add(MARKER)
    files, directories = set(), {"."}
    if not root.is_dir():
        raise engine.Refused("EXTENSION_ROOT_MISSING")
    for parent, subdirs, children in os.walk(root, followlinks=False):
        folder = Path(parent)
        for name in subdirs:
            path = bundle._admitted_path(folder / name)
            if not stat.S_ISDIR(path.lstat().st_mode):
                raise engine.Refused("EXTENSION_DIRECTORY_TYPE_REFUSED")
            directories.add(path.relative_to(root).as_posix())
        for name in children:
            path = bundle._admitted_path(folder / name)
            files.add(path.relative_to(root).as_posix())
            if len(files) > MAX_MEMBERS + 2:
                raise engine.Refused("EXTENSION_FILE_SET_BUDGET")
    if files != expected:
        raise engine.Refused("EXTENSION_FILE_SET_MISMATCH")
    if directories != _directories(expected):
        raise engine.Refused("EXTENSION_DIRECTORY_SET_MISMATCH")
    actual_receipt = bundle._read_regular(root / RECEIPT)
    engine.strict_json(actual_receipt)  # duplicate keys/nonstandard JSON refused
    if actual_receipt != receipt:
        raise engine.Refused("EXTENSION_RECEIPT_NOT_CANONICAL")
    for name, raw in members.items():
        if bundle._read_regular(root / name, limit=kit.MAX_FILE) != raw:
            raise engine.Refused("EXTENSION_SOURCE_DRIFT:" + name)
    if incomplete and bundle._read_regular(root / MARKER) != MARKER_BYTES:
        raise engine.Refused("EXTENSION_INCOMPLETE_MARKER_DRIFT")


def _restore_marker(root: Path) -> None:
    """Best-effort fail-closed marking after our own late completion failure.

    Never delete source or replace an existing marker. This is not an atomic
    hostile-same-user filesystem sandbox or a power-loss transaction proof.
    """
    try:
        path = bundle._admitted_path(root / MARKER)
        if not path.exists():
            bundle._write_new(path, MARKER_BYTES)
    except (OSError, engine.Refused):
        pass


def stage_extension(destination: Path, *, include_toy_training: bool = False) -> dict:
    """Create one new source extension only after explicit, exact boolean opt-in."""
    if include_toy_training is not True:
        raise engine.Refused("EXPLICIT_TOY_OPT_IN_REQUIRED")
    target = bundle._new_path(Path(destination))
    members = _canonical_members()
    if _canonical_members() != members:
        raise engine.Refused("CANONICAL_SOURCE_CHANGED_DURING_PREFLIGHT")
    receipt = _receipt(members)
    target.mkdir(mode=0o700, exist_ok=False)
    try:
        bundle._write_new(target / MARKER, MARKER_BYTES)
        for name, raw in sorted(members.items()):
            path = target / name
            path.parent.mkdir(parents=True, exist_ok=True)
            bundle._write_new(path, raw)
        bundle._write_new(target / RECEIPT, receipt)
        _inspect_tree(target, members, receipt, incomplete=True)
        if _canonical_members() != members:
            raise engine.Refused("CANONICAL_SOURCE_CHANGED_BEFORE_COMPLETION")
        (target / MARKER).unlink()
        _inspect_tree(target, members, receipt)
        if _canonical_members() != members:
            raise engine.Refused("CANONICAL_SOURCE_CHANGED_AFTER_READBACK")
    except BaseException:
        _restore_marker(target)
        raise
    return {
        "status": "SOURCE_ONLY_TOY_EXTENSION_STAGED",
        "scope": "OPT_IN_SYNTHETIC_TOY_EXTENSION_ONLY",
        "stage_receipt_sha256": engine.digest(receipt),
        "member_count": len(members) + 1,
        "training_started": False,
        "native_installed": False,
        "external_effect_authorized": False,
        "legacy_role_modified": False,
    }


def inspect_extension(root: Path, expected_stage_sha256: str) -> dict:
    """Read-only exact source comparison with an out-of-band stage receipt pin."""
    if not engine._sha(expected_stage_sha256):
        raise engine.Refused("STAGE_RECEIPT_PIN_REQUIRED")
    root = bundle._admitted_path(Path(root))
    if (root / MARKER).exists() or (root / MARKER).is_symlink():
        raise engine.Refused("INCOMPLETE_STAGE_HELD")
    original = bundle._read_regular(root / RECEIPT)
    if engine.digest(original) != expected_stage_sha256:
        raise engine.Refused("STAGE_RECEIPT_PIN_MISMATCH")
    members = _canonical_members()
    expected = _receipt(members)
    _inspect_tree(root, members, expected)
    if _canonical_members() != members:
        raise engine.Refused("CANONICAL_SOURCE_CHANGED_DURING_INSPECTION")
    if bundle._read_regular(root / RECEIPT) != original:
        raise engine.Refused("STAGE_RECEIPT_CHANGED_DURING_INSPECTION")
    return {
        "status": "LOCAL_TOY_EXTENSION_STAGE_MATCH",
        "stage_receipt_sha256": expected_stage_sha256,
        "member_count": len(members) + 1,
        "training_started": False,
        "native_installed": False,
        "external_effect_authorized": False,
        "publisher_authenticated": False,
        "legacy_role_modified": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="operation", required=True)
    stage = sub.add_parser("stage")
    stage.add_argument("--to", type=Path, required=True)
    stage.add_argument("--include-toy-training", action="store_true")
    inspect = sub.add_parser("inspect")
    inspect.add_argument("--root", type=Path, required=True)
    inspect.add_argument("--stage-sha256", required=True)
    args = parser.parse_args(argv)
    try:
        result = (stage_extension(args.to, include_toy_training=args.include_toy_training)
                  if args.operation == "stage" else
                  inspect_extension(args.root, args.stage_sha256))
        print(json.dumps(result, sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"status": "REFUSED", "reason": str(exc),
                          "native_installed": False,
                          "external_effect_authorized": False,
                          "training_started_by_stager": False}, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

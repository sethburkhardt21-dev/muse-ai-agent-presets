"""Create-only toy experiment evidence, recomputation and baseline restoration.

This is not a scheduler or transaction authority. Outputs are owned disposable
local artifacts. An incomplete directory is preserved and cannot be retried in
place. Checksums do not authenticate an external experimenter. All checkpoints
are non-executable JSON; no pickle, model download, subprocess or provider call.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import stat
import sys
from typing import Any

if __package__:
    from . import model_toy_math as engine
else:
    # A source-kit runner is imported only from its own explicitly reviewed path.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import model_toy_math as engine

Refused = engine.Refused
FILES = frozenset({"dataset.json", "config.json", "baseline.json", "candidate.json", "evaluation.json"})
MANIFEST = "MANIFEST.json"
MARKER = "STAGING_INCOMPLETE"
SCHEMA = "r60/toy-experiment-bundle-v1"


def runtime_pins() -> dict[str, str]:
    return {"math": engine.digest(Path(engine.__file__).read_bytes()),
            "bundle": engine.digest(Path(__file__).read_bytes())}


def _trusted_darwin_root_alias(path: Path) -> bool:
    """Admit only the standard root-owned Darwin root aliases.

    Mirrors the existing repository database_paths source predicate without
    requiring a repository import in an extracted extension kit. This is a
    narrow compatibility exception, not an atomic filesystem sandbox.
    """
    targets = {"/var": "/private/var", "/tmp": "/private/tmp", "/etc": "/private/etc"}
    target = targets.get(str(path))
    if sys.platform != "darwin" or target is None:
        return False
    try:
        return (path.is_symlink() and path.lstat().st_uid == 0
                and path.resolve(strict=True) == Path(target)
                and Path(target).is_dir())
    except (OSError, RuntimeError):
        return False


def _admitted_path(path: Path) -> Path:
    p = Path(path)
    if not p.is_absolute() or ".." in p.parts:
        raise Refused("ABSOLUTE_CANONICAL_PATH_REQUIRED")
    # Apply the Windows filename boundary even on POSIX so a validated local
    # artifact cannot acquire alternate-stream or device semantics when moved.
    # The anchor itself contains a drive colon / UNC separators on Windows.
    devices = {"CON", "PRN", "AUX", "NUL"}
    devices.update(f"{prefix}{suffix}" for prefix in ("COM", "LPT")
                   for suffix in "123456789¹²³")
    for component in p.parts:
        if component == p.anchor:
            continue
        if (component.endswith((".", " "))
                or any(char in '<>:"|?*\\' or ord(char) < 32 or ord(char) == 127
                       for char in component)
                or component.split(".", 1)[0].upper() in devices):
            raise Refused("PORTABLE_PATH_COMPONENT_REFUSED")
    for node in (p, *p.parents):
        junction = hasattr(node, "is_junction") and node.is_junction()
        if junction or (node.is_symlink() and not _trusted_darwin_root_alias(node)):
            raise Refused("LINKED_PATH_REFUSED")
    return p


def _read_regular(path: Path, *, limit: int = engine.MAX_JSON_BYTES) -> bytes:
    p = _admitted_path(path)
    try:
        before = p.lstat()
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or before.st_size > limit:
            raise Refused("REGULAR_BOUNDED_SINGLE_LINK_FILE_REQUIRED")
        fd = os.open(p, os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0))
        with os.fdopen(fd, "rb") as stream:
            opened = os.fstat(stream.fileno())
            if (opened.st_ino, opened.st_dev) != (before.st_ino, before.st_dev):
                raise Refused("READ_FILE_IDENTITY_CHANGED")
            raw = stream.read(limit + 1)
            after = os.fstat(stream.fileno())
        if (opened.st_size, opened.st_mtime_ns, opened.st_nlink) != (
                after.st_size, after.st_mtime_ns, after.st_nlink):
            raise Refused("READ_FILE_CHANGED")
        if len(raw) > limit:
            raise Refused("FILE_SIZE_BUDGET")
        return raw
    except OSError as exc:
        raise Refused("SOURCE_FILE_UNAVAILABLE") from exc


def _new_path(path: Path) -> Path:
    p = _admitted_path(path)
    if p.exists() or not p.parent.is_dir():
        raise Refused("DESTINATION_OCCUPIED_OR_PARENT_MISSING")
    return p


def _write_new(path: Path, data: bytes) -> None:
    # Exclusive creation never overwrites an owner path. Flush actual file bytes;
    # no assertion of Windows power-loss directory metadata durability is made.
    with path.open("xb") as output:
        output.write(data)
        output.flush()
        os.fsync(output.fileno())


def _result_bytes(raw: bytes, *, steps: int, learning_rate: str) -> tuple[dict[str, bytes], dict]:
    data = engine.strict_json(raw)
    result = engine.fit_experiment(data, steps=steps, learning_rate=learning_rate)
    blobs = {"dataset.json": raw, "config.json": engine.canonical_json(result["config"]),
             "baseline.json": engine.canonical_json(result["baseline"]),
             "candidate.json": engine.canonical_json(result["candidate"]),
             "evaluation.json": engine.canonical_json(result["evaluation"])}
    return blobs, result


def _manifest(blobs: dict[str, bytes], pins: dict[str, str]) -> dict:
    return {"schema": SCHEMA, "scope": engine.SCOPE,
            "status": "LOCAL_TOY_EXPERIMENT_RECORDED",
            "files_sha256": {name: engine.digest(raw) for name, raw in sorted(blobs.items())},
            "runtime_sha256": pins, "final_status": "HELD_UNEVALUATED",
            "promotion_authorized": False, "native_muse_invoked": False,
            "external_effect_authorized": False, "independent_reviewer_verified": False,
            "os_sandboxed": False, "power_loss_durability_proven": False}


def _current_runtime() -> dict[str, str]:
    pins = runtime_pins()
    if pins != _LOADED_SOURCE_PINS:
        raise Refused("RUNTIME_SOURCE_CHANGED_AFTER_IMPORT")
    return pins


def run_experiment(dataset: Path, expected_sha256: str, destination: Path, *,
                   steps: int = 64, learning_rate: str = "0.05",
                   reviewed_data: bool = False) -> dict:
    """Actually optimize a toy model, writing only a new disposable directory."""
    if reviewed_data is not True:
        raise Refused("OPERATOR_REVIEWED_DATA_REQUIRED")
    pins = _current_runtime()
    if not engine._sha(expected_sha256):
        raise Refused("INPUT_SHA256_PIN_REQUIRED")
    target = _new_path(Path(destination))
    raw = _read_regular(Path(dataset))
    if engine.digest(raw) != expected_sha256:
        raise Refused("DATASET_PIN_MISMATCH")
    blobs, result = _result_bytes(raw, steps=steps, learning_rate=learning_rate)
    if _current_runtime() != pins:
        raise Refused("RUNTIME_DRIFT_DURING_COMPUTATION")
    target.mkdir(mode=0o700, exist_ok=False)
    _write_new(target / MARKER, b"INCOMPLETE: inspect effects; never retry into this path.\n")
    for name in ("dataset.json", "config.json", "baseline.json", "candidate.json", "evaluation.json"):
        _write_new(target / name, blobs[name])
    manifest = engine.canonical_json(_manifest(blobs, pins))
    _write_new(target / MANIFEST, manifest)
    if _current_runtime() != pins:
        raise Refused("RUNTIME_DRIFT_BEFORE_COMPLETION")
    (target / MARKER).unlink()  # only this run's own completeness marker
    verified = verify_bundle(target, engine.digest(manifest))
    return {"status": "LOCAL_TOY_EXPERIMENT_RECORDED", "scope": engine.SCOPE,
            "receipt_sha256": engine.digest(manifest),
            "candidate_sha256": engine.digest(blobs["candidate.json"]),
            "baseline_sha256": engine.digest(blobs["baseline.json"]),
            "optimizer_steps": result["candidate"]["optimizer_steps"],
            "evaluation": result["evaluation"],
            "readback_status": verified["status"],
            "promotion_authorized": False, "native_muse_invoked": False,
            "external_effect_authorized": False}


def verify_bundle(directory: Path, expected_receipt_sha256: str) -> dict:
    """Recompute the bounded optimization and metrics, not just local self-hashes."""
    pins = _current_runtime()
    root = _admitted_path(directory)
    if not root.is_dir():
        raise Refused("BUNDLE_DIRECTORY_MISSING")
    if (root / MARKER).exists() or (root / MARKER).is_symlink():
        raise Refused("INCOMPLETE_BUNDLE_UNKNOWN_HOLD")
    if {p.name for p in root.iterdir()} != FILES | {MANIFEST}:
        raise Refused("BUNDLE_FILE_SET_MISMATCH")
    if not engine._sha(expected_receipt_sha256):
        raise Refused("RECEIPT_PIN_REQUIRED")
    manifest_raw = _read_regular(root / MANIFEST)
    if engine.digest(manifest_raw) != expected_receipt_sha256:
        raise Refused("RECEIPT_PIN_MISMATCH")
    manifest = engine.strict_json(manifest_raw)
    # Validate a closed authority contract before inspecting source metrics.
    prototype = _manifest({name: b"" for name in FILES}, pins)
    if set(manifest) != set(prototype):
        raise Refused("MANIFEST_FIELDS_MISMATCH")
    for key in set(prototype) - {"files_sha256"}:
        if type(manifest[key]) is not type(prototype[key]) or manifest[key] != prototype[key]:
            raise Refused("RUNTIME_PIN_MISMATCH" if key == "runtime_sha256" else "MANIFEST_POLICY_MISMATCH")
    claimed = manifest["files_sha256"]
    if type(claimed) is not dict or set(claimed) != FILES:
        raise Refused("MANIFEST_FILE_SET_MISMATCH")
    actual = {name: _read_regular(root / name) for name in sorted(FILES)}
    if any(not engine._sha(claimed[name]) or engine.digest(actual[name]) != claimed[name] for name in FILES):
        raise Refused("ARTIFACT_PIN_MISMATCH")
    config = engine.strict_json(actual["config.json"])
    if set(config) != {"schema", "steps", "learning_rate"} or config["schema"] != "r60/toy-training-config-v1":
        raise Refused("CONFIG_SCHEMA_MISMATCH")
    recomputed, result = _result_bytes(actual["dataset.json"], steps=config["steps"],
                                      learning_rate=config["learning_rate"])
    if recomputed != actual:
        raise Refused("CHECKPOINT_OR_EVALUATION_RECOMPUTATION_MISMATCH")
    if engine.canonical_json(_manifest(actual, pins)) != manifest_raw:
        raise Refused("MANIFEST_CANONICAL_BYTES_MISMATCH")
    if _current_runtime() != pins:
        raise Refused("RUNTIME_DRIFT_DURING_VERIFICATION")
    return {"status": "LOCAL_TOY_BUNDLE_RECOMPUTED", "scope": engine.SCOPE,
            "receipt_sha256": expected_receipt_sha256,
            "optimizer_steps": result["candidate"]["optimizer_steps"],
            "baseline_sha256": engine.digest(actual["baseline.json"]),
            "candidate_sha256": engine.digest(actual["candidate.json"]),
            "evaluation": result["evaluation"], "final_status": "HELD_UNEVALUATED",
            "promotion_authorized": False, "native_muse_invoked": False,
            "external_effect_authorized": False, "independent_reviewer_verified": False}


def restore_baseline(directory: Path, expected_receipt_sha256: str, destination: Path) -> dict:
    """Restore exact baseline JSON to a NEW path; never alter the original bundle."""
    target = _new_path(destination)
    root = _admitted_path(directory)
    if target.is_relative_to(root):
        raise Refused("RESTORATION_MUST_NOT_MUTATE_EVIDENCE_BUNDLE")
    verified = verify_bundle(root, expected_receipt_sha256)
    raw = _read_regular(root / "baseline.json")
    if engine.digest(raw) != verified["baseline_sha256"]:
        raise Refused("BASELINE_CHANGED_AFTER_VERIFICATION")
    baseline = engine.strict_json(raw)
    engine.validate_checkpoint(baseline)
    if baseline["optimizer_steps"] != 0 or baseline["kind"] != "baseline":
        raise Refused("BASELINE_ROLLBACK_LINEAGE_INVALID")
    _write_new(target, raw)
    if _read_regular(target) != raw:
        raise Refused("RESTORE_READBACK_BYTES_DIFFER")
    return {"status": "BASELINE_RESTORED_TO_NEW_FILE", "sha256": engine.digest(raw),
            "source_receipt_sha256": expected_receipt_sha256,
            "optimizer_steps": 0, "promotion_authorized": False,
            "external_effect_authorized": False, "native_muse_invoked": False}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="operation", required=True)
    run = sub.add_parser("run", help="bounded real toy-model optimization")
    run.add_argument("--dataset", type=Path, required=True)
    run.add_argument("--dataset-sha256", required=True)
    run.add_argument("--to", type=Path, required=True)
    run.add_argument("--steps", type=int, default=64)
    run.add_argument("--learning-rate", default="0.05")
    run.add_argument("--reviewed-data", action="store_true")
    for command in ("verify", "restore-baseline"):
        p = sub.add_parser(command)
        p.add_argument("--bundle", type=Path, required=True)
        p.add_argument("--receipt-sha256", required=True)
        if command == "restore-baseline":
            p.add_argument("--to", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.operation == "run":
            report = run_experiment(args.dataset, args.dataset_sha256, args.to,
                                    steps=args.steps, learning_rate=args.learning_rate,
                                    reviewed_data=args.reviewed_data)
        elif args.operation == "verify":
            report = verify_bundle(args.bundle, args.receipt_sha256)
        else:
            report = restore_baseline(args.bundle, args.receipt_sha256, args.to)
        print(json.dumps(report, sort_keys=True, allow_nan=False))
        return 0
    except (Refused, OSError, ValueError, TypeError, KeyError) as exc:
        print(json.dumps({"status": "REFUSED", "reason": str(exc),
                          "native_muse_invoked": False, "promotion_authorized": False,
                          "external_effect_authorized": False}, sort_keys=True))
        return 2


_LOADED_SOURCE_PINS = runtime_pins()

if __name__ == "__main__":
    raise SystemExit(main())

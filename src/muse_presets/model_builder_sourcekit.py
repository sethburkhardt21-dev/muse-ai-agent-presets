"""Self-contained Model Builder ZIP, reusing the original disabled-role stager.

A source kit is not native registration or an inference service. Only pristine
canonical role bytes may ship; mutable local receipts cannot authorize exporting
owner memory. Distribution-only newline/receipt normalization is deterministic.
"""
from __future__ import annotations

import hashlib
import io
import json
import stat
import tempfile
from pathlib import Path, PurePosixPath
import zipfile

from .coordinator_sourcekit import _zip_member
from .model_builder_dropin import stage_model_builder_dropin, inspect_model_builder_dropin
from .native_canary import _no_duplicate_json, _reject_constant, _serialized
from .native_skill_binding import _unsafe_source_path
from .toy_model import example_toy_experiment
from .model_toy_fixture import example_dataset

PREFIX = "model-builder/"
MANIFEST = "SOURCEKIT_MANIFEST.json"
SCHEMA = "r61/model-builder-sourcekit-v1"
MAX_BYTES = 4 * 1024 * 1024
MAX_FILES = 160

START_HERE = """# Model Builder — bounded offline toy experiment source kit

This package actually trains a small integer perceptron, saves/reloads JSON
numeric weights, computes its predictions, compares a training-only majority
baseline and recovers baseline checkpoint bytes. It is NOT an LLM/LoRA trainer,
GPU job, automatic model loader, provider endpoint or native Muse agent.

Requirements: Python 3.12+. No pip packages, Git, downloaded model or account.
Verify the ZIP SHA-256 from a separate trusted source before extracting into
an absent directory. The embedded source hashes are unsigned integrity only.

From the extracted directory (macOS may use python3):

python -I -B model-builder/custom-skills/model_development_metrics/run.py --operation toy-demo --allow-local-training

The included opt-in extension installer can stage a separate reviewed source
copy without training. Run it only with a NEW absolute directory and opt-in:

python -I -B model-builder/runtime/model_toy_install.py stage --to ABSOLUTE_NEW_EXTENSION --include-toy-training

Preserve its stage_receipt_sha256. Inspect with the same runtime using the
inspect verb, --root ABSOLUTE_EXTENSION and --stage-sha256 ORIGINAL_STAGE_SHA.
No opt-in, source drift, altered receipts, links, extra files or occupied paths
are refused. Staging starts no optimizer, provider, model, service or native agent.

The recovered decimal-linear engine is also present:

python -I -B model-builder/custom-skills/model_development_metrics/run.py --operation linear-demo --allow-local-training

Expected: LOCAL_LINEAR_MODEL_DEMO_PASSED; 64 real gradient updates,
bundle_recomputed true and baseline_restored_byte_exact true. Its separate
runtime/model_toy_bundle.py supports run, verify and restore-baseline using
EXAMPLE_LINEAR_DATASET.json, explicit hashes and a new absolute output path.
No test of the protected-final set or production model promotion is allowed.

For the integer perceptron, expected: LOCAL_TOY_MODEL_DEMO_PASSED; trained_this_call true, candidate_correct
4 versus baseline_correct 2, checkpoint_reloaded true, baseline_recovered true.
The demo uses disposable local files and removes only its own temporary files.

To evaluate a supplied bounded experiment, pass EXAMPLE_TOY_EXPERIMENT.json
through stdin with --operation toy-train --allow-local-training. Without the
explicit opt-in flag, training is refused. The response includes JSON checkpoint
text and its exact SHA-256. Preserve both separately. toy-evaluate computes
predictions from the numeric weights using development rows, not caller
predictions. toy-restore returns the exact baseline bytes; it does NOT change
any deployed model. Original evaluate/checkpoint/demo operations remain usable.

Budget: 1–8 features, each -1/0/1; at most 96 rows, at most 64 per partition,
and 1–32 epochs (at most 2,048 sample steps). Protected final features/labels
must be null. Training/dev families and exact feature vectors must be disjoint;
those guards persist in reloaded checkpoint evaluation. Inputs are strict JSON,
not pickle, Python expressions, import paths, URLs or shell commands.

All native skills/config remain disabled. Local toy-training opt-in grants no
external training permission, source rights, publisher authentication, examiner
independence, final-set approval or deployment authorization. Caller labels and
claimed lineage remain unverified. Tiny development accuracy is not real-world
model quality. No network, GPU or provider call is part of this toy engine.
"""


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _read_tree(root: Path) -> dict[str, bytes]:
    if _unsafe_source_path(root) or not root.is_dir():
        raise ValueError("MODEL_SOURCEKIT_UNSAFE_ROOT")
    result, total = {}, 0
    for p in root.rglob("*"):
        if p.is_symlink() or (hasattr(p, "is_junction") and p.is_junction()):
            raise ValueError("MODEL_SOURCEKIT_LINK_REFUSED")
        if p.is_file():
            if p.stat().st_nlink != 1 or p.stat().st_size > 262144:
                raise ValueError("MODEL_SOURCEKIT_FILE_NOT_ADMITTED")
            relative = p.relative_to(root).as_posix()
            raw = p.read_bytes()
            total += len(raw)
            if total > MAX_BYTES or len(result) >= MAX_FILES:
                raise ValueError("MODEL_SOURCEKIT_SOURCE_BUDGET_EXCEEDED")
            result[relative] = raw
    return result


def _canonical() -> dict[str, bytes]:
    with tempfile.TemporaryDirectory(prefix="model-source-canonical-") as temp:
        root = Path(temp) / "model-builder"
        if stage_model_builder_dropin(root)["status"] != "SOURCE_ONLY_MODEL_BUILDER_STAGED":
            raise ValueError("MODEL_SOURCEKIT_CANONICAL_STAGE_REFUSED")
        if inspect_model_builder_dropin(root)["status"] != "LOCAL_MODEL_BUILDER_MATCH":
            raise ValueError("MODEL_SOURCEKIT_CANONICAL_INSPECTION_REFUSED")
        return _read_tree(root)


def _portable(original: dict[str, bytes]) -> dict[str, bytes]:
    # This only transforms independently generated source, never caller data.
    out = {name: raw.replace(b"\r\n", b"\n") if name.startswith(("profile/", "system-files/"))
           else raw for name, raw in original.items()}
    profile_name = "profile/RECEIPT.json"
    profile = json.loads(out[profile_name], object_pairs_hook=_no_duplicate_json,
                         parse_constant=_reject_constant)
    if profile.get("schema") != "muse-presets/render-v3":
        raise ValueError("MODEL_SOURCEKIT_PROFILE_SCHEMA_CHANGED")
    for name in profile["rendered_sha256"]:
        profile["rendered_sha256"][name] = _sha(out["profile/" + name])
    out[profile_name] = (json.dumps(profile, indent=2) + "\n").encode("utf-8")
    for name in list(out):
        if name.startswith("profile/"):
            mirror = "system-files/" + name.removeprefix("profile/")
            if mirror in out:
                out[mirror] = out[name]
    receipt_name = "receipts/MODEL_BUILDER_RECEIPT.json"
    receipt = json.loads(out[receipt_name], object_pairs_hook=_no_duplicate_json,
                         parse_constant=_reject_constant)
    if (receipt.get("schema") != "r33/model-builder-dropin-v1"
            or set(receipt["files_sha256"]) != set(out) - {receipt_name}
            or receipt.get("native_installed") is not False
            or receipt.get("external_effect_authorized") is not False):
        raise ValueError("MODEL_SOURCEKIT_RECEIPT_SCHEMA_CHANGED")
    receipt["files_sha256"] = {n: _sha(out[n]) for n in sorted(receipt["files_sha256"])}
    out[receipt_name] = _serialized(receipt)
    return out


def _distribution(canonical: dict[str, bytes]) -> dict[str, bytes]:
    return {**{PREFIX + n: b for n, b in _portable(canonical).items()},
            "START_HERE.md": START_HERE.encode("utf-8"),
            "EXAMPLE_TOY_EXPERIMENT.json": _serialized(example_toy_experiment()),
            "EXAMPLE_LINEAR_DATASET.json": _serialized(example_dataset())}


def _manifest(members: dict[str, bytes]) -> dict:
    return {"schema": SCHEMA, "role_id": "model-builder",
            "files_sha256": {n: _sha(b) for n, b in sorted(members.items())},
            "bounded_toy_training_available": True, "local_training_requires_opt_in": True,
            "native_installed": False, "external_effect_authorized": False,
            "gpu_training_available": False, "provider_authenticated": False,
            "protected_final_evaluated": False, "public_release_published": False}


def export_model_builder_sourcekit(pristine: Path, destination: Path) -> dict:
    root, target = Path(pristine), Path(destination)
    canonical = _canonical()
    if (inspect_model_builder_dropin(root).get("status") != "LOCAL_MODEL_BUILDER_MATCH"
            or _read_tree(root) != canonical):
        raise ValueError("MODEL_SOURCEKIT_PRISTINE_CANONICAL_SOURCE_REQUIRED")
    members = _distribution(canonical)
    members[MANIFEST] = _serialized(_manifest(members))
    if _unsafe_source_path(target) or target.suffix.lower() != ".zip" or not target.parent.is_dir():
        raise ValueError("MODEL_SOURCEKIT_DESTINATION_REFUSED")
    if target.exists() or target.is_symlink():
        raise FileExistsError("MODEL_SOURCEKIT_DESTINATION_OCCUPIED")
    # No source reads after freezing independent canonical members for export.
    with zipfile.ZipFile(target, "x", allowZip64=False) as archive:
        for name, raw in sorted(members.items()):
            _zip_member(archive, name, raw)
    digest = _sha(target.read_bytes())
    if verify_model_builder_sourcekit(target, digest)["status"] != "LOCAL_MODEL_SOURCEKIT_VERIFIED":
        raise RuntimeError("MODEL_SOURCEKIT_POST_EXPORT_FAILED")
    return {"status": "LOCAL_MODEL_SOURCEKIT_EXPORTED", "role_id": "model-builder",
            "sha256": digest, "archive_bytes": target.stat().st_size,
            "member_count": len(members), "native_installed": False,
            "external_effect_authorized": False}


def verify_model_builder_sourcekit(path: Path, expected_sha256: str) -> dict:
    p = Path(path)
    if _unsafe_source_path(p) or not p.is_file() or p.is_symlink() or p.stat().st_size > MAX_BYTES:
        raise ValueError("MODEL_SOURCEKIT_ARCHIVE_NOT_ADMITTED")
    frozen = p.read_bytes()
    if type(expected_sha256) is not str or _sha(frozen) != expected_sha256:
        raise ValueError("MODEL_SOURCEKIT_PIN_MISMATCH")
    expected = _distribution(_canonical())
    expected[MANIFEST] = _serialized(_manifest(expected))
    # Parse the same verified byte snapshot, not a second mutable-path read.
    with zipfile.ZipFile(io.BytesIO(frozen)) as archive:
        entries = archive.infolist()
        if len(entries) != len(expected) or len(entries) > MAX_FILES:
            raise ValueError("MODEL_SOURCEKIT_MEMBER_COUNT_REFUSED")
        seen, folded, total = set(), set(), 0
        for member in entries:
            name = member.filename
            parts = PurePosixPath(name).parts
            if (not parts or name.startswith("/") or ".." in parts or "\\" in name
                    or ":" in parts[0] or name not in expected or member.is_dir()
                    or name in seen or name.casefold() in folded
                    or stat.S_IFMT(member.external_attr >> 16) != stat.S_IFREG):
                raise ValueError("MODEL_SOURCEKIT_UNSAFE_MEMBER")
            seen.add(name); folded.add(name.casefold()); total += member.file_size
        if total > MAX_BYTES or seen != set(expected) or archive.testzip() is not None:
            raise ValueError("MODEL_SOURCEKIT_INTEGRITY_REFUSED")
        for name, raw in expected.items():
            if archive.read(name) != raw:
                raise ValueError("MODEL_SOURCEKIT_CANONICAL_BYTES_DRIFT")
    return {"status": "LOCAL_MODEL_SOURCEKIT_VERIFIED", "role_id": "model-builder",
            "archive_sha256": expected_sha256, "member_count": len(expected),
            "native_installed": False, "external_effect_authorized": False,
            "gpu_training_available": False, "provider_authenticated": False}

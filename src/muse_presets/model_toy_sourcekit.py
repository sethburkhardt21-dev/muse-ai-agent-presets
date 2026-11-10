"""Deterministic, source-pinned toy Model Builder extension kit; no publication.

The old Model Builder drop-in and its synthetic-byte verifier remain unchanged.
This creates a separate opt-in, local toy-model experiment artifact. It is not
an installed agent, model registry, training service or full T21 acceptance.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import stat
import sys
import zipfile

if __package__:
    from . import model_toy_math as math
    from . import model_toy_bundle as bundle
    from .model_toy_fixture import example_dataset
else:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import model_toy_math as math
    import model_toy_bundle as bundle
    from model_toy_fixture import example_dataset

MANIFEST = "SOURCEKIT_MANIFEST.json"
SCHEMA = "r61/model-builder-toy-sourcekit-v1"
BASE = "ed141e107a1344eb1f33238559460815b8567396"
LEGACY_BLOB = "d8143578cf942841184dc2a55233df8557b7eb61"
MAX_ARCHIVE = 2 * 1024 * 1024
MAX_TOTAL = 1024 * 1024
MAX_FILE = 131072
RUNTIME = ("model_toy_math.py", "model_toy_bundle.py", "model_toy_fixture.py",
           "model_toy_sourcekit.py", "model_eval.py", "model_toy_install.py")

LICENSE = '''MIT License

Copyright (c) 2026 Muse AI Agent Presets contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''

START = '''# Model Builder — bounded toy experiment extension candidate

This kit actually learns a small linear model using batch gradient descent.
It does NOT train an LLM, load a pretrained checkpoint, use a GPU, install an
agent, authenticate a reviewer, evaluate the protected final set, or call a
provider. It extends, rather than replaces, the original R33 verifier.

Requirements: Python 3.12+. No pip dependencies, network, external account,
model download, subprocess workload, scheduler or service installation.

Before extraction: verify the ZIP SHA-256 against a separately trusted value.
Inspect the exact member set; never extract over an existing owner directory.
The manifest is unsigned. An archive hash does not authenticate its publisher.

Optional source-only stage from a verified fresh extraction, never into an
existing agent directory (this does NOT start training):

python -I -B runtime/model_toy_install.py stage --to ABSOLUTE_NEW_EXTENSION_DIRECTORY --include-toy-training

Use the returned stage_receipt_sha256 for a read-only current-source check:

python -I -B runtime/model_toy_install.py inspect --root ABSOLUTE_EXTENSION_DIRECTORY --stage-sha256 ORIGINAL_STAGE_RECEIPT_SHA

The native registry stays DISABLED. A failed/interrupted stage retains its
STAGING_INCOMPLETE marker; never blindly retry into that destination.

From a fresh extraction or opt-in stage, after inspecting EXAMPLE_DATASET.json:

python -I -B runtime/model_toy_bundle.py run --dataset ABSOLUTE_DATASET_PATH --dataset-sha256 DATASET_SHA_FROM_MANIFEST --to ABSOLUTE_NEW_RUN_DIRECTORY --reviewed-data

The command returns receipt_sha256 and actual optimizer/evaluation results.
It creates baseline.json, candidate.json, original dataset.json, config.json,
evaluation.json and MANIFEST.json in the new directory. No final labels exist.

Read back by recomputing the bounded training, inference and metrics:

python -I -B runtime/model_toy_bundle.py verify --bundle ABSOLUTE_RUN_DIRECTORY --receipt-sha256 ORIGINAL_RECEIPT_SHA

Restore the original baseline to a NEW file, without altering the experiment:

python -I -B runtime/model_toy_bundle.py restore-baseline --bundle ABSOLUTE_RUN_DIRECTORY --receipt-sha256 ORIGINAL_RECEIPT_SHA --to ABSOLUTE_NEW_BASELINE_FILE

The example learns approximately y=2*x+1, compares dev mean squared error
against a train-mean baseline, and holds final examples UNEVALUATED. A locally
preferred candidate is advisory; promotion_authorized always remains false.
A worse or tied candidate leaves the baseline selected.

Strict budgets: 1-4 normalized features, at most 128 rows and 128 optimizer
steps, finite bounded decimal strings, exact schemas and disjoint families.
No arbitrary Python input, pickle, exec, shell command, URL or model package.
Data is caller-provided and NOT independently authenticated.

All native skills are DISABLED. Subchat folders are neutral templates, not
real host chats. Source/local evidence does not establish production training,
physical-host parity, OS sandboxing or power-loss durability. If a run fails,
STAGING_INCOMPLETE is retained; never blindly retry into the same directory.

Status: LOCAL CANDIDATE. Full repository and Windows/macOS fleet review,
private GitHub integration and any public release are still separate gates.
'''


def _source_members() -> dict[str, bytes]:
    root = Path(__file__).resolve().parent
    result = {}
    for name in RUNTIME:
        # Normalize a distribution view only; original source files are never changed.
        raw = bundle._read_regular(root / name, limit=MAX_FILE).replace(b"\r\n", b"\n").replace(b"\r\n", b"\n")
        if name == "model_eval.py":
            blob = hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest()
            if blob != LEGACY_BLOB:
                raise math.Refused("ORIGINAL_R33_SOURCE_PIN_CHANGED")
        result["runtime/" + name] = raw
    result["START_HERE.md"] = START.encode("utf-8")
    result["LICENSE"] = LICENSE.encode("utf-8")
    result["EXAMPLE_DATASET.json"] = math.canonical_json(example_dataset())
    result["config/skills.yaml"] = (
        "version: 1\nentries:\n"
        "  toy_linear_experiment:\n    status: disabled\n"
        "  toy_checkpoint_review:\n    status: disabled\n"
    ).encode()
    result["config/host-binding.json"] = math.canonical_json({
        "schema": "r60/toy-host-binding-v1", "owner_id": None, "native_agent_id": None,
        "native_installed": False, "training_service_authorized": False,
        "external_effect_authorized": False, "scheduler_enabled": False})
    for name, purpose in (
        ("data-custody", "Inspect synthetic dataset source pins and disjoint partitions; never expose final labels."),
        ("development-lab", "Explicitly run bounded local toy optimization; no LLM, hosted model or GPU."),
        ("artifact-review", "Recompute exact evidence and restore the original baseline to a new file only."),
    ):
        result[f"subchats/{name}/ROLE.md"] = (
            f"# {name}\n\n{purpose}\n\nNeutral template, not a native chat or authenticated role.\n"
        ).encode()
    for name, purpose in (
        ("toy_linear_experiment", "Bounded actual linear-model training on reviewed synthetic data"),
        ("toy_checkpoint_review", "Recompute pinned toy results and restore exact baseline bytes"),
    ):
        result[f"skills/{name}/SKILL.md"] = (
            f"---\nname: {name}\ndescription: {purpose}\n---\n\n"
            "Use runtime/model_toy_bundle.py only with explicit reviewed local inputs.\n"
            "Native registration and provider effects remain disabled.\n"
        ).encode()
        result[f"skills/{name}/skill.yaml"] = (
            f"name: {name}\ninclude_in_prompt: false\nstatus: disabled\n"
        ).encode()
    return result


def _members() -> dict[str, bytes]:
    source = _source_members()
    metadata = {
        "schema": SCHEMA, "target_baseline_commit": BASE,
        "scope": "LOCAL_TOY_EXTENSION_CANDIDATE",
        "files_sha256": {name: math.digest(raw) for name, raw in sorted(source.items())},
        "example_dataset_sha256": math.digest(source["EXAMPLE_DATASET.json"]),
        "legacy_model_eval_git_blob": LEGACY_BLOB,
        "native_installed": False, "publicly_published": False,
        "independent_fleet_verified": False, "external_effect_authorized": False,
        "llm_training_performed": False, "reviewer_identity_authenticated": False,
    }
    return {**source, MANIFEST: math.canonical_json(metadata)}


def _archive(members: dict[str, bytes]) -> bytes:
    output = io.BytesIO()
    # ZIP_STORED avoids differences between compression-library versions.
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_STORED, allowZip64=False) as archive:
        for name, raw in sorted(members.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            archive.writestr(info, raw)
    return output.getvalue()


def export_sourcekit(destination: Path) -> dict:
    target = bundle._new_path(destination)
    if target.suffix.lower() != ".zip":
        raise math.Refused("SOURCEKIT_ZIP_DESTINATION_REQUIRED")
    members = _members()
    data = _archive(members)
    if len(data) > MAX_ARCHIVE:
        raise math.Refused("SOURCEKIT_ARCHIVE_BUDGET")
    bundle._write_new(target, data)
    pin = math.digest(data)
    check = verify_sourcekit(target, pin)
    return {"status": "LOCAL_TOY_SOURCEKIT_EXPORTED", "sha256": pin,
            "bytes": len(data), "members": check["members"],
            "native_installed": False, "publicly_published": False,
            "independent_fleet_verified": False}


def verify_sourcekit(path: Path, expected_sha256: str) -> dict:
    if not math._sha(expected_sha256):
        raise math.Refused("SOURCEKIT_PIN_REQUIRED")
    # Verify and parse the SAME captured bytes, not a mutable path reopened later.
    data = bundle._read_regular(path, limit=MAX_ARCHIVE)
    if math.digest(data) != expected_sha256:
        raise math.Refused("SOURCEKIT_PIN_MISMATCH")
    expected = _members()
    try:
        with zipfile.ZipFile(io.BytesIO(data), "r") as archive:
            infos = archive.infolist()
            if len(infos) != len(expected) or archive.comment:
                raise math.Refused("SOURCEKIT_FILE_SET_OR_COMMENT")
            seen = set()
            folded = set()
            total = 0
            for info in infos:
                name = info.filename
                parts = PurePosixPath(name).parts
                if (not name or not parts or name.startswith("/") or ".." in parts or
                    "\\" in name or ":" in name or "\x00" in name or name not in expected or
                    name in seen or name.casefold() in folded or info.is_dir() or
                    stat.S_IFMT(info.external_attr >> 16) != stat.S_IFREG or
                    info.extra or info.comment or info.file_size > MAX_FILE):
                    raise math.Refused("SOURCEKIT_UNSAFE_MEMBER")
                seen.add(name)
                folded.add(name.casefold())
                total += info.file_size
            if total > MAX_TOTAL or archive.testzip() is not None:
                raise math.Refused("SOURCEKIT_SIZE_OR_CRC")
            actual = {name: archive.read(name) for name in seen}
    except (zipfile.BadZipFile, NotImplementedError, RuntimeError, EOFError) as exc:
        raise math.Refused("SOURCEKIT_INVALID_ZIP") from exc
    if actual != expected:
        raise math.Refused("SOURCEKIT_SOURCE_OR_POLICY_MISMATCH")
    if _archive(expected) != data:
        raise math.Refused("SOURCEKIT_NONCANONICAL_ARCHIVE_BYTES")
    return {"status": "LOCAL_TOY_SOURCEKIT_VERIFIED", "sha256": expected_sha256,
            "members": len(actual), "native_installed": False,
            "publicly_published": False, "independent_fleet_verified": False}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="operation", required=True)
    export = sub.add_parser("export")
    export.add_argument("--to", type=Path, required=True)
    verify = sub.add_parser("verify")
    verify.add_argument("--archive", type=Path, required=True)
    verify.add_argument("--sha256", required=True)
    args = parser.parse_args(argv)
    try:
        report = export_sourcekit(args.to) if args.operation == "export" else verify_sourcekit(args.archive, args.sha256)
        print(json.dumps(report, sort_keys=True))
        return 0
    except (math.Refused, OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"status": "REFUSED", "reason": str(exc),
                          "native_installed": False, "publicly_published": False}, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

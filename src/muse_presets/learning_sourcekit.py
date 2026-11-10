"""Deterministic standalone Learning kit; no native account or scheduler.

Verification compares canonical bytes without parsing the supplied ZIP.
The unchanged SQLite engine requires a protected host-side authority resolver.
Packaging follows the accepted Garden R78 contract; original study bytes stay pinned.
"""
from __future__ import annotations
import hashlib
import io
import json
from pathlib import Path
import re
import stat
import zipfile
from .native_skill_binding import _unsafe_source_path

SCHEMA = "muse-presets/learning-executable-sourcekit-v1"
MAX_ARCHIVE = 500_000
SOURCE_SHA = {
    "LICENSE": "af30e586ca6503924d5e4d99894ec6c7ce61ba77a55ba081b7a129d33f43fddf",
    "examples/learning_session_demo.py": "4600987556e80ad06c27e8fe0a35d916618635ff5cfaaa49705cd6b9bab014ce",
    "presets/learning-coach/playbook.json": "78135472989a3a097914afb529e32a7a46b178c35f3341245828b33390f19a59",
    "presets/learning-coach/preset.json": "11ac7532685fdf00e037f69401bf9b5e72a87aec16b31b557335e9313b1a0c84",
    "src/muse_presets/database_paths.py": "1b3cb8a42cb29036aada91e314bffdbf397c46fdecf6227e4177022ac34acc79",
    "src/muse_presets/learning_session.py": "f81e1e786b6956f1f48acc0437e782c5eabe674f65d16322a0b8f3395dae7d3b",
    "tests/test_learning_session.py": "297abafe69d92dafec903ccb52499b89d7f90d25ec5d8de75884b111a50f4443"
}
SOURCE_MAP = {
    "src/muse_presets/learning_session.py": "muse_presets/learning_session.py",
    "src/muse_presets/database_paths.py": "muse_presets/database_paths.py",
    "examples/learning_session_demo.py": "demo.py",
    "tests/test_learning_session.py": "tests/test_learning_session.py",
    "presets/learning-coach/preset.json": "preset.json",
    "presets/learning-coach/playbook.json": "playbook.json",
    "LICENSE": "LICENSE",
}
START_HERE = '# Learning Coach — executable local source kit\n\nRequires Python 3.12+. No pip, Git, paid API or network service is required.\nVerify the ZIP SHA-256 using a separately trusted release record before\nextracting into a NEW directory. From the extracted folder run:\n\n    python -I -B run.py --operation demo\n    python -I -B run.py --operation self-test\n\nThe demo runs the original local SQLite pipeline: admit supplied science\nterms, create quote-backed draft questions, approve with a synthetic owner,\nissue a learner challenge without its answer, record a literal score, close\nand reopen the database, recover the same receipt and project review due\n24 hours later. It removes its disposable database at exit. The 25 original\nengine tests cover source mutation, wrong owner/learner/session, injected\nlesson rejection, stale versions, hidden answers, expiry, duplicate grading,\nconcurrent connections and transaction rollback. Platform skips are reported.\nThese tests use local fixtures; they do not authenticate a real person.\n\nThe engine recognizes only explicit Term :: Definition. source lines. It does\nnot use a language model, verify teaching material or perform semantic grading.\nScores use literal_casefold_whitespace_v1 and due times use\nHEURISTIC_V1_NOT_FSRS: no validated mastery or clinical-learning claim.\n\nThe package includes unchanged learning_session.py, database_paths.py, the\noriginal demo/tests, neutral role preset/playbook and LICENSE. The runner\nchecks fixed source pins, disallows unknown files and refuses symlinked or\nWindows-junction kit paths before imports. Keep custom code and databases\noutside this immutable kit. Hashes establish byte integrity, not publisher\nidentity or permission. Python -I is import isolation, not an OS sandbox.\n\nFor a custom local integration import LearningSession and LearningScope from\nmuse_presets.learning_session. Supply an absolute database path and a protected\nhost-side authority callable. Never allow an agent/browser to choose its own\nauthority resolver. Caller-supplied scope labels are not authentication.\nSQLite stores material and answers unencrypted; this reference is not approved\nfor clinical decisions, PHI, examination secrets or regulated assessments.\nThe full source and limitations are described in the original engine docs.\n\nNo native Muse account, Space, reminder, scheduled job, network connector or\nFamily Link message is installed or invoked. The verifier accepts only the\ncanonical deterministic ZIP, not a recompressed equivalent. Updates are new\nreviewed kits; preserve user databases separately. No automatic migration,\nbackground process or state-deleting uninstall is provided.\n'
RUNNER = r'''"""Offline Learning demo and original tests. No live-provider authority."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
import unittest

PINS = __PIN_MAP__
SCHEMA = "muse-presets/learning-executable-sourcekit-v1"
ALIASES = {"/var":"/private/var", "/tmp":"/private/tmp", "/etc":"/private/etc"}

def _safe(path):
    for part in (path, *path.parents):
        junction = getattr(part, "is_junction", None)
        if callable(junction) and junction():
            raise ValueError("LINKED_KIT_REFUSED")
        if part.is_symlink():
            target = ALIASES.get(str(part))
            if not (sys.platform == "darwin" and target and
                    part.lstat().st_uid == 0 and part.resolve(strict=True) == Path(target)):
                raise ValueError("LINKED_KIT_REFUSED")

def _read(path):
    _safe(path)
    if not path.is_file() or path.stat().st_nlink != 1:
        raise ValueError("KIT_FILE_UNSAFE")
    with path.open("rb") as stream:
        raw = stream.read(65537)
    if len(raw) > 65536:
        raise ValueError("KIT_FILE_OVERSIZED")
    return raw

def _pairs(items):
    values = {}
    for key, value in items:
        if key in values:
            raise ValueError("DUPLICATE_MANIFEST_KEY")
        values[key] = value
    return values

def _constant(_value):
    raise ValueError("NONFINITE_MANIFEST_VALUE")

def checked_root():
    if sys.flags.optimize:
        raise ValueError("OPTIMIZED_VALIDATION_UNSUPPORTED")
    script = Path(__file__).absolute()
    root = script.parent
    _safe(root)
    names = set(PINS) | {"run.py", "SOURCEKIT_MANIFEST.json"}
    directories = {str(Path(n).parent).replace("\\", "/") for n in names} - {"."}
    found = set()
    for count, path in enumerate(root.rglob("*"), 1):
        if count > 40:
            raise ValueError("KIT_ENTRY_LIMIT")
        _safe(path)
        name = path.relative_to(root).as_posix()
        if path.is_dir():
            if name not in directories:
                raise ValueError("UNKNOWN_KIT_DIRECTORY")
        elif name in names and path.is_file():
            found.add(name)
        else:
            raise ValueError("UNKNOWN_KIT_FILE")
    if found != names:
        raise ValueError("KIT_FILE_SET_CHANGED")
    for name, digest in PINS.items():
        if hashlib.sha256(_read(root / name)).hexdigest() != digest:
            raise ValueError("KIT_SOURCE_PIN_CHANGED")
    expected = dict(PINS, **{"run.py": hashlib.sha256(_read(script)).hexdigest()})
    manifest = json.loads(_read(root / "SOURCEKIT_MANIFEST.json"),
                          object_pairs_hook=_pairs, parse_constant=_constant)
    if (manifest.get("schema") != SCHEMA or manifest.get("files_sha256") != expected
            or manifest.get("native_installed") is not False
            or manifest.get("provider_authenticated") is not False
            or manifest.get("external_scheduler_writes") is not False
            or manifest.get("clinical_release_ready") is not False):
        raise ValueError("KIT_MANIFEST_CHANGED")
    return root

def main(argv=None):
    parser = argparse.ArgumentParser(description="Offline Learning source-kit checks")
    parser.add_argument("--operation", choices=("demo", "self-test"), required=True)
    options = parser.parse_args(argv)
    try:
        root = checked_root()
        sys.path.insert(0, str(root))
        if options.operation == "demo":
            from demo import main as demo
            demo()
            return 0
        suite = unittest.defaultTestLoader.discover(str(root / "tests"), pattern="test_learning_session.py")
        result = unittest.TextTestRunner(verbosity=1).run(suite)
        passed = result.wasSuccessful() and result.testsRun > 0
        print(json.dumps({"status": "LOCAL_LEARNING_SELF_TEST_PASSED" if passed else "LOCAL_LEARNING_SELF_TEST_FAILED",
                          "tests_run": result.testsRun, "skipped": len(result.skipped),
                          "failures": len(result.failures), "errors": len(result.errors),
                          "native_installed": False, "provider_authenticated": False,
                          "external_scheduler_writes": False, "clinical_release_ready": False}, sort_keys=True))
        return 0 if passed else 1
    except (ValueError, TypeError, KeyError, AttributeError, OSError, ImportError, RecursionError) as exc:
        print(json.dumps({"status": "REFUSED", "reason": type(exc).__name__ + ":" + str(exc)[:180],
                          "native_installed": False, "external_scheduler_writes": False, "clinical_release_ready": False}, sort_keys=True))
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
'''

def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def _json(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")

def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)

def _distribution(root: Path) -> dict[str, bytes]:
    root = Path(root)
    _require(root.is_dir() and not _unsafe_source_path(root), "LEARNING_SOURCE_ROOT_UNSAFE")
    members = {}
    for name, digest in SOURCE_SHA.items():
        path = root / name
        _require(path.is_file() and not _unsafe_source_path(path) and
                 path.stat().st_nlink == 1, "LEARNING_SOURCE_FILE_UNSAFE")
        with path.open("rb") as stream:
            raw = stream.read(65537)
        _require(len(raw) <= 65536 and _sha(raw) == digest, "LEARNING_SOURCE_PIN_MISMATCH:" + name)
        members[SOURCE_MAP[name]] = raw
    profile = json.loads(members["preset.json"])
    _require(profile.get("id") == "learning-coach" and
             profile.get("native_muse_status") == "UNBOUND" and
             profile["family_link"]["enabled"] is False, "LEARNING_PROFILE_AUTHORITY_CHANGED")
    members["muse_presets/__init__.py"] = b'"""Pinned offline Learning source only."""\n'
    members["START_HERE.md"] = START_HERE.encode("utf-8")
    pins = {name: _sha(raw) for name, raw in sorted(members.items())}
    members["run.py"] = RUNNER.replace("__PIN_MAP__", repr(pins)).encode("utf-8")
    members["SOURCEKIT_MANIFEST.json"] = _json({
        "schema": SCHEMA, "role_id": "learning-coach",
        "files_sha256": {name: _sha(raw) for name, raw in sorted(members.items())},
        "source_grade": "LOCAL_NONCLINICAL_STUDY_REFERENCE_ONLY", "native_installed": False,
        "provider_authenticated": False, "external_scheduler_writes": False, "clinical_release_ready": False,
        "public_release_published": False,
    })
    return members

def _archive_bytes(root: Path) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_STORED, allowZip64=False) as archive:
        for name, raw in sorted(_distribution(root).items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 11, 10, 0, 0, 0))
            info.create_system = 3
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            info.compress_type = zipfile.ZIP_STORED
            archive.writestr(info, raw)
    result = buffer.getvalue()
    _require(len(result) <= MAX_ARCHIVE, "LEARNING_CANONICAL_ARCHIVE_OVERSIZED")
    return result

def verify_learning_sourcekit(source_root: Path, archive_path: Path, expected_sha256: str) -> dict:
    _require(type(expected_sha256) is str and re.fullmatch(r"[a-f0-9]{64}", expected_sha256) is not None,
             "LEARNING_EXTERNAL_DIGEST_INVALID")
    target = Path(archive_path)
    _require(target.is_file() and not _unsafe_source_path(target) and
             target.stat().st_nlink == 1 and target.stat().st_size <= MAX_ARCHIVE, "LEARNING_ARCHIVE_UNSAFE")
    with target.open("rb") as stream:
        raw = stream.read(MAX_ARCHIVE + 1)
    _require(len(raw) <= MAX_ARCHIVE, "LEARNING_ARCHIVE_UNSAFE")
    _require(_sha(raw) == expected_sha256, "LEARNING_EXTERNAL_DIGEST_MISMATCH")
    # Do not parse, extract or decompress attacker-supplied archives.
    _require(raw == _archive_bytes(Path(source_root)), "LEARNING_CANONICAL_ARCHIVE_CHANGED")
    return {"status": "LOCAL_LEARNING_SOURCEKIT_VERIFIED", "archive_sha256": expected_sha256,
            "archive_bytes": len(raw), "native_installed": False,
            "provider_authenticated": False, "external_scheduler_writes": False, "clinical_release_ready": False}

def export_learning_sourcekit(source_root: Path, destination: Path) -> dict:
    target = Path(destination)
    _require(target.suffix.lower() == ".zip" and target.parent.is_dir() and
             not _unsafe_source_path(target.parent) and not target.exists() and not target.is_symlink(),
             "LEARNING_DESTINATION_OCCUPIED_OR_UNSAFE")
    raw = _archive_bytes(Path(source_root))
    with target.open("xb") as stream:
        stream.write(raw)
    result = verify_learning_sourcekit(source_root, target, _sha(raw))
    return dict(result, status="LOCAL_LEARNING_SOURCEKIT_EXPORTED")

"""Deterministic, standalone Garden source kit; no native account or calendar.

Verification compares canonical bytes without parsing the supplied ZIP.
The unchanged SQLite engine still requires a host-side authority resolver.
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

SCHEMA = "muse-presets/garden-executable-sourcekit-v1"
MAX_ARCHIVE = 500_000
SOURCE_SHA = {
    "src/muse_presets/garden_calendar.py": "af982eb2cdba413e6cb7fcaa04ac3235e37af45fc855e66377b1ca99a9fb662f",
    "src/muse_presets/database_paths.py": "1b3cb8a42cb29036aada91e314bffdbf397c46fdecf6227e4177022ac34acc79",
    "examples/garden_calendar_demo.py": "19c1cd3703bbd48aef210c4a2f5cad540c5efd2827c6add7fba791bf18b41344",
    "tests/test_garden_calendar.py": "63fb0c7ed0ea2407a07446ef798c3f9cf580445f32f410fd11dcf67d362b332d",
    "presets/garden-companion/preset.json": "8fa1478f149bc1a7a9cd7690d370266f245f982aeff5fd9c4bd018718784c7fe",
    "presets/garden-companion/playbook.json": "375a34f906b89680a9b384b9431445d526291963f918797c772cb04e498bd0bf",
    "LICENSE": "af30e586ca6503924d5e4d99894ec6c7ce61ba77a55ba081b7a129d33f43fddf",
}
SOURCE_MAP = {
    "src/muse_presets/garden_calendar.py": "muse_presets/garden_calendar.py",
    "src/muse_presets/database_paths.py": "muse_presets/database_paths.py",
    "examples/garden_calendar_demo.py": "demo.py",
    "tests/test_garden_calendar.py": "tests/test_garden_calendar.py",
    "presets/garden-companion/preset.json": "preset.json",
    "presets/garden-companion/playbook.json": "playbook.json",
    "LICENSE": "LICENSE",
}
START_HERE = """# Garden Companion — executable local source kit

Requirements: Python 3.12+ only. No pip, Git, paid API or network is required.
Verify the ZIP SHA-256 against a separately trusted release record before
extracting it to a NEW directory. From that directory run:

    python -I -B run.py --operation demo
    python -I -B run.py --operation self-test

The demo uses an actual disposable SQLite database: create an event, propose
a date shift, review/approve with a synthetic local owner, close/reopen the
connection and recover the receipt. The original bundled engine regression
suite also tests wrong-owner isolation, stale revisions, transaction rollback,
conflicting operations, expiry, rejection and recovery. Tests use fixtures;
they do not authenticate a real person. No external calendar is contacted.

The kit includes unchanged garden_calendar.py, database_paths.py, the original
demo/tests, neutral preset/playbook and LICENSE. The runner verifies fixed
source pins and refuses unknown files before importing package code. Do not
add files inside this immutable source kit: keep your own data elsewhere.
SHA-256 checks are integrity checks, not publisher signatures or permission.
Python -I isolates imports; it is NOT an OS security sandbox.

For a custom local integration import GardenCalendar and GardenScope from
muse_presets.garden_calendar. Supply a host-side authority callable and an
explicit database path. GardenScope construction alone is not authentication.
Never expose that resolver as an agent/browser input. The module documents
proposal -> review -> decision -> receipt; caller-controlled tests are not a
native provider. SQLite files are unencrypted and use host filesystem access.
The package deliberately does not bind an account, schedule jobs, install a
Muse agent, send Family Link messages, or provide live weather/plant diagnosis.

The verifier accepts only the exact deterministic canonical ZIP, not a
recompressed equivalent. Obtain a fresh reviewed kit for updates; preserve
user databases outside the old kit. There is no automatic migration or
uninstall command that deletes user state.
"""
RUNNER = r'''"""Offline Garden demo and original tests. No live-provider authority."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
import unittest

PINS = __PIN_MAP__
SCHEMA = "muse-presets/garden-executable-sourcekit-v1"
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
            or manifest.get("external_calendar_writes") is not False):
        raise ValueError("KIT_MANIFEST_CHANGED")
    return root

def main(argv=None):
    parser = argparse.ArgumentParser(description="Offline Garden source-kit checks")
    parser.add_argument("--operation", choices=("demo", "self-test"), required=True)
    options = parser.parse_args(argv)
    try:
        root = checked_root()
        sys.path.insert(0, str(root))
        if options.operation == "demo":
            from demo import main as demo
            demo()
            return 0
        suite = unittest.defaultTestLoader.discover(str(root / "tests"), pattern="test_garden_calendar.py")
        result = unittest.TextTestRunner(verbosity=1).run(suite)
        passed = result.wasSuccessful() and result.testsRun > 0
        print(json.dumps({"status": "LOCAL_GARDEN_SELF_TEST_PASSED" if passed else "LOCAL_GARDEN_SELF_TEST_FAILED",
                          "tests_run": result.testsRun, "skipped": len(result.skipped),
                          "failures": len(result.failures), "errors": len(result.errors),
                          "native_installed": False, "provider_authenticated": False,
                          "external_calendar_writes": False}, sort_keys=True))
        return 0 if passed else 1
    except (ValueError, TypeError, KeyError, AttributeError, OSError, ImportError, RecursionError) as exc:
        print(json.dumps({"status": "REFUSED", "reason": type(exc).__name__ + ":" + str(exc)[:180],
                          "native_installed": False, "external_calendar_writes": False}, sort_keys=True))
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
    _require(root.is_dir() and not _unsafe_source_path(root), "GARDEN_SOURCE_ROOT_UNSAFE")
    members = {}
    for name, digest in SOURCE_SHA.items():
        path = root / name
        _require(path.is_file() and not _unsafe_source_path(path) and
                 path.stat().st_nlink == 1, "GARDEN_SOURCE_FILE_UNSAFE")
        with path.open("rb") as stream:
            raw = stream.read(65537)
        _require(len(raw) <= 65536 and _sha(raw) == digest, "GARDEN_SOURCE_PIN_MISMATCH:" + name)
        members[SOURCE_MAP[name]] = raw
    profile = json.loads(members["preset.json"])
    _require(profile.get("id") == "garden-companion" and
             profile.get("native_muse_status") == "UNBOUND" and
             profile["family_link"]["enabled"] is False, "GARDEN_PROFILE_AUTHORITY_CHANGED")
    members["muse_presets/__init__.py"] = b'"""Pinned offline Garden source only."""\n'
    members["START_HERE.md"] = START_HERE.encode("utf-8")
    pins = {name: _sha(raw) for name, raw in sorted(members.items())}
    members["run.py"] = RUNNER.replace("__PIN_MAP__", repr(pins)).encode("utf-8")
    members["SOURCEKIT_MANIFEST.json"] = _json({
        "schema": SCHEMA, "role_id": "garden-companion",
        "files_sha256": {name: _sha(raw) for name, raw in sorted(members.items())},
        "source_grade": "LOCAL_SQLITE_REFERENCE_ONLY", "native_installed": False,
        "provider_authenticated": False, "external_calendar_writes": False,
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
    _require(len(result) <= MAX_ARCHIVE, "GARDEN_CANONICAL_ARCHIVE_OVERSIZED")
    return result

def verify_garden_sourcekit(source_root: Path, archive_path: Path, expected_sha256: str) -> dict:
    _require(type(expected_sha256) is str and re.fullmatch(r"[a-f0-9]{64}", expected_sha256) is not None,
             "GARDEN_EXTERNAL_DIGEST_INVALID")
    target = Path(archive_path)
    _require(target.is_file() and not _unsafe_source_path(target) and
             target.stat().st_nlink == 1 and target.stat().st_size <= MAX_ARCHIVE, "GARDEN_ARCHIVE_UNSAFE")
    with target.open("rb") as stream:
        raw = stream.read(MAX_ARCHIVE + 1)
    _require(len(raw) <= MAX_ARCHIVE, "GARDEN_ARCHIVE_UNSAFE")
    _require(_sha(raw) == expected_sha256, "GARDEN_EXTERNAL_DIGEST_MISMATCH")
    # Do not parse, extract or decompress attacker-supplied archives.
    _require(raw == _archive_bytes(Path(source_root)), "GARDEN_CANONICAL_ARCHIVE_CHANGED")
    return {"status": "LOCAL_GARDEN_SOURCEKIT_VERIFIED", "archive_sha256": expected_sha256,
            "archive_bytes": len(raw), "native_installed": False,
            "provider_authenticated": False, "external_calendar_writes": False}

def export_garden_sourcekit(source_root: Path, destination: Path) -> dict:
    target = Path(destination)
    _require(target.suffix.lower() == ".zip" and target.parent.is_dir() and
             not _unsafe_source_path(target.parent) and not target.exists() and not target.is_symlink(),
             "GARDEN_DESTINATION_OCCUPIED_OR_UNSAFE")
    raw = _archive_bytes(Path(source_root))
    with target.open("xb") as stream:
        stream.write(raw)
    result = verify_garden_sourcekit(source_root, target, _sha(raw))
    return dict(result, status="LOCAL_GARDEN_SOURCEKIT_EXPORTED")

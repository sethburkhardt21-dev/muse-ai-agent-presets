"""Create-only, exact-byte portable Reverse Researcher fixture comparison kit.

No executable binary inspection, live network access, desktop control,
security probing or malware execution is provided. Only caller-supplied
offline observation fixtures are compared by the pinned existing engine.
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

SCHEMA = "muse-presets/reverse-executable-sourcekit-v1"
MAX_ARCHIVE = 250_000

SOURCE_SHA = {
    "LICENSE": "af30e586ca6503924d5e4d99894ec6c7ce61ba77a55ba081b7a129d33f43fddf",
    "src/muse_presets/reverse.py": "3d5b4ff667ec996397f85a5a5746913d8aaff03801a864f1bbde5ffbe7dcc800",
    "tests/test_reverse_fixture.py": "d3229a34a348ea35ee18d9a0fcfe7a3b03ccb751e8eeac2bc946eaeb3b432aeb",
    "presets/reverse-engineering-researcher/preset.json": "a8d0933de95103e512339aefed4a1fc4f18c1c73a4d0d49c7c14ba00759ebdf1",
    "presets/reverse-engineering-researcher/playbook.json": "d363137bedaf2a974a66ab93cefe380270a623610f2cd1deb6a52c9e05b59294",
}
SOURCE_MAP = {
    "LICENSE": "LICENSE",
    "src/muse_presets/reverse.py": "muse_presets/reverse.py",
    "tests/test_reverse_fixture.py": "tests/test_reverse_fixture.py",
    "presets/reverse-engineering-researcher/preset.json": "preset.json",
    "presets/reverse-engineering-researcher/playbook.json": "playbook.json",
}

START_HERE = """# Reverse Engineering & Security Researcher — offline comparison kit

This source-only kit implements deterministic comparison of caller-supplied
UI observations. It does not reverse binaries, open apps, attach debuggers,
capture packets, scan hosts, send network messages or run malware.

Requires Python 3.12+. Verify the ZIP's SHA-256 from a separately trusted
record before extracting into a NEW directory. Then:

    python -I -B run.py --operation demo
    python -I -B run.py --operation self-test
    python -I -B run.py --operation compare --fixture /absolute/path/input.json

The compare fixture must be an external regular local file (not in this kit),
at most 128 KiB, with exactly these JSON keys:

    {
      "schema":"muse-presets/reverse-offline-fixture-input-v1",
      "analysis_boundary":"OFFLINE_SUPPLIED_OBSERVATIONS_ONLY",
      "authorization_declaration":"OWNER_OR_PERMISSION_DECLARED_UNVERIFIED",
      "before":[{"action":"click","target":"save","outcome":"silent"}],
      "after":[{"action":"click","target":"save","outcome":"toast"}]
    }

Only view/click/scroll/hover actions and short symbolic target names are
supported. Output contains changed/added/removed action:target keys and
the input SHA-256, not the original outcome strings. The declaration is
provided by the caller and is NOT verified ownership or a permission grant.

The demo uses a synthetic form before/after fixture and labels a difference,
not a proven security defect or remediation. The 10 bundled regression cases
exercise the pinned source engine. The package refuses unknown/modified
source files, rehashed altered manifests, import shadows, links and
unsupported Python optimization before importing its engine.

SHA-256 manifests only attest byte identity, not trusted publisher identity,
permission, malware safety or code-signing. Python -I is not an OS sandbox.
No native Muse agent, Family Link transport, network connector, automation,
exploit or external effect is installed or invoked.

Keep personal observations, secrets and user data outside this immutable kit.
The kit stores no user state. Upgrades are fresh reviewed archives; no
automatic update, destructive uninstall or data migration is provided.
"""

RUNNER = r'''"""Bounded, offline-only observation diff; no live target behavior."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import unittest

PINS = __PIN_MAP__
SCHEMA = "muse-presets/reverse-executable-sourcekit-v1"
INPUT_SCHEMA = "muse-presets/reverse-offline-fixture-input-v1"
ALIASES = {"/var":"/private/var","/tmp":"/private/tmp","/etc":"/private/etc"}

def _safe(path):
    for part in (path, *path.parents):
        junction = getattr(part, "is_junction", None)
        if callable(junction) and junction():
            raise ValueError("LINKED_PATH_REFUSED")
        if part.is_symlink():
            target = ALIASES.get(str(part))
            if not (sys.platform == "darwin" and target and
                    part.lstat().st_uid == 0 and
                    part.resolve(strict=True) == Path(target)):
                raise ValueError("LINKED_PATH_REFUSED")

def _read(path, limit):
    _safe(path)
    if not path.is_file() or path.stat().st_nlink != 1:
        raise ValueError("NONREGULAR_OR_LINKED_FILE")
    if path.stat().st_size > limit:
        raise ValueError("INPUT_FILE_BUDGET")
    with path.open("rb") as stream:
        raw = stream.read(limit+1)
    if len(raw) > limit:
        raise ValueError("INPUT_FILE_BUDGET")
    return raw

def _pairs(items):
    obj = {}
    for key,value in items:
        if key in obj:
            raise ValueError("DUPLICATE_JSON_KEY")
        obj[key] = value
    return obj

def _constant(_value):
    raise ValueError("NONFINITE_JSON_VALUE")

def _parse(raw):
    return json.loads(raw, object_pairs_hook=_pairs, parse_constant=_constant)

def checked_root():
    if sys.flags.optimize:
        raise ValueError("OPTIMIZED_VALIDATION_UNSUPPORTED")
    script = Path(__file__).absolute()
    root = script.parent
    _safe(root)
    expected = set(PINS) | {"run.py","SOURCEKIT_MANIFEST.json"}
    directories = {str(Path(name).parent).replace("\\","/") for name in expected} - {"."}
    found = set()
    for i,path in enumerate(root.rglob("*"),1):
        if i > 40:
            raise ValueError("KIT_ENTRY_LIMIT")
        _safe(path)
        name = path.relative_to(root).as_posix()
        if path.is_dir():
            if name not in directories:
                raise ValueError("UNKNOWN_KIT_DIRECTORY")
        elif name in expected and path.is_file():
            found.add(name)
        else:
            raise ValueError("UNKNOWN_KIT_ENTRY")
    if found != expected:
        raise ValueError("KIT_FILE_SET_CHANGED")
    for name,pin in PINS.items():
        if hashlib.sha256(_read(root/name,65536)).hexdigest() != pin:
            raise ValueError("KIT_SOURCE_PIN_CHANGED")
    expected_pins = dict(PINS, **{"run.py":hashlib.sha256(_read(script,65536)).hexdigest()})
    manifest = _parse(_read(root/"SOURCEKIT_MANIFEST.json",65536))
    if (not isinstance(manifest,dict) or manifest.get("schema") != SCHEMA or
            manifest.get("files_sha256") != expected_pins or
            manifest.get("role_id") != "reverse-engineering-researcher" or
            manifest.get("native_installed") is not False or
            manifest.get("network_activity") is not False or
            manifest.get("external_effects_authorized") is not False or
            manifest.get("malware_executed") is not False or
            manifest.get("public_release_published") is not False):
        raise ValueError("KIT_MANIFEST_CHANGED")
    return root

def fixture(path_arg, root):
    if not path_arg:
        raise ValueError("OFFLINE_FIXTURE_REQUIRED")
    path = Path(path_arg).absolute()
    if path.is_relative_to(root) or path.resolve(strict=False).is_relative_to(root.resolve(strict=True)):
        raise ValueError("FIXTURE_MUST_BE_OUTSIDE_KIT")
    raw = _read(path,128*1024)
    obj = _parse(raw)
    if not isinstance(obj,dict) or set(obj) != {
        "schema","analysis_boundary","authorization_declaration","before","after"
    }:
        raise ValueError("INVALID_FIXTURE_FORMAT")
    if (obj["schema"] != INPUT_SCHEMA or
        obj["analysis_boundary"] != "OFFLINE_SUPPLIED_OBSERVATIONS_ONLY" or
        obj["authorization_declaration"] != "OWNER_OR_PERMISSION_DECLARED_UNVERIFIED"):
        raise ValueError("UNSUPPORTED_DECLARED_SCOPE")
    return obj, hashlib.sha256(raw).hexdigest()

def demo_case():
    return {
        "before":[{"action":"click","target":"save","outcome":"silent"},
                  {"action":"click","target":"help","outcome":"page"}],
        "after":[{"action":"click","target":"save","outcome":"toast"},
                 {"action":"click","target":"export","outcome":"file"}],
    }

def main(argv=None):
    p = argparse.ArgumentParser(description="Offline supplied-fixture comparison only")
    p.add_argument("--operation", choices=("demo","compare","self-test"), required=True)
    p.add_argument("--fixture", type=str)
    a = p.parse_args(argv)
    try:
        root = checked_root()
        if a.operation != "compare" and a.fixture is not None:
            raise ValueError("FIXTURE_ONLY_WITH_COMPARE")
        sys.path.insert(0,str(root))
        if a.operation == "self-test":
            suite = unittest.defaultTestLoader.discover(str(root/"tests"),pattern="test_reverse_fixture.py")
            result = unittest.TextTestRunner(verbosity=1).run(suite)
            passed = result.wasSuccessful() and result.testsRun == 10
            print(json.dumps({"status":"LOCAL_REVERSE_SELF_TEST_PASSED" if passed else "LOCAL_REVERSE_SELF_TEST_FAILED",
                "tests_run":result.testsRun,"skipped":len(result.skipped),"failures":len(result.failures),
                "errors":len(result.errors),"native_invoked":False,"target_accessed":False,
                "network_activity":False},sort_keys=True))
            return 0 if passed else 1
        from muse_presets.reverse import compare_observed_flows
        if a.operation == "demo":
            data = demo_case()
            out = compare_observed_flows(data["before"],data["after"])
            if (out["changed"],out["added"],out["removed"]) != (
                ["click:save"],["click:export"],["click:help"]):
                raise ValueError("SYNTHETIC_DEMO_DRIFT")
            status = "LOCAL_REVERSE_FIXTURE_DEMO_PASSED"
            digest = hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest()
        else:
            data,digest = fixture(a.fixture,root)
            out = compare_observed_flows(data["before"],data["after"])
            status = "LOCAL_REVERSE_FIXTURE_COMPARED"
        print(json.dumps({"status":status,"schema":"muse-presets/reverse-fixture-output-v1",
            "changed":out["changed"],"added":out["added"],"removed":out["removed"],
            "before_count":len(data["before"]),"after_count":len(data["after"]),
            "fixture_sha256":digest,"declaration_unverified":True,
            "inference_limit":"OBSERVATION_DIFF_ONLY_NO_CAUSALITY_OR_SECURITY_VERDICT",
            "target_accessed":False,"native_invoked":False,
            "network_activity":False,"external_effects_authorized":False,
            "malware_executed":False},sort_keys=True))
        return 0
    except (ValueError,TypeError,KeyError,AttributeError,OSError,ImportError,
            UnicodeError,RecursionError) as exc:
        print(json.dumps({"status":"REFUSED",
            "reason":type(exc).__name__+":"+str(exc)[:180],
            "native_invoked":False,"target_accessed":False,
            "network_activity":False,"external_effects_authorized":False},sort_keys=True))
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
'''

def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def _json(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True)+"\n").encode("utf-8")

def _require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)

def _distribution(source_root: Path) -> dict[str, bytes]:
    root = Path(source_root)
    _require(root.is_dir() and not _unsafe_source_path(root), "REVERSE_SOURCE_ROOT_UNSAFE")
    files = {}
    for name,pin in SOURCE_SHA.items():
        path = root/name
        _require(path.is_file() and not _unsafe_source_path(path)
                 and path.stat().st_nlink == 1, "REVERSE_SOURCE_UNSAFE")
        with path.open("rb") as stream:
            raw = stream.read(65537)
        _require(len(raw) <= 65536 and _sha(raw) == pin,
                 "REVERSE_SOURCE_PIN_MISMATCH:" + name)
        files[SOURCE_MAP[name]] = raw
    profile = json.loads(files["preset.json"])
    _require(profile.get("id") == "reverse-engineering-researcher"
             and profile.get("native_muse_status") == "UNBOUND"
             and profile.get("family_link",{}).get("enabled") is False,
             "REVERSE_PROFILE_SCOPE_CHANGED")
    files["muse_presets/__init__.py"] = b'"""Pinned offline reverse fixture comparison only."""\n'
    files["START_HERE.md"] = START_HERE.encode("utf-8")
    pins = {name:_sha(raw) for name,raw in sorted(files.items())}
    files["run.py"] = RUNNER.replace("__PIN_MAP__", repr(pins)).encode("utf-8")
    files["SOURCEKIT_MANIFEST.json"] = _json({
        "schema":SCHEMA,"role_id":"reverse-engineering-researcher",
        "source_grade":"OFFLINE_SUPPLIED_OBSERVATION_COMPARISON_ONLY",
        "files_sha256":{name:_sha(raw) for name,raw in sorted(files.items())},
        "declaration_unverified":True,"native_installed":False,
        "network_activity":False,"target_accessed":False,
        "external_effects_authorized":False,"malware_executed":False,
        "public_release_published":False,
    })
    return files

def _archive_bytes(source_root: Path) -> bytes:
    stream = io.BytesIO()
    with zipfile.ZipFile(stream,"w",compression=zipfile.ZIP_STORED,allowZip64=False) as archive:
        for name,raw in sorted(_distribution(source_root).items()):
            info = zipfile.ZipInfo(name,date_time=(2026,11,10,0,0,0))
            info.create_system=3
            info.external_attr=(stat.S_IFREG|0o644)<<16
            info.compress_type=zipfile.ZIP_STORED
            archive.writestr(info,raw)
    raw=stream.getvalue()
    _require(len(raw)<=MAX_ARCHIVE,"REVERSE_CANONICAL_ARCHIVE_BUDGET")
    return raw

def verify_reverse_sourcekit(source_root: Path, archive_path: Path, expected_sha256: str) -> dict:
    _require(type(expected_sha256) is str and
             re.fullmatch(r"[0-9a-f]{64}",expected_sha256) is not None,
             "REVERSE_EXTERNAL_DIGEST_INVALID")
    target=Path(archive_path)
    _require(target.is_file() and not _unsafe_source_path(target)
             and target.stat().st_nlink==1 and
             target.stat().st_size<=MAX_ARCHIVE,"REVERSE_ARCHIVE_UNSAFE")
    with target.open("rb") as stream:
        raw=stream.read(MAX_ARCHIVE+1)
    _require(len(raw)<=MAX_ARCHIVE,"REVERSE_ARCHIVE_UNSAFE")
    _require(_sha(raw)==expected_sha256,"REVERSE_EXTERNAL_DIGEST_MISMATCH")
    # Never parse/decompress/extract a submitted, untrusted archive.
    _require(raw==_archive_bytes(Path(source_root)),"REVERSE_CANONICAL_ARCHIVE_CHANGED")
    return {"status":"LOCAL_REVERSE_SOURCEKIT_VERIFIED",
            "archive_sha256":expected_sha256,"archive_bytes":len(raw),
            "native_installed":False,"network_activity":False,
            "external_effects_authorized":False}

def export_reverse_sourcekit(source_root: Path, destination: Path) -> dict:
    target=Path(destination)
    _require(target.suffix.lower()==".zip" and target.parent.is_dir()
             and not _unsafe_source_path(target.parent)
             and not target.exists() and not target.is_symlink(),
             "REVERSE_DESTINATION_OCCUPIED_OR_UNSAFE")
    raw=_archive_bytes(Path(source_root))
    with target.open("xb") as stream:
        stream.write(raw)
    result=verify_reverse_sourcekit(source_root,target,_sha(raw))
    return dict(result,status="LOCAL_REVERSE_SOURCEKIT_EXPORTED")

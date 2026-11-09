"""R55 source-local RED -> bounded patch -> GREEN -> pinned independent replay.

Only explicitly reviewed Python unittest code is supported. A disposable Git
repository and argument-vector execution are NOT an OS security sandbox.
No native host authority, network isolation or external-effect guarantee is
implied. Review identities need a separately authenticated operator channel.
The existing Claim Gate owns operation state; these JSON artifacts are evidence,
not a new ledger. Unknown execution is never automatically retried.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import signal
import socket
import stat
import subprocess
import sys
import threading
import time

# Python -I omits the script directory. Admit only this source-pinned runtime's
# own sibling modules; do not restore the working directory or PYTHONPATH.
_runtime_file = Path(__file__)
if _runtime_file.is_symlink():
    raise ValueError("LINKED_RUNTIME_REFUSED")
sys.path.insert(0, str(_runtime_file.resolve(strict=True).parent))

from claim_gate import ClaimGate
from portable_lock import exclusive_lock

SCHEMA = "r55/engineering-case-v1"
CASE_KEYS = {"schema", "case_id", "author_id", "files", "editable", "test_ids",
             "expected_failures", "patch", "command_profile", "timeout_seconds"}
MAX_FILE = 32768
MAX_CASE = 262144
MAX_LOG = 65536
MAX_ARTIFACT = 1048576
IDENTIFIER = re.compile(r"^[a-z][a-z0-9-]{0,63}$")
SHA = re.compile(r"^[0-9a-f]{64}$")
TEST_ID = re.compile(r"^test_[A-Za-z0-9_]+\.[A-Za-z_][A-Za-z0-9_]*\.test_[A-Za-z0-9_]+$")
SCOPE = "engineering-workflow"
WORKER = Path(__file__).with_name("workflow_worker.py")


def _require(condition, reason):
    if not condition:
        raise ValueError(reason)


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def canonical_sha(value):
    return _sha(_canonical(value))


def _unique(pairs):
    result = {}
    for key, value in pairs:
        _require(key not in result, "DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def _bad_constant(value):
    raise ValueError("NONFINITE_JSON_CONSTANT")


def _safe_path(path):
    path = Path(path)
    _require(path.is_absolute() and ".." not in path.parts, "PATH_NOT_ADMITTED")
    for node in (path, *path.parents):
        linked = node.is_symlink() or getattr(node, "is_junction", lambda: False)()
        apple_alias = (sys.platform == "darwin" and str(node) in ("/var", "/tmp", "/etc")
                       and str(node.resolve()) == "/private" + str(node))
        _require(not linked or apple_alias, "LINKED_PATH_REFUSED")
    return path


def _read(path, limit=MAX_ARTIFACT):
    path = _safe_path(path)
    info = path.lstat()
    _require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1, "REGULAR_FILE_REQUIRED")
    _require(info.st_size <= limit, "ARTIFACT_TOO_LARGE")
    raw = path.read_bytes()
    after = path.lstat()
    _require((info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns) ==
             (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns), "ARTIFACT_READ_DRIFT")
    _require(len(raw) == info.st_size and len(raw) <= limit, "ARTIFACT_TOO_LARGE")
    return raw


def _json_file(path, limit=MAX_ARTIFACT):
    return json.loads(_read(path, limit).decode("utf-8"),
                      object_pairs_hook=_unique, parse_constant=_bad_constant)


def _write_new(path, raw):
    path = _safe_path(path)
    _require(len(raw) <= MAX_ARTIFACT, "ARTIFACT_TOO_LARGE")
    with path.open("xb") as out:
        out.write(raw)
        out.flush()
        os.fsync(out.fileno())
    return _sha(raw)


def _source_name(name):
    _require(type(name) is str and 0 < len(name) <= 160, "UNSAFE_SOURCE_NAME")
    parts = name.split("/")
    _require(len(parts) <= 4 and all(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", p)
                                   for p in parts[:-1]), "UNSAFE_SOURCE_NAME")
    _require(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*\.py", parts[-1]) is not None,
             "UNSAFE_SOURCE_NAME")
    reserved = {"con", "prn", "aux", "nul", *[f"com{i}" for i in range(1, 10)],
                *[f"lpt{i}" for i in range(1, 10)]}
    _require(all(p.split(".")[0].lower() not in reserved for p in parts), "RESERVED_SOURCE_NAME")
    return name


def validate_case(case, expected_sha):
    _require(type(case) is dict and set(case) == CASE_KEYS and case.get("schema") == SCHEMA,
             "CASE_SCHEMA_REFUSED")
    raw = _canonical(case)
    _require(len(raw) <= MAX_CASE, "CASE_TOO_LARGE")
    _require(type(expected_sha) is str and SHA.fullmatch(expected_sha) and _sha(raw) == expected_sha,
             "CASE_PIN_MISMATCH")
    for key in ("case_id", "author_id"):
        _require(type(case[key]) is str and IDENTIFIER.fullmatch(case[key]), "INVALID_IDENTITY")
    _require(case["command_profile"] == "python-unittest-v1", "COMMAND_PROFILE_REFUSED")
    timeout = case["timeout_seconds"]
    _require(type(timeout) in (int, float) and math.isfinite(timeout) and 0.1 <= timeout <= 30,
             "INVALID_TIMEOUT")
    files = case["files"]
    _require(type(files) is dict and 2 <= len(files) <= 32, "INVALID_SOURCE_SET")
    names = set()
    for name, value in files.items():
        _source_name(name)
        _require(name.casefold() not in names, "CASE_COLLIDING_SOURCE")
        names.add(name.casefold())
        _require(type(value) is str and 0 < len(value.encode("utf-8")) <= MAX_FILE
                 and "\x00" not in value, "SOURCE_CONTENT_REFUSED")
    editable = case["editable"]
    _require(type(editable) is list and 0 < len(editable) <= 8
             and len(set(editable)) == len(editable), "INVALID_EDITABLE_SET")
    for name in editable:
        _source_name(name)
        _require(name in files and not name.startswith("tests/")
                 and not Path(name).name.startswith("test_"), "TEST_OR_UNADMITTED_PATCH")
    ids = case["test_ids"]
    _require(type(ids) is list and 1 <= len(ids) <= 64 and all(type(x) is str for x in ids)
             and len(set(ids)) == len(ids), "INVALID_TEST_IDENTITIES")
    for identity in ids:
        _require(TEST_ID.fullmatch(identity) is not None, "INVALID_TEST_IDENTITY")
        _require("tests/" + identity.split(".")[0] + ".py" in files, "MISSING_TEST_MODULE")
    failures = case["expected_failures"]
    _require(type(failures) is list and failures and all(type(x) is str and x in ids for x in failures)
             and len(set(failures)) == len(failures), "INVALID_RED_FAILURE_CONTRACT")
    patch = case["patch"]
    _require(type(patch) is list and 1 <= len(patch) <= len(editable), "INVALID_PATCH")
    changed = set()
    for change in patch:
        _require(type(change) is dict and set(change) == {"path", "before_sha256", "after_utf8"},
                 "PATCH_SCHEMA_REFUSED")
        name = _source_name(change["path"])
        _require(name in editable and name not in changed, "TEST_OR_UNADMITTED_PATCH")
        _require(_sha(files[name].encode("utf-8")) == change["before_sha256"], "SOURCE_REVISION_MISMATCH")
        after = change["after_utf8"]
        _require(type(after) is str and 0 < len(after.encode("utf-8")) <= MAX_FILE
                 and "\x00" not in after, "PATCH_CONTENT_REFUSED")
        _require(after != files[name], "NO_OP_PATCH")
        changed.add(name)
    return copy.deepcopy(case)


def _tree(root, *, metadata=False):
    root = _safe_path(root)
    _require(root.is_dir(), "MISSING_DISPOSABLE_REPOSITORY")
    rows = {}
    total = 0
    for parent, directories, filenames in os.walk(root, followlinks=False):
        here = Path(parent)
        for name in list(directories):
            node = here / name
            _safe_path(node)
            if not metadata and here == root and name == ".git":
                directories.remove(name)
        for name in filenames:
            p = here / name
            raw = _read(p, MAX_ARTIFACT if metadata else MAX_FILE)
            total += len(raw)
            rows[p.relative_to(root).as_posix()] = _sha(raw)
            _require(len(rows) <= (512 if metadata else 64) and total <= 4 * MAX_ARTIFACT,
                     "REPOSITORY_BOUNDS_EXCEEDED")
    return dict(sorted(rows.items()))


def _expected_tree(case, patched=False):
    files = dict(case["files"])
    if patched:
        for entry in case["patch"]:
            files[entry["path"]] = entry["after_utf8"]
    return {n: _sha(value.encode("utf-8")) for n, value in sorted(files.items())}


def _environment(root):
    env = {k: v for k, v in os.environ.items() if k.upper() in
           {"PATH", "SYSTEMROOT", "WINDIR", "COMSPEC", "TEMP", "TMP", "LANG", "LC_ALL"}}
    env.update({"HOME": str(root / "home"), "USERPROFILE": str(root / "home"),
                "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull,
                "GIT_CONFIG_NOSYSTEM": "1", "GIT_ATTR_NOSYSTEM": "1",
                "GIT_TERMINAL_PROMPT": "0", "GIT_OPTIONAL_LOCKS": "0",
                "GIT_AUTHOR_NAME": "Workflow Fixture", "GIT_COMMITTER_NAME": "Workflow Fixture",
                "GIT_AUTHOR_EMAIL": "fixture.invalid", "GIT_COMMITTER_EMAIL": "fixture.invalid",
                "GIT_AUTHOR_DATE": "2000-01-01T00:00:00Z", "GIT_COMMITTER_DATE": "2000-01-01T00:00:00Z"})
    return env


def _git(root, *args):
    executable = shutil.which("git")
    _require(executable is not None, "GIT_UNAVAILABLE")
    argv = [executable, "-c", "core.hooksPath=" + str(root / "empty-template"),
            "-c", "core.autocrlf=false", "-c", "core.attributesFile=" + os.devnull,
            "-c", "core.excludesFile=" + os.devnull, "-c", "commit.gpgSign=false",
            "-c", "core.fsmonitor=false", "-C", str(root / "repo"), *args]
    result = subprocess.run(argv, env=_environment(root), stdin=subprocess.DEVNULL,
                            capture_output=True, timeout=15, check=False)
    _require(result.returncode == 0 and len(result.stdout) + len(result.stderr) <= MAX_ARTIFACT,
             "DISPOSABLE_GIT_OPERATION_FAILED")
    return result.stdout.decode("utf-8", errors="strict").strip()


def _terminate_owned(process):
    # Only this call's child/group is eligible. This is cleanup, not sandboxing.
    if os.name == "nt":
        taskkill = Path(os.environ.get("SystemRoot", "C:/Windows")) / "System32/taskkill.exe"
        if process.poll() is None and taskkill.is_file():
            try:
                subprocess.run([str(taskkill), "/PID", str(process.pid), "/T", "/F"],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
            except (OSError, subprocess.TimeoutExpired):
                pass
        if process.poll() is None:
            process.kill()
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        raise ValueError("OWNED_CHILD_CLEANUP_UNCONFIRMED")


def _capture(argv, root, timeout):
    kwargs = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
    process = subprocess.Popen(argv, cwd=root / "repo", env=_environment(root),
                               stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, shell=False, **kwargs)
    buffers = [bytearray(), bytearray()]
    too_large = threading.Event()
    def drain(pipe, data):
        try:
            while True:
                chunk = pipe.read(4096)
                if not chunk:
                    break
                remaining = MAX_LOG - len(data)
                data.extend(chunk[:max(0, remaining)])
                if len(chunk) > remaining:
                    too_large.set()
        finally:
            pipe.close()
    threads = [threading.Thread(target=drain, args=(pipe, data), daemon=True)
               for pipe, data in zip((process.stdout, process.stderr), buffers)]
    for thread in threads:
        thread.start()
    reason = None
    deadline = time.monotonic() + timeout
    while process.poll() is None:
        if too_large.is_set() or time.monotonic() >= deadline:
            reason = "OUTPUT_LIMIT" if too_large.is_set() else "TIMEOUT"
            _terminate_owned(process)
            break
        time.sleep(0.01)
    for thread in threads:
        thread.join(timeout=1)
    if any(t.is_alive() for t in threads):
        reason = "DESCENDANT_PIPE_UNRECONCILED"
        _terminate_owned(process)
    if too_large.is_set():
        reason = "OUTPUT_LIMIT"
    return process.returncode, bytes(buffers[0]), bytes(buffers[1]), reason


def _observation_valid(value):
    keys = {"schema", "python", "tests_run", "observed_ids", "passed", "failures", "errors",
            "skipped", "expected_failures", "unexpected_successes"}
    if type(value) is not dict or set(value) != keys or value.get("schema") != "r55/unittest-observation-v1":
        return False
    if type(value["tests_run"]) is not int or not 0 <= value["tests_run"] <= 64:
        return False
    for key in keys - {"schema", "python", "tests_run"}:
        if type(value[key]) is not list or len(value[key]) > 64 or any(type(x) is not str for x in value[key]):
            return False
    return True


def _run_tests(root, case, label):
    _safe_path(WORKER)
    _require(WORKER.is_file(), "TRUSTED_WORKER_UNAVAILABLE")
    contract = root / (label + ".contract.json")
    result_path = root / (label + ".tests.json")
    _write_new(contract, _canonical(case["test_ids"]))
    metadata = _tree(root / "repo/.git", metadata=True)
    argv = [sys.executable, "-I", "-B", str(WORKER), "--repo", str(root / "repo"),
            "--contract", str(contract), "--result", str(result_path)]
    code, stdout, stderr, unknown = _capture(argv, root, case["timeout_seconds"])
    out_sha = _write_new(root / (label + ".stdout.log"), stdout)
    err_sha = _write_new(root / (label + ".stderr.log"), stderr)
    observed = None
    try:
        if result_path.exists():
            observed = _json_file(result_path, MAX_LOG)
    except (OSError, ValueError, UnicodeError):
        unknown = unknown or "INVALID_TEST_RESULT"
    if not _observation_valid(observed):
        unknown = unknown or "MISSING_OR_INVALID_TEST_RESULT"
    if _tree(root / "repo/.git", metadata=True) != metadata:
        unknown = "GIT_METADATA_DRIFT"
    return {"command_profile": "python-unittest-v1", "exit_code": code,
            "result": observed, "unknown_reason": unknown,
            "stdout_sha256": out_sha, "stderr_sha256": err_sha,
            "result_sha256": _sha(_read(result_path, MAX_LOG)) if result_path.is_file() else None}


def _matches_tests(observation, case, *, red):
    r = observation["result"]
    if observation["unknown_reason"] is not None or not _observation_valid(r):
        return False
    if observation["exit_code"] != (1 if red else 0):
        return False
    expected = case["expected_failures"] if red else []
    expected_passed = set(case["test_ids"]) - set(expected)
    return (r["tests_run"] == len(case["test_ids"])
            and r["observed_ids"] == case["test_ids"]
            and sorted(r["failures"]) == sorted(expected)
            and len(r["passed"]) == len(expected_passed) and set(r["passed"]) == expected_passed
            and not any(r[k] for k in ("errors", "skipped", "expected_failures", "unexpected_successes")))


def _artifacts(root):
    return {p.name: _sha(_read(p)) for p in sorted(root.iterdir(), key=lambda p: p.name)
            if p.is_file() and p.name not in ("result.json", ".workflow.lock")}


def _finish(root, gate, case, report, status, *, unknown=False):
    report["status"] = status
    report["events"].append(status)
    report["artifacts"] = _artifacts(root)
    report["source_tree"] = _tree(root / "repo") if (root / "repo").is_dir() else {}
    digest = _write_new(root / "result.json", _canonical(report))
    if unknown:
        gate.mark_unknown(SCOPE, case["case_id"], status)
    else:
        gate.mark_effect(SCOPE, case["case_id"], "SUCCESS" if status == "GREEN_TESTED" else "FAILED",
                         receipt={"result_sha256": digest})
    return report


def _prior_result(root, case, digest):
    _require((root / "plan.json").is_file() and (root / "claim-state/claims").is_dir(),
             "EXISTING_WORKSPACE_NOT_ADMITTED")
    _require(_sha(_read(root / "plan.json")) == digest, "CHANGED_PAYLOAD_REPLAY")
    gate = ClaimGate(str(root / "claim-state"))
    record = gate.reconcile_unknown(SCOPE, case["case_id"])
    _require(record is not None and record.get("payload_digest") == digest, "CLAIM_STATE_INVALID")
    if record["state"] in ("CLAIMED", "UNKNOWN"):
        return {"status": "UNKNOWN_EFFECT_HOLD", "case_id": case["case_id"],
                "automatic_retry_permitted": False, "native_muse_invoked": False,
                "external_effect_authorized": False}
    _require(record["state"] == "EFFECT_DONE", "CLAIM_STATE_REFUSED")
    raw = _read(root / "result.json")
    _require(_sha(raw) == record.get("receipt", {}).get("result_sha256"), "RESULT_RECEIPT_MISMATCH")
    result = json.loads(raw, object_pairs_hook=_unique, parse_constant=_bad_constant)
    _require(_tree(root / "repo") == result["source_tree"], "SOURCE_DRIFT")
    expected_head = result.get("patched_commit", result.get("baseline_commit"))
    _require(expected_head is not None and _git(root, "rev-parse", "HEAD") == expected_head,
             "SOURCE_REVISION_DRIFT")
    for name, expected in result["artifacts"].items():
        _require(_sha(_read(root / name)) == expected, "RESULT_ARTIFACT_DRIFT")
    return result


def execute(case, destination, *, expected_case_sha256, reviewed_code=False):
    """Run a pinned reviewed case, only inside a create-only disposable workspace."""
    _require(reviewed_code is True, "REVIEWED_CODE_REQUIRED")
    case = validate_case(case, expected_case_sha256)
    root = _safe_path(destination)
    _require(root.parent.is_dir(), "WORKSPACE_PARENT_MISSING")
    existing = root.exists()
    if not existing:
        root.mkdir(exist_ok=False)
    else:
        _require(root.is_dir() and (root / "plan.json").is_file(), "EXISTING_WORKSPACE_NOT_ADMITTED")
    with exclusive_lock(root / ".workflow.lock"):
        if existing:
            return _prior_result(root, case, expected_case_sha256)
        raw = _canonical(case)
        _write_new(root / "plan.json", raw)
        gate = ClaimGate(str(root / "claim-state"))
        created, _ = gate.claim(SCOPE, case["case_id"], raw)
        _require(created, "CLAIM_ALREADY_EXISTS")
        report = {"schema": "r55/workflow-result-v1", "case_id": case["case_id"],
                  "case_sha256": expected_case_sha256, "author_id": case["author_id"],
                  "writer_host": socket.gethostname(), "events": [],
                  "native_muse_invoked": False, "external_effect_authorized": False,
                  "os_sandboxed": False, "red": None, "green": None}
        try:
            for name in ("repo", "empty-template", "home"):
                (root / name).mkdir()
            for name, text in case["files"].items():
                target = root / "repo" / name
                target.parent.mkdir(parents=True, exist_ok=True)
                _write_new(target, text.encode("utf-8"))
            _git(root, "init", "--quiet", "--initial-branch=workflow", "--template=" + str(root / "empty-template"))
            _git(root, "add", "--", *sorted(case["files"]))
            _git(root, "commit", "--quiet", "-m", "Reviewed baseline " + expected_case_sha256)
            report["baseline_commit"] = _git(root, "rev-parse", "HEAD")
            _require(_tree(root / "repo") == _expected_tree(case), "SOURCE_DRIFT")
            report["red"] = _run_tests(root, case, "red")
            if _tree(root / "repo") != _expected_tree(case):
                return _finish(root, gate, case, report, "SOURCE_DRIFT", unknown=True)
            if report["red"]["unknown_reason"] is not None:
                return _finish(root, gate, case, report, "UNKNOWN_EFFECT_HOLD", unknown=True)
            if not _matches_tests(report["red"], case, red=True):
                return _finish(root, gate, case, report, "RED_NOT_REPRODUCED")
            report["events"].append("RED_REPRODUCED")
            _require(_git(root, "rev-parse", "HEAD") == report["baseline_commit"], "SOURCE_DRIFT")
            for patch in case["patch"]:
                target = root / "repo" / patch["path"]
                _require(_sha(_read(target, MAX_FILE)) == patch["before_sha256"], "SOURCE_DRIFT")
            for index, patch in enumerate(case["patch"]):
                temporary = root / ("patch-" + str(index) + ".tmp")
                _write_new(temporary, patch["after_utf8"].encode("utf-8"))
                os.replace(temporary, root / "repo" / patch["path"])
            _require(_tree(root / "repo") == _expected_tree(case, True), "SOURCE_DRIFT")
            report["events"].append("PATCH_APPLIED")
            diff = _git(root, "diff", "--no-ext-diff", "--no-textconv", "--", *case["editable"])
            _require(bool(diff), "NO_OP_PATCH")
            report["patch_sha256"] = _write_new(root / "patch.diff", (diff + "\n").encode("utf-8"))
            report["green"] = _run_tests(root, case, "green")
            if _tree(root / "repo") != _expected_tree(case, True):
                return _finish(root, gate, case, report, "SOURCE_DRIFT", unknown=True)
            if report["green"]["unknown_reason"] is not None:
                return _finish(root, gate, case, report, "UNKNOWN_EFFECT_HOLD", unknown=True)
            if not _matches_tests(report["green"], case, red=False):
                return _finish(root, gate, case, report, "GREEN_FAILED")
            _require(_git(root, "rev-parse", "HEAD") == report["baseline_commit"], "SOURCE_DRIFT")
            _git(root, "add", "--", *case["editable"])
            _git(root, "commit", "--quiet", "-m", "Verified repair " + expected_case_sha256)
            report["patched_commit"] = _git(root, "rev-parse", "HEAD")
            _require(not _git(root, "status", "--porcelain", "--untracked-files=all"), "SOURCE_DRIFT")
            candidate = {"schema": "r55/frozen-workflow-candidate-v1", "case": case,
                         "case_sha256": expected_case_sha256, "author_id": case["author_id"],
                         "writer_host": socket.gethostname(), "baseline_commit": report["baseline_commit"],
                         "patched_commit": report["patched_commit"], "patch_sha256": report["patch_sha256"],
                         "source_tree": _expected_tree(case, True), "status": "GREEN_TESTED",
                         "native_muse_invoked": False, "external_effect_authorized": False}
            report["candidate_sha256"] = _write_new(root / "candidate.json", _canonical(candidate))
            return _finish(root, gate, case, report, "GREEN_TESTED")
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            report["error"] = type(exc).__name__ + ":" + str(exc)[:300]
            return _finish(root, gate, case, report, "UNKNOWN_EFFECT_HOLD", unknown=True)


def _candidate(path, expected):
    raw = _read(path)
    _require(type(expected) is str and SHA.fullmatch(expected) and _sha(raw) == expected,
             "CANDIDATE_PIN_MISMATCH")
    candidate = json.loads(raw, object_pairs_hook=_unique, parse_constant=_bad_constant)
    keys = {"schema", "case", "case_sha256", "author_id", "writer_host", "baseline_commit",
            "patched_commit", "patch_sha256", "source_tree", "status",
            "native_muse_invoked", "external_effect_authorized"}
    _require(type(candidate) is dict and set(candidate) == keys
             and candidate["schema"] == "r55/frozen-workflow-candidate-v1"
             and candidate["status"] == "GREEN_TESTED", "CANDIDATE_SCHEMA_REFUSED")
    validate_case(candidate["case"], candidate["case_sha256"])
    _require(candidate["author_id"] == candidate["case"]["author_id"]
             and candidate["source_tree"] == _expected_tree(candidate["case"], True)
             and candidate["native_muse_invoked"] is False
             and candidate["external_effect_authorized"] is False, "CANDIDATE_SOURCE_MISMATCH")
    return candidate


def review(candidate_file, destination, *, expected_candidate_sha256, reviewer_id,
           expected_author_id, reviewed_code=False):
    """Recreate and test the original defect and repair on a separate disposable repo."""
    _require(reviewed_code is True, "REVIEWED_CODE_REQUIRED")
    candidate_file = _safe_path(candidate_file)
    candidate = _candidate(candidate_file, expected_candidate_sha256)
    _require(candidate["author_id"] == expected_author_id, "REVIEW_AUTHOR_MISMATCH")
    _require(type(reviewer_id) is str and IDENTIFIER.fullmatch(reviewer_id)
             and reviewer_id != expected_author_id, "SELF_REVIEW_REFUSED")
    root = _safe_path(destination)
    _require(root.parent.is_dir() and not root.exists(), "REVIEW_DESTINATION_OCCUPIED")
    root.mkdir(exist_ok=False)
    replay = execute(candidate["case"], root / "replay",
                     expected_case_sha256=candidate["case_sha256"], reviewed_code=True)
    matched = (replay["status"] == "GREEN_TESTED" and
               all(replay.get(k) == candidate[k] for k in
                   ("baseline_commit", "patched_commit", "patch_sha256", "source_tree")))
    _require(_sha(_read(candidate_file)) == expected_candidate_sha256, "CANDIDATE_READ_DRIFT")
    receipt = {"schema": "r55/independent-workflow-review-v1",
               "verdict": "REVIEW_PASS" if matched else "REVIEW_FAILED",
               "candidate_sha256": expected_candidate_sha256, "case_sha256": candidate["case_sha256"],
               "author_id": expected_author_id, "reviewer_id": reviewer_id, "host": socket.gethostname(),
               "replay_result_sha256": _sha(_read(root / "replay/result.json")),
               "replayed_red_failures": ((replay.get("red") or {}).get("result") or {}).get("failures", []),
               "replayed_green_tests": ((replay.get("green") or {}).get("result") or {}).get("tests_run", 0),
               "source_tree": replay.get("source_tree", {}), "identity_authenticated": False,
               "native_muse_invoked": False, "external_effect_authorized": False}
    _write_new(root / "REVIEW.json", _canonical(receipt))
    return receipt


def complete(candidate_file, *, expected_candidate_sha256, observations):
    """Validate TWO original host receipts against separately obtained observations.

    observations must be supplied by an authenticated operator, never the candidate.
    This function cannot authenticate the channel or turn a self-hash into identity.
    """
    candidate_file = _safe_path(candidate_file)
    candidate = _candidate(candidate_file, expected_candidate_sha256)
    _require(type(observations) is list and len(observations) == 2, "TWO_INDEPENDENT_REVIEWS_REQUIRED")
    writer_result = _prior_result(candidate_file.parent, candidate["case"], candidate["case_sha256"])
    _require(writer_result["status"] == "GREEN_TESTED"
             and writer_result["candidate_sha256"] == expected_candidate_sha256, "WRITER_SOURCE_DRIFT")
    hosts, reviewers, receipts = set(), set(), []
    for observation in observations:
        _require(type(observation) is dict and set(observation) == {"path", "sha256", "host", "reviewer_id"},
                 "EXTERNAL_REVIEW_OBSERVATION_REQUIRED")
        path = _safe_path(observation["path"])
        raw = _read(path)
        _require(_sha(raw) == observation["sha256"], "REVIEW_RECEIPT_PIN_MISMATCH")
        r = json.loads(raw, object_pairs_hook=_unique, parse_constant=_bad_constant)
        _require(r.get("schema") == "r55/independent-workflow-review-v1"
                 and r.get("verdict") == "REVIEW_PASS"
                 and r.get("candidate_sha256") == expected_candidate_sha256
                 and r.get("case_sha256") == candidate["case_sha256"], "REVIEW_FAILED_OR_SOURCE_MISMATCH")
        host, reviewer = observation["host"], observation["reviewer_id"]
        _require(type(host) is str and host and host not in hosts and host != candidate["writer_host"],
                 "INDEPENDENT_HOST_BINDING_REQUIRED")
        _require(type(reviewer) is str and IDENTIFIER.fullmatch(reviewer) and reviewer not in reviewers
                 and reviewer != candidate["author_id"], "INDEPENDENT_REVIEWER_REQUIRED")
        _require(r.get("host") == host and r.get("reviewer_id") == reviewer
                 and r.get("author_id") == candidate["author_id"], "REVIEW_IDENTITY_BINDING_MISMATCH")
        _require(all(r.get(k) is False for k in
                     ("identity_authenticated", "native_muse_invoked", "external_effect_authorized")),
                 "FORGED_REVIEW_AUTHORITY")
        replay_root = path.parent / "replay"
        _require(_sha(_read(replay_root / "result.json")) == r.get("replay_result_sha256"),
                 "REVIEW_RESULT_PIN_MISMATCH")
        replay = _prior_result(replay_root, candidate["case"], candidate["case_sha256"])
        _require(replay["status"] == "GREEN_TESTED" and replay["source_tree"] == candidate["source_tree"]
                 and all(replay.get(k) == candidate[k] for k in
                         ("baseline_commit", "patched_commit", "patch_sha256")), "REVIEW_REPLAY_MISMATCH")
        _require(_matches_tests(replay["red"], candidate["case"], red=True)
                 and _matches_tests(replay["green"], candidate["case"], red=False), "REVIEW_TEST_EVIDENCE_INVALID")
        hosts.add(host)
        reviewers.add(reviewer)
        receipts.append(observation["sha256"])
    return {"status": "COMPLETE", "scope": "DISPOSABLE_REPOSITORY_SOURCE_WORKFLOW_ONLY",
            "candidate_sha256": expected_candidate_sha256, "review_receipt_sha256": receipts,
            "review_hosts": sorted(hosts), "identity_grade": "OPERATOR_BOUND_UNSIGNED_HOST_OBSERVATIONS",
            "identity_authenticated": False, "native_muse_invoked": False,
            "external_effect_authorized": False, "os_sandboxed": False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest="action", required=True)
    run = actions.add_parser("execute")
    run.add_argument("--case", required=True, type=Path)
    run.add_argument("--case-sha256", required=True)
    run.add_argument("--to", required=True, type=Path)
    run.add_argument("--reviewed-code", action="store_true")
    verify = actions.add_parser("review")
    verify.add_argument("--candidate", required=True, type=Path)
    verify.add_argument("--candidate-sha256", required=True)
    verify.add_argument("--author", required=True)
    verify.add_argument("--reviewer", required=True)
    verify.add_argument("--to", required=True, type=Path)
    verify.add_argument("--reviewed-code", action="store_true")
    finish = actions.add_parser("complete")
    finish.add_argument("--candidate", required=True, type=Path)
    finish.add_argument("--candidate-sha256", required=True)
    finish.add_argument("--observations", required=True, type=Path,
                        help="Separate operator-observed receipt SHA/host/reviewer bindings, not candidate assertions")
    args = parser.parse_args(argv)
    try:
        if args.action == "execute":
            result = execute(_json_file(args.case, MAX_CASE), args.to,
                             expected_case_sha256=args.case_sha256, reviewed_code=args.reviewed_code)
            passed = result["status"] == "GREEN_TESTED"
        elif args.action == "review":
            result = review(args.candidate, args.to, expected_candidate_sha256=args.candidate_sha256,
                            reviewer_id=args.reviewer, expected_author_id=args.author,
                            reviewed_code=args.reviewed_code)
            passed = result["verdict"] == "REVIEW_PASS"
        else:
            result = complete(args.candidate, expected_candidate_sha256=args.candidate_sha256,
                              observations=_json_file(args.observations, MAX_LOG))
            passed = result["status"] == "COMPLETE"
        print(json.dumps(result, sort_keys=True, ensure_ascii=False))
        return 0 if passed else 2
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"status": "REFUSED", "reason": str(exc),
                          "native_muse_invoked": False, "external_effect_authorized": False}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

"""Create-only repo-scoped test worktrees for neutral Appwright/Swiftwright.

This *does not* implement, access or duplicate the original Appwright or
Swiftwright engines. It supplies a thin source-only Git/test delivery seam.
No native account, simulator, Xcode project, deployment or external effect.

IMPORTANT: Running reviewed repository tests executes arbitrary code under
the invoking user's OS privileges, not a sandbox. Only run trusted synthetic
or independently isolated source; --allow-reviewed-execution is an assertion,
not permission, isolation, identity or a safety guarantee.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys

from .native_canary import _no_duplicate_json, _reject_constant
from .native_skill_binding import _unsafe_source_path, _regular_bytes

SCHEMA="r69/builder-delivery-v1"
STAGE_SCHEMA="r69/disposable-worktree-stage-v1"
RUN_SCHEMA="r69/builder-worktree-test-v1"
ROLES={"appwright":"python-unittest","swiftwright":"swiftc-typecheck"}
SHA40=re.compile(r"^[0-9a-f]{40}$")
SHA64=re.compile(r"^[0-9a-f]{64}$")
MAX_STAGE_BYTES=64*1024
MAX_OUTPUT_BYTES=2*1024*1024
STAGE_KEYS=frozenset({
 "schema","role","recipe","source_repo","worktree","source_commit",
 "git_tree_oid","tests_executed","native_app_installed",
 "external_effect_authorized","original_engine_invoked"
})
RUN_INTENT="RUN_INTENT.json"
RUN_RECEIPT="RUN_RECEIPT.json"


def _require(ok: bool, name: str) -> None:
    if not ok:
        raise ValueError(name)


def _sha(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()


def _serialized(value:object)->bytes:
    try:
        payload=(json.dumps(value,indent=2,sort_keys=True,
                            ensure_ascii=False,allow_nan=False)+"\n").encode("utf-8")
    except (ValueError,TypeError,UnicodeError,RecursionError) as exc:
        raise ValueError("BUILDER_JSON_SERIALIZATION_REFUSED") from exc
    _require(len(payload)<=MAX_STAGE_BYTES,"BUILDER_RECEIPT_TOO_LARGE")
    return payload


def _path(value:object, *, must_exist:bool) -> Path:
    if not isinstance(value,(str,Path)):
        raise ValueError("BUILDER_PATH_TYPE_REFUSED")
    original=Path(value)
    _require(original.is_absolute() and ".." not in original.parts
             and not _unsafe_source_path(original),"BUILDER_UNSAFE_PATH")
    try:
        resolved=original.resolve(strict=must_exist)
    except (OSError,ValueError,RuntimeError) as exc:
        raise ValueError("BUILDER_PATH_UNRESOLVED") from exc
    _require(not _unsafe_source_path(resolved),"BUILDER_PATH_SYMLINK_REFUSED")
    return resolved


def _new_path(value:object) -> Path:
    dest=_path(value,must_exist=False)
    _require(dest.parent.is_dir() and not dest.exists() and
             not dest.is_symlink() and
             not (hasattr(dest,"is_junction") and dest.is_junction()),
             "BUILDER_OUTPUT_OCCUPIED_OR_PARENT_MISSING")
    return dest


def _git(root:Path,*args:str,timeout:int=35)->str:
    try:
        proc=subprocess.run(["git","-C",str(root),*args],
              capture_output=True,timeout=timeout,
              env=dict(os.environ,GIT_TERMINAL_PROMPT="0"))
    except (OSError,subprocess.TimeoutExpired) as exc:
        raise ValueError("BUILDER_GIT_UNAVAILABLE_OR_TIMED_OUT") from exc
    if proc.returncode!=0:
        raise ValueError("BUILDER_GIT_OPERATION_REFUSED")
    return proc.stdout.decode("utf-8",errors="replace").strip()


def _source(repo:object,commit:object)->tuple[Path,str]:
    _require(type(commit) is str and SHA40.fullmatch(commit) is not None,
             "BUILDER_EXACT_GIT_COMMIT_REQUIRED")
    path=_path(repo,must_exist=True)
    _require(path.is_dir() and (path/".git").exists(),
             "BUILDER_SOURCE_REPOSITORY_REQUIRED")
    top=_path(_git(path,"rev-parse","--show-toplevel"),must_exist=True)
    _require(top==path,"BUILDER_REPOSITORY_ROOT_REQUIRED")
    _require(_git(path,"rev-parse","HEAD")==commit and
             _git(path,"cat-file","-t",commit)=="commit" and
             _git(path,"status","--porcelain","--untracked-files=all")=="",
             "BUILDER_SOURCE_NOT_FROZEN_AND_CLEAN")
    oid=_git(path,"rev-parse",commit+"^{tree}")
    _require(SHA40.fullmatch(oid) is not None,"BUILDER_GIT_TREE_OID_INVALID")
    return path,oid


def _no_containment(a:Path,b:Path)->None:
    _require(a!=b and a not in b.parents and b not in a.parents,
             "BUILDER_REPOSITORY_AND_OUTPUT_MUST_BE_DISJOINT")


def preview_builder_delivery(repo:object,commit:object,role:object)->dict:
    """Create zero files; plan only, never invoke original engines."""
    _require(type(role) is str and role in ROLES,"BUILDER_ROLE_NOT_ADMITTED")
    root,tree=_source(repo,commit)
    return {
        "schema":SCHEMA,
        "role":role,
        "source_commit":commit,
        "git_tree_oid":tree,
        "recipe":ROLES[role],
        "status":"SOURCE_RECIPE_ONLY",
        "requirements":(
          ["Python 3.10+","Git","reviewed disposable repository"] if role=="appwright"
          else ["macOS","Swift command-line tools","Git","reviewed disposable repository"]),
        "source_root":str(root),
        "worktree_stage_requires_optin":True,
        "local_test_execution_requires_separate_optin":True,
        "tests_executed":False,"worker_dispatched":False,
        "original_engine_invoked":False,"native_app_installed":False,
        "external_effect_authorized":False,
        "os_sandbox_provided":False,
    }


def stage_builder_worktree(
    repo:object,commit:object,role:object,
    worktree:object,evidence:object,
    *,allow_disposable_stage:bool=False
)->dict:
    """Create-only detached Git worktree, retain INTENT on unknown effect.

    Makes a local Git worktree metadata change to the *supplied* Git repo.
    The caller must own it. Source files and remote branches remain unchanged.
    It does NOT run tests. Never delete unknown/partial directories for retry.
    """
    _require(allow_disposable_stage is True,"BUILDER_STAGE_OPTIN_REQUIRED")
    preview=preview_builder_delivery(repo,commit,role)
    source=_path(repo,must_exist=True)
    target=_new_path(worktree)
    receipts=_new_path(evidence)
    _no_containment(source,target)
    _no_containment(source,receipts)
    _no_containment(target,receipts)
    receipts.mkdir(exist_ok=False)
    intent={
       "schema":"r69/disposable-worktree-intent-v1",
       "source_repo":str(source),"target_worktree":str(target),
       "role":role,"source_commit":commit,
       "git_tree_oid":preview["git_tree_oid"],
       "effect":"LOCAL_GIT_WORKTREE_METADATA_AND_CHECKOUT_ONLY",
       "tests_executed":False,"external_effect_authorized":False,
    }
    with (receipts/"STAGING_INCOMPLETE").open("xb") as f:
        f.write(_serialized(intent))
        f.flush();os.fsync(f.fileno())
    # The hooks override is intentionally an absent per-run path. It does
    # not disable Git filters or replace actual OS execution isolation.
    _git(source,"-c","core.hooksPath="+str(receipts/"NO_HOOKS"),
         "worktree","add","--detach","--",str(target),commit,timeout=65)
    _require(target.is_dir() and
         _git(target,"rev-parse","HEAD")==commit and
         _git(target,"rev-parse",commit+"^{tree}")==preview["git_tree_oid"] and
         _git(target,"status","--porcelain","--untracked-files=all")=="",
         "BUILDER_STAGED_WORKTREE_NOT_QUALIFIED")
    _source(source,commit)
    receipt={
       "schema":STAGE_SCHEMA,"role":role,"recipe":preview["recipe"],
       "source_repo":str(source),"worktree":str(target),
       "source_commit":commit,"git_tree_oid":preview["git_tree_oid"],
       "tests_executed":False,"native_app_installed":False,
       "external_effect_authorized":False,"original_engine_invoked":False,
    }
    file=receipts/"STAGE_RECEIPT.json"
    with file.open("xb") as f:
        f.write(_serialized(receipt))
        f.flush();os.fsync(f.fileno())
    (receipts/"STAGING_INCOMPLETE").unlink()
    return {
       "schema":STAGE_SCHEMA,"role":role,
       "status":"DISPOSABLE_GIT_WORKTREE_STAGED",
       "source_commit":commit,"git_tree_oid":preview["git_tree_oid"],
       "stage_receipt_sha256":_sha(file.read_bytes()),
       "tests_executed":False,"native_app_installed":False,
       "external_effect_authorized":False,
    }


def inspect_builder_worktree(evidence:object,expected_stage_sha256:object)->dict:
    """Read-only cross-check of exact staged Git HEAD, tree and stage receipt.

    This is local consistency only; same-account edits, Git filters and
    unsigned receipts are not independent source or reviewer authentication.
    """
    _require(type(expected_stage_sha256) is str and
             SHA64.fullmatch(expected_stage_sha256) is not None,
             "EXTERNAL_STAGE_RECEIPT_SHA_REQUIRED")
    root=_path(evidence,must_exist=True)
    _require(root.is_dir() and {p.name for p in root.iterdir()}==
             {"STAGE_RECEIPT.json"},"BUILDER_STAGE_INCOMPLETE_OR_EXTRA_FILES")
    path=root/"STAGE_RECEIPT.json"
    raw=_regular_bytes(path,MAX_STAGE_BYTES)
    _require(_sha(raw)==expected_stage_sha256,
             "BUILDER_STAGE_RECEIPT_SHA_MISMATCH")
    try:
        obj=json.loads(raw,object_pairs_hook=_no_duplicate_json,
                       parse_constant=_reject_constant)
    except (ValueError,TypeError,UnicodeError) as exc:
        raise ValueError("BUILDER_STAGE_RECEIPT_INVALID_JSON") from exc
    _require(type(obj) is dict and set(obj)==STAGE_KEYS
             and obj["schema"]==STAGE_SCHEMA
             and type(obj["role"]) is str and obj["role"] in ROLES
             and obj["recipe"]==ROLES[obj["role"]]
             and obj["tests_executed"] is False
             and obj["native_app_installed"] is False
             and obj["external_effect_authorized"] is False
             and obj["original_engine_invoked"] is False,
             "BUILDER_STAGE_POLICY_OR_SCHEMA_INVALID")
    repo,tree=_source(obj["source_repo"],obj["source_commit"])
    target=_path(obj["worktree"],must_exist=True)
    _require(target.is_dir() and target!=repo and repo not in target.parents
             and obj["git_tree_oid"]==tree,
             "BUILDER_STAGE_SOURCE_OR_TARGET_CHANGED")
    _require(_git(target,"rev-parse","HEAD")==obj["source_commit"]
             and _git(target,"rev-parse",obj["source_commit"]+"^{tree}")==tree
             and _git(target,"status","--porcelain","--untracked-files=all")=="",
             "BUILDER_STAGE_GIT_HEAD_OR_CLEANNESS_DRIFT")
    return {
      **obj,"status":"LOCAL_WORKTREE_SOURCE_MATCH",
      "stage_receipt_sha256":expected_stage_sha256,
      "source_review_authenticated":False,
      "external_effect_authorized":False,
      "os_sandbox_provided":False,
    }


def run_builder_worktree(
    evidence:object,expected_stage_sha256:object,
    output:object,*,allow_reviewed_execution:bool=False
)->dict:
    """Run only reviewed local Python tests or macOS Swift syntax typecheck.

    Explicit caller opt-in is required: arbitrary Python unittest code may
    access the whole OS. This function provides NO security sandbox.
    """
    _require(allow_reviewed_execution is True,
             "BUILDER_REVIEWED_SOURCE_EXECUTION_OPTIN_REQUIRED")
    stage=inspect_builder_worktree(evidence,expected_stage_sha256)
    out=_new_path(output)
    source=_path(stage["source_repo"],must_exist=True)
    worktree=_path(stage["worktree"],must_exist=True)
    _no_containment(source,out)
    _no_containment(worktree,out)
    role=stage["role"]
    if role=="appwright":
        tests=worktree/"tests"
        _require(tests.is_dir() and not _unsafe_source_path(tests)
                 and (tests/"test_sample.py").is_file()
                 and not _unsafe_source_path(tests/"test_sample.py"),
                 "BUILDER_REVIEWED_PYTHON_FIXTURE_MISSING")
        command=[sys.executable,"-B","-m","unittest","discover","-s","tests","-q"]
        status_if_pass="LOCAL_REVIEWED_TEST_PASS"
    else:
        swift=worktree/"Sources/Smoke.swift"
        _require(swift.is_file() and not _unsafe_source_path(swift),
                 "BUILDER_SWIFT_SOURCE_FIXTURE_REQUIRED")
        executable=shutil.which("swiftc") if platform.system()=="Darwin" else None
        command=[executable,"-typecheck",str(swift)] if executable else []
        status_if_pass="LOCAL_REVIEWED_TYPECHECK_PASS"
    out.mkdir(exist_ok=False)
    intent={
       "schema":"r69/builder-run-intent-v1","role":role,
       "source_commit":stage["source_commit"],
       "stage_receipt_sha256":expected_stage_sha256,
       "recipe":stage["recipe"],
       "reviewed_source_optin":True,
       "OS_sandbox":False,"native_app_installed":False,
    }
    with (out/RUN_INTENT).open("xb") as file:
        file.write(_serialized(intent))
        file.flush();os.fsync(file.fileno())
    return_code=None
    raw_out=b"";raw_err=b""
    ran=bool(command)
    spawn_failed=False
    timed_out=False
    if ran:
        try:
            process=subprocess.run(command,cwd=worktree,
                capture_output=True,timeout=90,
                env=dict(os.environ,PYTHONDONTWRITEBYTECODE="1",
                         GIT_TERMINAL_PROMPT="0"))
            return_code=process.returncode
            raw_out=process.stdout[:MAX_OUTPUT_BYTES]
            raw_err=process.stderr[:MAX_OUTPUT_BYTES]
        except OSError:
            # No child process was created: never claim tests executed.
            ran=False
            spawn_failed=True
            raw_err=b"REVIEWED_TEST_SUBPROCESS_NOT_STARTED\n"
        except subprocess.TimeoutExpired:
            # A timed-out process may have made effects before termination.
            # There is no exit code or safe automatic retry.
            timed_out=True
            raw_err=b"REVIEWED_TEST_TIMEOUT_UNKNOWN_EFFECT\n"
    (out/"RUN_STDOUT.log").write_bytes(raw_out)
    (out/"RUN_STDERR.log").write_bytes(raw_err)
    status=("LOCAL_REVIEWED_TEST_NOT_STARTED" if spawn_failed
            else "LOCAL_REVIEWED_TEST_TIMEOUT_HOLD" if timed_out
            else "NOT_RUN_SWIFT_TOOLCHAIN_REQUIRED" if not ran
            else status_if_pass if return_code==0
            else "LOCAL_REVIEWED_TEST_FAIL")
    # Actual worktree writes following a failed test must never be called pass.
    try:
        inspect_builder_worktree(evidence,expected_stage_sha256)
    except ValueError:
        status="LOCAL_REVIEWED_TEST_FAIL"
    result={
      "schema":RUN_SCHEMA,"role":role,
      "source_commit":stage["source_commit"],
      "git_tree_oid":stage["git_tree_oid"],
      "stage_receipt_sha256":expected_stage_sha256,
      "status":status,"test_exit_code":return_code,
      "tests_executed":ran,"native_app_installed":False,
      "original_engine_invoked":False,
      "external_effect_authorized":False,
      "os_sandbox_provided":False,
      "stdout_sha256":_sha(raw_out),"stderr_sha256":_sha(raw_err),
    }
    with (out/RUN_RECEIPT).open("xb") as f:
        f.write(_serialized(result))
        f.flush();os.fsync(f.fileno())
    return result

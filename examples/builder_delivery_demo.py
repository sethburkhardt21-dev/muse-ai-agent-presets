"""End-to-end synthetic Appwright/Swiftwright source-worktree demonstration.

Runs *only* controlled, newly created temporary Git repositories. The Python
unit fixture is actually executed and the Swift fixture is typechecked on
macOS with Swift CLI tools. No native iOS/Xcode app build, deployment,
original Appwright/Swiftwright provider, model or external service.
"""
from __future__ import annotations

import json,os,platform,subprocess,sys,tempfile
from pathlib import Path
from muse_presets.builder_delivery import (
    preview_builder_delivery,stage_builder_worktree,
    inspect_builder_worktree,run_builder_worktree
)

PY_CODE="""import unittest
class FixtureTests(unittest.TestCase):
 def test_fixture(self):
  self.assertEqual((2 * 3), 6)
"""
SWIFT_CODE="struct FixtureSmoke { let answer: Int = 42 }\n"


def _git(repo:Path,*args:str)->str:
    proc=subprocess.run(["git","-C",str(repo),*args],
        capture_output=True,timeout=25)
    if proc.returncode:
        raise RuntimeError("FIXTURE_GIT_OPERATION_FAILED")
    return proc.stdout.decode("utf-8",errors="replace").strip()


def main()->int:
    with tempfile.TemporaryDirectory(prefix="r69-t17-disposable-git-") as folder:
        root=Path(folder).resolve()
        repo=root/"source"
        repo.mkdir()
        initial=subprocess.run(["git","init","-q",str(repo)],
                               capture_output=True,timeout=25)
        if initial.returncode:
            raise RuntimeError("FIXTURE_GIT_INIT_FAILED")
        (repo/"tests").mkdir()
        (repo/"Sources").mkdir()
        (repo/"tests/test_sample.py").write_text(PY_CODE,encoding="utf-8")
        (repo/"Sources/Smoke.swift").write_text(SWIFT_CODE,encoding="utf-8")
        _git(repo,"add","--","tests/test_sample.py","Sources/Smoke.swift")
        _git(repo,"-c","user.name=Fixture","-c",
             "user.email=fixture@example.com","commit","-qm",
             "Synthetic builder source fixture")
        commit=_git(repo,"rev-parse","HEAD")
        results={}
        for role in ("appwright","swiftwright"):
            plan=preview_builder_delivery(repo,commit,role)
            if plan["status"]!="SOURCE_RECIPE_ONLY":
                raise RuntimeError("SOURCE_RECIPE_NOT_SAFE")
            name="worktree-"+role
            target=root/name
            evidence=root/(name+"-receipt")
            stage=stage_builder_worktree(
                repo,commit,role,target,evidence,allow_disposable_stage=True)
            if stage["status"]!="DISPOSABLE_GIT_WORKTREE_STAGED" or stage["tests_executed"]:
                raise RuntimeError("STAGING_EXECUTED_SOURCE_UNEXPECTEDLY")
            reviewed=inspect_builder_worktree(evidence,stage["stage_receipt_sha256"])
            if reviewed["status"]!="LOCAL_WORKTREE_SOURCE_MATCH":
                raise RuntimeError("STAGED_WORKTREE_NOT_PINNED")
            tested=run_builder_worktree(
                evidence,stage["stage_receipt_sha256"],
                root/("local-test-"+role),allow_reviewed_execution=True)
            if role=="appwright" and tested["status"]!="LOCAL_REVIEWED_TEST_PASS":
                raise RuntimeError("SYNTHETIC_PYTHON_TEST_FAILED")
            if role=="swiftwright" and platform.system()=="Darwin":
                if tested["status"]!="LOCAL_REVIEWED_TYPECHECK_PASS":
                    raise RuntimeError("LOCAL_SWIFT_TYPECHECK_FAILED")
            elif role=="swiftwright":
                if tested["status"]!="NOT_RUN_SWIFT_TOOLCHAIN_REQUIRED":
                    raise RuntimeError("PLATFORM_UNSUPPORTED_WAS_CLAIMED_PASS")
            if (tested["native_app_installed"] or
                tested["external_effect_authorized"] or
                tested["original_engine_invoked"]):
                raise RuntimeError("FALSE_NATIVE_AUTHORITY_CLAIM")
            results[role]={
                "stage_status":stage["status"],
                "test_status":tested["status"],
                "tests_executed":tested["tests_executed"],
                "native_app_installed":False,
            }
        clean=_git(repo,"status","--porcelain","--untracked-files=all")==""
        if not clean:
            raise RuntimeError("SOURCE_GIT_REPO_MUTATED")
        print(json.dumps({
            "schema":"r69/builder-delivery-synthetic-demo-v1",
            "status":"LOCAL_SYNTHETIC_BUILDER_DEMO_PASS",
            "roles":results,
            "source_root_clean":clean,
            "temporary_git_repositories_only":True,
            "actual_swift_toolchain":platform.system()=="Darwin",
            "xcodebuild_or_ios_app_build":False,
            "original_appwright_engine_invoked":False,
            "original_swiftwright_engine_invoked":False,
            "native_app_installed":False,
            "external_effect_authorized":False,
            "OS_sandbox_provided":False,
        },sort_keys=True,indent=2))
    return 0


if __name__=="__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError,ValueError,OSError) as exc:
        print(json.dumps({"status":"REFUSED","reason":str(exc),
            "native_app_installed":False,
            "external_effect_authorized":False},sort_keys=True))
        raise SystemExit(2)

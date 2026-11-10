"""T17 opt-in CLI acceptance in synthetic Git repositories only."""
from __future__ import annotations
import contextlib,io,json,os,platform,subprocess,sys,tempfile,unittest
from pathlib import Path
from muse_presets.cli import main

class BuilderCliTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(prefix="r69-builder-cli-")
  self.addCleanup(self.tmp.cleanup)
  self.root=Path(self.tmp.name).resolve()
  self.repo=self.root/"repo";self.repo.mkdir()
  git=lambda *args:subprocess.run(["git",*args],cwd=self.repo,capture_output=True,text=True,timeout=20,check=True)
  git("init","-q")
  (self.repo/"tests").mkdir()
  (self.repo/"Sources").mkdir()
  (self.repo/"tests/test_sample.py").write_text(
   "import unittest\nclass Foo(unittest.TestCase):\n def test_one(self): self.assertEqual(1,1)\n",encoding="utf-8")
  (self.repo/"Sources/Smoke.swift").write_text(
   "struct Smoke { let value: Int = 1 }\n",encoding="utf-8")
  git("add","tests/test_sample.py","Sources/Smoke.swift")
  git("-c","user.name=Fixture","-c","user.email=fixture@example.com",
      "commit","-qm","Fixture")
  self.sha=git("rev-parse","HEAD").stdout.strip()
  self.dest=self.root/"worktree"
  self.evidence=self.root/"receipt"

 def call(self,args):
  out=io.StringIO()
  with contextlib.redirect_stdout(out):
   code=main(args)
  return code,json.loads(out.getvalue())

 def test_plan_cli_has_no_git_or_file_effect(self):
  code,data=self.call(["builder-plan","--role","appwright",
     "--repo",str(self.repo),"--commit",self.sha])
  self.assertEqual(code,0)
  self.assertEqual(data["status"],"SOURCE_RECIPE_ONLY")
  self.assertFalse(data["tests_executed"])
  self.assertFalse(self.dest.exists())
  self.assertFalse(self.evidence.exists())

 def test_stage_requires_separate_optin_and_then_inspects(self):
  args=["builder-stage","--role","appwright",
    "--repo",str(self.repo),"--commit",self.sha,
    "--to",str(self.dest),"--evidence",str(self.evidence)]
  rc,refused=self.call(args)
  self.assertEqual(rc,2)
  self.assertEqual(refused["status"],"REFUSED")
  self.assertFalse(self.dest.exists())
  rc,staged=self.call(args+["--allow-disposable-stage"])
  self.assertEqual(rc,0)
  self.assertEqual(staged["status"],"DISPOSABLE_GIT_WORKTREE_STAGED")
  rc,inspected=self.call(["builder-inspect","--evidence",str(self.evidence),
       "--stage-sha256",staged["stage_receipt_sha256"]])
  self.assertEqual(rc,0)
  self.assertEqual(inspected["status"],"LOCAL_WORKTREE_SOURCE_MATCH")

 def test_cli_actually_runs_disposable_python_and_checks_result(self):
  args=["builder-stage","--role","appwright","--repo",str(self.repo),
    "--commit",self.sha,"--to",str(self.dest),
    "--evidence",str(self.evidence),"--allow-disposable-stage"]
  rc,stage=self.call(args)
  self.assertEqual(rc,0)
  out=self.root/"results"
  cmd=["builder-run","--evidence",str(self.evidence),
     "--stage-sha256",stage["stage_receipt_sha256"],"--to",str(out)]
  rc,refused=self.call(cmd)
  self.assertEqual(rc,2)
  self.assertEqual(refused["status"],"REFUSED")
  self.assertFalse(out.exists())
  rc,executed=self.call(cmd+["--allow-reviewed-execution"])
  self.assertEqual(rc,0)
  self.assertEqual(executed["status"],"LOCAL_REVIEWED_TEST_PASS")
  self.assertEqual(executed["test_exit_code"],0)
  self.assertTrue((out/"RUN_RECEIPT.json").is_file())

 def test_wrong_external_sha_is_refused(self):
  args=["builder-stage","--role","appwright","--repo",str(self.repo),
    "--commit",self.sha,"--to",str(self.dest),
    "--evidence",str(self.evidence),"--allow-disposable-stage"]
  rc,data=self.call(args)
  self.assertEqual(rc,0)
  out=self.root/"bad"
  rc,refused=self.call(["builder-run","--evidence",str(self.evidence),
     "--stage-sha256","0"*64,"--to",str(out),
     "--allow-reviewed-execution"])
  self.assertEqual(rc,2)
  self.assertEqual(refused["status"],"REFUSED")
  self.assertFalse(out.exists())

 def test_actual_separate_process_disposable_build_demo(self):
  source=Path(__file__).resolve().parents[1]
  env=dict(os.environ,PYTHONPATH=str(source/"src"),PYTHONDONTWRITEBYTECODE="1")
  proc=subprocess.run([sys.executable,"-B",str(source/"examples/builder_delivery_demo.py")],
       cwd=source,env=env,capture_output=True,text=True,timeout=110)
  self.assertEqual(proc.returncode,0,proc.stdout+proc.stderr)
  result=json.loads(proc.stdout)
  self.assertEqual(result["status"],"LOCAL_SYNTHETIC_BUILDER_DEMO_PASS")
  self.assertTrue(result["source_root_clean"])
  self.assertTrue(result["temporary_git_repositories_only"])
  self.assertEqual(result["roles"]["appwright"]["test_status"],"LOCAL_REVIEWED_TEST_PASS")
  if platform.system()=="Darwin":
   self.assertEqual(result["roles"]["swiftwright"]["test_status"],
                    "LOCAL_REVIEWED_TYPECHECK_PASS")
  else:
   self.assertEqual(result["roles"]["swiftwright"]["test_status"],
                    "NOT_RUN_SWIFT_TOOLCHAIN_REQUIRED")
  self.assertFalse(result["native_app_installed"])
  self.assertFalse(result["external_effect_authorized"])

 def test_cli_spawn_refusal_or_unknown_timeout_returns_nonzero(self):
  from unittest.mock import patch
  for status,executed in (
      ("LOCAL_REVIEWED_TEST_NOT_STARTED",False),
      ("LOCAL_REVIEWED_TEST_TIMEOUT_HOLD",True)):
   with self.subTest(status=status):
    with patch("muse_presets.builder_delivery.run_builder_worktree",
               return_value={"status":status,"tests_executed":executed,
                   "test_exit_code":None,"native_app_installed":False,
                   "external_effect_authorized":False}):
     rc,reply=self.call([
       "builder-run","--evidence",str(self.evidence),
       "--stage-sha256","a"*64,"--to",str(self.root/"not-created"),
       "--allow-reviewed-execution"])
    self.assertEqual(rc,2)
    self.assertEqual(reply["status"],status)
    self.assertEqual(reply["tests_executed"],executed)
    self.assertFalse((self.root/"not-created").exists())

if __name__=="__main__":
 unittest.main()

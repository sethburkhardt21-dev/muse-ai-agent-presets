"""T17 source-only repo-scoped Appwright/Swiftwright build/test delivery adapter.

Runs only self-created disposable repositories; no deployment or connected
Appwright/Swiftwright engines. Includes real Git worktree and subprocess checks.
"""
from __future__ import annotations
import hashlib,json,os,platform,subprocess,sys,tempfile,unittest
from pathlib import Path
from muse_presets.builder_delivery import (
 preview_builder_delivery,stage_builder_worktree,
 inspect_builder_worktree,run_builder_worktree
)

PY_SAMPLE="""import unittest
class SampleTests(unittest.TestCase):
 def test_addition(self):
  self.assertEqual(2 + 2, 4)
"""
SWIFT_SAMPLE="struct BuilderSmoke { let value: Int = 7 }\n"
def git(repo,*argv,allow_failure=False):
 p=subprocess.run(["git","-C",str(repo),*argv],capture_output=True,text=True,timeout=20)
 if not allow_failure and p.returncode:
  raise AssertionError(f"git {argv} failed: {p.stderr}")
 return p.stdout.strip()


class BuilderDeliveryTests(unittest.TestCase):
 def setUp(self):
  temp=tempfile.TemporaryDirectory(prefix="r69-builder-")
  self.addCleanup(temp.cleanup)
  self.root=Path(temp.name).resolve()
  self.repo=self.root/"source"
  self.repo.mkdir()
  p=subprocess.run(["git","init","-q",str(self.repo)],capture_output=True,text=True,timeout=20)
  self.assertEqual(p.returncode,0,p.stderr)
  (self.repo/"tests").mkdir()
  (self.repo/"Sources").mkdir()
  (self.repo/"tests/test_sample.py").write_text(PY_SAMPLE,encoding="utf-8")
  (self.repo/"Sources/Smoke.swift").write_text(SWIFT_SAMPLE,encoding="utf-8")
  git(self.repo,"add","--","tests/test_sample.py","Sources/Smoke.swift")
  git(self.repo,"-c","user.name=Fixture",
      "-c","user.email=fixture@example.com","commit","-qm","Synthetic fixture")
  self.commit=git(self.repo,"rev-parse","HEAD")
  self.assertEqual(len(self.commit),40)

 def stage(self,role="appwright",suffix="one"):
  dest=self.root/("stage-"+suffix)
  evidence=self.root/("stage-evidence-"+suffix)
  result=stage_builder_worktree(self.repo,self.commit,role,dest,evidence,
                                allow_disposable_stage=True)
  return dest,evidence,result

 def test_preview_has_explicit_separate_engine_and_no_auto_execution(self):
  for role in ("appwright","swiftwright"):
   with self.subTest(role=role):
    row=preview_builder_delivery(self.repo,self.commit,role)
    self.assertEqual(row["status"],"SOURCE_RECIPE_ONLY")
    self.assertEqual(row["source_commit"],self.commit)
    self.assertEqual(row["role"],role)
    self.assertFalse(row["native_app_installed"])
    self.assertFalse(row["tests_executed"])
    self.assertFalse(row["external_effect_authorized"])
    self.assertFalse(row["worker_dispatched"])
    self.assertEqual(git(self.repo,"status","--porcelain"),"")

 def test_real_git_worktree_stage_is_create_only_and_no_tests_auto_run(self):
  dest,evidence,result=self.stage()
  self.assertEqual(result["status"],"DISPOSABLE_GIT_WORKTREE_STAGED")
  self.assertFalse(result["tests_executed"])
  self.assertFalse(result["native_app_installed"])
  self.assertEqual(git(dest,"rev-parse","HEAD"),self.commit)
  self.assertEqual(git(dest,"status","--porcelain"),"")
  self.assertEqual(git(self.repo,"status","--porcelain"),"")
  pinned=result["stage_receipt_sha256"]
  inspected=inspect_builder_worktree(evidence,pinned)
  self.assertEqual(inspected["status"],"LOCAL_WORKTREE_SOURCE_MATCH")
  self.assertEqual(inspected["source_commit"],self.commit)
  self.assertFalse(inspected["external_effect_authorized"])
  self.assertEqual(set(p.name for p in evidence.iterdir()),
                   {"STAGE_RECEIPT.json"})

 def test_no_staging_without_explicit_operator_optin(self):
  dest=self.root/"forbidden"
  evidence=self.root/"forbidden-evidence"
  with self.assertRaises(ValueError):
   stage_builder_worktree(self.repo,self.commit,"appwright",dest,evidence)
  self.assertFalse(dest.exists())
  self.assertFalse(evidence.exists())

 def test_occupied_worktree_does_not_overwrite_or_mutate(self):
  dest=self.root/"occupied";dest.mkdir()
  (dest/"owner.txt").write_text("preserve",encoding="utf-8")
  with self.assertRaises(ValueError):
   stage_builder_worktree(self.repo,self.commit,"appwright",
      dest,self.root/"evidence",allow_disposable_stage=True)
  self.assertEqual((dest/"owner.txt").read_text(),"preserve")
  self.assertFalse((self.root/"evidence").exists())

 def test_already_existing_evidence_refused_without_new_worktree(self):
  evidence=self.root/"evidence";evidence.mkdir()
  dest=self.root/"dest"
  with self.assertRaises(ValueError):
   stage_builder_worktree(self.repo,self.commit,"appwright",
      dest,evidence,allow_disposable_stage=True)
  self.assertFalse(dest.exists())

 def test_wrong_commit_and_untrusted_roles_refused(self):
  for wrong in ("0"*40,"ABC"*13+"A","main","",[],None):
   with self.subTest(wrong=repr(wrong)),self.assertRaises(ValueError):
    preview_builder_delivery(self.repo,wrong,"appwright")
  for role in ("hack",[],"appwright; rm -rf /",None,False):
   with self.subTest(role=repr(role)),self.assertRaises(ValueError):
    preview_builder_delivery(self.repo,self.commit,role)

 def test_dirty_source_refuses_preview_and_stage(self):
  (self.repo/"owner-new.txt").write_text("scratch",encoding="utf-8")
  with self.assertRaises(ValueError):
   preview_builder_delivery(self.repo,self.commit,"appwright")
  with self.assertRaises(ValueError):
   stage_builder_worktree(self.repo,self.commit,"appwright",
      self.root/"dest",self.root/"evidence",allow_disposable_stage=True)
  self.assertFalse((self.root/"dest").exists())

 def test_symlinked_source_repo_refused(self):
  alias=self.root/"repo-link"
  try:alias.symlink_to(self.repo,target_is_directory=True)
  except (OSError,NotImplementedError):self.skipTest("symlink unavailable")
  with self.assertRaises(ValueError):
   preview_builder_delivery(alias,self.commit,"appwright")

 def test_source_path_cannot_be_nested_git_subfolder(self):
  with self.assertRaises(ValueError):
   preview_builder_delivery(self.repo/"tests",self.commit,"appwright")

 def test_inspect_refuses_wrong_hash_tampered_receipt_or_extra_evidence(self):
  _,evidence,result=self.stage()
  with self.assertRaises(ValueError):
   inspect_builder_worktree(evidence,"0"*64)
  (evidence/"STAGE_RECEIPT.json").write_text('{"forged":true}',encoding="utf-8")
  with self.assertRaises(ValueError):
   inspect_builder_worktree(evidence,result["stage_receipt_sha256"])

 def test_inspect_refuses_dirty_worktree_after_stage(self):
  dest,evidence,result=self.stage()
  (dest/"unexpected.txt").write_text("mutated",encoding="utf-8")
  with self.assertRaises(ValueError):
   inspect_builder_worktree(evidence,result["stage_receipt_sha256"])

 def test_actual_appwright_python_unit_suite_in_disposable_worktree(self):
  dest,evidence,result=self.stage()
  out=self.root/"test-results"
  with self.assertRaises(ValueError):
   run_builder_worktree(evidence,result["stage_receipt_sha256"],
                        out)
  self.assertFalse(out.exists())
  grade=run_builder_worktree(evidence,result["stage_receipt_sha256"],out,
                             allow_reviewed_execution=True)
  self.assertEqual(grade["status"],"LOCAL_REVIEWED_TEST_PASS")
  self.assertEqual(grade["role"],"appwright")
  self.assertEqual(grade["test_exit_code"],0)
  self.assertTrue((out/"RUN_RECEIPT.json").exists())
  self.assertFalse(grade["native_app_installed"])
  self.assertFalse(grade["external_effect_authorized"])
  self.assertEqual(git(self.repo,"status","--porcelain"),"")
  self.assertEqual(git(dest,"status","--porcelain"),"")

 def test_python_failure_is_fail_not_hidden_as_pass(self):
  (self.repo/"tests/test_sample.py").write_text(
    PY_SAMPLE.replace("2 + 2, 4","2 + 2, 5"),encoding="utf-8")
  git(self.repo,"add","--","tests/test_sample.py")
  git(self.repo,"-c","user.name=Fixture",
      "-c","user.email=fixture@example.com","commit","-qm","Intentional RED fixture")
  new_sha=git(self.repo,"rev-parse","HEAD")
  dest=self.root/"broken-stage";evidence=self.root/"broken-evidence"
  stage=stage_builder_worktree(self.repo,new_sha,"appwright",
       dest,evidence,allow_disposable_stage=True)
  output=self.root/"red-receipt"
  report=run_builder_worktree(evidence,stage["stage_receipt_sha256"],
      output,allow_reviewed_execution=True)
  self.assertEqual(report["status"],"LOCAL_REVIEWED_TEST_FAIL")
  self.assertNotEqual(report["test_exit_code"],0)
  self.assertTrue((output/"RUN_RECEIPT.json").is_file())

 def test_test_receipt_cannot_be_replayed_with_changed_source(self):
  dest,evidence,result=self.stage()
  (dest/"tests/test_sample.py").write_text("print('changed')",encoding="utf-8")
  output=self.root/"replay"
  with self.assertRaises(ValueError):
   run_builder_worktree(evidence,result["stage_receipt_sha256"],
       output,allow_reviewed_execution=True)
  self.assertFalse(output.exists())

 def test_wrong_receipt_pin_cannot_run_tests(self):
  _,evidence,result=self.stage()
  output=self.root/"wrongpin"
  with self.assertRaises(ValueError):
   run_builder_worktree(evidence,"f"*64,output,
        allow_reviewed_execution=True)
  self.assertFalse(output.exists())

 def test_multiple_disjoint_worktrees_preserve_original_source(self):
  a,ea,ra=self.stage("appwright","a")
  b,eb,rb=self.stage("swiftwright","b")
  self.assertNotEqual(a,b)
  self.assertEqual(git(a,"rev-parse","HEAD"),
                   git(b,"rev-parse","HEAD"))
  self.assertEqual(git(self.repo,"status","--porcelain"),"")
  self.assertEqual(inspect_builder_worktree(ea,ra["stage_receipt_sha256"])["status"],
                   "LOCAL_WORKTREE_SOURCE_MATCH")
  self.assertEqual(inspect_builder_worktree(eb,rb["stage_receipt_sha256"])["status"],
                   "LOCAL_WORKTREE_SOURCE_MATCH")

 def test_swiftwright_native_typecheck_only_when_toolchain_available(self):
  dest,evidence,result=self.stage("swiftwright","swift")
  output=self.root/"swift-typecheck"
  tested=run_builder_worktree(evidence,result["stage_receipt_sha256"],
        output,allow_reviewed_execution=True)
  if platform.system()!="Darwin":
   self.assertEqual(tested["status"],"NOT_RUN_SWIFT_TOOLCHAIN_REQUIRED")
   self.assertFalse(tested["tests_executed"])
  else:
   self.assertEqual(tested["status"],"LOCAL_REVIEWED_TYPECHECK_PASS")
   self.assertTrue(tested["tests_executed"])
   self.assertEqual(tested["test_exit_code"],0)
  self.assertFalse(tested["native_app_installed"])

 def test_interrupted_git_worktree_stage_preserves_intent_and_refuses_retry(self):
  from unittest.mock import patch
  from muse_presets import builder_delivery as builder
  original=builder._git
  def simulate_worktree_add_failure(root,*args,**kwargs):
   if "worktree" in args and "add" in args:
    raise ValueError("SIMULATED_DISPOSABLE_GIT_INTERRUPTION")
   return original(root,*args,**kwargs)
  dest=self.root/"interrupted-stage"
  evidence=self.root/"interrupted-evidence"
  with patch.object(builder,"_git",side_effect=simulate_worktree_add_failure):
   with self.assertRaises(ValueError):
    stage_builder_worktree(self.repo,self.commit,"appwright",
       dest,evidence,allow_disposable_stage=True)
  self.assertTrue((evidence/"STAGING_INCOMPLETE").is_file())
  self.assertFalse((evidence/"STAGE_RECEIPT.json").exists())
  self.assertFalse(dest.exists())
  with self.assertRaises(ValueError):
   stage_builder_worktree(self.repo,self.commit,"appwright",
       dest,evidence,allow_disposable_stage=True)
  self.assertTrue((evidence/"STAGING_INCOMPLETE").is_file())

 def test_self_rehashed_forged_native_authority_is_refused(self):
  _,evidence,result=self.stage()
  receipt=evidence/"STAGE_RECEIPT.json"
  forged=json.loads(receipt.read_text(encoding="utf-8"))
  forged["native_app_installed"]=True
  raw=(json.dumps(forged,indent=2,sort_keys=True,ensure_ascii=False)+"\n").encode("utf-8")
  # Caller also rehashes to simulate a malicious same-account writer;
  # a correct local pin alone is never native authority.
  receipt.write_bytes(raw)
  with self.assertRaises(ValueError):
   inspect_builder_worktree(evidence,hashlib.sha256(raw).hexdigest())

 def test_path_traversal_and_symlink_stage_destination_refused(self):
  for dest in (self.root/".." /"escape",):
   with self.assertRaises(ValueError):
    stage_builder_worktree(self.repo,self.commit,"appwright",
         dest,self.root/"not-used",allow_disposable_stage=True)
  link=self.root/"folderlink"
  try:link.symlink_to(self.root,target_is_directory=True)
  except (OSError,NotImplementedError):self.skipTest("symlink unavailable")
  with self.assertRaises(ValueError):
   stage_builder_worktree(self.repo,self.commit,"appwright",
     link/"stage",self.root/"should-not-exist",allow_disposable_stage=True)

 def test_fail_closed_input_types_do_not_crash_unhandled(self):
  for invalid in ([],{},None,False,0,""):
   with self.subTest(input=repr(invalid)),self.assertRaises(ValueError):
    preview_builder_delivery(invalid,self.commit,"appwright")
   with self.subTest(commit=repr(invalid)),self.assertRaises(ValueError):
    preview_builder_delivery(self.repo,invalid,"appwright")

 def test_pre_spawn_failure_cannot_claim_tests_executed(self):
  from unittest.mock import patch
  from muse_presets import builder_delivery as builder
  _,evidence,stage=self.stage("appwright","spawn-refusal")
  out=self.root/"spawn-refusal-output"
  orig_run=subprocess.run
  def deny_python_spawn(command,*args,**kwargs):
   if (type(command) is list and
       command[:4]==[sys.executable,"-B","-m","unittest"]):
    raise OSError("synthetic Python subprocess did not start")
   return orig_run(command,*args,**kwargs)
  with patch.object(builder.subprocess,"run",side_effect=deny_python_spawn):
   outcome=run_builder_worktree(evidence,stage["stage_receipt_sha256"],
      out,allow_reviewed_execution=True)
  self.assertEqual(outcome["status"],"LOCAL_REVIEWED_TEST_NOT_STARTED")
  self.assertFalse(outcome["tests_executed"])
  self.assertIsNone(outcome["test_exit_code"])
  self.assertEqual(json.loads((out/"RUN_RECEIPT.json").read_text()),outcome)
  with self.assertRaises(ValueError):
   run_builder_worktree(evidence,stage["stage_receipt_sha256"],
      out,allow_reviewed_execution=True)

 def test_timeout_is_unknown_effect_hold_not_invented_exit_code(self):
  from unittest.mock import patch
  from muse_presets import builder_delivery as builder
  _,evidence,stage=self.stage("appwright","timeout")
  out=self.root/"timeout-output"
  orig_run=subprocess.run
  def timeout_python_test(command,*args,**kwargs):
   if (type(command) is list and
       command[:4]==[sys.executable,"-B","-m","unittest"]):
    raise subprocess.TimeoutExpired(cmd=command,timeout=90)
   return orig_run(command,*args,**kwargs)
  with patch.object(builder.subprocess,"run",side_effect=timeout_python_test):
   outcome=run_builder_worktree(evidence,stage["stage_receipt_sha256"],
      out,allow_reviewed_execution=True)
  self.assertEqual(outcome["status"],"LOCAL_REVIEWED_TEST_TIMEOUT_HOLD")
  self.assertTrue(outcome["tests_executed"])
  self.assertIsNone(outcome["test_exit_code"])
  self.assertTrue((out/"RUN_INTENT.json").is_file())
  self.assertEqual(json.loads((out/"RUN_RECEIPT.json").read_text()),outcome)


if __name__=="__main__":
 unittest.main()

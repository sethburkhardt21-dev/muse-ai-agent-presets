"""R31 public-neutral executable Claim Gate CLI acceptance tests."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
CLI=ROOT/"presets/software-engineer/runtime/claim-gate/engineering_claim_gate.py"

@unittest.skipUnless(os.name=="posix","Exact original implementation requires POSIX fcntl")
class CliContractTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory(prefix="neutral-engineering-")
  self.addCleanup(self.temp.cleanup)
  self.home=Path(self.temp.name)
  self.scope=self.home/"sources"
  self.scope.mkdir()
  self.state=self.home/"state"
  self.state.mkdir()
  self.payload=self.scope/"input.txt"
  self.payload.write_bytes(b"synthetic change v1")

 def run_cli(self,action,*args):
  cmd=[sys.executable,"-I","-B",str(CLI),
       "--state-dir",str(self.state),
       "--scope","engineering",
       "--claim-id","issue-001",action,*args]
  res=subprocess.run(cmd,capture_output=True,text=True,timeout=8,
                     env={"PYTHONDONTWRITEBYTECODE":"1","PATH":os.environ.get("PATH","")})
  try:body=json.loads(res.stdout)
  except ValueError:self.fail("Non-JSON CLI: "+res.stdout+" "+res.stderr)
  return res.returncode,body

 def claim(self):
  return self.run_cli("claim","--source-root",str(self.scope),"--payload","input.txt")

 def test_original_atomic_gate_claim_and_identical_reuse_across_processes(self):
  rc,a=self.claim()
  self.assertEqual(rc,0,a)
  self.assertEqual(a["status"],"LOCAL_CLAIM_RECORDED")
  self.assertEqual(a["state"],"CLAIMED")
  self.assertFalse(a["native_muse_invoked"])
  self.assertFalse(a["external_effect_authorized"])
  rc,b=self.claim()
  self.assertEqual(rc,0)
  self.assertEqual(b["status"],"LOCAL_CLAIM_REUSED")
  self.assertEqual(b["payload_sha256"],a["payload_sha256"])
  rc,c=self.run_cli("inspect")
  self.assertEqual(rc,0)
  self.assertEqual(c["state"],"CLAIMED")

 def test_changed_bytes_refuse_without_creating_second_operation(self):
  self.assertEqual(self.claim()[0],0)
  self.payload.write_bytes(b"synthetic change v2")
  rc,r=self.claim()
  self.assertEqual(rc,2)
  self.assertEqual(r["error_code"],"REPLAY_REFUSED")
  self.assertEqual(self.run_cli("inspect")[1]["state"],"CLAIMED")

 def test_cancelled_same_bytes_is_terminal_and_changed_bytes_refuse(self):
  self.assertEqual(self.claim()[0],0)
  rc,held=self.run_cli("cancel","--reason","synthetic owner cancellation")
  self.assertEqual(rc,0);self.assertEqual(held["state"],"CANCELLED")
  rc,same=self.claim()
  self.assertEqual(rc,0);self.assertEqual(same["state"],"CANCELLED")
  self.payload.write_bytes(b"synthetic changed after cancel")
  rc,bad=self.claim()
  self.assertEqual(rc,2);self.assertEqual(bad["error_code"],"REPLAY_REFUSED")
  self.assertEqual(self.run_cli("inspect")[1]["state"],"CANCELLED")

 def test_unknown_after_interruption_blocks_reexecution(self):
  self.assertEqual(self.claim()[0],0)
  rc,r=self.run_cli("hold-unknown","--reason","synthetic effect uncertain")
  self.assertEqual(rc,0);self.assertEqual(r["state"],"UNKNOWN")
  rc,r=self.claim()
  self.assertEqual(rc,0);self.assertEqual(r["status"],"LOCAL_CLAIM_REUSED")
  rc,r=self.run_cli("inspect")
  self.assertEqual(rc,0);self.assertEqual(r["state"],"UNKNOWN")
  self.assertFalse(r["external_effect_authorized"])

 def test_missing_claim_read_does_not_mint_effect(self):
  rc,r=self.run_cli("inspect")
  self.assertEqual(rc,0)
  self.assertEqual(r["status"],"LOCAL_CLAIM_ABSENT")
  self.assertFalse(r["external_effect_authorized"])

 def test_untrusted_source_symlink_and_traversal_refused(self):
  bad=self.scope/"alias.txt"
  try:bad.symlink_to(self.payload)
  except (OSError,NotImplementedError):self.skipTest("symlink unavailable")
  rc,x=self.run_cli("claim","--source-root",str(self.scope),"--payload","alias.txt")
  self.assertEqual(rc,2);self.assertEqual(x["error_code"],"SOURCE_PATH_REFUSED")
  rc,x=self.run_cli("claim","--source-root",str(self.scope),"--payload","../outside.txt")
  self.assertEqual(rc,2);self.assertEqual(x["error_code"],"SOURCE_PATH_REFUSED")
  self.assertFalse((self.state/"claims").exists())

 def test_no_shell_command_or_effect_clearance_supported(self):
  rc,x=self.run_cli("mark-effect","--reason","forged success")
  self.assertNotEqual(rc,0)
  self.assertFalse(x["external_effect_authorized"])
  rc,x=self.run_cli("run-command","--reason","echo nope")
  self.assertNotEqual(rc,0)
  self.assertFalse(x["native_muse_invoked"])

 def test_actual_original_fencing_guard_stays_durable(self):
  sys.path.insert(0,str(ROOT/"presets/software-engineer/runtime/claim-gate"))
  from gate_token_guard import TokenGuard
  digest=hashlib.sha256(b"synthetic proposed output").hexdigest()
  guard=TokenGuard(str(self.home/"fenced-resource"))
  self.assertTrue(guard.honor("engineering","issue-001",1,effect_digest=digest))
  self.assertFalse(guard.honor("engineering","issue-001",1,effect_digest=digest))
  self.assertTrue(guard.honor("engineering","issue-001",2,effect_digest=digest))
  reloaded=TokenGuard(str(self.home/"fenced-resource"))
  self.assertFalse(reloaded.honor("engineering","issue-001",1,effect_digest=digest))

if __name__=="__main__":unittest.main(verbosity=2)

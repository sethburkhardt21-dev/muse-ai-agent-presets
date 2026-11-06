"""Acceptance tests for neutral runtime transplanted from exact original source."""
from __future__ import annotations
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
RUNTIME=ROOT/"presets/software-engineer/runtime/claim-gate"
MODULES=(
 "claim_gate.py","gate_retention.py","distributed_claim_gate.py",
 "gate_token_guard.py","gate_approval.py","gate_composite.py",
 "gate_admission.py","gate_restart.py")
PRIVATE_TERMS=re.compile(
 r"(?i)\b(?:"
 r"private-persona|character-title)\b|" + re.escape("/"+"home/")+r"[a-z0-9_-]+/"
)
sys.path.insert(0,str(RUNTIME))


class PortableSourceContract(unittest.TestCase):
 def test_nine_runtime_sources_are_byte_pinned_and_neutral_on_every_platform(self):
  manifest=json.loads((RUNTIME/"ENGINE.json").read_text())
  names={*MODULES,"engineering_claim_gate.py"}
  self.assertEqual(set(manifest["files"]),names)
  self.assertEqual(manifest["native_muse_status"],"UNBOUND")
  self.assertFalse(manifest["external_effects_enabled"])
  self.assertEqual(manifest["registered_native_tools"],[])
  for name,expected in manifest["files"].items():
   source=(RUNTIME/name).read_bytes()
   self.assertEqual(hashlib.sha256(source).hexdigest(),expected,name)
   ast.parse(source.decode("utf8"),filename=name)
   self.assertIsNone(PRIVATE_TERMS.search(source.decode("utf8")),name)


@unittest.skipUnless(os.name=="posix","Original gate uses POSIX fcntl locking")
class PortTests(unittest.TestCase):
 def test_all_eight_real_source_modules_present_parse_and_are_neutral(self):
  self.assertEqual(len(MODULES),8)
  for name in MODULES:
   p=RUNTIME/name
   self.assertTrue(p.is_file(),name)
   src=p.read_text(encoding="utf8")
   ast.parse(src,filename=str(p))
   self.assertIsNone(PRIVATE_TERMS.search(src),name)
   self.assertNotIn("subprocess.Popen",src)
   self.assertGreater(p.stat().st_size,1500)

 def test_original_atomic_claim_replay_and_restart(self):
  from claim_gate import ClaimGate,ReplayRefused
  with tempfile.TemporaryDirectory(prefix="generic-gate-") as path:
   first=ClaimGate(path)
   created,_=first.claim("engineering","issue-001",b"synthetic bug fix A")
   self.assertTrue(created)
   second=ClaimGate(path)
   reused,record=second.claim("engineering","issue-001",b"synthetic bug fix A")
   self.assertFalse(reused);self.assertEqual(record["state"],"CLAIMED")
   with self.assertRaises(ReplayRefused):
    second.claim("engineering","issue-001",b"synthetic bug fix B")
   self.assertTrue(second.verify_bytes("engineering","issue-001",b"synthetic bug fix A"))

 def test_unknown_is_durable_and_read_only_after_restart(self):
  from claim_gate import ClaimGate
  with tempfile.TemporaryDirectory(prefix="generic-gate-") as path:
   gate=ClaimGate(path)
   gate.claim("engineering","issue-002",b"synthetic operation")
   gate.mark_unknown("engineering","issue-002","no original worker receipt")
   reopened=ClaimGate(path)
   one=reopened.reconcile_unknown("engineering","issue-002")
   two=reopened.reconcile_unknown("engineering","issue-002")
   self.assertEqual(one,two);self.assertEqual(one["state"],"UNKNOWN")
   self.assertIsNone(one["outcome"])

 def test_approval_is_distinct_from_claimant_and_does_not_mint_host_identity(self):
  from gate_approval import ApprovalGate,SelfApprovalRefused
  with tempfile.TemporaryDirectory(prefix="generic-approve-") as path:
   gate=ApprovalGate(path)
   gate.register_approvers("engineering",["reviewer-a","author-a"])
   held=gate.hold("engineering","issue-003",b"synthetic patch",claimant_id="author-a")
   self.assertEqual(held["state"],"HELD_APPROVAL")
   with self.assertRaises(SelfApprovalRefused):
    gate.approve("engineering","issue-003","author-a",1,b"synthetic patch")
   self.assertEqual(gate.verify("engineering","issue-003")["approval_state"],"HELD_APPROVAL")

 def test_generic_default_scopes_not_personal(self):
  from gate_admission import SCOPE_REGISTRY,AuthorityKind
  self.assertIn("collaboration",SCOPE_REGISTRY)
  self.assertIn("engineering-ops",SCOPE_REGISTRY)
  self.assertNotIn("family-comm",SCOPE_REGISTRY)
  self.assertIn("SCOPED_WORKER",AuthorityKind.__members__)
  self.assertNotIn("CHAMBER_WORKER",AuthorityKind.__members__)

 if __name__ == "__main__":unittest.main()

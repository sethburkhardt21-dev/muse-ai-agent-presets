"""T14 pure offline review→checkpoint→reopen, never another Omnium compiler."""
from __future__ import annotations

import copy
import hashlib
import importlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from muse_presets.coordinator_review import review_workgraph


def graph_fixture():
    return {
        "schema":"r33/coordinator-workgraph-v1",
        "workspace":"fixture-offline",
        "budget_units":4,
        "tasks":[
            {"id":"diagnose-1","role":"software-engineer",
             "reviewer":"adversarial-verifier","requires":[],
             "estimated_units":2,"effect_class":"none",
             "source_sha256":"a"*64,
             "acceptance":["Synthetic defect verified by reviewer"]},
            {"id":"analyze-2","role":"claims-adjudicator",
             "reviewer":"research-evaluator","requires":["diagnose-1"],
             "estimated_units":2,"effect_class":"external",
             "source_sha256":"b"*64,
             "acceptance":["Hold external recipient until independently verified"]}
        ]}


def assertions_fixture(graph):
    return {
        "schema":"r33/coordinator-assertions-v1",
        "workgraph_sha256":review_workgraph(graph)["workgraph_sha256"],
        "items":[
            {"task_id":"diagnose-1","actor_role":"software-engineer",
             "reviewer_role":"adversarial-verifier","source_sha256":"a"*64,
             "actor_claim":"completed","reviewer_claim":"pass"},
            {"task_id":"analyze-2","actor_role":"claims-adjudicator",
             "reviewer_role":"research-evaluator","source_sha256":"b"*64,
             "actor_claim":"unknown_effect","reviewer_claim":"hold"}]}


def adapter():
    return importlib.import_module("muse_presets.continuum_checkpoint")


class ContinuumOfflineResumeTests(unittest.TestCase):
    def setUp(self):
        self.graph=graph_fixture()
        self.assertions=assertions_fixture(self.graph)

    def checkpoint(self):
        return adapter().capture_offline_checkpoint(self.graph,self.assertions)

    def test_source_module_exists_with_explicit_no_dispatch_interface(self):
        # RED before implementation: source adapter does not exist.
        self.assertIsNotNone(importlib.util.find_spec("muse_presets.continuum_checkpoint"))

    def test_capture_returns_deterministic_immutable_advisory_snapshot(self):
        g=copy.deepcopy(self.graph);a=copy.deepcopy(self.assertions)
        result=self.checkpoint()
        self.assertEqual(result["schema"],"r65/continuum-checkpoint-v1")
        self.assertEqual(result["status"],"UNATTESTED_LOCAL_CHECKPOINT")
        self.assertEqual(result["advisory_order"],["diagnose-1","analyze-2"])
        self.assertEqual(result["held_task_ids"],["analyze-2"])
        self.assertFalse(result["provider_authenticated"])
        self.assertFalse(result["native_execution_verified"])
        self.assertFalse(result["effect_authorized"])
        self.assertFalse(result["recipient_readback_verified"])
        self.assertEqual(self.graph,g)
        self.assertEqual(self.assertions,a)
        self.assertEqual(result,self.checkpoint())

    def test_exact_pin_reopened_checkpoint_produces_source_only_resume_advice(self):
        m=adapter();c=self.checkpoint()
        digest=m.checkpoint_sha256(c)
        result=m.resume_offline_checkpoint(c,self.graph,self.assertions,digest)
        self.assertEqual(result["status"],"LOCAL_REVIEW_ONLY_RESUME")
        self.assertEqual(result["advisory_order"],["diagnose-1","analyze-2"])
        self.assertEqual(result["held_task_ids"],["analyze-2"])
        self.assertEqual(result["checkpoint_sha256"],digest)
        self.assertFalse(result["native_execution_verified"])
        self.assertFalse(result["effect_authorized"])
        self.assertFalse(result["recipient_readback_verified"])
        self.assertFalse(result["independent_review_authenticated"])
        self.assertEqual(len(digest),64)

    def test_forged_checkpoint_with_self_rehashed_pin_is_not_an_authenticated_proof(self):
        # A malicious caller can compute a new self-hash; the adapter must
        # never turn that hash into effect or reviewer authority.
        m=adapter(); c=self.checkpoint()
        modified=copy.deepcopy(c)
        modified["provider_authenticated"]=True
        with self.assertRaises(ValueError):
            m.resume_offline_checkpoint(modified,self.graph,self.assertions,
                                        m.checkpoint_sha256(modified))
        modified=copy.deepcopy(c)
        modified["advisory_order"]=["analyze-2","diagnose-1"]
        with self.assertRaises(ValueError):
            m.resume_offline_checkpoint(modified,self.graph,self.assertions,
                                        m.checkpoint_sha256(modified))

    def test_changed_graph_source_sha_refused_even_with_self_rehashed_checkpoint(self):
        m=adapter();c=self.checkpoint();x=copy.deepcopy(self.graph)
        x["tasks"][0]["source_sha256"]="f"*64
        with self.assertRaises(ValueError):
            m.resume_offline_checkpoint(c,x,self.assertions,m.checkpoint_sha256(c))

    def test_changed_workgraph_dependency_or_budget_is_refused(self):
        m=adapter();c=self.checkpoint()
        for field,value in (("budget_units",3),("workspace","different-workspace")):
            changed=copy.deepcopy(self.graph);changed[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):
                m.resume_offline_checkpoint(c,changed,self.assertions,
                                            m.checkpoint_sha256(c))

    def test_changed_assertion_or_unknown_to_pass_is_refused(self):
        m=adapter();c=self.checkpoint()
        altered=copy.deepcopy(self.assertions)
        altered["items"][1]["reviewer_claim"]="pass"
        with self.assertRaises(ValueError):
            m.resume_offline_checkpoint(c,self.graph,altered,m.checkpoint_sha256(c))
        altered=copy.deepcopy(self.assertions)
        altered["items"][0]["reviewer_role"]="software-engineer"
        with self.assertRaises(ValueError):
            m.resume_offline_checkpoint(c,self.graph,altered,m.checkpoint_sha256(c))

    def test_wrong_out_of_band_checkpoint_sha_refused(self):
        m=adapter();c=self.checkpoint()
        for bad in ("0"*64,"F"*64,"missing",None,42):
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                m.resume_offline_checkpoint(c,self.graph,self.assertions,bad)

    def test_invalid_checkpoint_fields_and_nested_malicious_status_refused(self):
        m=adapter();c=self.checkpoint()
        for name,bad in (("status","AUTHORIZED"),("held_task_ids",[]),
                         ("native_execution_verified",True),
                         ("recipient_readback_verified",True),
                         ("effect_authorized",True),
                         ("workgraph_sha256","0"*64)):
            altered=copy.deepcopy(c);altered[name]=bad
            with self.subTest(name=name),self.assertRaises(ValueError):
                m.resume_offline_checkpoint(altered,self.graph,self.assertions,
                                            m.checkpoint_sha256(altered))
        altered=copy.deepcopy(c);altered["new_native_grant"]=True
        with self.assertRaises(ValueError):
            m.resume_offline_checkpoint(altered,self.graph,self.assertions,
                                        m.checkpoint_sha256(altered))

    def test_invalid_graph_cycle_or_unauthorized_role_refuses_capture(self):
        m=adapter()
        graph=graph_fixture();graph["tasks"][0]["requires"]=["analyze-2"]
        with self.assertRaises(ValueError):
            m.capture_offline_checkpoint(graph,assertions_fixture(self.graph))
        graph=graph_fixture();graph["tasks"][0]["role"]="personal-private-agent"
        with self.assertRaises(ValueError):
            m.capture_offline_checkpoint(graph,assertions_fixture(self.graph))

    def test_exact_checkpoint_serialization_and_sha_stable_after_json_roundtrip(self):
        m=adapter(); c=self.checkpoint()
        wire=json.dumps(c,sort_keys=True,separators=(",",":"),ensure_ascii=True,
                        allow_nan=False).encode("utf-8")
        clone=json.loads(wire.decode("utf-8"))
        self.assertEqual(c,clone)
        self.assertEqual(m.checkpoint_sha256(c),hashlib.sha256(wire).hexdigest())
        self.assertEqual(m.checkpoint_sha256(c),m.checkpoint_sha256(clone))

    def test_actual_separate_process_restart_demo(self):
        root=Path(__file__).resolve().parents[1]
        env=dict(os.environ,PYTHONPATH=str(root/"src"),PYTHONDONTWRITEBYTECODE="1")
        demo=root/"examples/continuum_checkpoint_demo.py"
        result=subprocess.run([sys.executable,"-B",str(demo)],
          cwd=root,env=env,capture_output=True,text=True,timeout=50)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        data=json.loads(result.stdout)
        self.assertEqual(data["status"],"LOCAL_REVIEW_ONLY_RESUME")
        self.assertEqual(data["held_task_ids"],["analyze-2"])
        self.assertTrue(data["separate_process_verified"])
        self.assertFalse(data["external_effect_authorized"])


if __name__=="__main__":
    unittest.main()

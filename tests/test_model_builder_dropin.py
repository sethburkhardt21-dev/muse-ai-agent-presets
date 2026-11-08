"""R33 independent Model Builder role packaging and offline canary acceptance."""
import base64
import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from muse_presets.model_builder_dropin import stage_model_builder_dropin, inspect_model_builder_dropin

SKILLS={"model_development_metrics","model_checkpoint_verifier"}
ROOMS={"data-custody","development-evaluation","artifact-verification"}


class ModelBuilderDropinTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory(prefix="r33-model-builder-")
        self.addCleanup(t.cleanup)
        self.root=Path(t.name)

    def stage(self):
        p=self.root/"model-builder"
        r=stage_model_builder_dropin(p)
        self.assertEqual(r["status"],"SOURCE_ONLY_MODEL_BUILDER_STAGED")
        return p

    def execute(self,pack,skill,operation,data=None):
        runner=pack/"custom-skills"/skill/"run.py"
        result=subprocess.run([sys.executable,"-I","-B",str(runner),"--operation",operation],
                              input=json.dumps(data) if data is not None else None,
                              capture_output=True,text=True,timeout=15)
        return result.returncode,json.loads(result.stdout)

    def test_full_pack_is_role_specific_and_has_boundaries(self):
        p=self.stage()
        self.assertEqual(inspect_model_builder_dropin(p)["status"],"LOCAL_MODEL_BUILDER_MATCH")
        self.assertEqual({x.name for x in (p/"custom-skills").iterdir()},SKILLS)
        self.assertEqual({x.name for x in (p/"subchats").iterdir()},ROOMS)
        for name in SKILLS:
            self.assertTrue((p/"custom-skills"/name/"run.py").is_file())
            self.assertTrue((p/"custom-skills"/name/"SKILL.md").read_text().startswith("---\nname: "+name+"\n"))
            self.assertIn("name: "+name+"\n",(p/"custom-skills"/name/"skill.yaml").read_text())
            self.assertIn("  "+name+":\n    status: disabled",(p/"config"/"skills.yaml").read_text())
        for room in ROOMS:
            for file in ("ROLE.md","CONTEXT.md","MEMORY.md","TOOLS.md","SUBCHAT.json"):
                self.assertTrue((p/"subchats"/room/file).is_file())
            info=json.loads((p/"subchats"/room/"SUBCHAT.json").read_text())
            self.assertIsNone(info["native_chat_id"])
            self.assertFalse(info["native_loaded"])
        for file in ("AGENTS.md","SOUL.md","IDENTITY.md","USER.md","TOOLS.md",
                     "MEMORY.md","HEARTBEAT.md","SYSTEM_INSTRUCTIONS.md",
                     "CONNECTORS.md","BROWSER.md","VOICE.md"):
            self.assertTrue((p/"system-files"/file).is_file())
        self.assertTrue((p/"runtime"/"model_eval.py").is_file())

    def test_actual_development_and_checkpoint_canary(self):
        p=self.stage()
        code,report=self.execute(p,"model_development_metrics","demo")
        self.assertEqual(code,0)
        self.assertEqual(report["status"],"LOCAL_MODEL_BUILDER_DEMO_PASSED")
        self.assertEqual(report["dev_n"],2)
        self.assertEqual(report["candidate_correct"],2)
        self.assertEqual(report["checkpoint_status"],"LOCAL_CHECKPOINT_DIGEST_MATCH")
        self.assertFalse(report["model_trained"])
        self.assertFalse(report["native_tool_invoked"])
        self.assertFalse(report["external_effect_authorized"])

    def test_standalone_evaluate_stdin_reports_actual_metrics(self):
        p=self.stage()
        data={
            "schema":"r33/model-builder-development-v1",
            "model_source_sha256":"a"*64,"dataset_source_sha256":"b"*64,
            "rights_status":"UNVERIFIED",
            "rows":[
                {"sample_id":"train-1","family_id":"source-a","split":"train","label":1,"baseline":None,"candidate":None},
                {"sample_id":"dev-1","family_id":"source-b","split":"dev","label":1,"baseline":0,"candidate":1},
                {"sample_id":"final-1","family_id":"source-c","split":"final","label":None,"baseline":None,"candidate":None},
            ]}
        code,result=self.execute(p,"model_development_metrics","evaluate",data)
        self.assertEqual(code,0)
        self.assertEqual(result["status"],"LOCAL_DEV_METRICS_ONLY")
        self.assertEqual(result["dev_n"],1)
        self.assertFalse(result["promotion_authorized"])
        data["rows"][-1]["label"]=1
        code,result=self.execute(p,"model_development_metrics","evaluate",data)
        self.assertEqual(code,2)
        self.assertEqual(result["status"],"REVIEW_REQUIRED")

    def test_standalone_checkpoint_verifier_hashes_bytes_not_optimizer_claims(self):
        p=self.stage()
        raw=b"synthetic-student-checkpoint"
        manifest={
            "schema":"r33/model-builder-checkpoint-v1",
            "artifact_kind":"synthetic-checkpoint-bytes",
            "artifact_sha256":hashlib.sha256(raw).hexdigest(),
            "parent_model_sha256":"a"*64,
            "dataset_source_sha256":"b"*64,
            "optimizer_steps":0,"weights_trained":False,
            "rights_status":"UNVERIFIED",
        }
        data={"manifest":manifest,"bytes_base64":base64.b64encode(raw).decode()}
        code,result=self.execute(p,"model_checkpoint_verifier","checkpoint",data)
        self.assertEqual(code,0)
        self.assertEqual(result["status"],"LOCAL_CHECKPOINT_DIGEST_MATCH")
        self.assertEqual(result["artifact_bytes"],len(raw))
        data["manifest"]["optimizer_steps"]=20
        code,result=self.execute(p,"model_checkpoint_verifier","checkpoint",data)
        self.assertEqual(code,2)
        self.assertEqual(result["status"],"REVIEW_REQUIRED")

    def test_checkpoints_cannot_be_promoted_or_assigned_provider_identity(self):
        p=self.stage()
        binding=p/"config"/"host-binding.json"
        meta=json.loads(binding.read_text())
        self.assertIsNone(meta["owner_user_id"])
        self.assertFalse(meta["native_authenticated"])
        meta["native_authenticated"]=True
        binding.write_text(json.dumps(meta))
        self.assertEqual(inspect_model_builder_dropin(p)["status"],"REVIEW_REQUIRED")

    def test_local_doctor_reopens_then_detects_source_change(self):
        p=self.stage()
        runner=p/"scripts"/"doctor.py"
        result=subprocess.run([sys.executable,"-I","-B",str(runner)],
                              capture_output=True,text=True,timeout=12)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(json.loads(result.stdout)["status"],"LOCAL_SELF_HASH_MATCH")
        (p/"runtime"/"model_eval.py").write_text("altered")
        result=subprocess.run([sys.executable,"-I","-B",str(runner)],
                              capture_output=True,text=True,timeout=12)
        self.assertEqual(result.returncode,2)
        self.assertEqual(json.loads(result.stdout)["status"],"REVIEW_REQUIRED")

    def test_added_executable_deleted_subchat_and_skill_tamper_denied(self):
        p=self.stage()
        (p/"unlisted.py").write_text("print(1)")
        self.assertEqual(inspect_model_builder_dropin(p)["status"],"REVIEW_REQUIRED")
        p2=self.root/"new2"
        stage_model_builder_dropin(p2)
        (p2/"subchats"/"data-custody"/"ROLE.md").unlink()
        self.assertEqual(inspect_model_builder_dropin(p2)["status"],"REVIEW_REQUIRED")
        p3=self.root/"new3"
        stage_model_builder_dropin(p3)
        (p3/"custom-skills"/"model_checkpoint_verifier"/"SKILL.md").write_text("forged")
        self.assertEqual(inspect_model_builder_dropin(p3)["status"],"REVIEW_REQUIRED")

    def test_no_existing_owner_files_are_overwritten(self):
        p=self.root/"existing"
        p.mkdir()
        (p/"MEMORY.md").write_text("protected owner memory")
        with self.assertRaises((ValueError,FileExistsError)):
            stage_model_builder_dropin(p)
        self.assertEqual((p/"MEMORY.md").read_text(),"protected owner memory")

    def test_incomplete_stage_is_never_accepted(self):
        p=self.stage()
        (p/"STAGING_INCOMPLETE").write_text("unfinished")
        self.assertEqual(inspect_model_builder_dropin(p)["status"],"INCOMPLETE_STAGE")


if __name__=="__main__":
    unittest.main()

"""R33 Coordinator source pack has genuine offline review and no native grants."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from muse_presets.coordinator_dropin import stage_coordinator_dropin, inspect_coordinator_dropin
from muse_presets.native_skill_binding import inspect_skill_bindings

SKILLS={"coordinator_workgraph","coordinator_evidence"}
ROOMS={"intake","dependency-review","acceptance-review"}


class CoordinatorDropinTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory(prefix="r33-coordinator-role-")
        self.addCleanup(temp.cleanup)
        self.root=Path(temp.name)

    def stage(self):
        dest=self.root/"coordinator"
        result=stage_coordinator_dropin(dest)
        self.assertEqual(result["status"],"SOURCE_ONLY_COORDINATOR_STAGED")
        return dest

    def test_exact_role_packet_has_real_runner_skills_and_independent_rooms(self):
        pack=self.stage()
        self.assertEqual(inspect_coordinator_dropin(pack)["status"],"LOCAL_COORDINATOR_MATCH")
        self.assertEqual({p.name for p in (pack/"custom-skills").iterdir()},SKILLS)
        for skill in SKILLS:
            d=pack/"custom-skills"/skill
            self.assertTrue((d/"SKILL.md").read_text().startswith("---\nname: "+skill+"\n"))
            self.assertIn("name: "+skill,(d/"skill.yaml").read_text())
            self.assertTrue((d/"run.py").is_file())
        self.assertEqual({p.name for p in (pack/"subchats").iterdir()},ROOMS)
        for room in ROOMS:
            for file in ("ROLE.md","CONTEXT.md","MEMORY.md","TOOLS.md","SUBCHAT.json"):
                self.assertTrue((pack/"subchats"/room/file).is_file())
            manifest=json.loads((pack/"subchats"/room/"SUBCHAT.json").read_text())
            self.assertIsNone(manifest["native_chat_id"])
            self.assertFalse(manifest["native_loaded"])
        for name in ("AGENTS.md","SOUL.md","IDENTITY.md","USER.md","TOOLS.md",
                     "MEMORY.md","HEARTBEAT.md","SYSTEM_INSTRUCTIONS.md",
                     "CONNECTORS.md","BROWSER.md","VOICE.md"):
            self.assertTrue((pack/"system-files"/name).is_file())
        self.assertTrue((pack/"runtime"/"coordinator_review.py").is_file())
        self.assertTrue((pack/"runtime"/"coordinator_roles.json").is_file())

    def test_registry_is_intentionally_disabled_and_local_catalog_is_not_native_proof(self):
        pack=self.stage()
        registry=(pack/"config"/"skills.yaml").read_text()
        for name in SKILLS:
            self.assertIn(f"  {name}:\n    status: disabled",registry)
        observed=inspect_skill_bindings(
            custom_root=pack/"custom-skills",
            registry_path=pack/"config"/"skills.yaml",
            skill_names=sorted(SKILLS)
        )
        self.assertEqual(observed["status"],"LOCAL_CATALOG_NOT_ADVERTISED")
        self.assertTrue(all(r["descriptor_present"] for r in observed["skills"]))
        self.assertFalse(observed["authority"]["native_skill_search_verified"])

    def test_standalone_runner_demo_executes_real_deterministic_review(self):
        pack=self.stage()
        runner=pack/"custom-skills"/"coordinator_workgraph"/"run.py"
        run=subprocess.run([sys.executable,"-I","-B",str(runner),"--operation","demo"],
                           capture_output=True,text=True,timeout=15)
        report=json.loads(run.stdout)
        self.assertEqual(run.returncode,0,run.stderr)
        self.assertEqual(report["status"],"LOCAL_COORDINATOR_DEMO_PASSED")
        self.assertEqual(report["execution_order"],["diagnose-1","review-2"])
        self.assertFalse(report["native_tool_invoked"])
        self.assertFalse(report["external_effect_authorized"])

    def test_standalone_runner_accepts_bounded_stdin_and_refuses_forged_receipt(self):
        pack=self.stage()
        runner=pack/"custom-skills"/"coordinator_workgraph"/"run.py"
        workgraph={
            "schema":"r33/coordinator-workgraph-v1",
            "workspace":"fictional-demo",
            "budget_units":1,
            "tasks":[{"id":"verify-1","role":"software-engineer",
                      "reviewer":"adversarial-verifier","requires":[],
                      "estimated_units":1,"effect_class":"none",
                      "source_sha256":"a"*64,"acceptance":["Independent local check"]}]
        }
        good=subprocess.run([sys.executable,"-I","-B",str(runner),"--operation","review"],
                            input=json.dumps(workgraph),text=True,capture_output=True,timeout=15)
        self.assertEqual(good.returncode,0,good.stderr)
        self.assertEqual(json.loads(good.stdout)["status"],"LOCAL_PLAN_REVIEW_ONLY")
        forged=json.dumps(workgraph)[:-1]+',"native_authenticated":true}'
        bad=subprocess.run([sys.executable,"-I","-B",str(runner),"--operation","review"],
                           input=forged,text=True,capture_output=True,timeout=15)
        self.assertEqual(bad.returncode,2)
        self.assertEqual(json.loads(bad.stdout)["status"],"REVIEW_REQUIRED")

    def test_offline_evidence_runner_never_turns_self_claims_into_native_proof(self):
        from muse_presets.coordinator_review import review_workgraph
        pack=self.stage()
        graph={
            "schema":"r33/coordinator-workgraph-v1","workspace":"fictional-demo",
            "budget_units":1,
            "tasks":[{"id":"observe-1","role":"software-engineer",
                      "reviewer":"adversarial-verifier","requires":[],
                      "estimated_units":1,"effect_class":"none",
                      "source_sha256":"a"*64,"acceptance":["Source tested offline"]}],
        }
        reports={
            "schema":"r33/coordinator-assertions-v1",
            "workgraph_sha256":review_workgraph(graph)["workgraph_sha256"],
            "items":[{"task_id":"observe-1","actor_role":"software-engineer",
                      "reviewer_role":"adversarial-verifier","source_sha256":"a"*64,
                      "actor_claim":"completed","reviewer_claim":"pass"}],
        }
        runner=pack/"custom-skills"/"coordinator_evidence"/"run.py"
        run=subprocess.run([sys.executable,"-I","-B",str(runner),"--operation","evidence"],
                           input=json.dumps({"graph":graph,"assertions":reports}),
                           capture_output=True,text=True,timeout=15)
        self.assertEqual(run.returncode,0,run.stderr)
        output=json.loads(run.stdout)
        self.assertEqual(output["status"],"UNATTESTED_ASSERTIONS_ONLY")
        self.assertFalse(output["native_tool_invoked"])
        self.assertFalse(output["recipient_readback_verified"])
        reports["items"][0]["actor_role"]="claims-adjudicator"
        forged=subprocess.run([sys.executable,"-I","-B",str(runner),"--operation","evidence"],
                              input=json.dumps({"graph":graph,"assertions":reports}),
                              capture_output=True,text=True,timeout=15)
        self.assertEqual(forged.returncode,2)
        self.assertEqual(json.loads(forged.stdout)["status"],"REVIEW_REQUIRED")

    def test_doctor_reopens_then_detects_tamper(self):
        pack=self.stage()
        doctor=pack/"scripts"/"doctor.py"
        run=subprocess.run([sys.executable,"-I","-B",str(doctor)],capture_output=True,text=True,timeout=12)
        self.assertEqual(run.returncode,0,run.stderr)
        self.assertEqual(json.loads(run.stdout)["status"],"LOCAL_SELF_HASH_MATCH")
        (pack/"runtime"/"coordinator_roles.json").write_text('{"roles":["forged"]}')
        run=subprocess.run([sys.executable,"-I","-B",str(doctor)],capture_output=True,text=True,timeout=12)
        self.assertEqual(run.returncode,2)
        self.assertEqual(json.loads(run.stdout)["status"],"REVIEW_REQUIRED")

    def test_inspector_rejects_policy_tamper_extra_file_missing_subchat(self):
        pack=self.stage()
        (pack/"custom-skills"/"coordinator_evidence"/"SKILL.md").write_text("forged")
        self.assertEqual(inspect_coordinator_dropin(pack)["status"],"REVIEW_REQUIRED")
        second=self.root/"second"
        stage_coordinator_dropin(second)
        (second/"subchats"/"acceptance-review"/"MEMORY.md").unlink()
        self.assertEqual(inspect_coordinator_dropin(second)["status"],"REVIEW_REQUIRED")
        third=self.root/"third"
        stage_coordinator_dropin(third)
        (third/"unlisted.py").write_text("print('unapproved')")
        self.assertEqual(inspect_coordinator_dropin(third)["status"],"REVIEW_REQUIRED")

    def test_host_identity_forgery_refused(self):
        pack=self.stage()
        binding=pack/"config"/"host-binding.json"
        record=json.loads(binding.read_text())
        record["native_authenticated"]=True
        binding.write_text(json.dumps(record))
        self.assertEqual(inspect_coordinator_dropin(pack)["status"],"REVIEW_REQUIRED")

    def test_create_only_never_changes_existing_owner_directory(self):
        folder=self.root/"user-profile"
        folder.mkdir()
        (folder/"MEMORY.md").write_text("private prior state")
        with self.assertRaises((FileExistsError,ValueError)):
            stage_coordinator_dropin(folder)
        self.assertEqual((folder/"MEMORY.md").read_text(),"private prior state")

    def test_partial_stage_is_fenced(self):
        pack=self.stage()
        (pack/"STAGING_INCOMPLETE").write_text("torn")
        self.assertEqual(inspect_coordinator_dropin(pack)["status"],"INCOMPLETE_STAGE")


if __name__=="__main__":
    unittest.main()

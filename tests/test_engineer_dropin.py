"""R33 native-format Software Engineer drop-in: no personal Muse installation."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from muse_presets.engineer_dropin import (
    stage_engineer_dropin, inspect_engineer_dropin
)
from muse_presets.engineering_pack import inspect_engineer_pack
from muse_presets.native_skill_binding import inspect_skill_bindings

IDS = {"engineering_claim_gate", "engineering_source_provenance",
       "engineering_evidence_receipt_consumer"}
SUBCHATS = {"diagnostics", "implementation", "verification"}


class EngineerDropinTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="r33-engineer-dropin-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def stage(self):
        path = self.root / "software-engineer-dropin"
        result = stage_engineer_dropin(path)
        self.assertEqual(result["status"], "SOURCE_ONLY_NATIVE_FORMAT_STAGED")
        self.assertFalse(result["native_installed"])
        return path

    def test_complete_pack_has_real_engine_and_3_skill_metadata_pairs(self):
        root = self.stage()
        self.assertEqual(inspect_engineer_dropin(root)["status"], "LOCAL_DROPIN_MATCH")
        self.assertEqual(inspect_engineer_pack(root / "engine")["status"], "LOCAL_MATCH")
        names = {p.name for p in (root / "custom-skills").iterdir()}
        self.assertEqual(names, IDS)
        registry = (root / "config" / "skills.yaml").read_text()
        for name in IDS:
            self.assertIn(f"  {name}:\n    status: disabled", registry)
            d = root / "custom-skills" / name
            self.assertTrue((d / "SKILL.md").read_text().startswith(f"---\nname: {name}\n"))
            self.assertIn(f"name: {name}\n", (d / "skill.yaml").read_text())
        self.assertTrue((root / "custom-skills" / "engineering_claim_gate" / "run.py").is_file())
        self.assertEqual({p.name for p in (root / "subchats").iterdir()}, SUBCHATS)
        for sub in SUBCHATS:
            with self.subTest(subchat=sub):
                for name in ("ROLE.md", "CONTEXT.md", "MEMORY.md", "TOOLS.md", "SUBCHAT.json"):
                    self.assertTrue((root / "subchats" / sub / name).is_file())
                manifest=json.loads((root/"subchats"/sub/"SUBCHAT.json").read_text())
                self.assertIsNone(manifest["native_chat_id"])
                self.assertFalse(manifest["native_loaded"])
        for name in ("AGENTS.md","SOUL.md","IDENTITY.md","USER.md","TOOLS.md",
                     "MEMORY.md","HEARTBEAT.md","SYSTEM_INSTRUCTIONS.md",
                     "CONNECTORS.md","BROWSER.md","VOICE.md"):
            self.assertTrue((root/"system-files"/name).is_file(), name)

    def test_local_registry_is_intentionally_not_natively_discoverable(self):
        root = self.stage()
        result=inspect_skill_bindings(
            custom_root=root/"custom-skills",
            registry_path=root/"config"/"skills.yaml",
            skill_names=sorted(IDS)
        )
        self.assertEqual(result["status"], "LOCAL_CATALOG_NOT_ADVERTISED")
        self.assertTrue(all(r["source_status"]=="DESCRIPTOR_VALID" for r in result["skills"]))
        self.assertFalse(result["authority"]["native_skill_search_verified"])

    def test_exact_rollback_and_grant_limits_are_honest(self):
        root=self.stage()
        manifest=json.loads((root/"receipts"/"R33_DROPIN_RECEIPT.json").read_text())
        self.assertFalse(manifest["native_installed"])
        self.assertFalse(manifest["external_effect_authorized"])
        self.assertFalse(manifest["host_authenticated"])
        self.assertFalse(manifest["scheduler_enabled"])
        self.assertEqual(manifest["license_disposition"], "PRIVATE_REVIEW_ONLY")
        config=json.loads((root/"config"/"host-binding.json").read_text())
        self.assertIsNone(config["owner_user_id"])
        self.assertIsNone(config["provider_session_id"])
        self.assertFalse(config["registered"])
        self.assertFalse(config["installed"])
        flags=json.loads((root/"hooks"/"HOOKS.json").read_text())
        self.assertFalse(flags["enabled"])

    def test_changes_to_engine_and_skill_code_cannot_be_hashed_away(self):
        root=self.stage()
        path=root/"engine"/"runtime"/"claim-gate"/"engineering_claim_gate.py"
        path.write_bytes(path.read_bytes()+b"\n# unauthorized alteration\n")
        self.assertEqual(inspect_engineer_dropin(root)["status"],"REVIEW_REQUIRED")

    def test_local_catalog_mutation_and_forged_grants_rejected(self):
        root=self.stage()
        registry=root/"config"/"skills.yaml"
        registry.write_text(registry.read_text().replace("status: disabled","status: available"))
        self.assertEqual(inspect_engineer_dropin(root)["status"],"REVIEW_REQUIRED")
        registry.write_text(registry.read_text().replace("status: available","status: disabled"))
        receipt=root/"receipts"/"R33_DROPIN_RECEIPT.json"
        data=json.loads(receipt.read_text())
        data["native_installed"]=True
        receipt.write_text(json.dumps(data))
        self.assertEqual(inspect_engineer_dropin(root)["status"],"REVIEW_REQUIRED")

    def test_missing_subchat_and_unlisted_executable_refused(self):
        root=self.stage()
        (root/"subchats"/"verification"/"ROLE.md").unlink()
        self.assertEqual(inspect_engineer_dropin(root)["status"],"REVIEW_REQUIRED")
        root2=self.root/"second"
        stage_engineer_dropin(root2)
        (root2/"scripts"/"unreviewed.py").write_text("raise SystemExit(0)")
        self.assertEqual(inspect_engineer_dropin(root2)["status"],"REVIEW_REQUIRED")

    def test_existing_target_and_symlinked_parent_refused(self):
        d=self.root/"existing"
        d.mkdir()
        (d/"USER.md").write_text("owner input unchanged")
        with self.assertRaises((ValueError,FileExistsError)):
            stage_engineer_dropin(d)
        self.assertEqual((d/"USER.md").read_text(),"owner input unchanged")
        real=self.root/"actual"
        real.mkdir()
        alias=self.root/"alias"
        try:
            alias.symlink_to(real,target_is_directory=True)
        except (OSError,NotImplementedError):
            self.skipTest("host disallows symlink fixture")
        with self.assertRaises(ValueError):
            stage_engineer_dropin(alias/"candidate")

    def test_standalone_offline_doctor_verifies_zip_style_copy(self):
        root = self.stage()
        runner = root / "scripts" / "doctor.py"
        result = subprocess.run([sys.executable, "-I", "-B", str(runner)],
                                capture_output=True, text=True, timeout=15)
        report = json.loads(result.stdout)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(report["status"], "LOCAL_SELF_HASH_MATCH")
        self.assertFalse(report["native_authenticated"])
        self.assertFalse(report["external_effect_authorized"])
        self.assertFalse(report["provider_invocation_verified"])
        (root / "custom-skills" / "engineering_claim_gate" / "SKILL.md").write_text("forged")
        result = subprocess.run([sys.executable, "-I", "-B", str(runner)],
                                capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)["status"], "REVIEW_REQUIRED")

    def test_existing_engine_source_bytes_are_not_modified_by_staging(self):
        from muse_presets.engineering_pack import ENGINE_MANIFEST
        orig=ENGINE_MANIFEST.read_bytes()
        self.stage()
        self.assertEqual(ENGINE_MANIFEST.read_bytes(),orig)

    def test_disposable_claim_gate_demo_runs_without_host_effects(self):
        root=self.stage()
        script=root/"custom-skills"/"engineering_claim_gate"/"run.py"
        result=subprocess.run([sys.executable,"-I","-B",str(script),"--canary"],
                              capture_output=True,text=True,timeout=25)
        report=json.loads(result.stdout)
        if os.name!="posix":
            self.assertEqual(result.returncode,2)
            self.assertEqual(report["status"],"UNSUPPORTED_PLATFORM_POSIX_FCNTL_REQUIRED")
        else:
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(report["status"],"LOCAL_CLAIM_GATE_CANARY_PASSED")
            self.assertEqual(report["observed"],["LOCAL_CLAIM_RECORDED",
                                                "LOCAL_CLAIM_REUSED",
                                                "LOCAL_UNKNOWN_HELD",
                                                "LOCAL_CLAIM_OBSERVED"])
        self.assertFalse(report["native_muse_invoked"])
        self.assertFalse(report["external_effect_authorized"])
        self.assertFalse(report["recipient_readback_verified"])


if __name__=="__main__":
    unittest.main()

"""T07: compose three verified source layers without touching an original Muse host."""
from __future__ import annotations

import hashlib
import io
import json
import tempfile
import unittest
import zipfile
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from muse_presets.catalog import load_registry
from muse_presets.system_profile import plan_system_profile
from muse_presets import standalone_pack as api
from muse_presets.cli import main


class StandaloneInstallTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name)

    def make(self, role="garden-companion", *,name=None):
        dst=self.base/role
        pin=plan_system_profile(role,display_name=name)["source_sha256"]
        r=api.stage_standalone_pack(dst,role,display_name=name,expected_profile_source_sha256=pin)
        self.assertEqual(r["status"],"LOCAL_STANDALONE_STAGED")
        return dst

    def test_all_eleven_independent_standalone_packs(self):
        roles=load_registry()["presets"]
        self.assertEqual(len(roles),15)
        for role in roles:
            d=self.make(role)
            self.assertEqual({p.name for p in d.iterdir()},
                             {"system-profile","subchat-scopes","role-skills",api.MANIFEST})
            report=api.inspect_standalone_pack(d)
            self.assertEqual(report["status"],"LOCAL_STANDALONE_MATCH",role)
            self.assertEqual(report["role"],role)
            self.assertFalse(report["native_installed"])
            self.assertFalse(report["can_apply"])
            self.assertEqual(report["subchat_count"],3)
            self.assertEqual(report["skill_count"],8)
            self.assertIsNone(report.get("provider_owner_id"))
            receipt=json.loads((d/api.MANIFEST).read_text(encoding="utf-8"))
            self.assertEqual(len(receipt["components"]),3)
            self.assertEqual(len(set(c["profile_source_sha256"] for c in receipt["components"].values())),1)

    def test_plan_does_not_create_destination(self):
        r=api.plan_standalone_pack("software-engineer",display_name="Engineering Helper")
        self.assertEqual(r["status"],"SOURCE_PLAN_ONLY")
        self.assertEqual(len(r["components"]),3)
        self.assertFalse(r["can_apply"])
        self.assertFalse(r["native_installed"])
        self.assertEqual(list(self.base.iterdir()),[])

    def test_wrong_or_missing_source_pin_rejected_before_write(self):
        dst=self.base/"invalid"
        with self.assertRaisesRegex(ValueError,"SOURCE_PIN_MISMATCH"):
            api.stage_standalone_pack(dst,"coordinator",expected_profile_source_sha256="0"*64)
        self.assertFalse(dst.exists())

    def test_invalid_role_and_display_name_no_write(self):
        for role in ("../../owner","unknown-role"):
            d=self.base/"bad"
            with self.assertRaises(ValueError):api.stage_standalone_pack(d,role)
            self.assertFalse(d.exists())
        with self.assertRaises(ValueError):
            api.stage_standalone_pack(self.base/"bad","coordinator",display_name="Injected\nName")

    def test_occupied_destination_never_overwritten(self):
        d=self.base/"occupied"
        d.mkdir()
        (d/"MEMORY.md").write_text("owner memory",encoding="utf-8")
        with self.assertRaises(FileExistsError):api.stage_standalone_pack(d,"coordinator")
        self.assertEqual((d/"MEMORY.md").read_text(),"owner memory")

    def test_missing_parent_refused(self):
        d=self.base/"missing"/"candidate"
        with self.assertRaises(FileNotFoundError):api.stage_standalone_pack(d,"learning-coach")
        self.assertFalse(d.parent.exists())

    def test_partial_stage_kept_fenced(self):
        d=self.base/"interrupt"
        def failure(*args,**kwargs):raise OSError("simulated interruption")
        with patch.object(api.subchat_scopes,"stage_subchat_scopes",side_effect=failure):
            with self.assertRaises(OSError):api.stage_standalone_pack(d,"learning-coach")
        self.assertTrue((d/"STAGING_INCOMPLETE").exists())
        self.assertEqual(api.inspect_standalone_pack(d)["status"],"INCOMPLETE_STAGE")
        with self.assertRaises(FileExistsError):api.stage_standalone_pack(d,"learning-coach")
        self.assertTrue(d.exists())

    def test_source_drift_during_stage_keeps_marker(self):
        d=self.base/"drift"
        real=api._current_plan
        count=[0]
        def changed(*a,**k):
            count[0]+=1
            value=real(*a,**k)
            # Admission calls the plan directly, then again while sealing
            # its initial source-backed manifest. Inject drift only *after*
            # staging has begun and the incomplete marker exists.
            if count[0]>2:
                return {**value,"profile_source_sha256":"a"*64}
            return value
        with patch.object(api,"_current_plan",side_effect=changed):
            with self.assertRaisesRegex(ValueError,"SOURCE_CHANGED"):
                api.stage_standalone_pack(d,"coordinator")
        self.assertEqual(api.inspect_standalone_pack(d)["status"],"INCOMPLETE_STAGE")

    def test_owner_memory_customized_but_never_mutated(self):
        d=self.make()
        m=d/"subchat-scopes"/"subchats"/"observe-plant"/"MEMORY.md"
        m.write_text("owner secret",encoding="utf-8")
        profile=d/"system-profile"/"profile"/"MEMORY.md"
        profile.write_text("separate owner memory",encoding="utf-8")
        r=api.inspect_standalone_pack(d)
        self.assertEqual(r["status"],"OWNER_CUSTOMIZED")
        self.assertEqual(m.read_text(),"owner secret")
        self.assertEqual(profile.read_text(),"separate owner memory")

    def test_forged_manifest_and_policy_change_refused(self):
        d=self.make()
        policy=d/"role-skills"/"config"/"skills.yaml"
        policy.write_text(policy.read_text().replace("disabled","available",1))
        receipt=d/api.MANIFEST
        bad=json.loads(receipt.read_text())
        bad["components"]["role-skills"]["receipt_sha256"]="b"*64
        receipt.write_text(json.dumps(bad))
        self.assertEqual(api.inspect_standalone_pack(d)["status"],"REVIEW_REQUIRED")

    def test_forged_owner_native_binding_refused(self):
        d=self.make()
        f=d/"system-profile"/"config"/"host-binding.json"
        b=json.loads(f.read_text())
        b["owner_id"]="forged"
        b["native_loaded"]=True
        f.write_text(json.dumps(b))
        self.assertEqual(api.inspect_standalone_pack(d)["status"],"REVIEW_REQUIRED")

    def test_missing_extra_file_or_symlink_refused(self):
        d=self.make()
        (d/"role-skills"/"config"/"local-code-links.json").unlink()
        self.assertEqual(api.inspect_standalone_pack(d)["status"],"REVIEW_REQUIRED")
        other=self.make("coordinator")
        (other/"rogue.py").write_text("print('bad')")
        self.assertEqual(api.inspect_standalone_pack(other)["status"],"REVIEW_REQUIRED")
        third=self.make("software-engineer")
        original=third/"role-skills"/"config"/"skills.yaml"
        original.unlink()
        external=self.base/"private"
        external.write_text("private text")
        try:original.symlink_to(external)
        except (OSError,NotImplementedError):self.skipTest("Windows symlink unavailable")
        self.assertEqual(api.inspect_standalone_pack(third)["status"],"REVIEW_REQUIRED")
        self.assertEqual(external.read_text(),"private text")

    def test_upgrade_preview_never_writes_and_preserves_owner_edit(self):
        candidate=self.make("coordinator")
        target=self.base/"target"
        folder=target/"system-profile"/"profile"
        folder.mkdir(parents=True)
        memory=folder/"MEMORY.md"
        memory.write_text("existing memory")
        policy=folder/"AGENTS.md"
        policy.write_text("previous policy")
        unknown=target/"owner-original.txt"
        unknown.write_text("protected")
        report=api.preview_standalone_upgrade(candidate,target)
        self.assertEqual(report["status"],"UPGRADE_PREVIEW_ONLY")
        self.assertFalse(report["can_apply"])
        self.assertFalse(report["native_installed"])
        self.assertIn({"path":"system-profile/profile/MEMORY.md","action":"PRESERVE_OWNER_EDIT"},report["files"])
        self.assertIn({"path":"system-profile/profile/AGENTS.md","action":"REVIEW_CONFLICT"},report["files"])
        self.assertEqual(memory.read_text(),"existing memory")
        self.assertEqual(unknown.read_text(),"protected")

    def test_upgrade_preview_untrusted_candidate_refuses_before_target(self):
        candidate=self.make()
        (candidate/"role-skills"/"config"/"skills.yaml").write_text("bad")
        target=self.base/"target"
        target.mkdir()
        (target/"MEMORY.md").write_text("private")
        with self.assertRaisesRegex(ValueError,"UNTRUSTED_STANDALONE_CANDIDATE"):
            api.preview_standalone_upgrade(candidate,target)
        self.assertEqual((target/"MEMORY.md").read_text(),"private")

    def test_upgrade_preview_refuses_wrong_target_type(self):
        candidate=self.make()
        f=self.base/"file"
        f.write_text("owner")
        with self.assertRaisesRegex(ValueError,"UNSAFE_UPGRADE_TARGET"):
            api.preview_standalone_upgrade(candidate,f)
        self.assertEqual(f.read_text(),"owner")

    def test_export_clean_source_archive_create_only(self):
        package=self.make("software-engineer")
        output=self.base/"source.zip"
        result=api.export_clean_standalone_pack(package,output)
        self.assertEqual(result["status"],"LOCAL_EXPORT_CREATED")
        self.assertFalse(result["native_installed"])
        self.assertEqual(result["sha256"],hashlib.sha256(output.read_bytes()).hexdigest())
        with zipfile.ZipFile(output,"r") as z:
            names=z.namelist()
            self.assertEqual(len(names),len(set(names)))
            self.assertIsNone(z.testzip())
            self.assertIn("INSTALL_RECEIPT.json",names)
            self.assertIn("role-skills/config/skills.yaml",names)
            self.assertNotIn(".git",names)
            self.assertTrue(all(not s.startswith("/") and ".." not in Path(s).parts for s in names))
        with self.assertRaises(FileExistsError):api.export_clean_standalone_pack(package,output)

    def test_export_refuses_owner_customized_state(self):
        p=self.make()
        (p/"system-profile"/"profile"/"MEMORY.md").write_text("owner-private")
        out=self.base/"export.zip"
        with self.assertRaisesRegex(ValueError,"UNTRUSTED_OR_CUSTOMIZED_EXPORT"):
            api.export_clean_standalone_pack(p,out)
        self.assertFalse(out.exists())

    def test_uninstall_plan_does_not_remove_any_file(self):
        d=self.make("learning-coach")
        before={p.relative_to(d).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
                for p in d.rglob("*") if p.is_file()}
        plan=api.plan_uninstall_standalone(d)
        self.assertEqual(plan["status"],"UNINSTALL_PREVIEW_ONLY")
        self.assertFalse(plan["can_delete"])
        self.assertTrue(plan["requires_owner_confirmation"])
        self.assertEqual(plan["grade"],"LOCAL_SOURCE_ONLY")
        after={p.relative_to(d).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
               for p in d.rglob("*") if p.is_file()}
        self.assertEqual(before,after)

    def test_uninstall_plan_owner_memory_requires_protected_export(self):
        d=self.make()
        (d/"system-profile"/"profile"/"MEMORY.md").write_text("owner private")
        plan=api.plan_uninstall_standalone(d)
        self.assertFalse(plan["can_delete"])
        self.assertTrue(plan["owner_customizations_present"])
        self.assertTrue(plan["requires_private_owner_export"])

    def test_uninstall_plan_rejects_tampered_policy(self):
        d=self.make()
        (d/"role-skills"/"config"/"skills.yaml").write_text("available")
        with self.assertRaisesRegex(ValueError,"UNTRUSTED_UNINSTALL_SOURCE"):
            api.plan_uninstall_standalone(d)

    def test_empty_source_path_not_accepted(self):
        self.assertEqual(api.inspect_standalone_pack(self.base/"unknown")["status"],"REVIEW_REQUIRED")

    def test_cli_all_six_actions(self):
        out=io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(main(["dropin-install-plan","--preset","coordinator"]),0)
        plan=json.loads(out.getvalue())
        self.assertEqual(plan["status"],"SOURCE_PLAN_ONLY")
        dest=self.base/"cli-dropin"
        with redirect_stdout(io.StringIO()):
            self.assertEqual(main(["dropin-stage","--preset","coordinator","--to",str(dest),
                                   "--profile-source-sha256",plan["profile_source_sha256"]]),0)
        out=io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(main(["dropin-inspect","--path",str(dest)]),0)
        self.assertEqual(json.loads(out.getvalue())["status"],"LOCAL_STANDALONE_MATCH")
        out=io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(main(["dropin-upgrade-preview","--candidate",str(dest),
                                   "--target",str(self.base/"new-target")]),0)
        self.assertFalse(json.loads(out.getvalue())["can_apply"])
        out=io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(main(["dropin-uninstall-plan","--path",str(dest)]),0)
        self.assertFalse(json.loads(out.getvalue())["can_delete"])
        output=self.base/"export.zip"
        with redirect_stdout(io.StringIO()):
            self.assertEqual(main(["dropin-export","--path",str(dest),"--to",str(output)]),0)
        self.assertTrue(output.is_file())

if __name__=="__main__":
    unittest.main()

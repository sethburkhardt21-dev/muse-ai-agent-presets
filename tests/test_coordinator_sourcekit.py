"""T19: independently runnable Coordinator graph/evidence source-kit export."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

from muse_presets import coordinator_sourcekit as kits
from muse_presets.coordinator_dropin import (
    stage_coordinator_dropin,inspect_coordinator_dropin
)


class CoordinatorSourcekitAcceptance(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix="r58-coordinator-kit-")
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.pack=self.root/"coordinator"
        self.archive=self.root/"coordinator-sourcekit.zip"

    def stage(self):
        created=stage_coordinator_dropin(self.pack)
        self.assertEqual(created["status"],"SOURCE_ONLY_COORDINATOR_STAGED")
        self.assertEqual(inspect_coordinator_dropin(self.pack)["status"],
                         "LOCAL_COORDINATOR_MATCH")

    def export(self):
        self.stage()
        report=kits.export_coordinator_sourcekit(self.pack,self.archive)
        self.assertEqual(report["status"],"LOCAL_COORDINATOR_SOURCEKIT_EXPORTED")
        self.assertEqual(report["role_id"],"coordinator")
        self.assertFalse(report["native_installed"])
        self.assertFalse(report["external_effect_authorized"])
        self.assertEqual(report["sha256"],hashlib.sha256(self.archive.read_bytes()).hexdigest())
        checked=kits.verify_coordinator_sourcekit(self.archive,report["sha256"])
        self.assertEqual(checked["status"],"LOCAL_COORDINATOR_SOURCEKIT_VERIFIED")
        return report

    def test_sourcekit_contains_complete_runtime_disabled_skills_and_three_rooms(self):
        self.export()
        with zipfile.ZipFile(self.archive) as archive:
            names=set(archive.namelist())
            self.assertEqual(len(names),len(archive.namelist()))
            for path in ("coordinator/runtime/coordinator_review.py",
                         "coordinator/runtime/coordinator_roles.json",
                         "coordinator/custom-skills/coordinator_workgraph/run.py",
                         "coordinator/custom-skills/coordinator_evidence/run.py",
                         "coordinator/scripts/doctor.py",
                         "coordinator/config/skills.yaml",
                         "coordinator/system-files/MEMORY.md",
                         "coordinator/subchats/acceptance-review/SUBCHAT.json",
                         "coordinator/receipts/COORDINATOR_RECEIPT.json",
                         "START_HERE.md","SOURCEKIT_MANIFEST.json",
                         "EXAMPLE_WORKGRAPH.json","EXAMPLE_ASSERTIONS.json"):
                self.assertIn(path,names)
            metadata=json.loads(archive.read("SOURCEKIT_MANIFEST.json"))
            self.assertEqual(set(metadata["files_sha256"]),names-{"SOURCEKIT_MANIFEST.json"})
            self.assertFalse(metadata["native_installed"])
            self.assertFalse(metadata["external_effect_authorized"])
            self.assertFalse(metadata["omnium_mission_compiled"])
            self.assertFalse(metadata["provider_authenticated"])
            self.assertIn(b"status: disabled",archive.read("coordinator/config/skills.yaml"))

    def test_real_fresh_extract_runs_demo_graph_and_holds_unknown_effect_assertion(self):
        report=self.export()
        new=self.root/"fresh"
        new.mkdir()
        with zipfile.ZipFile(self.archive) as archive:
            archive.extractall(new)
        runner=new/"coordinator/custom-skills/coordinator_workgraph/run.py"
        demo=subprocess.run([sys.executable,"-I","-B",str(runner),"--operation","demo"],
           capture_output=True,text=True,timeout=25)
        self.assertEqual(demo.returncode,0,demo.stderr)
        example=json.loads(demo.stdout)
        self.assertEqual(example["status"],"LOCAL_COORDINATOR_DEMO_PASSED")
        graph=(new/"EXAMPLE_WORKGRAPH.json").read_text(encoding="utf-8")
        review=subprocess.run([sys.executable,"-I","-B",str(runner),
                               "--operation","review"],input=graph,
                               capture_output=True,text=True,timeout=25)
        self.assertEqual(review.returncode,0,review.stderr)
        reviewed=json.loads(review.stdout)
        self.assertEqual(reviewed["status"],"LOCAL_PLAN_REVIEW_ONLY")
        self.assertEqual(reviewed["execution_order"],["diagnose-1","review-2"])
        self.assertEqual(reviewed["held_effect_tasks"],["review-2"])
        self.assertFalse(reviewed["native_tool_invoked"])
        evidence=(new/"EXAMPLE_ASSERTIONS.json").read_text(encoding="utf-8")
        independent=new/"coordinator/custom-skills/coordinator_evidence/run.py"
        e=subprocess.run([sys.executable,"-I","-B",str(independent),
                          "--operation","evidence"],input=evidence,
                         capture_output=True,text=True,timeout=25)
        self.assertEqual(e.returncode,0,e.stderr)
        claims=json.loads(e.stdout)
        self.assertEqual(claims["status"],"UNATTESTED_ASSERTIONS_ONLY")
        self.assertEqual(claims["held_task_ids"],["review-2"])
        self.assertFalse(claims["recipient_readback_verified"])
        self.assertFalse(claims["external_effect_authorized"])
        self.assertEqual(report["sha256"],hashlib.sha256(self.archive.read_bytes()).hexdigest())

    def test_fresh_extract_rejects_forged_native_authority_and_wrong_reviewer(self):
        self.export()
        new=self.root/"fresh"
        new.mkdir()
        with zipfile.ZipFile(self.archive) as zipin:
            zipin.extractall(new)
        graph=json.loads((new/"EXAMPLE_WORKGRAPH.json").read_text())
        evidence=json.loads((new/"EXAMPLE_ASSERTIONS.json").read_text())
        evidence["assertions"]["items"][0]["reviewer_role"]="software-engineer"
        runner=new/"coordinator/custom-skills/coordinator_evidence/run.py"
        p=subprocess.run([sys.executable,"-I","-B",str(runner),"--operation","evidence"],
            input=json.dumps(evidence),capture_output=True,text=True,timeout=25)
        self.assertEqual(p.returncode,2)
        self.assertEqual(json.loads(p.stdout)["status"],"REVIEW_REQUIRED")
        graph["host_authenticated"]=True
        p=subprocess.run([sys.executable,"-I","-B",str(runner),"--operation","review"],
            input=json.dumps(graph),capture_output=True,text=True,timeout=25)
        self.assertEqual(p.returncode,2)
        self.assertEqual(json.loads(p.stdout)["status"],"REVIEW_REQUIRED")

    def test_deterministic_second_export_and_existing_destination_refusal(self):
        first=self.export()
        clone=self.root/"same-second.zip"
        second=kits.export_coordinator_sourcekit(self.pack,clone)
        self.assertEqual(first["sha256"],second["sha256"])
        self.assertEqual(self.archive.read_bytes(),clone.read_bytes())
        original=self.archive.read_bytes()
        with self.assertRaises((FileExistsError,ValueError)):
            kits.export_coordinator_sourcekit(self.pack,self.archive)
        self.assertEqual(self.archive.read_bytes(),original)

    def test_pristine_source_check_rejects_owner_memory_with_forged_self_receipt(self):
        self.stage()
        private=self.pack/"system-files/MEMORY.md"
        private.write_text("SYNTHETIC_PRIVATE_OWNER_MEMORY_SHOULD_NOT_SHIP",encoding="utf-8")
        receipt=self.pack/"receipts/COORDINATOR_RECEIPT.json"
        obj=json.loads(receipt.read_text(encoding="utf-8"))
        obj["files_sha256"]["system-files/MEMORY.md"]=hashlib.sha256(private.read_bytes()).hexdigest()
        receipt.write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"PRISTINE"):
            kits.export_coordinator_sourcekit(self.pack,self.archive)
        self.assertFalse(self.archive.exists())

    def test_wrong_source_code_unexpected_executable_and_modified_skills_refused(self):
        for relative in ("runtime/coordinator_review.py",
                         "custom-skills/coordinator_workgraph/run.py",
                         "config/skills.yaml"):
            dest=self.root/(relative.replace("/","-"))
            stage_coordinator_dropin(dest)
            file=dest/relative
            file.write_bytes(file.read_bytes()+b"\n# unreviewed code\n")
            with self.assertRaisesRegex(ValueError,"PRISTINE"):
                kits.export_coordinator_sourcekit(dest,self.archive)
            self.assertFalse(self.archive.exists())
        outsider=self.root/"outsider"
        stage_coordinator_dropin(outsider)
        (outsider/"unlisted.py").write_text("print('unauthorized')",encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"PRISTINE"):
            kits.export_coordinator_sourcekit(outsider,self.archive)

    def test_checksum_mismatch_modified_download_and_duplicate_zip_entries_denied(self):
        report=self.export()
        with self.assertRaisesRegex(ValueError,"PIN_MISMATCH"):
            kits.verify_coordinator_sourcekit(self.archive,"0"*64)
        altered=self.root/"changed.zip"
        altered.write_bytes(self.archive.read_bytes()+b"x")
        with self.assertRaises(ValueError):
            kits.verify_coordinator_sourcekit(altered,report["sha256"])
        for i,names in enumerate((
           ("coordinator/a.py","coordinator/a.py"),
           ("../path-escape.py","coordinator/a.py"),
           ("coordinator/A.py","coordinator/a.py"))):
            bad=self.root/("unsafe-"+str(i)+".zip")
            with zipfile.ZipFile(bad,"w") as z:
                for n in names:z.writestr(n,b"synthetic")
            with self.assertRaises(ValueError):
                kits.verify_coordinator_sourcekit(bad,hashlib.sha256(bad.read_bytes()).hexdigest())

    def test_rehashed_in_zip_forged_native_receipt_refused(self):
        self.export()
        with zipfile.ZipFile(self.archive) as z:
            values={name:z.read(name) for name in z.namelist()}
        name="coordinator/receipts/COORDINATOR_RECEIPT.json"
        data=json.loads(values[name])
        data["native_installed"]=True
        values[name]=(json.dumps(data,sort_keys=True)+"\n").encode("utf-8")
        manifest=json.loads(values["SOURCEKIT_MANIFEST.json"])
        manifest["files_sha256"][name]=hashlib.sha256(values[name]).hexdigest()
        values["SOURCEKIT_MANIFEST.json"]=(json.dumps(manifest,sort_keys=True)+"\n").encode("utf-8")
        bad=self.root/"forge.zip"
        with zipfile.ZipFile(bad,"w") as z:
            for n,payload in values.items():
                info=zipfile.ZipInfo(n)
                info.create_system=3
                info.external_attr=0o100644<<16
                z.writestr(info,payload)
        with self.assertRaisesRegex(ValueError,"CANONICAL_PIN_MISMATCH"):
            kits.verify_coordinator_sourcekit(bad,hashlib.sha256(bad.read_bytes()).hexdigest())

    def test_symlink_member_and_attempted_private_parent_exfiltration_refused(self):
        self.stage()
        private=self.root/"PRIVATE_OWNER.txt"
        private.write_text("SYNTHETIC_OWNER_CONTENT",encoding="utf-8")
        target=self.pack/"system-files/MEMORY.md"
        target.unlink()
        try:target.symlink_to(private)
        except (OSError,NotImplementedError):
            self.skipTest("OS symlink privilege unavailable")
        with self.assertRaises((ValueError,OSError)):
            kits.export_coordinator_sourcekit(self.pack,self.archive)
        self.assertFalse(self.archive.exists())

    def test_cli_export_is_create_only_and_isolated_from_owner(self):
        root=Path(__file__).resolve().parents[1]
        dest=self.root/"cli-sourcekit.zip"
        cli=root/"examples/export_coordinator_sourcekit.py"
        env=dict(os.environ,PYTHONPATH=str(root/"src"),PYTHONDONTWRITEBYTECODE="1")
        p=subprocess.run([sys.executable,"-B",str(cli),"--to",str(dest)],
           cwd=root,env=env,capture_output=True,text=True,timeout=60)
        self.assertEqual(p.returncode,0,p.stdout+p.stderr)
        claim=json.loads(p.stdout)
        self.assertEqual(claim["status"],"LOCAL_COORDINATOR_SOURCEKIT_EXPORTED")
        self.assertEqual(claim["sha256"],hashlib.sha256(dest.read_bytes()).hexdigest())
        before=dest.read_bytes()
        second=subprocess.run([sys.executable,"-B",str(cli),"--to",str(dest)],
           cwd=root,env=env,capture_output=True,text=True,timeout=30)
        self.assertEqual(second.returncode,2,second.stdout+second.stderr)
        self.assertEqual(json.loads(second.stdout)["status"],"REFUSED")
        self.assertEqual(dest.read_bytes(),before)


if __name__=="__main__":
    unittest.main()

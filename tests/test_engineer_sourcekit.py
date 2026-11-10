"""T20 independent source-kit: an exported ZIP must contain the real runtime."""
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

from muse_presets import engineering_pack
from muse_presets import engineer_sourcekit as kits
from examples.software_engineer_workflow_demo import fixture_case


class SoftwareEngineerSourcekitAcceptance(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="r56-sourcekit-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.pack = self.root/"software-engineer"
        self.archive = self.root/"software-engineer-sourcekit.zip"

    def stage(self):
        report = engineering_pack.stage_engineer_pack(self.pack)
        self.assertEqual(report["status"], "LOCAL_ENGINE_PACK_STAGED")
        self.assertEqual(engineering_pack.inspect_engineer_pack(self.pack)["status"], "LOCAL_MATCH")

    def export(self):
        self.stage()
        result = kits.export_engineer_sourcekit(self.pack, self.archive)
        self.assertEqual(result["status"], "LOCAL_SOURCEKIT_EXPORTED")
        self.assertEqual(result["role_id"], "software-engineer")
        self.assertFalse(result["native_installed"])
        self.assertFalse(result["external_effect_authorized"])
        self.assertEqual(result["sha256"], hashlib.sha256(self.archive.read_bytes()).hexdigest())
        self.assertEqual(kits.verify_engineer_sourcekit(self.archive,result["sha256"])["status"],
                         "LOCAL_SOURCEKIT_ARCHIVE_VERIFIED")
        return result

    def test_export_includes_twelve_actual_runtime_modules_and_disabled_skills(self):
        exported = self.export()
        with zipfile.ZipFile(self.archive) as z:
            names = z.namelist()
            self.assertEqual(len(names), len(set(names)))
            self.assertIn("software-engineer/runtime/claim-gate/engineering_workflow.py", names)
            self.assertIn("software-engineer/runtime/claim-gate/workflow_worker.py", names)
            self.assertIn("software-engineer/runtime/claim-gate/portable_lock.py", names)
            self.assertIn("software-engineer/skills/claim-gate/SKILL.md", names)
            self.assertIn("software-engineer/skills/claim-gate/skill.yaml", names)
            self.assertIn("START_HERE.md",names)
            manifest = json.loads(z.read("SOURCEKIT_MANIFEST.json"))
            self.assertEqual(manifest["runtime_modules"], 12)
            self.assertEqual(set(manifest["files_sha256"]), set(names)-{"SOURCEKIT_MANIFEST.json"})
            self.assertFalse(manifest["native_installed"])
            self.assertFalse(manifest["external_effect_authorized"])
            self.assertFalse(manifest["host_identity_authenticated"])
            self.assertFalse(manifest["os_sandboxed"])
        self.assertEqual(exported["runtime_modules"],12)

    def test_fresh_unpacked_kit_executes_real_disposable_red_patch_green_without_repo(self):
        exported = self.export()
        dest=self.root/"fresh"
        dest.mkdir()
        with zipfile.ZipFile(self.archive) as z:
            z.extractall(dest)
        cli=dest/"software-engineer/runtime/claim-gate/engineering_workflow.py"
        self.assertTrue(cli.is_file())
        case=fixture_case()
        raw=(json.dumps(case,sort_keys=True,separators=(",",":"),ensure_ascii=False)+"\n").encode()
        approved=self.root/"approved-case.json"
        approved.write_bytes(raw)
        state=self.root/"real-work"
        result=subprocess.run([sys.executable,"-I","-B",str(cli),
                              "execute","--case",str(approved),
                              "--case-sha256",hashlib.sha256(raw).hexdigest(),
                              "--to",str(state),"--reviewed-code"],
                              capture_output=True,text=True,timeout=75)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        receipt=json.loads(result.stdout)
        self.assertEqual(receipt["status"],"GREEN_TESTED")
        self.assertEqual(receipt["red"]["exit_code"],1)
        self.assertEqual(receipt["green"]["exit_code"],0)
        self.assertEqual(receipt["green"]["result"]["tests_run"],4)
        self.assertEqual(receipt["red"]["result"]["failures"],case["expected_failures"])
        self.assertEqual((state/"repo/bounds.py").is_file(),True)
        self.assertFalse(receipt["native_muse_invoked"])
        self.assertFalse(receipt["external_effect_authorized"])

    def test_sourcekit_two_exports_from_identical_pristine_pack_are_byte_identical(self):
        first=self.export()
        second=self.root/"same-again.zip"
        again=kits.export_engineer_sourcekit(self.pack,second)
        self.assertEqual(first["sha256"],again["sha256"])
        self.assertEqual(self.archive.read_bytes(),second.read_bytes())

    def test_existing_archive_and_modified_owner_memory_refused_without_overwrite(self):
        self.stage()
        self.archive.write_bytes(b"owner-existing-archive")
        with self.assertRaises((FileExistsError,ValueError)):
            kits.export_engineer_sourcekit(self.pack,self.archive)
        self.assertEqual(self.archive.read_bytes(),b"owner-existing-archive")
        self.archive.unlink()
        original=self.pack/"profile/MEMORY.md"
        original.write_text("sensitive private owner memory",encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"PRISTINE"):
            kits.export_engineer_sourcekit(self.pack,self.archive)
        self.assertFalse(self.archive.exists())

    def test_modified_engine_policy_and_unlisted_executable_refused(self):
        self.stage()
        engine=self.pack/"runtime/claim-gate/engineering_workflow.py"
        engine.write_bytes(engine.read_bytes()+b"\n# unreviewed\n")
        with self.assertRaisesRegex(ValueError,"PRISTINE"):
            kits.export_engineer_sourcekit(self.pack,self.archive)
        self.assertFalse(self.archive.exists())
        self.assertEqual(engineering_pack.inspect_engineer_pack(self.pack)["status"],"REVIEW_REQUIRED")

    def test_unexpected_pack_member_refused_before_archive_created(self):
        self.stage()
        (self.pack/"runtime/claim-gate/extra.py").write_text("print('unexpected')",encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"PRISTINE"):
            kits.export_engineer_sourcekit(self.pack,self.archive)
        self.assertFalse(self.archive.exists())

    def test_wrong_archive_sha_and_replayed_changed_bytes_refused(self):
        result=self.export()
        with self.assertRaisesRegex(ValueError,"PIN_MISMATCH"):
            kits.verify_engineer_sourcekit(self.archive,"0"*64)
        replacement=self.root/"changed.zip"
        replacement.write_bytes(self.archive.read_bytes()+b"x")
        with self.assertRaises(ValueError):
            kits.verify_engineer_sourcekit(replacement,result["sha256"])

    def test_malicious_archive_duplicate_and_traversal_refused_even_with_matching_sha(self):
        self.stage()
        for names in (("software-engineer/a.py","software-engineer/a.py"),
                      ("../escape.py","software-engineer/a.py"),
                      ("software-engineer/A.py","software-engineer/a.py")):
            path=self.root/("bad-"+str(len(list(self.root.glob("bad-*.zip"))))+".zip")
            with zipfile.ZipFile(path,"w") as z:
                for member in names:z.writestr(member,b"print('bad')")
            digest=hashlib.sha256(path.read_bytes()).hexdigest()
            with self.assertRaises(ValueError):
                kits.verify_engineer_sourcekit(path,digest)

    def test_forged_mutable_pack_receipt_cannot_bless_private_owner_memory(self):
        self.stage()
        secret=self.pack/"profile/MEMORY.md"
        secret.write_text("SYNTHETIC_PRIVATE_OWNER_MEMORY_DO_NOT_EXPORT",encoding="utf-8")
        receipt=self.pack/"receipts/PACK_RECEIPT.json"
        state=json.loads(receipt.read_text(encoding="utf-8"))
        state["files_sha256"]["profile/MEMORY.md"]=hashlib.sha256(secret.read_bytes()).hexdigest()
        receipt.write_text(json.dumps(state,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        # This currently passes the older mutable local-receipt inspector:
        self.assertEqual(engineering_pack.inspect_engineer_pack(self.pack)["status"],"LOCAL_MATCH")
        with self.assertRaisesRegex(ValueError,"OWNER_PROFILE_NOT_CANONICAL"):
            kits.export_engineer_sourcekit(self.pack,self.archive)
        self.assertFalse(self.archive.exists())

    def test_self_rehashed_forged_runtime_authority_is_refused(self):
        self.export()
        with zipfile.ZipFile(self.archive) as archive:
            payload={name:archive.read(name) for name in archive.namelist()}
        receipt_name="software-engineer/receipts/PACK_RECEIPT.json"
        receipt=json.loads(payload[receipt_name])
        receipt["installed_native_tools"]=["unreviewed-external-tool"]
        payload[receipt_name]=(json.dumps(receipt,sort_keys=True)+"\n").encode()
        manifest=json.loads(payload["SOURCEKIT_MANIFEST.json"])
        manifest["files_sha256"][receipt_name]=hashlib.sha256(payload[receipt_name]).hexdigest()
        payload["SOURCEKIT_MANIFEST.json"]=(json.dumps(manifest,sort_keys=True)+"\n").encode()
        forged=self.root/"self-rehashed-forged-authority.zip"
        with zipfile.ZipFile(forged,"w") as zip_out:
            for name,data in sorted(payload.items()):
                entry=zipfile.ZipInfo(name)
                entry.create_system=3
                entry.external_attr=0o100644<<16
                zip_out.writestr(entry,data)
        digest=hashlib.sha256(forged.read_bytes()).hexdigest()
        with self.assertRaisesRegex(ValueError,"RECEIPT"):
            kits.verify_engineer_sourcekit(forged,digest)

    def test_export_refuses_symlinked_member_even_if_original_file_exists(self):
        self.stage()
        member=self.pack/"profile/MEMORY.md"
        original=member.read_bytes()
        member.unlink()
        target=self.root/"target.txt"
        target.write_bytes(original)
        try:
            member.symlink_to(target)
        except (OSError,NotImplementedError):
            self.skipTest("symlink not permitted by OS")
        with self.assertRaises((ValueError,OSError)):
            kits.export_engineer_sourcekit(self.pack,self.archive)
        self.assertFalse(self.archive.exists())


    def test_documented_create_only_cli_exports_a_verified_archive(self):
        root=Path(__file__).resolve().parents[1]
        output=self.root/"user-facing-sourcekit.zip"
        env=dict(os.environ,PYTHONPATH=str(root/"src"),PYTHONDONTWRITEBYTECODE="1")
        cli=root/"examples/export_software_engineer_sourcekit.py"
        run=subprocess.run([sys.executable,"-B",str(cli),"--to",str(output)],
                           cwd=root,env=env,capture_output=True,text=True,timeout=45)
        self.assertEqual(run.returncode,0,run.stdout+run.stderr)
        receipt=json.loads(run.stdout)
        self.assertEqual(receipt["status"],"LOCAL_SOURCEKIT_EXPORTED")
        self.assertEqual(receipt["sha256"],hashlib.sha256(output.read_bytes()).hexdigest())
        self.assertEqual(kits.verify_engineer_sourcekit(output,receipt["sha256"])["status"],
                         "LOCAL_SOURCEKIT_ARCHIVE_VERIFIED")
        original_zip=output.read_bytes()
        replay=subprocess.run([sys.executable,"-B",str(cli),"--to",str(output)],
                              cwd=root,env=env,capture_output=True,text=True,timeout=20)
        self.assertEqual(replay.returncode,2,replay.stdout+replay.stderr)
        self.assertEqual(json.loads(replay.stdout)["status"],"REFUSED")
        self.assertEqual(output.read_bytes(),original_zip)

if __name__=="__main__":
    unittest.main()

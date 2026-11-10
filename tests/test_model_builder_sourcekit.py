"""Executable Model Builder distribution, including real toy training/checkpoint replay."""
from __future__ import annotations
import hashlib
import importlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile
from muse_presets.model_builder_dropin import stage_model_builder_dropin,inspect_model_builder_dropin


class ModelBuilderSourcekitTests(unittest.TestCase):
    def setUp(self):
        try:self.kits=importlib.import_module("muse_presets.model_builder_sourcekit")
        except ModuleNotFoundError:self.fail("Missing independently runnable Model Builder ZIP export")
        self.tmp=tempfile.TemporaryDirectory(prefix="model-sourcekit-")
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.pack=self.root/"model-builder"
        self.zip=self.root/"model-builder.zip"
        stage_model_builder_dropin(self.pack)

    def export(self):
        report=self.kits.export_model_builder_sourcekit(self.pack,self.zip)
        self.assertEqual(report["status"],"LOCAL_MODEL_SOURCEKIT_EXPORTED")
        self.assertFalse(report["native_installed"])
        self.assertFalse(report["external_effect_authorized"])
        self.assertEqual(hashlib.sha256(self.zip.read_bytes()).hexdigest(),report["sha256"])
        self.assertEqual(self.kits.verify_model_builder_sourcekit(self.zip,report["sha256"])["status"],
                         "LOCAL_MODEL_SOURCEKIT_VERIFIED")
        return report

    def test_export_contains_real_engine_fixture_and_disabled_registrations(self):
        self.export()
        with zipfile.ZipFile(self.zip) as archive:
            names=archive.namelist()
            self.assertEqual(len(names),len(set(names)))
            for path in ("model-builder/runtime/toy_model.py","model-builder/runtime/model_eval.py",
                         "model-builder/custom-skills/model_development_metrics/run.py",
                         "model-builder/receipts/MODEL_BUILDER_RECEIPT.json",
                         "SOURCEKIT_MANIFEST.json","START_HERE.md","EXAMPLE_TOY_EXPERIMENT.json"):
                self.assertIn(path,names)
            metadata=json.loads(archive.read("SOURCEKIT_MANIFEST.json"))
            self.assertEqual(set(metadata["files_sha256"]),set(names)-{"SOURCEKIT_MANIFEST.json"})
            self.assertTrue(metadata["bounded_toy_training_available"])
            self.assertTrue(metadata["local_training_requires_opt_in"])
            self.assertFalse(metadata["native_installed"])
            self.assertFalse(metadata["external_effect_authorized"])
            self.assertFalse(metadata["gpu_training_available"])
            self.assertIn(b"status: disabled",archive.read("model-builder/config/skills.yaml"))

    def test_fresh_extracted_pack_trains_reloads_and_recovers_baseline_with_no_repo_import(self):
        self.export()
        destination=self.root/"fresh";destination.mkdir()
        with zipfile.ZipFile(self.zip) as z:z.extractall(destination)
        runner=destination/"model-builder/custom-skills/model_development_metrics/run.py"
        p=subprocess.run([sys.executable,"-I","-B",str(runner),"--operation","toy-demo","--allow-local-training"],
                         cwd=destination,capture_output=True,text=True,timeout=35)
        self.assertEqual(p.returncode,0,p.stdout+p.stderr)
        result=json.loads(p.stdout)
        self.assertEqual(result["status"],"LOCAL_TOY_MODEL_DEMO_PASSED")
        self.assertTrue(result["trained_this_call"])
        self.assertTrue(result["checkpoint_reloaded"])
        self.assertTrue(result["baseline_recovered"])
        self.assertEqual(result["candidate_correct"],4)
        self.assertEqual(result["baseline_correct"],2)
        doctor=subprocess.run([sys.executable,"-I","-B",str(destination/"model-builder/scripts/doctor.py")],
                              cwd=destination,capture_output=True,text=True,timeout=30)
        self.assertEqual(doctor.returncode,0,doctor.stderr)
        self.assertEqual(json.loads(doctor.stdout)["status"],"LOCAL_SELF_HASH_MATCH")
        denied=subprocess.run([sys.executable,"-I","-B",str(runner),"--operation","toy-train"],
            input=(destination/"EXAMPLE_TOY_EXPERIMENT.json").read_text(),
            capture_output=True,text=True,timeout=30)
        self.assertEqual(denied.returncode,2)
        self.assertEqual(json.loads(denied.stdout)["status"],"REVIEW_REQUIRED")

    def test_portable_profiles_and_receipts_use_lf_with_correct_embedded_hashes(self):
        self.export()
        with zipfile.ZipFile(self.zip) as archive:
            data={p:archive.read(p) for p in archive.namelist()}
        for name,raw in data.items():
            if name.startswith(("model-builder/profile/","model-builder/system-files/")):
                self.assertNotIn(b"\r\n",raw,name)
        profile=json.loads(data["model-builder/profile/RECEIPT.json"])
        for name,digest in profile["rendered_sha256"].items():
            self.assertEqual(hashlib.sha256(data["model-builder/profile/"+name]).hexdigest(),digest)
        pack=json.loads(data["model-builder/receipts/MODEL_BUILDER_RECEIPT.json"])
        for name,digest in pack["files_sha256"].items():
            self.assertEqual(hashlib.sha256(data["model-builder/"+name]).hexdigest(),digest)

    def test_exports_of_two_pristine_stages_are_identical_and_never_overwrite(self):
        first=self.export()
        secondpack=self.root/"second-pack";stage_model_builder_dropin(secondpack)
        secondzip=self.root/"second.zip"
        second=self.kits.export_model_builder_sourcekit(secondpack,secondzip)
        self.assertEqual(first["sha256"],second["sha256"])
        before=self.zip.read_bytes()
        with self.assertRaises((ValueError,FileExistsError)):
            self.kits.export_model_builder_sourcekit(self.pack,self.zip)
        self.assertEqual(self.zip.read_bytes(),before)

    def test_forged_self_receipts_cannot_bless_private_owner_profile(self):
        for relative in ("profile/MEMORY.md","system-files/MEMORY.md"):
            (self.pack/relative).write_bytes(b"SYNTHETIC_PRIVATE_OWNER_MEMORY_NOT_FOR_EXPORT\n")
        profile=self.pack/"profile/RECEIPT.json"
        value=json.loads(profile.read_bytes())
        value["rendered_sha256"]["MEMORY.md"]=hashlib.sha256((self.pack/"profile/MEMORY.md").read_bytes()).hexdigest()
        profile.write_bytes((json.dumps(value,indent=2)+"\n").encode())
        receipt=self.pack/"receipts/MODEL_BUILDER_RECEIPT.json"
        meta=json.loads(receipt.read_bytes())
        for relative in meta["files_sha256"]:
            meta["files_sha256"][relative]=hashlib.sha256((self.pack/relative).read_bytes()).hexdigest()
        receipt.write_bytes((json.dumps(meta,indent=2,sort_keys=True,ensure_ascii=False)+"\n").encode())
        with self.assertRaisesRegex(ValueError,"PRISTINE"):
            self.kits.export_model_builder_sourcekit(self.pack,self.zip)
        self.assertFalse(self.zip.exists())

    def test_changed_runtime_extra_files_and_linked_members_refused(self):
        (self.pack/"runtime/toy_model.py").write_text("raise SystemExit('wrong')",encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"PRISTINE"):
            self.kits.export_model_builder_sourcekit(self.pack,self.zip)
        extra=self.root/"other";stage_model_builder_dropin(extra)
        (extra/"unexpected.py").write_text("print('extra')")
        with self.assertRaises(ValueError):self.kits.export_model_builder_sourcekit(extra,self.zip)
        self.assertFalse(self.zip.exists())

    def test_wrong_archive_pin_unsafe_members_and_duplicate_names_refused(self):
        result=self.export()
        with self.assertRaisesRegex(ValueError,"PIN_MISMATCH"):
            self.kits.verify_model_builder_sourcekit(self.zip,"0"*64)
        for index,names in enumerate((("../escape.py","a.py"),("a.py","a.py"),("a.py","A.py"))):
            invalid=self.root/(str(index)+".zip")
            with zipfile.ZipFile(invalid,"w") as z:
                for n in names:z.writestr(n,b"invalid")
            with self.assertRaises(ValueError):
                self.kits.verify_model_builder_sourcekit(invalid,hashlib.sha256(invalid.read_bytes()).hexdigest())

    def test_rehashed_native_authority_forgery_is_still_refused(self):
        self.export()
        with zipfile.ZipFile(self.zip) as z:data={p:z.read(p) for p in z.namelist()}
        name="model-builder/receipts/MODEL_BUILDER_RECEIPT.json"
        value=json.loads(data[name]);value["native_installed"]=True
        data[name]=(json.dumps(value,sort_keys=True)+"\n").encode()
        manifest=json.loads(data["SOURCEKIT_MANIFEST.json"])
        manifest["files_sha256"][name]=hashlib.sha256(data[name]).hexdigest()
        data["SOURCEKIT_MANIFEST.json"]=(json.dumps(manifest,sort_keys=True)+"\n").encode()
        forged=self.root/"forged.zip"
        with zipfile.ZipFile(forged,"w") as z:
            for n,b in data.items():
                info=zipfile.ZipInfo(n);info.create_system=3;info.external_attr=0o100644<<16
                z.writestr(info,b)
        with self.assertRaises(ValueError):
            self.kits.verify_model_builder_sourcekit(forged,hashlib.sha256(forged.read_bytes()).hexdigest())


if __name__=="__main__":unittest.main()

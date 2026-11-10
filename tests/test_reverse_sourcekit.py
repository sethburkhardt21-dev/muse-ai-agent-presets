"""R80 source-package integrity and executable offline comparison acceptance."""
from __future__ import annotations
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
from muse_presets import reverse_sourcekit as kit
from muse_presets.public_export import select_public_files

ROOT = Path(__file__).resolve().parents[1]

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def observation(action,target,outcome):
    return {"action":action,"target":target,"outcome":outcome}

VALID = {
  "schema":"muse-presets/reverse-offline-fixture-input-v1",
  "analysis_boundary":"OFFLINE_SUPPLIED_OBSERVATIONS_ONLY",
  "authorization_declaration":"OWNER_OR_PERMISSION_DECLARED_UNVERIFIED",
  "before":[observation("click","save","silent"),observation("click","cancel","closed")],
  "after":[observation("click","save","toast"),observation("click","cancel","closed"),observation("click","export","file")]
}

class ReverseSourcekitTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="reverse-kit-test-")
        self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name)

    def make(self,name="reverse.zip"):
        target=self.base/name
        info=kit.export_reverse_sourcekit(ROOT,target)
        return target,info

    def unpack(self):
        target,_=self.make()
        folder=self.base/"kit"
        with zipfile.ZipFile(target) as z:
            z.extractall(folder) # trusted freshly generated canonical local kit
        return folder

    def run_kit(self,folder,operation="demo",fixture=None,optimize=False):
        cmd=[sys.executable,"-I","-B"]
        if optimize:
            cmd.append("-O")
        cmd.extend([str(folder/"run.py"),"--operation",operation])
        if fixture is not None:
            cmd.extend(["--fixture",str(fixture)])
        env=dict(os.environ,PYTHONPATH="not-the-repo",PYTHONDONTWRITEBYTECODE="1")
        return subprocess.run(cmd,cwd=self.base,env=env,capture_output=True,text=True,timeout=50)

    def fixture(self,value=None,name="input.json"):
        p=self.base/name
        p.write_text(json.dumps(value if value is not None else VALID),encoding="utf-8")
        return p

    def refusal(self,folder,operation="demo",fixture=None,optimize=False):
        p=self.run_kit(folder,operation,fixture,optimize)
        self.assertEqual(p.returncode,2,p.stdout+p.stderr)
        self.assertNotIn("Traceback",p.stderr)
        obj=json.loads(p.stdout)
        self.assertEqual(obj["status"],"REFUSED")
        self.assertFalse(obj["native_invoked"])
        self.assertFalse(obj["network_activity"])
        return obj

    def test_source_bytes_pinned_and_manifest_signed_only_by_hash(self):
        target,_=self.make()
        with zipfile.ZipFile(target) as z:
            for source,dest in kit.SOURCE_MAP.items():
                self.assertEqual(z.read(dest),(ROOT/source).read_bytes())
            manifest=json.loads(z.read("SOURCEKIT_MANIFEST.json"))
            self.assertEqual(set(z.namelist()),set(manifest["files_sha256"])|{"SOURCEKIT_MANIFEST.json"})
            self.assertFalse(manifest["native_installed"])
            self.assertFalse(manifest["network_activity"])
            self.assertFalse(manifest["external_effects_authorized"])

    def test_canonical_repeat_and_verify(self):
        a,one=self.make()
        b,two=self.make("second.zip")
        self.assertEqual(a.read_bytes(),b.read_bytes())
        self.assertEqual(one["archive_sha256"],two["archive_sha256"])
        self.assertEqual(kit.verify_reverse_sourcekit(ROOT,a,one["archive_sha256"])["status"],
                         "LOCAL_REVERSE_SOURCEKIT_VERIFIED")

    def test_destination_create_only(self):
        target,_=self.make()
        before=target.read_bytes()
        with self.assertRaises(ValueError):
            kit.export_reverse_sourcekit(ROOT,target)
        self.assertEqual(target.read_bytes(),before)

    def test_external_digest_invalid(self):
        target,_=self.make()
        for digest in (None,"","0"*64,"invalid"):
            with self.subTest(digest=digest),self.assertRaises(ValueError):
                kit.verify_reverse_sourcekit(ROOT,target,digest)

    def test_rehashed_tampered_zip_refused(self):
        target,_=self.make()
        target.write_bytes(target.read_bytes()+b"appended")
        with self.assertRaisesRegex(ValueError,"CANONICAL_ARCHIVE_CHANGED"):
            kit.verify_reverse_sourcekit(ROOT,target,sha(target.read_bytes()))

    def test_untrusted_zip_not_parsed(self):
        target=self.base/"bad.zip"
        target.write_bytes(b"not a zip")
        real=zipfile.ZipFile
        def guarded(*args,**kwargs):
            mode=args[1] if len(args)>1 else kwargs.get("mode","r")
            self.assertEqual(mode,"w","Untrusted ZIP opened")
            return real(*args,**kwargs)
        with patch.object(zipfile,"ZipFile",side_effect=guarded):
            with self.assertRaisesRegex(ValueError,"CANONICAL_ARCHIVE_CHANGED"):
                kit.verify_reverse_sourcekit(ROOT,target,sha(target.read_bytes()))

    def test_untrusted_source_pin_refused(self):
        copied=self.base/"source"
        for name in kit.SOURCE_SHA:
            dest=copied/name
            dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(ROOT/name,dest)
        altered=copied/"src/muse_presets/reverse.py"
        altered.write_bytes(altered.read_bytes()+b"\n# drift\n")
        with self.assertRaisesRegex(ValueError,"SOURCE_PIN_MISMATCH"):
            kit.export_reverse_sourcekit(copied,self.base/"drift.zip")

    def test_original_engine_selftest_standalone(self):
        folder=self.unpack()
        result=self.run_kit(folder,"self-test")
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        payload=json.loads(result.stdout)
        self.assertEqual(payload["status"],"LOCAL_REVERSE_SELF_TEST_PASSED")
        self.assertEqual(payload["tests_run"],10)
        self.assertEqual(payload["errors"],0)
        self.assertEqual(payload["failures"],0)

    def test_demo_reconstructs_synthetic_difference(self):
        folder=self.unpack()
        result=self.run_kit(folder,"demo")
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        payload=json.loads(result.stdout)
        self.assertEqual(payload["status"],"LOCAL_REVERSE_FIXTURE_DEMO_PASSED")
        self.assertEqual(payload["changed"],["click:save"])
        self.assertEqual(payload["added"],["click:export"])
        self.assertFalse(payload["target_accessed"])
        self.assertFalse(payload["network_activity"])
        self.assertFalse(payload["native_invoked"])

    def test_compare_real_supplied_local_fixture(self):
        folder=self.unpack()
        fixture=self.fixture()
        result=self.run_kit(folder,"compare",fixture)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        payload=json.loads(result.stdout)
        self.assertEqual(payload["status"],"LOCAL_REVERSE_FIXTURE_COMPARED")
        self.assertEqual(payload["changed"],["click:save"])
        self.assertEqual(payload["added"],["click:export"])
        self.assertEqual(payload["fixture_sha256"],sha(fixture.read_bytes()))
        self.assertTrue(payload["declaration_unverified"])
        self.assertFalse(payload["target_accessed"])

    def test_compare_declared_out_of_scope_refused(self):
        folder=self.unpack()
        for val in (dict(VALID,analysis_boundary="LIVE_SCAN"),
                    dict(VALID,authorization_declaration="NO_RIGHTS"),
                    dict(VALID,before=[observation("click","https://other.example","ok")]),
                    dict(VALID,extra="unknown")):
            with self.subTest(val=repr(val)[:75]):
                self.refusal(folder,"compare",self.fixture(val))

    def test_compare_no_fixture_refused(self):
        self.refusal(self.unpack(),"compare")

    def test_compare_fixture_path_inside_immutable_kit_refused(self):
        folder=self.unpack()
        p=folder/"input.json"
        p.write_text(json.dumps(VALID),encoding="utf-8")
        self.refusal(folder,"compare",p)

    def test_compare_oversized_external_fixture_refused(self):
        folder=self.unpack()
        p=self.base/"oversized.json"
        p.write_bytes(b"x"*131073)
        self.refusal(folder,"compare",p)

    def test_compare_extra_bytes_refused(self):
        folder=self.unpack()
        p=self.base/"bad.json"
        p.write_bytes(b'{"schema":"ok"} trailing')
        self.refusal(folder,"compare",p)

    def test_modified_engine_even_if_manifest_rehashed_refused(self):
        folder=self.unpack()
        path=folder/"muse_presets/reverse.py"
        path.write_bytes(path.read_bytes()+b"\n# altered\n")
        m=folder/"SOURCEKIT_MANIFEST.json"
        doc=json.loads(m.read_bytes())
        doc["files_sha256"]["muse_presets/reverse.py"]=sha(path.read_bytes())
        m.write_text(json.dumps(doc),encoding="utf-8")
        self.refusal(folder)

    def test_duplicated_manifest_key_refused(self):
        folder=self.unpack()
        p=folder/"SOURCEKIT_MANIFEST.json"
        p.write_bytes(b'{"schema":"forged",'+p.read_bytes().lstrip()[1:])
        self.refusal(folder)

    def test_deep_manifest_refused(self):
        folder=self.unpack()
        p=folder/"SOURCEKIT_MANIFEST.json"
        p.write_bytes(b"["*10000+b"0"+b"]"*10000)
        self.refusal(folder)

    def test_extra_import_shadow_refused(self):
        folder=self.unpack()
        (folder/"json.py").write_text("raise RuntimeError('not run')\n")
        self.refusal(folder)

    def test_optimized_interpreter_refused(self):
        folder=self.unpack()
        r=self.refusal(folder,optimize=True)
        self.assertIn("OPTIMIZED_VALIDATION_UNSUPPORTED",r["reason"])

    def test_root_symlink_refused_if_available(self):
        folder=self.unpack()
        link=self.base/"linked"
        try:
            link.symlink_to(folder,target_is_directory=True)
        except (OSError,NotImplementedError) as e:
            self.skipTest("OS directory symlink privilege absent:"+str(e))
        self.refusal(link)

    def test_root_junction_refused_on_windows(self):
        if os.name!="nt":
            self.skipTest("Native Windows junction case")
        folder=self.unpack()
        link=self.base/"junction"
        p=subprocess.run(["cmd","/c","mklink","/J",str(link),str(folder)],capture_output=True,text=True,timeout=15)
        self.assertEqual(p.returncode,0,p.stdout+p.stderr)
        self.assertTrue(link.is_junction())
        try:
            self.refusal(link)
        finally:
            os.rmdir(link)

    def test_public_snapshot_includes_source_kit(self):
        files=select_public_files(ROOT)
        for name in ("src/muse_presets/reverse_sourcekit.py","examples/export_reverse_sourcekit.py",
                     "tests/test_reverse_sourcekit.py","tests/test_reverse_fixture.py",
                     "docs/kits/REVERSE_SOURCEKIT.md"):
            self.assertIn(name,files)
        self.assertFalse(any(name.startswith("control/") for name in files))

if __name__=="__main__":
    unittest.main()

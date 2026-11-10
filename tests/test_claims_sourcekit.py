"""A genuinely runnable, independent, zero-provider Claims Adjudicator ZIP."""
from __future__ import annotations
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile
from muse_presets.claims_sourcekit import export_claims_sourcekit, verify_claims_sourcekit

SOURCE=Path(__file__).resolve().parents[1]
REQUIRED={
    "claims-adjudicator/claims.py",
    "claims-adjudicator/run.py",
    "claims-adjudicator/preset.json",
    "claims-adjudicator/playbook.json",
    "LICENSE",
    "START_HERE.md",
    "EXAMPLE_CLAIM.json",
    "SOURCEKIT_MANIFEST.json",
}
def sha(raw):
    return hashlib.sha256(raw).hexdigest()

class ClaimsSourcekitTests(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory(prefix="claims-sourcekit-")
        self.addCleanup(self.t.cleanup)
        self.base=Path(self.t.name)
        self.zip=self.base/"claims.zip"

    def export(self):
        result=export_claims_sourcekit(SOURCE,self.zip)
        self.assertEqual(result["status"],"LOCAL_CLAIMS_SOURCEKIT_EXPORTED")
        self.assertFalse(result["native_installed"])
        self.assertFalse(result["external_effect_authorized"])
        self.assertEqual(sha(self.zip.read_bytes()),result["archive_sha256"])
        self.assertEqual(verify_claims_sourcekit(SOURCE,self.zip,result["archive_sha256"])["status"],
                         "LOCAL_CLAIMS_SOURCEKIT_VERIFIED")
        return result

    def run_bundle(self,*args,input_text=None):
        extracted=self.base/"extracted"
        if not extracted.exists():
            extracted.mkdir()
            with zipfile.ZipFile(self.zip) as z:z.extractall(extracted)
        runner=extracted/"claims-adjudicator"/"run.py"
        cmd=[sys.executable,"-I","-B",str(runner),*args]
        p=subprocess.run(cmd,cwd=extracted,input=input_text,
                         text=True,capture_output=True,timeout=25)
        return p,json.loads(p.stdout)

    def test_export_exact_members_manifest_and_disabled_native(self):
        self.export()
        with zipfile.ZipFile(self.zip) as z:
            self.assertEqual(set(z.namelist()),REQUIRED)
            manifest=json.loads(z.read("SOURCEKIT_MANIFEST.json"))
            self.assertEqual(set(manifest["files_sha256"]),REQUIRED-{"SOURCEKIT_MANIFEST.json"})
            for name,digest in manifest["files_sha256"].items():
                self.assertEqual(sha(z.read(name)),digest)
            for prop in ("native_installed","provider_authenticated",
                         "external_effect_authorized","independent_verified",
                         "public_release_published"):
                self.assertFalse(manifest[prop])
            self.assertNotIn(b"token",z.read("EXAMPLE_CLAIM.json"))
            self.assertIn(b"claims-adjudicator",z.read("START_HERE.md"))

    def test_independent_extracted_pure_demo(self):
        self.export()
        proc,obj=self.run_bundle("--operation","demo")
        self.assertEqual(proc.returncode,0,proc.stderr)
        self.assertEqual(obj["status"],"LOCAL_CLAIMS_DEMO_PASSED")
        self.assertEqual(obj["result"]["disposition"],"OVERCLAIM")
        self.assertFalse(obj["result"]["independent_verified"])
        self.assertFalse(obj["external_effect_authorized"])

    def test_actual_stdin_review_requires_optin(self):
        self.export()
        with zipfile.ZipFile(self.zip) as z: example=z.read("EXAMPLE_CLAIM.json").decode("utf-8")
        proc,denied=self.run_bundle("--operation","assess",input_text=example)
        self.assertEqual(proc.returncode,2)
        self.assertEqual(denied["status"],"REVIEW_REQUIRED")
        proc,accepted=self.run_bundle("--operation","assess","--allow-reviewed-local",
                                      input_text=example)
        self.assertEqual(proc.returncode,0,proc.stderr)
        self.assertEqual(accepted["result"]["disposition"],"OVERCLAIM")
        self.assertFalse(accepted["provider_authenticated"])

    def test_negative_duplicate_json_nan_invalid_grade_and_bad_type(self):
        self.export()
        for data in ('{"statement":"a","statement":"b"}',
                     '{"statement":NaN}',
                     '{"statement":[],"asserted_grade":"LOCAL_TESTED","evidence_grade":"LOCAL_TESTED","conditions":["x"]}',
                     '{"statement":"x","asserted_grade":"IMPOSSIBLE","evidence_grade":"LOCAL_TESTED","conditions":["x"]}'):
            with self.subTest(data=data):
                proc,obj=self.run_bundle("--operation","assess","--allow-reviewed-local",
                                         input_text=data)
                self.assertEqual(proc.returncode,2)
                self.assertEqual(obj["status"],"REFUSED")
                self.assertFalse(obj["external_effect_authorized"])

    def test_wrong_hash_and_rehashed_tampered_archive_refused(self):
        result=self.export()
        with self.assertRaisesRegex(ValueError,"PIN"):
            verify_claims_sourcekit(SOURCE,self.zip,"0"*64)
        with zipfile.ZipFile(self.zip) as z:
            members={name:z.read(name) for name in z.namelist()}
        members["claims-adjudicator/claims.py"]=b"print('tampered source')\n"
        manifest=json.loads(members["SOURCEKIT_MANIFEST.json"])
        manifest["files_sha256"]["claims-adjudicator/claims.py"]=sha(
            members["claims-adjudicator/claims.py"])
        members["SOURCEKIT_MANIFEST.json"]=(
            json.dumps(manifest,sort_keys=True)+"\n").encode()
        bad=self.base/"tampered.zip"
        with zipfile.ZipFile(bad,"w") as z:
            for name,payload in members.items():z.writestr(name,payload)
        with self.assertRaises(ValueError):
            verify_claims_sourcekit(SOURCE,bad,sha(bad.read_bytes()))

    def test_malicious_zip_members_case_alias_and_replay_refused(self):
        self.export()
        original=self.zip.read_bytes()
        with self.assertRaises((FileExistsError,ValueError)):
            export_claims_sourcekit(SOURCE,self.zip)
        self.assertEqual(original,self.zip.read_bytes())
        for i,names in enumerate((("../escape.py","claims-adjudicator/claims.py"),
                                  ("a.py","a.py"),("a.py","A.py"))):
            p=self.base/(str(i)+".zip")
            with zipfile.ZipFile(p,"w") as z:
                for name in names:z.writestr(name,b"invalid")
            with self.assertRaises(ValueError):
                verify_claims_sourcekit(SOURCE,p,sha(p.read_bytes()))

    def test_corrupt_zip_returns_bounded_value_error(self):
        for name,payload in (
            ("not-zip", b"not-a-zip"),
            ("truncated-header", bytes([0x50,0x4B,0x03,0x04]) + b"truncated"),
        ):
            with self.subTest(case=name):
                target=self.base/(name+".zip")
                target.write_bytes(payload)
                with self.assertRaisesRegex(ValueError,"CLAIMS_SOURCEKIT_CORRUPT_ARCHIVE"):
                    verify_claims_sourcekit(SOURCE,target,sha(payload))

    def test_corrupt_zip_cli_refuses_without_traceback(self):
        import os
        env=dict(os.environ,PYTHONPATH=str(SOURCE/"src"),PYTHONDONTWRITEBYTECODE="1")
        target=self.base/"malformed.zip"
        target.write_bytes(b"not a ZIP archive")
        proc=subprocess.run([
            sys.executable,"-B","examples/export_claims_sourcekit.py",
            "--verify",str(target),"--sha256",sha(target.read_bytes())
        ],cwd=SOURCE,env=env,text=True,capture_output=True,timeout=30)
        self.assertEqual(proc.returncode,2)
        result=json.loads(proc.stdout)
        self.assertEqual(result["status"],"REFUSED")
        self.assertFalse(result["external_effect_authorized"])
        self.assertNotIn("Traceback",proc.stderr)

    def test_repeatable_two_fresh_archives(self):
        self.export()
        second=self.base/"second.zip"
        export_claims_sourcekit(SOURCE,second)
        self.assertEqual(self.zip.read_bytes(),second.read_bytes())

    def test_modified_canonical_source_is_refused(self):
        import shutil
        clone=self.base/"clone"
        (clone/"src/muse_presets").mkdir(parents=True)
        (clone/"presets/claims-adjudicator").mkdir(parents=True)
        shutil.copy2(SOURCE/"LICENSE",clone/"LICENSE")
        shutil.copy2(SOURCE/"src/muse_presets/claims.py",clone/"src/muse_presets/claims.py")
        for name in ("playbook.json","preset.json"):
            shutil.copy2(SOURCE/"presets/claims-adjudicator"/name,
                         clone/"presets/claims-adjudicator"/name)
        (clone/"src/muse_presets/claims.py").write_text("raise RuntimeError('tampered')\n")
        with self.assertRaises(ValueError):
            export_claims_sourcekit(clone,self.base/"forged.zip")

    def test_actual_export_cli_and_external_sha_readback(self):
        import os
        env=dict(os.environ,PYTHONPATH=str(SOURCE/"src"),PYTHONDONTWRITEBYTECODE="1")
        command=[sys.executable,"-B","examples/export_claims_sourcekit.py"]
        written=subprocess.run(command+["--to",str(self.zip)],cwd=SOURCE,
            env=env,capture_output=True,text=True,timeout=35)
        self.assertEqual(written.returncode,0,written.stdout+written.stderr)
        original=json.loads(written.stdout)
        self.assertEqual(original["status"],"LOCAL_CLAIMS_SOURCEKIT_EXPORTED")
        verified=subprocess.run(command+["--verify",str(self.zip),"--sha256",
              original["archive_sha256"]],cwd=SOURCE,env=env,
              capture_output=True,text=True,timeout=30)
        self.assertEqual(verified.returncode,0,verified.stderr)
        self.assertEqual(json.loads(verified.stdout)["status"],
                         "LOCAL_CLAIMS_SOURCEKIT_VERIFIED")
        again=subprocess.run(command+["--to",str(self.zip)],cwd=SOURCE,
              env=env,capture_output=True,text=True,timeout=30)
        self.assertEqual(again.returncode,2)
        self.assertEqual(json.loads(again.stdout)["status"],"REFUSED")

    def test_public_export_carries_complete_useful_kit_not_internal_work(self):
        from muse_presets.public_export import select_public_files
        selected=select_public_files(SOURCE)
        for path in ("src/muse_presets/claims_sourcekit.py",
                     "examples/export_claims_sourcekit.py",
                     "tests/test_claims_sourcekit.py",
                     "tests/test_claims_archive_corruption.py",
                     "docs/kits/CLAIMS_SOURCEKIT.md"):
            self.assertIn(path,selected)
        self.assertFalse(any(x.startswith("control/") for x in selected))

if __name__=="__main__":
    unittest.main()

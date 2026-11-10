"""R64: original Model Builder role carries the recovered opt-in installer.

Runs actual isolated CLIs after original role staging, never a native agent.
"""
from __future__ import annotations
import hashlib,json,subprocess,sys,tempfile,unittest,zipfile
from pathlib import Path
from muse_presets.model_builder_dropin import stage_model_builder_dropin,inspect_model_builder_dropin
from muse_presets.model_builder_sourcekit import export_model_builder_sourcekit,verify_model_builder_sourcekit

class InstallerRoleIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="r64-optin-role-")
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve()
        self.role=self.root/"model-builder"
        self.assertEqual(stage_model_builder_dropin(self.role)["status"],"SOURCE_ONLY_MODEL_BUILDER_STAGED")

    def test_original_role_carries_pinned_installer_and_sourcekit(self):
        receipt=json.loads((self.role/"receipts/MODEL_BUILDER_RECEIPT.json").read_bytes())
        for name in ("model_toy_install.py","model_toy_sourcekit.py"):
            path=self.role/"runtime"/name
            self.assertTrue(path.is_file(),"Original role lacks recovered R61 "+name)
            self.assertEqual(receipt["files_sha256"]["runtime/"+name],hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertEqual(inspect_model_builder_dropin(self.role)["status"],"LOCAL_MODEL_BUILDER_MATCH")
        self.assertFalse(receipt["native_installed"])

    def test_staged_role_installer_refuses_without_optin_and_does_not_train(self):
        cli=self.role/"runtime/model_toy_install.py"
        self.assertTrue(cli.is_file(),"Original role installer is not integrated")
        dest=self.root/"extension"
        denied=subprocess.run([sys.executable,"-I","-B",str(cli),"stage","--to",str(dest)],capture_output=True,text=True,timeout=25)
        self.assertEqual(denied.returncode,2,denied.stdout+denied.stderr)
        self.assertFalse(dest.exists())
        staged=subprocess.run([sys.executable,"-I","-B",str(cli),"stage","--to",str(dest),"--include-toy-training"],capture_output=True,text=True,timeout=35)
        self.assertEqual(staged.returncode,0,staged.stdout+staged.stderr)
        result=json.loads(staged.stdout)
        self.assertFalse(result["training_started"])
        self.assertFalse(result["native_installed"])
        self.assertFalse((dest/"candidate.json").exists())
        reviewed=subprocess.run([sys.executable,"-I","-B",str(cli),"inspect","--root",str(dest),"--stage-sha256",result["stage_receipt_sha256"]],capture_output=True,text=True,timeout=30)
        self.assertEqual(reviewed.returncode,0,reviewed.stdout+reviewed.stderr)
        self.assertEqual(json.loads(reviewed.stdout)["status"],"LOCAL_TOY_EXTENSION_STAGE_MATCH")
        repeat=subprocess.run([sys.executable,"-I","-B",str(cli),"stage","--to",str(dest),"--include-toy-training"],capture_output=True,text=True,timeout=25)
        self.assertEqual(repeat.returncode,2)
        self.assertEqual(inspect_model_builder_dropin(self.role)["status"],"LOCAL_MODEL_BUILDER_MATCH")

    def test_complete_download_contains_functional_installer(self):
        archive=self.root/"model-builder.zip"
        report=export_model_builder_sourcekit(self.role,archive)
        self.assertEqual(verify_model_builder_sourcekit(archive,report["sha256"])["status"],"LOCAL_MODEL_SOURCEKIT_VERIFIED")
        fresh=self.root/"extracted";fresh.mkdir()
        with zipfile.ZipFile(archive) as z:
            self.assertIn("model-builder/runtime/model_toy_install.py",z.namelist(),"Full ZIP missing source installer")
            self.assertIn("model-builder/runtime/model_toy_sourcekit.py",z.namelist())
            z.extractall(fresh)
        cli=fresh/"model-builder/runtime/model_toy_install.py"
        dest=self.root/"fresh-extension"
        p=subprocess.run([sys.executable,"-I","-B",str(cli),"stage","--to",str(dest),"--include-toy-training"],cwd=fresh,capture_output=True,text=True,timeout=35)
        self.assertEqual(p.returncode,0,p.stdout+p.stderr)
        info=json.loads(p.stdout)
        self.assertEqual(info["status"],"SOURCE_ONLY_TOY_EXTENSION_STAGED")
        self.assertFalse(info["training_started"])
        verifier=dest/"runtime/model_toy_install.py"
        checked=subprocess.run([sys.executable,"-I","-B",str(verifier),"inspect","--root",str(dest),"--stage-sha256",info["stage_receipt_sha256"]],cwd=fresh,capture_output=True,text=True,timeout=35)
        self.assertEqual(checked.returncode,0,checked.stdout+checked.stderr)
        self.assertEqual(json.loads(checked.stdout)["status"],"LOCAL_TOY_EXTENSION_STAGE_MATCH")

if __name__=="__main__":unittest.main()

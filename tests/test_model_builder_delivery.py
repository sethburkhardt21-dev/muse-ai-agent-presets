"""Real CLI and generic role acceptance for bounded Model Builder training."""
from __future__ import annotations
import hashlib,json,os,subprocess,sys,tempfile,unittest,zipfile
from pathlib import Path
from examples import verify_role_packages

ROOT=Path(__file__).resolve().parents[1]

class ModelBuilderDeliveryTests(unittest.TestCase):
    def test_role_acceptance_actually_runs_toy_training_inference_and_recovery(self):
        result=verify_role_packages.verify_one(ROOT,"model-builder")
        self.assertTrue(result.get("toy_training_executed"),result)
        self.assertTrue(result.get("checkpoint_inference_executed"),result)
        self.assertTrue(result.get("baseline_recovery_tested"),result)
        self.assertEqual(result.get("toy_model_family"),"binary-integer-perceptron")
        self.assertFalse(result["native_installed"])
        self.assertFalse(result["external_effects_authorized"])

    def test_export_cli_works_without_importing_repository_examples_in_runtime(self):
        with tempfile.TemporaryDirectory(prefix="model-cli-delivery-") as temp:
            target=Path(temp)/"model-builder.zip"
            script=ROOT/"examples/export_model_builder_sourcekit.py"
            env=dict(os.environ,PYTHONPATH=str(ROOT/"src"),PYTHONDONTWRITEBYTECODE="1")
            p=subprocess.run([sys.executable,"-B",str(script),"--to",str(target)],
                             cwd=ROOT,env=env,capture_output=True,text=True,timeout=45)
            self.assertEqual(p.returncode,0,p.stdout+p.stderr)
            r=json.loads(p.stdout)
            self.assertEqual(r["status"],"LOCAL_MODEL_SOURCEKIT_EXPORTED")
            self.assertEqual(r["sha256"],hashlib.sha256(target.read_bytes()).hexdigest())
            before=target.read_bytes()
            repeated=subprocess.run([sys.executable,"-B",str(script),"--to",str(target)],
                             cwd=ROOT,env=env,capture_output=True,text=True,timeout=45)
            self.assertEqual(repeated.returncode,2)
            self.assertEqual(json.loads(repeated.stdout)["status"],"REFUSED")
            self.assertEqual(target.read_bytes(),before)

if __name__=="__main__":unittest.main()

"""R61 actual staged toy training/inference, preserving original source-only APIs."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from muse_presets.model_builder_dropin import stage_model_builder_dropin, inspect_model_builder_dropin


def case():
    rows=[]
    for sid,group,split,x,y in (
        ("train-a","a","train",[-1,0],0),("train-b","b","train",[1,0],1),
        ("dev-a","c","dev",[-1,-1],0),("dev-b","d","dev",[1,1],1),
        ("final-a","e","final",None,None)):
        rows.append({"sample_id":sid,"family_id":"group-"+group,"split":split,"features":x,"label":y})
    return {"schema":"r61/toy-perceptron-experiment-v1","experiment_id":"cli-case",
            "feature_count":2,"epochs":3,"rows":rows}


class ToyModelDropinTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix="toy-dropin-")
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.pack=self.root/"pack"
        stage_model_builder_dropin(self.pack)
        self.runner=self.pack/"custom-skills/model_development_metrics/run.py"

    def run_cli(self,operation,doc=None,allow=False):
        command=[sys.executable,"-I","-B",str(self.runner),"--operation",operation]
        if allow:command.append("--allow-local-training")
        p=subprocess.run(command,input=json.dumps(doc) if doc is not None else None,
                         capture_output=True,text=True,timeout=30)
        try:result=json.loads(p.stdout)
        except ValueError:result={"raw_stdout":p.stdout,"stderr":p.stderr}
        return p.returncode,result

    def test_staged_runtime_has_both_original_scoring_and_real_training_sources(self):
        self.assertTrue((self.pack/"runtime/model_eval.py").is_file())
        self.assertTrue((self.pack/"runtime/toy_model.py").is_file())
        self.assertEqual(inspect_model_builder_dropin(self.pack)["status"],"LOCAL_MODEL_BUILDER_MATCH")
        receipt=json.loads((self.pack/"receipts/MODEL_BUILDER_RECEIPT.json").read_bytes())
        self.assertEqual(receipt["files_sha256"]["runtime/toy_model.py"],
                         hashlib.sha256((self.pack/"runtime/toy_model.py").read_bytes()).hexdigest())
        binding=json.loads((self.pack/"config/host-binding.json").read_bytes())
        self.assertFalse(binding["training_authorized"])
        self.assertFalse(binding["native_authenticated"])

    def test_real_standalone_training_and_checkpoint_replay(self):
        request=case()
        code,result=self.run_cli("toy-train",request,allow=True)
        self.assertEqual(code,0,result)
        self.assertEqual(result["status"],"LOCAL_TOY_TRAIN_EVAL_COMPLETE")
        self.assertTrue(result["trained_this_call"])
        self.assertEqual(result["candidate_correct"],2)
        model=result["checkpoint_utf8"]
        code,observed=self.run_cli("toy-evaluate",{
            "checkpoint_utf8":model,"expected_sha256":result["checkpoint_sha256"],
            "rows":[x for x in request["rows"] if x["split"]=="dev"]})
        self.assertEqual(code,0,observed)
        self.assertEqual(observed["correct"],2)
        self.assertFalse(observed["training_provenance_verified"])
        code,restored=self.run_cli("toy-restore",{
            "candidate_utf8":model,"candidate_sha256":result["checkpoint_sha256"],
            "baseline_utf8":result["baseline_checkpoint_utf8"],
            "baseline_sha256":result["baseline_checkpoint_sha256"]})
        self.assertEqual(code,0,restored)
        self.assertEqual(restored["checkpoint_utf8"],result["baseline_checkpoint_utf8"])
        self.assertFalse(restored["deployment_changed"])

    def test_training_requires_flag_but_original_nontraining_demo_still_works(self):
        code,out=self.run_cli("toy-train",case())
        self.assertEqual(code,2,out)
        self.assertEqual(out.get("status"),"REVIEW_REQUIRED",out)
        code,old=self.run_cli("demo")
        self.assertEqual(code,0,old)
        self.assertEqual(old["status"],"LOCAL_MODEL_BUILDER_DEMO_PASSED")
        self.assertFalse(old["model_trained"])

    def test_new_toy_demo_produces_real_inference_and_checkpoint_readback(self):
        code,out=self.run_cli("toy-demo",allow=True)
        self.assertEqual(code,0,out)
        self.assertEqual(out["status"],"LOCAL_TOY_MODEL_DEMO_PASSED")
        self.assertTrue(out["trained_this_call"])
        self.assertTrue(out["checkpoint_reloaded"])
        self.assertTrue(out["baseline_recovered"])
        self.assertEqual(out["candidate_correct"],4)
        self.assertFalse(out["external_effect_authorized"])
        self.assertFalse(out["native_tool_invoked"])

    def test_runtime_tampering_is_refused_before_toy_import(self):
        target=self.pack/"runtime/toy_model.py"
        self.assertTrue(target.is_file())
        target.write_bytes(target.read_bytes()+b"\n# changed source\n")
        code,out=self.run_cli("toy-train",case(),allow=True)
        self.assertEqual(code,2,out)
        self.assertEqual(out["status"],"REVIEW_REQUIRED")
        self.assertEqual(inspect_model_builder_dropin(self.pack)["status"],"REVIEW_REQUIRED")

    def test_extra_authority_fields_and_protected_final_input_are_refused(self):
        for field,value in (("promotion_authorized",True),("provider_session","fake")):
            request=case();request[field]=value
            code,out=self.run_cli("toy-train",request,allow=True)
            self.assertEqual(code,2,out)
            self.assertEqual(out["status"],"REVIEW_REQUIRED")
        request=case();request["rows"][-1]["label"]=1
        code,out=self.run_cli("toy-train",request,allow=True)
        self.assertEqual(code,2,out)
        self.assertFalse(out["external_effect_authorized"])


if __name__=="__main__":
    unittest.main()

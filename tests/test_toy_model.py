"""Actual bounded toy training/checkpoint inference; no caller predictions or GPUs."""
from __future__ import annotations
import copy
import hashlib
import importlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


def specimen():
    return {
        "schema": "r61/toy-perceptron-experiment-v1",
        "experiment_id": "inclusive-demo", "feature_count": 2, "epochs": 4,
        "rows": [
            {"sample_id":"train-a","family_id":"family-a","split":"train","features":[-1,0],"label":0},
            {"sample_id":"train-b","family_id":"family-b","split":"train","features":[1,0],"label":1},
            {"sample_id":"dev-a","family_id":"family-c","split":"dev","features":[-1,-1],"label":0},
            {"sample_id":"dev-b","family_id":"family-d","split":"dev","features":[1,1],"label":1},
            {"sample_id":"dev-c","family_id":"family-e","split":"dev","features":[-1,1],"label":0},
            {"sample_id":"dev-d","family_id":"family-f","split":"dev","features":[1,-1],"label":1},
            {"sample_id":"final-a","family_id":"family-g","split":"final","features":None,"label":None},
        ],
    }


class ToyModelTests(unittest.TestCase):
    def setUp(self):
        try:
            self.engine=importlib.import_module("muse_presets.toy_model")
        except ModuleNotFoundError:
            self.fail("Missing executable toy-model engine: current role only scores supplied predictions")
        self.case=specimen()

    def run_case(self,case=None):
        return self.engine.run_toy_experiment(case or self.case,allow_training=True)

    def dev(self,case=None):
        return [r for r in (case or self.case)["rows"] if r["split"]=="dev"]

    def assert_refused(self,result):
        self.assertEqual(result["status"],"REVIEW_REQUIRED",result)
        self.assertFalse(result["promotion_authorized"])
        self.assertFalse(result["external_effect_authorized"])

    def test_real_optimizer_updates_and_checkpoint_inference_replace_supplied_predictions(self):
        before=copy.deepcopy(self.case)
        r=self.run_case()
        self.assertEqual(r["status"],"LOCAL_TOY_TRAIN_EVAL_COMPLETE")
        self.assertTrue(r["trained_this_call"])
        self.assertTrue(r["inference_executed"])
        self.assertEqual(r["training_steps"],8)
        self.assertGreater(r["update_count"],0)
        self.assertEqual(r["dev_n"],4)
        self.assertEqual(r["candidate_correct"],4)
        self.assertEqual(r["baseline_correct"],2)
        self.assertEqual(r["final_status"],"HELD_UNEVALUATED")
        self.assertEqual(r["selected_checkpoint_sha256"],r["checkpoint_sha256"])
        self.assertEqual(self.case,before)
        self.assertFalse(r["promotion_authorized"])
        self.assertFalse(r["independent_examiner_verified"])
        self.assertFalse(r["external_effect_authorized"])

    def test_explicit_opt_in_required_including_truthy_non_boolean_refusal(self):
        for consent in (False,None,1,"yes",[],{}):
            with self.subTest(consent=consent):
                self.assert_refused(self.engine.run_toy_experiment(self.case,allow_training=consent))

    def test_checkpoint_bytes_reload_reproduce_identical_predictions(self):
        r=self.run_case()
        payload=r["checkpoint_utf8"].encode("utf-8")
        self.assertEqual(hashlib.sha256(payload).hexdigest(),r["checkpoint_sha256"])
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"candidate.json"
            p.write_bytes(payload)
            scored=self.engine.score_toy_checkpoint(p.read_bytes(),r["checkpoint_sha256"],self.dev())
        self.assertEqual(scored["status"],"LOCAL_TOY_CHECKPOINT_EVALUATED")
        self.assertEqual(scored["correct"],4)
        self.assertEqual([v["prediction"] for v in scored["predictions"]],[0,1,0,1])
        self.assertFalse(scored["training_provenance_verified"])
        self.assertFalse(scored["trained_this_call"])

    def test_deterministic_checkpoints_and_source_input_not_mutated(self):
        first=self.run_case()
        second=self.run_case()
        self.assertEqual(first,second)
        reordered=copy.deepcopy(self.case)
        reordered["rows"]=list(reversed(reordered["rows"]))
        third=self.run_case(reordered)
        self.assertEqual(first["checkpoint_utf8"],third["checkpoint_utf8"])

    def test_degraded_candidate_retains_baseline_and_exact_baseline_rollback(self):
        self.case["rows"][3]["label"]=0
        self.case["rows"][5]["label"]=0
        r=self.run_case()
        self.assertEqual(r["candidate_correct"],2)
        self.assertEqual(r["baseline_correct"],4)
        self.assertEqual(r["selected_checkpoint_sha256"],r["baseline_checkpoint_sha256"])
        self.assertEqual(r["selection_reason"],"KEEP_BASELINE_NO_DEV_IMPROVEMENT")
        rollback=self.engine.restore_toy_baseline(
            r["checkpoint_utf8"].encode(),r["checkpoint_sha256"],
            r["baseline_checkpoint_utf8"].encode(),r["baseline_checkpoint_sha256"])
        self.assertEqual(rollback["status"],"LOCAL_BASELINE_BYTES_RECOVERED")
        self.assertEqual(rollback["checkpoint_utf8"],r["baseline_checkpoint_utf8"])
        self.assertFalse(rollback["deployment_changed"])

    def test_corrupted_candidate_or_baseline_cannot_pass_rollback(self):
        r=self.run_case()
        for which in (0,2):
            args=[r["checkpoint_utf8"].encode(),r["checkpoint_sha256"],
                  r["baseline_checkpoint_utf8"].encode(),r["baseline_checkpoint_sha256"]]
            args[which]+=b" "
            self.assert_refused(self.engine.restore_toy_baseline(*args))

    def test_checkpoint_pin_drift_and_non_json_executable_serialization_refused(self):
        r=self.run_case()
        original=r["checkpoint_utf8"].encode()
        self.assert_refused(self.engine.score_toy_checkpoint(original,"0"*64,self.dev()))
        for b in (b"\x80\x04pickle",b"__import__('os')",b"{}",original+b"x"):
            self.assert_refused(self.engine.score_toy_checkpoint(b,hashlib.sha256(b).hexdigest(),self.dev()))

    def test_duplicate_json_keys_and_nonfinite_checkpoints_refused(self):
        r=self.run_case()
        raw=r["checkpoint_utf8"]
        duplicate=raw.replace('"bias":', '"bias":0,"bias":',1).encode()
        self.assert_refused(self.engine.score_toy_checkpoint(duplicate,hashlib.sha256(duplicate).hexdigest(),self.dev()))
        for value in (float("nan"),float("inf"),True,1.5,"1"):
            c=json.loads(raw);c["weights"][0]=value
            b=json.dumps(c).encode()
            self.assert_refused(self.engine.score_toy_checkpoint(b,hashlib.sha256(b).hexdigest(),self.dev()))

    def test_checkpoint_cannot_claim_native_training_or_promotion_authority(self):
        r=self.run_case()
        for key in ("native_authenticated","promotion_authorized","remote_training_proven"):
            c=json.loads(r["checkpoint_utf8"]);c[key]=True
            b=json.dumps(c).encode()
            self.assert_refused(self.engine.score_toy_checkpoint(b,hashlib.sha256(b).hexdigest(),self.dev()))

    def test_training_limits_refuse_excessive_epochs_rows_dimensions_and_coefficients(self):
        for key,val in (("epochs",0),("epochs",33),("epochs",True),
                        ("feature_count",0),("feature_count",9),("feature_count",True)):
            c=copy.deepcopy(self.case);c[key]=val
            self.assert_refused(self.run_case(c))
        c=copy.deepcopy(self.case);c["rows"]*=20
        self.assert_refused(self.run_case(c))
        r=self.run_case();doc=json.loads(r["checkpoint_utf8"]);doc["weights"][0]=10**100
        b=json.dumps(doc).encode()
        self.assert_refused(self.engine.score_toy_checkpoint(b,hashlib.sha256(b).hexdigest(),self.dev()))

    def test_invalid_feature_types_and_dimension_mismatch_are_refused(self):
        for features in ([True,0],[1.0,0],[2,0],[float("nan"),0],[0],None,"xx"):
            c=copy.deepcopy(self.case);c["rows"][0]["features"]=features
            self.assert_refused(self.run_case(c))

    def test_train_dev_family_overlap_duplicate_ids_and_content_leakage_refused(self):
        c=copy.deepcopy(self.case);c["rows"][2]["family_id"]="family-a"
        self.assert_refused(self.run_case(c))
        c=copy.deepcopy(self.case);c["rows"][2]["sample_id"]="train-a"
        self.assert_refused(self.run_case(c))
        c=copy.deepcopy(self.case);c["rows"][2]["features"]=[-1,0]
        self.assert_refused(self.run_case(c))

    def test_protected_final_labels_and_features_never_accepted_or_evaluated(self):
        for field,val in (("label",0),("features",[0,0])):
            c=copy.deepcopy(self.case);c["rows"][-1][field]=val
            self.assert_refused(self.run_case(c))
        r=self.run_case()
        self.assert_refused(self.engine.score_toy_checkpoint(
            r["checkpoint_utf8"].encode(),r["checkpoint_sha256"],self.case["rows"]))

    def test_missing_partitions_single_training_class_and_extra_predictions_refused(self):
        for split in ("train","dev","final"):
            c=copy.deepcopy(self.case);c["rows"]=[x for x in c["rows"] if x["split"]!=split]
            self.assert_refused(self.run_case(c))
        c=copy.deepcopy(self.case);c["rows"][0]["label"]=1
        self.assert_refused(self.run_case(c))
        c=copy.deepcopy(self.case);c["rows"][2]["candidate"]=1
        self.assert_refused(self.run_case(c))

    def test_invalid_labels_untrusted_identifiers_and_oversized_json_are_refused(self):
        for val in (True,2,-1,"0",None):
            c=copy.deepcopy(self.case);c["rows"][0]["label"]=val
            self.assert_refused(self.run_case(c))
        c=copy.deepcopy(self.case);c["experiment_id"]="../private"
        self.assert_refused(self.run_case(c))
        r=self.run_case();b=b" "*16385
        self.assert_refused(self.engine.score_toy_checkpoint(b,hashlib.sha256(b).hexdigest(),self.dev()))

    def test_training_result_reports_bounded_actual_work_and_no_external_grant(self):
        r=self.run_case()
        self.assertEqual(r["model_type"],"binary-integer-perceptron")
        self.assertEqual(r["train_n"],2)
        self.assertEqual(r["final_n"],1)
        self.assertEqual(len(r["epoch_mistakes"]),4)
        self.assertEqual(sum(r["epoch_mistakes"]),r["update_count"])
        self.assertFalse(r["gpu_used"])
        self.assertFalse(r["network_used"])
        self.assertFalse(r["native_tool_invoked"])
        self.assertFalse(r["training_provenance_verified"])

    def test_reloaded_checkpoint_rejects_training_family_and_feature_reuse_as_dev(self):
        r=self.run_case()
        leaked=copy.deepcopy(self.case["rows"][0]);leaked["split"]="dev"
        self.assert_refused(self.engine.score_toy_checkpoint(
            r["checkpoint_utf8"].encode(),r["checkpoint_sha256"],[leaked]))
        leaked["family_id"]="different-family";leaked["sample_id"]="different-id"
        self.assert_refused(self.engine.score_toy_checkpoint(
            r["checkpoint_utf8"].encode(),r["checkpoint_sha256"],[leaked]))

    def test_nonseparable_dataset_terminates_at_exact_admitted_work_budget(self):
        c=specimen();c["epochs"]=32
        c["rows"]=[]
        for index,(features,label) in enumerate((([-1,-1],0),([-1,1],1),([1,-1],1),([1,1],0))):
            c["rows"].append({"sample_id":"train-"+str(index),"family_id":"family-"+str(index),
                              "split":"train","features":features,"label":label})
        c["rows"].append({"sample_id":"dev-new","family_id":"dev-family","split":"dev","features":[0,0],"label":0})
        c["rows"].append({"sample_id":"final-hidden","family_id":"final-family","split":"final","features":None,"label":None})
        r=self.run_case(c)
        self.assertEqual(r["status"],"LOCAL_TOY_TRAIN_EVAL_COMPLETE")
        self.assertEqual(r["training_steps"],128)
        self.assertLessEqual(r["update_count"],128)
        self.assertEqual(len(r["epoch_mistakes"]),32)
        self.assertFalse(r["promotion_authorized"])


if __name__=="__main__":
    unittest.main()

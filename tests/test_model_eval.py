"""R33 Model Builder: actual bounded dev metrics and byte-checkpoint verification."""
import copy
import hashlib
import math
import unittest

from muse_presets.model_eval import evaluate_development, verify_checkpoint_bytes


def sample():
    return {
        "schema": "r33/model-builder-development-v1",
        "model_source_sha256": "a" * 64,
        "dataset_source_sha256": "b" * 64,
        "rights_status": "UNVERIFIED",
        "rows": [
            {"sample_id":"train-1","family_id":"group-a","split":"train",
             "label":1,"baseline":None,"candidate":None},
            {"sample_id":"train-2","family_id":"group-a","split":"train",
             "label":0,"baseline":None,"candidate":None},
            {"sample_id":"dev-1","family_id":"group-b","split":"dev",
             "label":1,"baseline":0,"candidate":1},
            {"sample_id":"dev-2","family_id":"group-c","split":"dev",
             "label":0,"baseline":0,"candidate":0},
            {"sample_id":"final-1","family_id":"group-d","split":"final",
             "label":None,"baseline":None,"candidate":None}
        ],
    }


def checkpoint(payload=b"synthetic-candidate-weights"):
    return {
        "schema":"r33/model-builder-checkpoint-v1",
        "artifact_kind":"synthetic-checkpoint-bytes",
        "artifact_sha256":hashlib.sha256(payload).hexdigest(),
        "parent_model_sha256":"a"*64,
        "dataset_source_sha256":"b"*64,
        "optimizer_steps":0,
        "weights_trained":False,
        "rights_status":"UNVERIFIED",
    }


class DevelopmentEvaluationTests(unittest.TestCase):
    def test_real_dev_accuracy_computed_from_rows_with_frozen_final(self):
        doc=sample()
        copy_before=copy.deepcopy(doc)
        report=evaluate_development(doc)
        self.assertEqual(report["status"],"LOCAL_DEV_METRICS_ONLY")
        self.assertEqual(report["dev_n"],2)
        self.assertEqual(report["baseline_correct"],1)
        self.assertEqual(report["candidate_correct"],2)
        self.assertEqual(report["baseline_accuracy"],0.5)
        self.assertEqual(report["candidate_accuracy"],1.0)
        self.assertEqual(report["delta_accuracy"],0.5)
        self.assertEqual(report["final_status"],"HELD_UNEVALUATED")
        self.assertEqual(report["rights_status"],"UNVERIFIED")
        self.assertFalse(report["trained"])
        self.assertFalse(report["native_tool_invoked"])
        self.assertFalse(report["external_effect_authorized"])
        self.assertEqual(doc,copy_before)

    def test_cross_partition_family_contamination_refused(self):
        doc=sample()
        doc["rows"][2]["family_id"]="group-a"
        self.assertEqual(evaluate_development(doc)["status"],"REVIEW_REQUIRED")

    def test_duplicate_ids_and_missing_splits_refused(self):
        doc=sample()
        doc["rows"][2]["sample_id"]="train-1"
        self.assertEqual(evaluate_development(doc)["status"],"REVIEW_REQUIRED")
        doc=sample()
        doc["rows"]=[r for r in doc["rows"] if r["split"]!="final"]
        self.assertEqual(evaluate_development(doc)["status"],"REVIEW_REQUIRED")

    def test_final_labels_or_predictions_cannot_be_revealed(self):
        for key,value in (("label",1),("candidate",1),("baseline",0)):
            doc=sample()
            doc["rows"][-1][key]=value
            with self.subTest(key=key):
                self.assertEqual(evaluate_development(doc)["status"],"REVIEW_REQUIRED")

    def test_forged_train_evidence_and_grants_refused(self):
        doc=sample()
        doc["trained"]=True
        self.assertEqual(evaluate_development(doc)["status"],"REVIEW_REQUIRED")
        doc=sample()
        doc["rights_status"]="CLEARED"
        self.assertEqual(evaluate_development(doc)["status"],"REVIEW_REQUIRED")

    def test_invalid_types_and_unbounded_input_refused(self):
        for field,value in (("label",True),("candidate",2),
                            ("candidate",float("nan")),("candidate","1")):
            doc=sample()
            doc["rows"][2][field]=value
            self.assertEqual(evaluate_development(doc)["status"],"REVIEW_REQUIRED")
        doc=sample()
        doc["rows"]=doc["rows"]*16
        self.assertEqual(evaluate_development(doc)["status"],"REVIEW_REQUIRED")

    def test_extra_fields_and_malformed_sha_refused(self):
        doc=sample()
        doc["rows"][0]["grant"]="owner"
        self.assertEqual(evaluate_development(doc)["status"],"REVIEW_REQUIRED")
        doc=sample()
        doc["model_source_sha256"]="short"
        self.assertEqual(evaluate_development(doc)["status"],"REVIEW_REQUIRED")

    def test_arithmetic_is_deterministic_even_when_candidate_worse(self):
        doc=sample()
        doc["rows"][2]["candidate"]=0
        doc["rows"][3]["candidate"]=1
        report=evaluate_development(doc)
        self.assertEqual(report["status"],"LOCAL_DEV_METRICS_ONLY")
        self.assertEqual(report["delta_accuracy"],-0.5)
        self.assertFalse(report["promotion_authorized"])


class CheckpointVerificationTests(unittest.TestCase):
    def test_real_bytes_are_hashed_and_matched(self):
        raw=b"synthetic-candidate-weights"
        report=verify_checkpoint_bytes(checkpoint(raw),raw)
        self.assertEqual(report["status"],"LOCAL_CHECKPOINT_DIGEST_MATCH")
        self.assertEqual(report["observed_sha256"],hashlib.sha256(raw).hexdigest())
        self.assertEqual(report["artifact_bytes"],len(raw))
        self.assertFalse(report["trained"])
        self.assertFalse(report["weights_proven"])
        self.assertFalse(report["promotion_authorized"])

    def test_checkpoint_bytes_tampering_refused(self):
        self.assertEqual(verify_checkpoint_bytes(checkpoint(),b"altered")["status"],"REVIEW_REQUIRED")

    def test_fake_optimizer_steps_or_weights_refused(self):
        for key,value in (("optimizer_steps",5),("weights_trained",True),
                          ("rights_status","CLEARED")):
            meta=checkpoint()
            meta[key]=value
            with self.subTest(key=key):
                self.assertEqual(verify_checkpoint_bytes(meta,b"synthetic-candidate-weights")["status"],"REVIEW_REQUIRED")

    def test_missing_payload_wrong_type_or_fake_grant_refused(self):
        self.assertEqual(verify_checkpoint_bytes(checkpoint(),b"")["status"],"REVIEW_REQUIRED")
        self.assertEqual(verify_checkpoint_bytes(checkpoint(),{"raw":"byte"})["status"],"REVIEW_REQUIRED")
        self.assertEqual(verify_checkpoint_bytes(checkpoint(),b"X"*4097)["status"],"REVIEW_REQUIRED")
        meta=checkpoint()
        meta["host_authenticated"]=True
        self.assertEqual(verify_checkpoint_bytes(meta,b"synthetic-candidate-weights")["status"],"REVIEW_REQUIRED")


if __name__=="__main__":
    unittest.main()

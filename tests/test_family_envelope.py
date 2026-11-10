"""T13 local-only Family Link envelope/consent/replay-shape fixture tests."""
from __future__ import annotations

import copy
from datetime import datetime,timedelta,timezone
import hashlib
import importlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

NOW=datetime(2026,11,9,18,0,0,tzinfo=timezone.utc)
OPEN="2026-11-09T17:59:00Z"
CLOSE="2026-11-09T18:30:00Z"


def mod():
    return importlib.import_module("muse_presets.family_envelope")


def finding():
    text="Fictional source-only observation: green sprouts appear.\n"
    return {"source_uri":"fictional-example.txt",
            "source_sha256":hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "observation":text,"result":"FOUND"}


def build(**overrides):
    fields={
       "sender_role":"model-builder",
       "receiver_role":"research-evaluator",
       "request_id":"fixture-13",
       "capability":"finding-review",
       "finding":finding(),
       "declared_consent":True,
       "valid_from_utc":OPEN,
       "valid_until_utc":CLOSE,
       "now_utc":NOW,
    }
    fields.update(overrides)
    return mod().prepare_offline_envelope(**fields)


class FamilyOfflineEnvelopeTests(unittest.TestCase):
    def review(self,*args,**kwargs):
        return mod().review_local_envelope(*args,expected_receiver_role="research-evaluator",**kwargs)

    def test_missing_production_module_is_a_real_red_gate(self):
        self.assertIsNotNone(importlib.util.find_spec("muse_presets.family_envelope"))

    def test_prepared_envelope_is_bounded_source_only_and_closed(self):
        f=finding()
        out=build()
        self.assertEqual(out["schema"],"r66/family-offline-envelope-v1")
        self.assertEqual(out["state"],"PROPOSAL_ONLY_NOT_SENT")
        self.assertEqual(out["sender_role"],"model-builder")
        self.assertEqual(out["receiver_role"],"research-evaluator")
        self.assertEqual(out["request_id"],"fixture-13")
        self.assertEqual(out["requested_capability"],"finding-review")
        self.assertTrue(out["caller_declared_consent"])
        self.assertEqual(out["finding_sha256"],mod().finding_sha256(f))
        self.assertNotIn(f["observation"],json.dumps(out))
        for key in ("native_receipt","recipient_acknowledged","effect_authorized",
                    "sender_authenticated","recipient_authenticated",
                    "consent_authenticated","replay_history_authenticated"):
            self.assertIs(out[key],False,key)
        self.assertEqual(out,build())

    def test_review_accepts_untrusted_local_shape_without_grant(self):
        out=build()
        observed=self.review(
            envelope=out,finding=finding(),
            expected_envelope_sha256=mod().envelope_sha256(out),
            seen_request_ids=[],revoked_request_ids=[],now_utc=NOW)
        self.assertEqual(observed["status"],"LOCAL_HANDOFF_REVIEW_ONLY_NOT_DELIVERED")
        self.assertEqual(observed["request_id"],"fixture-13")
        self.assertFalse(observed["recipient_acknowledged"])
        self.assertFalse(observed["effect_authorized"])
        self.assertFalse(observed["replay_history_authenticated"])
        self.assertFalse(observed["consent_authenticated"])

    def test_declared_consent_is_required_but_not_authenticated(self):
        for bad in (False,None,1,"yes",{},[]):
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                build(declared_consent=bad)
        self.assertFalse(build()["consent_authenticated"])

    def test_wrong_receiver_self_handoff_or_unknown_sender_denied(self):
        for changed in ({"receiver_role":"coordinator"},
                        {"receiver_role":"model-builder"},
                        {"sender_role":"private-agent"},
                        {"capability":"not a bounded capability"}):
            with self.subTest(changed=changed),self.assertRaises(ValueError):
                build(**changed)

    def test_replay_is_refused_with_supplied_history_but_history_not_trusted(self):
        e=build();digest=mod().envelope_sha256(e)
        with self.assertRaisesRegex(ValueError,"REPLAY"):
            self.review(
                e,finding(),digest,seen_request_ids=["fixture-13"],
                revoked_request_ids=[],now_utc=NOW)
        clean=self.review(
            e,finding(),digest,seen_request_ids=[],
            revoked_request_ids=[],now_utc=NOW)
        self.assertFalse(clean["replay_history_authenticated"])

    def test_explicit_revocation_is_refused_without_claiming_external_revocation(self):
        e=build();digest=mod().envelope_sha256(e)
        with self.assertRaisesRegex(ValueError,"REVOKED"):
            self.review(e,finding(),digest,
                seen_request_ids=[],revoked_request_ids=["fixture-13"],now_utc=NOW)

    def test_malformed_role_and_request_types_fail_as_value_error(self):
        for changed in (
            {"sender_role":[]},
            {"sender_role":{"role":"model-builder"}},
            {"receiver_role":[]},
            {"receiver_role":{"role":"research-evaluator"}},
            {"request_id":[]},
            {"capability":{"intent":"finding-review"}},
        ):
            with self.subTest(changed=str(changed)),self.assertRaises(ValueError):
                build(**changed)
        e=build()
        e["sender_role"]=[]
        with self.assertRaises(ValueError):
            self.review(e,finding(),mod().envelope_sha256(e),[],[],NOW)

    def test_time_window_bounded_and_expiry_refused(self):
        for from_utc,to_utc in (
            ("2026-11-09T18:10:00Z","2026-11-09T19:00:00Z"),
            ("2026-11-09T17:00:00Z","2026-11-09T17:01:00Z"),
            ("2026-11-09T17:00:00Z","2026-11-09T19:00:01Z"),
            ("not-time",CLOSE),("2026-11-09T18:00:00Z","2026-11-09T18:00:00Z")):
            with self.subTest(start=from_utc,end=to_utc),self.assertRaises(ValueError):
                build(valid_from_utc=from_utc,valid_until_utc=to_utc)
        e=build()
        with self.assertRaises(ValueError):
            self.review(e,finding(),mod().envelope_sha256(e),
                [],[],NOW+timedelta(hours=1))

    def test_modified_finding_and_wrong_out_of_band_sha_refused(self):
        e=build();digest=mod().envelope_sha256(e)
        mutated=finding();mutated["observation"]="Changed content"
        with self.assertRaises(ValueError):
            self.review(e,mutated,digest,[],[],NOW)
        with self.assertRaisesRegex(ValueError,"PIN"):
            self.review(e,finding(),"f"*64,[],[],NOW)

    def test_rehashed_forged_grants_remain_refused(self):
        for key,value in (
            ("recipient_acknowledged",True),("effect_authorized",True),
            ("consent_authenticated",True),("sender_authenticated",True),
            ("replay_history_authenticated",True),("state","SENT"),
            ("receiver_role","claims-adjudicator")):
            e=build();e[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):
                self.review(e,finding(),mod().envelope_sha256(e),
                   [],[],NOW)
        e=build();e["host_grant"]="claimed"
        with self.assertRaises(ValueError):
            self.review(e,finding(),mod().envelope_sha256(e),
                [],[],NOW)

    def test_missing_or_malformed_caller_supplied_history_refused(self):
        e=build();digest=mod().envelope_sha256(e)
        for seen in (None,["fixture-1","fixture-1"],["bad request"],"fixture-13",
                     ["x"]*257):
            with self.subTest(seen=repr(seen)[:30]),self.assertRaises(ValueError):
                self.review(e,finding(),digest,seen,[],NOW)
        for revoked in (None,["fixture-2","fixture-2"],[42]):
            with self.subTest(revoked=revoked),self.assertRaises(ValueError):
                self.review(e,finding(),digest,[],revoked,NOW)

    def test_observation_or_uri_or_found_digest_changed_refused(self):
        for changes in (
            {"source_uri":"../private"},
            {"source_uri":"source\nprivate"},
            {"observation":"x"*50000},
            {"source_sha256":"0"*64},
            {"result":"FOUND","observation":""}):
            f=finding();f.update(changes)
            with self.subTest(changes=changes),self.assertRaises(ValueError):
                build(finding=f)

    def test_envelope_digest_deterministic_json_and_no_dynamic_status(self):
        e=build();digest=mod().envelope_sha256(e)
        raw=json.dumps(e,sort_keys=True,separators=(",",":"),
                       ensure_ascii=True,allow_nan=False).encode()
        self.assertEqual(digest,hashlib.sha256(raw).hexdigest())
        self.assertEqual(digest,mod().envelope_sha256(json.loads(raw)))
        self.assertEqual(len(digest),64)

    def test_actual_two_process_offline_fixture_handoff_and_replay_refusal(self):
        root=Path(__file__).resolve().parents[1]
        env=dict(os.environ,PYTHONPATH=str(root/"src"),PYTHONDONTWRITEBYTECODE="1")
        proc=subprocess.run([sys.executable,"-B",
            str(root/"examples/family_offline_handoff_demo.py")],
            cwd=root,env=env,capture_output=True,text=True,timeout=45)
        self.assertEqual(proc.returncode,0,proc.stderr)
        doc=json.loads(proc.stdout)
        self.assertEqual(doc["status"],"LOCAL_HANDOFF_REVIEW_ONLY_NOT_DELIVERED")
        self.assertTrue(doc["separate_process_verified"])
        self.assertTrue(doc["replayed_id_refused"])
        self.assertFalse(doc["external_effect_authorized"])
        self.assertFalse(doc["recipient_acknowledged"])


if __name__=="__main__":
    unittest.main()

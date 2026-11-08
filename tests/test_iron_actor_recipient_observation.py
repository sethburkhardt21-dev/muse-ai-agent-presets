"""R32.2c read-only host/recipient reconciliation boundary (test-first).

This is an offline schema/identity and anti-staleness contract, NOT real
host auth, a recipient signature, permission to perform an effect or a
replacement for existing Claim Gate. All fixtures are synthetic.
"""
from __future__ import annotations

import hashlib
import json
import unittest
from unittest.mock import Mock

from muse_presets.iron_ledger_consumer import (
    IronLedgerRefused,
    task_run_claim_id,
    review_local_task_observations,
)

DIGEST=hashlib.sha256(b"synthetic bounded task").hexdigest()
SCOPE="software-engineer"
TASK="task-42"
RUN="run-3"
CLAIM_ID=task_run_claim_id(TASK,RUN)
OWNER="test-owner"
ACTOR="test-actor"
SESSION="session-123"
RECIPIENT="sandbox-recipient"


class LocalActorRecipientReviewTests(unittest.TestCase):
    def setUp(self):
        self.local={
            "scope":SCOPE,"claim_id":CLAIM_ID,"payload_digest":DIGEST,
            "state":"EFFECT_DONE","outcome":"SUCCESS",
            "fencing_token":15,"lease_owner":"test-actor",
        }
        self.actor={
            "schema":"software-engineer/local-actor-observation-v1",
            "scope":SCOPE,"owner_id":OWNER,
            "actor_id":ACTOR,"session_id":SESSION,
            "status":"CALLER_SUPPLIED_ASSERTION",
            "host_authenticated":False,
            "effect_authorized":False,
        }
        self.target={
            "schema":"software-engineer/local-recipient-observation-v1",
            "recipient_id":RECIPIENT,"claim_id":CLAIM_ID,
            "payload_sha256":DIGEST,"status":"SUCCESS",
            "recipient_authenticated":False,
            "external_effect_verified":False,
        }
        self.claim_reader=Mock()
        self.claim_reader.reconcile_unknown.return_value=dict(self.local)
        self.claim_reader.claim.side_effect=AssertionError("NO CLAIM EFFECT")
        self.claim_reader.mark_effect.side_effect=AssertionError("NO EFFECT")
        self.claim_reader.mark_unknown.side_effect=AssertionError("NO CLAIM MUTATION")
        self.actor_reader=Mock()
        self.actor_reader.inspect_actor.return_value=dict(self.actor)
        self.recipient_reader=Mock()
        self.recipient_reader.inspect_receipt.return_value=dict(self.target)

    def assess(self,**changes):
        args={
            "scope":SCOPE,"task_id":TASK,"run_id":RUN,
            "expected_payload_sha256":DIGEST,
            "owner_id":OWNER,"actor_id":ACTOR,"session_id":SESSION,
            "recipient_id":RECIPIENT,
        }
        args.update(changes)
        return review_local_task_observations(
            self.claim_reader,self.actor_reader,self.recipient_reader,**args)

    def assert_all_authority_denied(self, observation):
        self.assertTrue(observation["hold_required"])
        for key in ("safe_to_claim","safe_to_retry","safe_to_release",
                    "safe_to_resume","host_owner_authenticated",
                    "recipient_acknowledged","independent_recipient_acknowledged",
                    "external_effect_authorized","external_effect_performed",
                    "native_muse_bound","claim_registry_modified",
                    "source_owner_authenticated","redistribution_rights_verified"):
            with self.subTest(key=key):
                self.assertIs(observation[key],False)
        self.assertEqual(observation["proof_grade"],"LOCAL_ASSERTION_ONLY")

    def test_matching_local_claim_actor_target_report_still_not_authenticated(self):
        result=self.assess()
        self.assertEqual(result["status"],"LOCAL_CONSISTENT_UNAUTHENTICATED_HELD")
        self.assertTrue(result["actor_binding_matches"])
        self.assertTrue(result["recipient_binding_matches"])
        self.assertTrue(result["reported_outcome_consistent"])
        self.assert_all_authority_denied(result)
        self.assertNotIn("test-actor",json.dumps(result))
        self.assertNotIn("sandbox-recipient",json.dumps(result))
        self.assertNotIn("synthetic bounded task",json.dumps(result))
        self.assertEqual(self.claim_reader.reconcile_unknown.call_count,2)
        self.actor_reader.inspect_actor.assert_called_once_with(SCOPE,OWNER,ACTOR,SESSION)
        self.recipient_reader.inspect_receipt.assert_called_once_with(RECIPIENT,CLAIM_ID)
        self.claim_reader.claim.assert_not_called()
        self.claim_reader.mark_effect.assert_not_called()

    def test_missing_or_corrupt_local_claim_never_reads_actor_or_target(self):
        for val in (None,{},{"state":"UNKNOWN"}):
            with self.subTest(local=repr(val)):
                self.setUp()
                self.claim_reader.reconcile_unknown.return_value=val
                out=self.assess()
                self.assertEqual(out["status"],"LOCAL_CLAIM_NOT_ADMITTED_HELD")
                self.assert_all_authority_denied(out)
                self.actor_reader.inspect_actor.assert_not_called()
                self.recipient_reader.inspect_receipt.assert_not_called()

    def test_local_unknown_and_matching_target_report_still_remain_unknown(self):
        self.claim_reader.reconcile_unknown.return_value={**self.local,"state":"UNKNOWN","outcome":None}
        out=self.assess()
        self.assertEqual(out["status"],"LOCAL_UNKNOWN_WITH_TARGET_ASSERTION_HELD")
        self.assertTrue(out["recipient_binding_matches"])
        self.assertFalse(out["reported_outcome_consistent"])
        self.assert_all_authority_denied(out)

    def test_claimed_but_unfinished_never_promoted_to_success(self):
        self.claim_reader.reconcile_unknown.return_value={**self.local,"state":"CLAIMED","outcome":None}
        out=self.assess()
        self.assertEqual(out["status"],"LOCAL_IN_FLIGHT_WITH_TARGET_ASSERTION_HELD")
        self.assert_all_authority_denied(out)

    def test_cancelled_local_claim_not_promoted(self):
        self.claim_reader.reconcile_unknown.return_value={**self.local,"state":"CANCELLED","outcome":None}
        out=self.assess()
        self.assertEqual(out["status"],"LOCAL_CANCELLED_WITH_TARGET_ASSERTION_HELD")
        self.assert_all_authority_denied(out)

    def test_local_outcome_and_recipient_disagree_holds(self):
        self.recipient_reader.inspect_receipt.return_value={**self.target,"status":"FAILED"}
        out=self.assess()
        self.assertEqual(out["status"],"LOCAL_TARGET_OUTCOME_MISMATCH_HELD")
        self.assertFalse(out["reported_outcome_consistent"])
        self.assert_all_authority_denied(out)

    def test_target_missing_or_unknown_holds(self):
        for status in ("NOT_FOUND","UNKNOWN"):
            with self.subTest(status=status):
                self.recipient_reader.inspect_receipt.return_value={**self.target,"status":status}
                out=self.assess()
                self.assertEqual(out["status"],"LOCAL_TARGET_UNRESOLVED_HELD")
                self.assert_all_authority_denied(out)

    def test_actor_binding_mismatch_skips_recipient_read(self):
        for key,value in (("actor_id","other"),("session_id","wrong"),
                          ("scope","research-evaluator"),("owner_id","other")):
            with self.subTest(field=key):
                self.setUp()
                self.actor_reader.inspect_actor.return_value={**self.actor,key:value}
                result=self.assess()
                self.assertEqual(result["status"],"LOCAL_ACTOR_BINDING_MISMATCH_HELD")
                self.assert_all_authority_denied(result)
                self.recipient_reader.inspect_receipt.assert_not_called()

    def test_actor_authentication_or_effect_claim_true_is_untrusted(self):
        for key in ("host_authenticated","effect_authorized"):
            with self.subTest(key=key):
                self.setUp()
                self.actor_reader.inspect_actor.return_value={**self.actor,key:True}
                result=self.assess()
                self.assertEqual(result["status"],"LOCAL_UNTRUSTED_ACTOR_ASSERTION_HELD")
                self.assert_all_authority_denied(result)
                self.recipient_reader.inspect_receipt.assert_not_called()

    def test_target_forged_authentication_claim_true_is_untrusted(self):
        for key in ("recipient_authenticated","external_effect_verified"):
            with self.subTest(key=key):
                self.setUp()
                self.recipient_reader.inspect_receipt.return_value={**self.target,key:True}
                result=self.assess()
                self.assertEqual(result["status"],"LOCAL_UNTRUSTED_TARGET_ASSERTION_HELD")
                self.assert_all_authority_denied(result)

    def test_recipient_binding_mismatch_holds(self):
        for key,value in (("recipient_id","other"),("claim_id","tg_wrong"),
                          ("payload_sha256","f"*64)):
            with self.subTest(field=key):
                self.setUp()
                self.recipient_reader.inspect_receipt.return_value={**self.target,key:value}
                out=self.assess()
                self.assertEqual(out["status"],"LOCAL_TARGET_BINDING_MISMATCH_HELD")
                self.assert_all_authority_denied(out)

    def test_missing_invalid_or_extra_fields_in_responses_hold(self):
        cases=[
            ("actor",{"schema":"nonsense"}),
            ("actor",{**self.actor,"unreviewed":True}),
            ("recipient",{"schema":"nonsense"}),
            ("recipient",{**self.target,"permission_granted":True}),
        ]
        for dest,payload in cases:
            with self.subTest(dest=dest,payload=payload):
                self.setUp()
                if dest=="actor":
                    self.actor_reader.inspect_actor.return_value=payload
                    status="LOCAL_UNTRUSTED_ACTOR_ASSERTION_HELD"
                else:
                    self.recipient_reader.inspect_receipt.return_value=payload
                    status="LOCAL_UNTRUSTED_TARGET_ASSERTION_HELD"
                out=self.assess()
                self.assertEqual(out["status"],status)
                self.assert_all_authority_denied(out)

    def test_host_and_target_reader_exceptions_do_not_leak_private_error(self):
        self.actor_reader.inspect_actor.side_effect=RuntimeError("sensitive /path/from/host")
        result=self.assess()
        self.assertEqual(result["status"],"LOCAL_ACTOR_READ_FAILED_HELD")
        self.assertNotIn("sensitive",json.dumps(result))
        self.setUp()
        self.recipient_reader.inspect_receipt.side_effect=RuntimeError("secret token")
        result=self.assess()
        self.assertEqual(result["status"],"LOCAL_TARGET_READ_FAILED_HELD")
        self.assertNotIn("secret",json.dumps(result))

    def test_claim_changed_during_target_observation_refuses(self):
        self.claim_reader.reconcile_unknown.side_effect=[
            dict(self.local),
            {**self.local,"fencing_token":16},
        ]
        out=self.assess()
        self.assertEqual(out["status"],"LOCAL_CLAIM_CHANGED_DURING_REVIEW_HELD")
        self.assertFalse(out["reported_outcome_consistent"])
        self.assert_all_authority_denied(out)

    def test_unreadable_second_claim_observation_holds(self):
        self.claim_reader.reconcile_unknown.side_effect=[
            dict(self.local),RuntimeError("secret restore location")
        ]
        out=self.assess()
        self.assertEqual(out["status"],"LOCAL_CLAIM_CHANGED_DURING_REVIEW_HELD")
        self.assert_all_authority_denied(out)

    def test_invalid_inputs_refuse_before_any_reader_access(self):
        cases=({"owner_id":"../bad"},{"actor_id":"bad actor"},
               {"session_id":""},{"recipient_id":"../../oops"},
               {"scope":"../bad"},{"run_id":"bad run"},
               {"expected_payload_sha256":"not-a-digest"})
        for override in cases:
            with self.subTest(override=override):
                with self.assertRaises(IronLedgerRefused):
                    self.assess(**override)
        self.claim_reader.reconcile_unknown.assert_not_called()
        self.actor_reader.inspect_actor.assert_not_called()
        self.recipient_reader.inspect_receipt.assert_not_called()

    def test_identical_host_and_recipient_reader_refused_before_lookup(self):
        with self.assertRaisesRegex(IronLedgerRefused,"INDEPENDENCE"):
            review_local_task_observations(
                self.claim_reader,self.actor_reader,self.actor_reader,
                scope=SCOPE,task_id=TASK,run_id=RUN,
                expected_payload_sha256=DIGEST,
                owner_id=OWNER,actor_id=ACTOR,session_id=SESSION,
                recipient_id=RECIPIENT)
        self.claim_reader.reconcile_unknown.assert_not_called()

    def test_claim_attestation_flag_forged_is_held_before_target_lookup(self):
        self.claim_reader.reconcile_unknown.return_value={
            **self.local,"recipient_acknowledged":"true"
        }
        result=self.assess()
        self.assertEqual(result["status"],"LOCAL_CLAIM_NOT_ADMITTED_HELD")
        self.recipient_reader.inspect_receipt.assert_not_called()


if __name__=="__main__":
    unittest.main()

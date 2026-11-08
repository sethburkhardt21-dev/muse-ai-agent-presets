"""R32.2b: fail-closed TaskGuard admission reviews on the existing Claim Gate.

Synthetic-only source fixtures. No original donor claims, task execution,
release() invocation, remote provider effect or second persistent ledger.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import os
import unittest
from unittest.mock import Mock

from muse_presets.iron_ledger_consumer import (
    IronLedgerRefused,
    task_run_claim_id,
    review_local_task_run,
    review_local_task_runs,
)

DIGEST=sha256(b"synthetic task payload").hexdigest()


class LocalTaskGuardRecovery(unittest.TestCase):
    def record(self, task="task-A", run="run-1", state="CLAIMED", **extras):
        return {
            "scope":"software-engineer",
            "claim_id":task_run_claim_id(task,run),
            "state":state,
            "payload_digest":DIGEST,
            **extras,
        }

    def reader(self, record=None, *, error=None):
        obj=Mock()
        if error:
            obj.reconcile_unknown.side_effect=error
        else:
            obj.reconcile_unknown.return_value=record
        obj.claim.side_effect=AssertionError("NO CLAIM WRITES AUTHORIZED")
        obj.release.side_effect=AssertionError("NO RELEASE WRITES AUTHORIZED")
        obj.mark_effect.side_effect=AssertionError("NO EFFECT WRITES AUTHORIZED")
        return obj

    def assess(self, reader, **kwargs):
        return review_local_task_run(
            reader, scope="software-engineer",
            task_id=kwargs.pop("task_id","task-A"),
            run_id=kwargs.pop("run_id","run-1"),
            expected_payload_sha256=kwargs.pop("pin",DIGEST),
            **kwargs,
        )

    def test_claim_id_binds_task_and_run_without_unsafe_names(self):
        a=task_run_claim_id("task-A","run-1")
        b=task_run_claim_id("task-A","run-2")
        c=task_run_claim_id("task-B","run-1")
        self.assertRegex(a,r"^[A-Za-z0-9_-]{1,128}$")
        self.assertNotEqual(a,b)
        self.assertNotEqual(a,c)
        self.assertEqual(a,task_run_claim_id("task-A","run-1"))

    def test_absent_claim_is_unknown_held_not_permission_to_start(self):
        reader=self.reader(None)
        out=self.assess(reader)
        self.assertEqual(out["status"],"LOCAL_UNVERIFIED_ABSENCE_HELD")
        self.assertTrue(out["hold_required"])
        self.assertFalse(out["safe_to_claim"])
        self.assertFalse(out["safe_to_retry"])
        self.assertFalse(out["independent_recipient_acknowledged"])
        reader.reconcile_unknown.assert_called_once_with(
            "software-engineer",task_run_claim_id("task-A","run-1"))
        reader.claim.assert_not_called()
        reader.release.assert_not_called()
        self.assertNotIn("synthetic task payload",json.dumps(out))

    def test_unknown_claim_blocks_all_reexecution(self):
        reader=self.reader(self.record(state="UNKNOWN"))
        out=self.assess(reader)
        self.assertEqual(out["status"],"LOCAL_UNKNOWN_HELD")
        self.assertTrue(out["hold_required"])
        self.assertFalse(out["safe_to_resume"])
        self.assertFalse(out["safe_to_retry"])
        reader.claim.assert_not_called()

    def test_claimed_without_terminal_receipt_remains_held(self):
        reader=self.reader(self.record(state="CLAIMED",fencing_token=4))
        out=self.assess(reader)
        self.assertEqual(out["status"],"LOCAL_IN_FLIGHT_HELD")
        self.assertFalse(out["safe_to_resume"])
        self.assertFalse(out["safe_to_release"])
        self.assertFalse(out["safe_to_retry"])

    def test_terminal_local_effect_not_mistaken_for_external_ack(self):
        reader=self.reader(self.record(state="EFFECT_DONE",outcome="SUCCESS",
                                       receipt={"self_reported":True}))
        out=self.assess(reader)
        self.assertEqual(out["status"],"LOCAL_TERMINAL_UNVERIFIED")
        self.assertFalse(out["safe_to_release"])
        self.assertFalse(out["independent_recipient_acknowledged"])
        self.assertFalse(out["external_effect_performed"])
        self.assertTrue(out["local_terminal_observed"])
        reader.release.assert_not_called()

    def test_cancelled_claim_not_available_for_reclaim(self):
        reader=self.reader(self.record(state="CANCELLED"))
        out=self.assess(reader)
        self.assertEqual(out["status"],"LOCAL_CANCELLED_HELD")
        self.assertFalse(out["safe_to_claim"])
        self.assertFalse(out["safe_to_retry"])

    def test_pruned_claim_remains_held_without_new_identity(self):
        reader=self.reader(self.record(state="EFFECT_DONE",pruned=True))
        out=self.assess(reader)
        self.assertEqual(out["status"],"LOCAL_TERMINAL_UNVERIFIED")
        self.assertTrue(out["hold_required"])
        self.assertFalse(out["safe_to_retry"])

    def test_corrupt_claim_marker_fails_closed(self):
        reader=self.reader(error=ValueError("corrupt synthetic claim marker"))
        out=self.assess(reader)
        self.assertEqual(out["status"],"LOCAL_UNREADABLE_HELD")
        self.assertFalse(out["safe_to_retry"])
        self.assertNotIn("synthetic claim marker",json.dumps(out))

    def test_mismatched_run_identity_fails_closed(self):
        reader=self.reader(self.record(run="run-2",state="EFFECT_DONE"))
        out=self.assess(reader)
        self.assertEqual(out["status"],"LOCAL_IDENTITY_MISMATCH_HELD")
        self.assertFalse(out["local_terminal_observed"])

    def test_mismatched_source_payload_fails_closed(self):
        reader=self.reader(self.record(state="EFFECT_DONE"))
        out=self.assess(reader,pin="f"*64)
        self.assertEqual(out["status"],"LOCAL_PAYLOAD_MISMATCH_HELD")
        self.assertFalse(out["safe_to_retry"])

    def test_forged_or_unknown_claim_state_refuses_release(self):
        for state in ("released","resolved_unknown","READY","SUCCESS","",None):
            with self.subTest(state=state):
                reader=self.reader(self.record(state=state))
                out=self.assess(reader)
                self.assertEqual(out["status"],"LOCAL_UNTRUSTED_RECORD_HELD")
                self.assertFalse(out["safe_to_release"])

    def test_forged_authority_claims_refused(self):
        for key in ("native_muse_bound","source_owner_authenticated",
                    "external_effect_authorized","recipient_acknowledged",
                    "host_authority_authenticated"):
            with self.subTest(flag=key):
                reader=self.reader(self.record(state="EFFECT_DONE",**{key:True}))
                out=self.assess(reader)
                self.assertEqual(out["status"],"LOCAL_UNTRUSTED_RECORD_HELD")
                self.assertFalse(out["independent_recipient_acknowledged"])

    def test_invalid_ids_scope_or_digest_refused_before_reader(self):
        bad=[("", "run-1"),("../task","run-1"),("task-A","../run"),("x"*100,"run-1"),
             ("task-A","run 1"),("task-A","\u0000run")]
        for t,r in bad:
            with self.subTest(t=t,r=r),self.assertRaises(IronLedgerRefused):
                task_run_claim_id(t,r)
        reader=self.reader(None)
        with self.assertRaises(IronLedgerRefused):
            review_local_task_run(reader,scope="../owner",
                task_id="task-A",run_id="run-1",
                expected_payload_sha256=DIGEST)
        with self.assertRaises(IronLedgerRefused):
            self.assess(reader,pin="nope")
        reader.reconcile_unknown.assert_not_called()

    def test_batch_selects_specific_run_and_does_not_duplicate_claims(self):
        class FakeGate:
            calls=[]
            def reconcile_unknown(self,scope,claim_id):
                self.calls.append((scope,claim_id))
                if claim_id==task_run_claim_id("task-A","run-1"):
                    return {
                        "scope":scope,"claim_id":claim_id,"state":"EFFECT_DONE",
                        "payload_digest":DIGEST,
                    }
                return {
                    "scope":scope,"claim_id":claim_id,"state":"UNKNOWN",
                    "payload_digest":DIGEST,
                }
        gate=FakeGate()
        entries=[{"task_id":"task-A","run_id":"run-2","expected_payload_sha256":DIGEST},
                 {"task_id":"task-A","run_id":"run-1","expected_payload_sha256":DIGEST}]
        result=review_local_task_runs(gate,scope="software-engineer",entries=entries)
        self.assertEqual(result["status"],"LOCAL_HOLDS_REQUIRE_REVIEW")
        self.assertEqual(len(gate.calls),2)
        self.assertEqual(len(result["assessments"]),2)
        self.assertFalse(result["claim_registry_modified"])
        self.assertFalse(result["native_muse_bound"])
        with self.assertRaisesRegex(IronLedgerRefused,"DUPLICATE"):
            review_local_task_runs(gate,scope="software-engineer",
                                   entries=[entries[0],entries[0]])

    @unittest.skipUnless(os.name=="posix","POSIX Claim Gate; iMac acceptance")
    def test_actual_staged_claim_gate_receipts_not_modified_by_readonly_guard(self):
        from muse_presets.engineering_pack import stage_engineer_pack,inspect_engineer_pack
        from importlib.util import spec_from_file_location,module_from_spec
        import sys
        with TemporaryDirectory(prefix="guard-integration-") as t:
            root=Path(t).resolve()
            pack=root/"source-pack"
            stage_engineer_pack(pack)
            self.assertEqual(inspect_engineer_pack(pack)["status"],"LOCAL_MATCH")
            module=pack/"runtime/iron-ledger/iron_ledger_consumer.py"
            spec=spec_from_file_location("staged_task_guard_review",module)
            iron=module_from_spec(spec)
            spec.loader.exec_module(iron)
            runtime=pack/"runtime/claim-gate"
            sys.path.insert(0,str(runtime))
            try:
                from claim_gate import ClaimGate
                gate=ClaimGate(str(root/"owned-state"))
                task="task-A"
                run="run-1"
                ident=iron.task_run_claim_id(task,run)
                existing,_=gate.claim("software-engineer",ident,b"synthetic task payload")
                self.assertTrue(existing)
                record=root/"owned-state"/"claims"/"software-engineer"/(ident+".json")
                before=(record.read_bytes(),record.stat().st_mtime_ns)
                out=iron.review_local_task_run(gate,scope="software-engineer",
                    task_id=task,run_id=run,expected_payload_sha256=DIGEST)
                self.assertEqual(out["status"],"LOCAL_IN_FLIGHT_HELD")
                self.assertEqual((record.read_bytes(),record.stat().st_mtime_ns),before)
                gate.mark_unknown("software-engineer",ident,"unconfirmed synthetic")
                out=iron.review_local_task_run(gate,scope="software-engineer",
                    task_id=task,run_id=run,expected_payload_sha256=DIGEST)
                self.assertEqual(out["status"],"LOCAL_UNKNOWN_HELD")
                self.assertFalse(out["safe_to_retry"])
            finally:
                if str(runtime) in sys.path:sys.path.remove(str(runtime))


if __name__=="__main__":
    unittest.main()

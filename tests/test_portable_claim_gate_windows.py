"""R54: native Windows claim/approval/token lock behavior from real source."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

ROOT=Path(__file__).resolve().parents[1]
ENGINE=ROOT/"presets"/"software-engineer"/"runtime"/"claim-gate"
sys.path.insert(0,str(ENGINE))

class PortableLockAcceptance(unittest.TestCase):
    @unittest.skipUnless(os.name=="nt","Windows nonblocking timeout and msvcrt release")
    def test_windows_lock_held_by_other_process_is_exclusive_and_released_on_crash(self):
        from portable_lock import exclusive_lock, PortableLockUnavailable
        with tempfile.TemporaryDirectory(prefix="portable-lock-win-") as tmp:
            lock=Path(tmp)/".lock"
            ready=Path(tmp)/"ready"
            child=(
                "import sys,time,pathlib;"
                f"sys.path.insert(0,{str(ENGINE)!r});"
                "from portable_lock import exclusive_lock;"
                "from pathlib import Path;"
                "p=Path(sys.argv[1]);ready=Path(sys.argv[2])\n"
                "with exclusive_lock(p):\n"
                " ready.write_text('locked',encoding='ascii')\n"
                " time.sleep(15)\n"
            )
            holder=subprocess.Popen([sys.executable,"-B","-c",child,str(lock),str(ready)],
                                    stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True)
            try:
                deadline=time.monotonic()+8
                while not ready.exists() and holder.poll() is None and time.monotonic()<deadline:
                    time.sleep(0.03)
                if not ready.exists():
                    self.fail("lock holder did not start: "+holder.communicate(timeout=1)[1][-500:])
                with self.assertRaises(PortableLockUnavailable):
                    with exclusive_lock(lock,timeout_seconds=0.3):
                        self.fail("contender entered held lock")
            finally:
                if holder.poll() is None:
                    holder.terminate()
                holder.communicate(timeout=5)  # close stderr pipe, even on forced exit
            with exclusive_lock(lock,timeout_seconds=2):
                self.assertTrue(lock.is_file())

    def test_refuse_planted_directory_lock_path(self):
        from portable_lock import exclusive_lock, PortableLockUnavailable
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"lock"
            path.mkdir()
            with self.assertRaises(PortableLockUnavailable):
                with exclusive_lock(path):
                    pass

    def test_real_claim_idempotency_changed_payload_and_unknown_after_restart(self):
        from claim_gate import ClaimGate,ReplayRefused
        with tempfile.TemporaryDirectory(prefix="claim-win-real-") as tmp:
            a=ClaimGate(tmp)
            new,rec=a.claim("engineering","case-1",b"payload version 1")
            self.assertTrue(new)
            self.assertIsNone(rec)  # original claim() returns no prior record for the first claim
            self.assertEqual(a.reconcile_unknown("engineering","case-1")["state"],"CLAIMED")
            b=ClaimGate(tmp)
            reused,existing=b.claim("engineering","case-1",b"payload version 1")
            self.assertFalse(reused)
            self.assertEqual(existing["state"],"CLAIMED")
            with self.assertRaises(ReplayRefused):
                b.claim("engineering","case-1",b"payload version 2")
            b.mark_unknown("engineering","case-1","simulated lost worker ACK")
            reopened=ClaimGate(tmp)
            first=reopened.reconcile_unknown("engineering","case-1")
            second=reopened.reconcile_unknown("engineering","case-1")
            self.assertEqual(first,second)
            self.assertEqual(first["state"],"UNKNOWN")
            self.assertIsNone(first["outcome"])
            self.assertTrue(reopened.verify_bytes("engineering","case-1",b"payload version 1"))

    def test_real_approval_self_approval_refused_after_reopen(self):
        from gate_approval import ApprovalGate,SelfApprovalRefused
        with tempfile.TemporaryDirectory(prefix="approval-win-") as tmp:
            g=ApprovalGate(tmp)
            g.register_approvers("engineering",["reviewer-one","author-one"])
            rec=g.hold("engineering","claim-one",b"fake patch",claimant_id="author-one")
            self.assertEqual(rec["state"],"HELD_APPROVAL")
            fresh=ApprovalGate(tmp)
            with self.assertRaises(SelfApprovalRefused):
                fresh.approve("engineering","claim-one","author-one",1,b"fake patch")
            self.assertEqual(fresh.verify("engineering","claim-one")["approval_state"],"HELD_APPROVAL")

    def test_token_guard_refuses_equal_and_stale_tokens_after_restart(self):
        from gate_token_guard import TokenGuard
        with tempfile.TemporaryDirectory(prefix="token-win-") as tmp:
            gate=TokenGuard(tmp)
            self.assertTrue(gate.honor("engineering","id-1",1))
            self.assertFalse(gate.honor("engineering","id-1",1))
            fresh=TokenGuard(tmp)
            self.assertEqual(fresh.greatest("engineering","id-1"),1)
            self.assertFalse(fresh.honor("engineering","id-1",1))
            self.assertTrue(fresh.honor("engineering","id-1",2))
            self.assertFalse(gate.honor("engineering","id-1",1))
            self.assertEqual(TokenGuard(tmp).greatest("engineering","id-1"),2)

    def test_token_guard_corrupted_state_fails_closed(self):
        from gate_token_guard import TokenGuard,ClaimGateError
        with tempfile.TemporaryDirectory() as tmp:
            gate=TokenGuard(tmp)
            self.assertTrue(gate.honor("engineering","id-2",1))
            (Path(tmp)/"token-guard.json").write_text("{broken",encoding="utf-8")
            with self.assertRaises(ClaimGateError):
                TokenGuard(tmp).honor("engineering","id-2",2)

    def test_directory_sync_is_os_qualified_not_silently_claimed(self):
        from portable_lock import sync_directory
        with tempfile.TemporaryDirectory() as tmp:
            result=sync_directory(tmp)
            self.assertIs(result,os.name=="posix")

    def test_competing_processes_record_one_claim_and_identical_reuses(self):
        from claim_gate import ClaimGate
        with tempfile.TemporaryDirectory(prefix="many-local-writers-") as tmp:
            base=Path(tmp)
            state=base/"state"
            source=base/"source"
            state.mkdir()
            source.mkdir()
            (source/"same.txt").write_bytes(b"synthetic concurrent write")
            cli=ENGINE/"engineering_claim_gate.py"
            argv=[sys.executable,"-I","-B",str(cli),"--state-dir",str(state),
                  "--scope","engineering","--claim-id","one-id","claim",
                  "--source-root",str(source),"--payload","same.txt"]
            children=[subprocess.Popen(argv,stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,text=True) for _ in range(8)]
            outputs=[]
            try:
                for child in children:
                    out,err=child.communicate(timeout=16)
                    outputs.append((child.returncode,out,err))
            finally:
                for child in children:
                    if child.poll() is None:
                        child.terminate()
                    if child.stdout and not child.stdout.closed:
                        child.stdout.close()
                    if child.stderr and not child.stderr.closed:
                        child.stderr.close()
            for rc,out,err in outputs:
                self.assertEqual(rc,0,(out+err)[-800:])
            statuses=[json.loads(out)["status"] for _,out,_ in outputs]
            self.assertEqual(statuses.count("LOCAL_CLAIM_RECORDED"),1)
            self.assertEqual(statuses.count("LOCAL_CLAIM_REUSED"),7)
            self.assertEqual(ClaimGate(str(state)).reconcile_unknown(
                "engineering","one-id")["state"],"CLAIMED")
            self.assertEqual(len(list((state/"claims"/"engineering").glob("*.json"))),1)

    def test_composite_and_approval_real_shared_state(self):
        from gate_composite import CompositeGate
        with tempfile.TemporaryDirectory(prefix="composite-platform-") as tmp:
            c=CompositeGate(tmp)
            c.approval.register_approvers("engineering",["reviewer-one","author-one"])
            first=c.create_composite("engineering","parent-one",b"synthetic plan", "author-one")
            self.assertEqual(first["state"],"ACTIVE")
            reopened=CompositeGate(tmp)
            again=reopened.create_composite("engineering","parent-one",b"synthetic plan", "author-one")
            self.assertEqual(first["payload_digest"],again["payload_digest"])
            self.assertEqual(len(list((Path(tmp)/"approvals"/"engineering").glob("parent-one.composite.json"))),1)

    @unittest.skipUnless(os.name=="nt","Windows lock deadline uses nonblocking msvcrt")
    def test_composite_scope_lock_excludes_other_process_on_approval_lock(self):
        from gate_composite import CompositeGate
        with tempfile.TemporaryDirectory(prefix="composite-lock-") as tmp:
            c=CompositeGate(tmp)
            lock=Path(tmp)/"approvals"/"engineering"/".lock"
            child=(
                "import sys\n"
                f"sys.path.insert(0,{str(ENGINE)!r})\n"
                "from portable_lock import exclusive_lock\n"
                "with exclusive_lock(sys.argv[1],timeout_seconds=0.25):\n"
                " print('OTHER_WRITER_ENTERED')\n"
            )
            with c._composite_lock("engineering"):
                r=subprocess.run([sys.executable,"-B","-c",child,str(lock)],
                                 capture_output=True,text=True,timeout=6)
                self.assertNotEqual(r.returncode,0)
                self.assertIn("WINDOWS_LOCK_BUSY_TIMEOUT",r.stderr)
            with c._composite_lock("engineering"):
                self.assertTrue(lock.is_file())

    def test_corrupted_claim_record_never_reinitialized(self):
        from claim_gate import ClaimGate,CorruptClaimRecord
        with tempfile.TemporaryDirectory(prefix="corrupt-claim-") as tmp:
            gate=ClaimGate(tmp)
            new,_=gate.claim("engineering","broken",b"synthetic")
            self.assertTrue(new)
            record=Path(tmp)/"claims"/"engineering"/"broken.json"
            record.write_text("{truncated",encoding="utf-8")
            before=record.read_bytes()
            with self.assertRaises(CorruptClaimRecord):
                ClaimGate(tmp).claim("engineering","broken",b"synthetic")
            self.assertEqual(record.read_bytes(),before)

    @unittest.skipUnless(os.name=="nt","Windows destructive pruning must stay disabled")
    def test_terminal_record_not_deleted_by_windows_retention(self):
        from claim_gate import ClaimGate
        from gate_retention import RetentionIntegrityError
        with tempfile.TemporaryDirectory(prefix="retention-win-") as tmp:
            gate=ClaimGate(tmp)
            gate.claim("engineering","keep-terminal",b"synthetic")
            gate.mark_effect("engineering","keep-terminal","SUCCESS",receipt={"local":True})
            original=Path(tmp)/"claims"/"engineering"/"keep-terminal.json"
            before=original.read_bytes()
            try:
                report=gate.prune_terminal("engineering",older_than_days=30,
                                           now=time.time()+40*86400)
            except RetentionIntegrityError:
                report=None
            self.assertTrue(original.exists())
            self.assertEqual(original.read_bytes(),before)
            if report is not None:
                self.assertNotIn("keep-terminal",report["pruned"])
            self.assertFalse((original.parent/".digest-log.jsonl").exists())

    def test_failed_atomic_replace_preserves_previous_claim_and_refuses_transition(self):
        from unittest.mock import patch
        import claim_gate
        with tempfile.TemporaryDirectory(prefix="interrupted-claim-") as tmp:
            gate=claim_gate.ClaimGate(tmp)
            gate.claim("engineering","replace-failure",b"synthetic")
            record=Path(tmp)/"claims"/"engineering"/"replace-failure.json"
            before=record.read_bytes()
            with patch.object(claim_gate.os,"replace",side_effect=OSError("injected rename error")):
                with self.assertRaises(OSError):
                    gate.mark_unknown("engineering","replace-failure","synthetic lost reply")
            self.assertEqual(before,record.read_bytes())
            fresh=claim_gate.ClaimGate(tmp)
            self.assertEqual(fresh.reconcile_unknown("engineering","replace-failure")["state"],"CLAIMED")
            with self.assertRaises(claim_gate.ReplayRefused):
                fresh.claim("engineering","replace-failure",b"different operation")

    def test_distributed_lease_takeover_rejects_stale_fence_and_keeps_unknown(self):
        from distributed_claim_gate import DistributedClaimGate,LeaseError
        with tempfile.TemporaryDirectory(prefix="distributed-win-port-") as tmp:
            first_gate=DistributedClaimGate(tmp)
            created,initial=first_gate.claim_lease(
                "engineering","lease-one",b"synthetic task","owner-one",lease_seconds=60)
            self.assertTrue(created)
            first_token=initial["fencing_token"]
            self.assertGreater(first_token,0)
            blocked,existing=DistributedClaimGate(tmp).claim_lease(
                "engineering","lease-one",b"synthetic task","owner-two",lease_seconds=60)
            self.assertFalse(blocked)
            self.assertEqual(existing["fencing_token"],first_token)
            first_gate.release_lease("engineering","lease-one","owner-one",first_token)
            second_gate=DistributedClaimGate(tmp)
            taken,new=second_gate.claim_lease(
                "engineering","lease-one",b"synthetic task","owner-two",lease_seconds=60)
            self.assertTrue(taken)
            next_token=new["fencing_token"]
            self.assertGreater(next_token,first_token)
            with self.assertRaises(LeaseError):
                first_gate.mark_effect_fenced(
                    "engineering","lease-one","owner-one",first_token,
                    "SUCCESS",receipt={"unauthorized":"old-owner"})
            second_gate.mark_unknown_fenced(
                "engineering","lease-one","owner-two",next_token,
                "synthetic uncertain worker response")
            observed=DistributedClaimGate(tmp).reconcile_unknown("engineering","lease-one")
            self.assertEqual(observed["state"],"UNKNOWN")
            self.assertIsNone(observed["outcome"])
            self.assertEqual(observed["fencing_token"],next_token)

if __name__=="__main__":
    unittest.main()

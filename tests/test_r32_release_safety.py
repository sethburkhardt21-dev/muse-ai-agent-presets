"""R32 release-safety regressions: original reviewer RED -> owner GREEN.

Synthetic disposable staged bundles only. No real Muse registration or effect.
"""
from __future__ import annotations

from contextlib import contextmanager
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

from muse_presets import engineering_pack as pack


class PackSafetyTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory(prefix="r32-safety-")
        self.addCleanup(t.cleanup)
        self.root=Path(t.name).resolve()
        self.staged=self.root/"engineer"
        pack.stage_engineer_pack(self.staged)

    def test_unlisted_runtime_file_is_not_local_match(self):
        (self.staged/"runtime/iron-ledger/unexpected.py").write_bytes(b"unreviewed")
        self.assertNotEqual(pack.inspect_engineer_pack(self.staged)["status"],"LOCAL_MATCH")

    def test_receipt_must_not_claim_native_rights_scheduler_or_effect(self):
        receipt=self.staged/"receipts/PACK_RECEIPT.json"
        claims=json.loads(receipt.read_text())
        claims.update(iron_ledger_rights_verified=True,
                      external_effect_authorized=True,
                      schedulers_enabled=True,
                      installed_native_tools=["new-tool"])
        receipt.write_text(json.dumps(claims))
        self.assertNotEqual(pack.inspect_engineer_pack(self.staged)["status"],"LOCAL_MATCH")

    def test_modified_executable_with_recomputed_receipt_still_refused(self):
        file=self.staged/"runtime/iron-ledger/iron_ledger_consumer.py"
        file.write_bytes(b"raise RuntimeError('tampered')\n")
        receipt=self.staged/"receipts/PACK_RECEIPT.json"
        claims=json.loads(receipt.read_text())
        import hashlib
        claims["files_sha256"]["runtime/iron-ledger/iron_ledger_consumer.py"]=hashlib.sha256(file.read_bytes()).hexdigest()
        receipt.write_text(json.dumps(claims))
        self.assertNotEqual(pack.inspect_engineer_pack(self.staged)["status"],"LOCAL_MATCH")

    def test_owner_customized_memory_preserved(self):
        memory=self.staged/"profile/MEMORY.md"
        memory.write_bytes(memory.read_bytes()+b"\nSynthetic owner note\n")
        self.assertEqual(pack.inspect_engineer_pack(self.staged)["status"],"OWNER_CUSTOMIZED")

    def test_profile_policy_mutation_requires_review(self):
        file=self.staged/"profile/ROLE_PLAYBOOK.md"
        file.write_bytes(file.read_bytes()+b"\nChanged\n")
        self.assertEqual(pack.inspect_engineer_pack(self.staged)["status"],"REVIEW_REQUIRED")

    def test_valid_baseline_is_local_match(self):
        self.assertEqual(pack.inspect_engineer_pack(self.staged)["status"],"LOCAL_MATCH")

    @unittest.skipUnless(os.name=="posix","POSIX filesystem")
    def test_runtime_directory_symlink_refuses(self):
        original=self.staged/"runtime/iron-ledger"
        outside=self.root/"outside"
        original.rename(outside)
        original.symlink_to(outside,target_is_directory=True)
        self.assertNotEqual(pack.inspect_engineer_pack(self.staged)["status"],"LOCAL_MATCH")

    @unittest.skipUnless(os.name=="posix","POSIX filesystem")
    def test_symlinked_destination_ancestor_refuses(self):
        real=self.root/"real"/"nested"
        real.mkdir(parents=True)
        alias=self.root/"redirect"
        alias.symlink_to(self.root/"real",target_is_directory=True)
        dest=alias/"nested"/"new"
        with self.assertRaises((ValueError,FileExistsError)):
            pack.stage_engineer_pack(dest)
        self.assertFalse((real/"new").exists())

    @unittest.skipUnless(os.name=="posix","POSIX Claim Gate")
    def test_claim_cli_source_state_symlinked_ancestor_refuses(self):
        real=self.root/"real"
        source=real/"source"
        state=real/"state"
        source.mkdir(parents=True)
        state.mkdir()
        (source/"payload.txt").write_bytes(b"synthetic")
        alias=self.root/"redirect"
        alias.symlink_to(real,target_is_directory=True)
        cli=self.staged/"runtime/claim-gate/engineering_claim_gate.py"
        proc=subprocess.run([
            sys.executable,"-I","-B",str(cli),"--state-dir",str(alias/"state"),
            "--scope","synthetic","--claim-id","one","claim",
            "--source-root",str(alias/"source"),"--payload","payload.txt"],
            capture_output=True,text=True,timeout=9)
        self.assertNotEqual(proc.returncode,0)
        self.assertFalse((state/"claims/synthetic/one.json").exists())

    @unittest.skipUnless(os.name=="nt","Windows NTFS junction")
    def test_ntfs_junction_ancestor_refuses(self):
        real=self.root/"target"/"nested"
        real.mkdir(parents=True)
        alias=self.root/"junction"
        p=subprocess.run(["cmd.exe","/d","/c","mklink","/J",str(alias),str(self.root/"target")],
                         capture_output=True,text=True,timeout=8)
        if p.returncode!=0 or not alias.is_junction():
            self.skipTest("NTFS junction unavailable")
        try:
            with self.assertRaises((ValueError,FileExistsError)):
                pack.stage_engineer_pack(alias/"nested"/"new")
            self.assertFalse((real/"new").exists())
        finally:
            alias.rmdir()

    @unittest.skipUnless(os.name=="nt","Windows NTFS junction")
    def test_runtime_junction_refuses(self):
        original=self.staged/"runtime/iron-ledger"
        out=self.root/"external"
        original.rename(out)
        p=subprocess.run(["cmd.exe","/d","/c","mklink","/J",str(original),str(out)],
                         capture_output=True,text=True,timeout=8)
        if p.returncode!=0 or not original.is_junction():
            self.skipTest("NTFS junction unavailable")
        try:
            self.assertNotEqual(pack.inspect_engineer_pack(self.staged)["status"],"LOCAL_MATCH")
        finally:
            original.rmdir()


@unittest.skipUnless(os.name=="posix","Claim Gate POSIX fcntl")
class RetentionSafetyTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory(prefix="r32-retention-")
        self.addCleanup(t.cleanup)
        self.root=Path(t.name).resolve()
        stage=self.root/"pack"
        pack.stage_engineer_pack(stage)
        self.runtime=stage/"runtime/claim-gate"
        sys.path.insert(0,str(self.runtime))
        from claim_gate import ClaimGate,ClaimGateError
        from gate_retention import digest_log_path
        self.error=ClaimGateError
        self.gate=ClaimGate(str(self.root/"state"))
        self.log=Path(digest_log_path(str(self.root/"state"),"scope"))
        granted,_=self.gate.claim("scope","previous",b"synthetic")
        self.assertTrue(granted)
        self.gate.mark_effect("scope","previous","SUCCESS",receipt={"fixture":True})
        report=self.gate.prune_terminal("scope",older_than_days=30,
                                        now=time.time()+86400*40)
        self.assertIn("previous",report["pruned"])
        self.assertFalse((self.root/"state/claims/scope/previous.json").exists())
        self.assertTrue(self.log.is_file())

    def tearDown(self):
        if str(self.runtime) in sys.path:sys.path.remove(str(self.runtime))

    def test_intact_pruned_terminal_refuses_reclaim(self):
        claimed,_=self.gate.claim("scope","previous",b"synthetic")
        self.assertFalse(claimed)

    def _assert_denied(self):
        with self.assertRaises(self.error):
            self.gate.claim("scope","previous",b"synthetic")
        self.assertFalse((self.root/"state/claims/scope/previous.json").exists())

    def test_torn_retention_log_holds(self):
        self.log.write_bytes(b'{"claim_id":"previous",broken\n')
        self._assert_denied()

    def test_deleted_retention_log_holds(self):
        self.log.unlink()
        self._assert_denied()

    def test_empty_retention_log_holds(self):
        self.log.write_bytes(b"")
        self._assert_denied()

    def test_unreadable_retention_log_holds(self):
        self.log.unlink()
        self.log.mkdir()
        self._assert_denied()

    def test_truncated_but_valid_retention_log_holds(self):
        self.log.write_bytes(b'{"claim_id":"not-the-original","payload_digest":"' +b"0"*64+b'"}\n')
        self._assert_denied()

    def test_missing_retention_anchor_holds(self):
        anchor=self.log.with_name(".digest-log.anchor.json")
        self.assertTrue(anchor.is_file())
        anchor.unlink()
        self._assert_denied()

    def test_restart_scanner_ignores_anchor_not_a_claim(self):
        from gate_restart import reconcile_on_restart
        report=reconcile_on_restart(str(self.root/"state"),
                                    report_path=str(self.root/"restart.json"))
        self.assertEqual(report["summary"]["total"],0)
        self.assertFalse(report["summary"]["action_required"])


if __name__=="__main__":
    unittest.main(verbosity=2)

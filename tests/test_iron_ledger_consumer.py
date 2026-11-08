"""R32.2 Iron Ledger consumer: no new ledger, sidecar, claim or authority.

The real existing EvidenceLedger is the sole persistence writer. The new
bounded index holds only readback receipt metadata, never source text.
"""
from __future__ import annotations
import hashlib
import json
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory
import sqlite3
import unittest
from unittest.mock import patch

from muse_presets.evidence_ledger import EvidenceLedger, EvidenceScope
from muse_presets.iron_ledger_consumer import (
    IronLedgerRefused, build_local_receipt_index,
    verify_local_receipt_index,
)


class IronConsumerTests(unittest.TestCase):
    def setUp(self):
        tmp=TemporaryDirectory(prefix="iron-consumer-test-")
        self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name).resolve()
        self.source=self.root/"source"
        self.source.mkdir()
        self.file=self.source/"fixture.txt"
        self.file.write_bytes(b"original synthetic alpha finding and a second sentence\n")
        self.db=self.root/"existing-finder.sqlite3"
        self.scope=EvidenceScope("owner-one","workspace-one","evidence-finder","worker-one")

    def ledger(self, scope=None):
        return EvidenceLedger(self.db,authority=lambda:scope or self.scope)

    def capture(self, queries=(("operation-one","alpha"),("operation-two","missing"))):
        with self.ledger() as existing:
            for operation,query in queries:
                existing.capture(self.source,"fixture.txt",query,operation_id=operation)

    def test_actual_existing_ledger_reopen_without_copying_or_raw_text(self):
        self.capture()
        before_bytes=self.db.read_bytes()
        before_stamp=self.db.stat().st_mtime_ns
        self.file.unlink()
        with self.ledger() as existing:
            index=build_local_receipt_index(existing,["operation-two","operation-one"])
            checked=verify_local_receipt_index(existing,index)
            current=existing.verify()
        self.assertEqual(index["status"],"LOCAL_RECEIPTS_INDEXED_ONLY")
        self.assertEqual(index["receipt_count"],2)
        self.assertEqual(index["indexed_operations"],2)
        self.assertEqual([x["operation_id"] for x in index["entries"]],
                         ["operation-one","operation-two"])
        self.assertEqual([x["outcome"] for x in index["entries"]],
                         ["FOUND","NOT_FOUND"])
        self.assertEqual(index["head_chain_sha256"],current["head_chain_sha256"])
        self.assertEqual(checked["status"],"LOCAL_INDEX_VERIFIED")
        self.assertEqual(self.db.read_bytes(),before_bytes)
        self.assertEqual(self.db.stat().st_mtime_ns,before_stamp)
        self.assertFalse((self.root/"pins.jsonl").exists())
        self.assertFalse((self.root/"registry_index.json").exists())
        self.assertFalse((self.root/"claims").exists())
        self.assertNotIn("original synthetic alpha",json.dumps(index))
        self.assertNotIn(str(self.root),json.dumps(index))
        for field in ("native_muse_bound","source_owner_authenticated",
                      "host_authority_authenticated","recipient_acknowledged",
                      "external_effect_authorized","redistribution_rights_verified",
                      "independent_truth_verified"):
            self.assertFalse(index[field])

    def test_requested_subset_is_not_entire_ledger(self):
        self.capture()
        with self.ledger() as existing:
            index=build_local_receipt_index(existing,["operation-two"])
        self.assertEqual(index["indexed_operations"],1)
        self.assertEqual(index["receipt_count"],2)
        self.assertEqual(index["entries"][0]["sequence"],2)
        self.assertEqual(index["entries"][0]["outcome"],"NOT_FOUND")

    def test_changed_evidence_head_invalidates_old_index(self):
        self.capture(queries=(("operation-one","alpha"),))
        with self.ledger() as existing:
            first=build_local_receipt_index(existing,["operation-one"])
        self.capture(queries=(("operation-two","alpha"),))
        with self.ledger() as reopened:
            with self.assertRaisesRegex(IronLedgerRefused,"STALE"):
                verify_local_receipt_index(reopened,first)
            refreshed=build_local_receipt_index(reopened,["operation-one","operation-two"])
            self.assertEqual(refreshed["receipt_count"],2)

    def test_failed_capture_or_corrupt_chain_does_not_generate_index(self):
        self.capture(queries=(("operation-one","alpha"),))
        with closing(sqlite3.connect(self.db)) as con:
            con.execute("UPDATE evidence_records SET record_json='{}' WHERE operation_key='operation-one'")
            con.commit()
        with self.ledger() as existing:
            with self.assertRaises(IronLedgerRefused):
                build_local_receipt_index(existing,["operation-one"])
        self.assertFalse((self.root/"registry_index.json").exists())

    def test_missing_and_unbounded_operation_ids_refused(self):
        self.capture(queries=(("operation-one","alpha"),))
        for ops in ([],["operation-one"]*2,["../path"],["operation one"],
                    ["missing"],["operation-one"]*33,["x"*81],None,True):
            with self.subTest(ops=repr(ops)),self.ledger() as existing:
                with self.assertRaises(IronLedgerRefused):
                    build_local_receipt_index(existing,ops)

    def test_wrong_scope_and_unbound_authority_rejected(self):
        self.capture(queries=(("operation-one","alpha"),))
        with self.assertRaises(ValueError):
            EvidenceLedger(self.db)
        scope=EvidenceScope("other-owner","workspace-one","evidence-finder","worker-one")
        with self.ledger(scope) as wrong:
            with self.assertRaises(IronLedgerRefused):
                build_local_receipt_index(wrong,["operation-one"])

    def test_tampered_index_forged_authority_or_receipt_digest_rejected(self):
        self.capture(queries=(("operation-one","alpha"),))
        with self.ledger() as existing:
            index=build_local_receipt_index(existing,["operation-one"])
            for field,new in (("native_muse_bound",True),
                              ("external_effect_authorized",True),
                              ("recipient_acknowledged",True),
                              ("host_authority_authenticated",True)):
                with self.subTest(field=field):
                    forged={**index,field:new}
                    with self.assertRaises(IronLedgerRefused):
                        verify_local_receipt_index(existing,forged)
            forged=json.loads(json.dumps(index))
            forged["entries"][0]["record_sha256"]="a"*64
            with self.assertRaises(IronLedgerRefused):
                verify_local_receipt_index(existing,forged)

    def test_untrusted_ledger_interface_cannot_mint_authority(self):
        self.capture(queries=(("operation-one","alpha"),))
        with self.ledger() as real:
            checked=real.verify()
            actual=real.read("operation-one")
        class FakeReader:
            def verify(self):return checked
            def read(self,_):return actual
        index=build_local_receipt_index(FakeReader(),["operation-one"])
        self.assertFalse(index["host_authority_authenticated"])
        self.assertFalse(index["native_muse_bound"])

        class Forged:
            def verify(self):return {**checked,"recipient_acknowledged":True}
            def read(self,_):return actual
        with self.assertRaises(IronLedgerRefused):
            build_local_receipt_index(Forged(),["operation-one"])

        class WrongReceipt:
            def verify(self):return checked
            def read(self,_):return {**actual,"receipt":{**actual["receipt"],"operation_id":"other-operation"}}
        with self.assertRaises(IronLedgerRefused):
            build_local_receipt_index(WrongReceipt(),["operation-one"])

    def test_during_read_append_is_detected_as_stale(self):
        self.capture(queries=(("operation-one","alpha"),))
        original=self.ledger()
        self.addCleanup(original.close)
        class MutatingReader:
            def __init__(self,ledger,outer):self.ledger=ledger;self.outer=outer
            def verify(self):return self.ledger.verify()
            def read(self,operation):
                value=self.ledger.read(operation)
                self.outer.capture(queries=(("operation-two","alpha"),))
                return value
        with self.assertRaisesRegex(IronLedgerRefused,"STALE"):
            build_local_receipt_index(MutatingReader(original,self),["operation-one"])

    def test_staged_engineer_pack_contains_pinned_iron_consumer(self):
        from importlib.util import spec_from_file_location,module_from_spec
        from muse_presets.engineering_pack import stage_engineer_pack,inspect_engineer_pack
        self.capture(queries=(("operation-one","alpha"),))
        stage=self.root/"software-engineer-pack"
        result=stage_engineer_pack(stage)
        self.assertFalse(result["native_installed"])
        script=stage/"runtime"/"iron-ledger"/"iron_ledger_consumer.py"
        self.assertTrue(script.is_file())
        manifest=json.loads((stage/"runtime"/"iron-ledger"/"ENGINE.json").read_text())
        self.assertFalse(manifest["redistribution_rights_verified"])
        self.assertEqual(hashlib.sha256(script.read_bytes()).hexdigest(),
                         manifest["files"]["iron_ledger_consumer.py"])
        spec=spec_from_file_location("staged_iron_ledger_consumer",script)
        mod=module_from_spec(spec);spec.loader.exec_module(mod)
        with self.ledger() as existing:
            idx=mod.build_local_receipt_index(existing,["operation-one"])
            self.assertEqual(idx["status"],"LOCAL_RECEIPTS_INDEXED_ONLY")
            self.assertEqual(mod.verify_local_receipt_index(existing,idx)["status"],
                             "LOCAL_INDEX_VERIFIED")
        self.assertEqual(inspect_engineer_pack(stage)["status"],"LOCAL_MATCH")
        self.assertFalse((stage/"memory").exists())

    def test_preflight_refuses_modified_iron_module_without_installing(self):
        from muse_presets import engineering_pack as pack
        self.capture(queries=(("operation-one","alpha"),))
        changed=self.root/"altered-module.py"
        changed.write_text("raise RuntimeError('unexpected')",encoding="utf-8")
        dest=self.root/"never-created-pack"
        with patch.object(pack,"IRON_SOURCE",changed):
            with self.assertRaisesRegex(ValueError,"SOURCE_PIN_MISMATCH"):
                pack.stage_engineer_pack(dest)
        self.assertFalse(dest.exists())

    def test_preflight_refuses_modified_iron_skill_without_installing(self):
        from muse_presets import engineering_pack as pack
        from shutil import copytree
        copied=self.root/"altered-skill"
        copytree(pack.IRON_SKILL_ROOT,copied)
        (copied/"SKILL.md").write_text("untrusted changed skill",encoding="utf-8")
        dest=self.root/"never-created-pack"
        with patch.object(pack,"IRON_SKILL_ROOT",copied):
            with self.assertRaisesRegex(ValueError,"SOURCE_PIN_MISMATCH"):
                pack.stage_engineer_pack(dest)
        self.assertFalse(dest.exists())

    def test_index_refuses_wrong_actor_in_read_response(self):
        self.capture(queries=(("operation-one","alpha"),))
        with self.ledger() as existing:
            trusted=existing.verify()
            observed=existing.read("operation-one")
        class WrongActor:
            def verify(self):return trusted
            def read(self,op):
                return {**observed,"scope":{**observed["scope"],
                        "actor_id":"forged-actor"}}
        with self.assertRaisesRegex(IronLedgerRefused,"SCOPE_MISMATCH"):
            build_local_receipt_index(WrongActor(),["operation-one"])

    def test_absent_index_is_refused_even_when_ledger_has_existing_receipts(self):
        self.capture(queries=(("operation-one","alpha"),))
        with self.ledger() as existing:
            with self.assertRaises(IronLedgerRefused):
                verify_local_receipt_index(existing,{"status":"LOCAL_RECEIPTS_INDEXED_ONLY"})

    def test_no_stale_allowlist_or_sidecar_created(self):
        self.capture(queries=(("operation-one","alpha"),))
        with self.ledger() as existing:
            index=build_local_receipt_index(existing,["operation-one"])
            with self.assertRaises(IronLedgerRefused):
                verify_local_receipt_index(existing,{**index,"allow_stale":True})
        self.assertFalse((self.root/"iron-ledger").exists())


if __name__=="__main__":
    unittest.main()

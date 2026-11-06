"""Public showcase: source-bound, recoverable Evidence Finder local custody.

Synthetic fixtures only. No private donors, native Muse permission or
external effects. The original finder.py remains independently tested.
"""
from __future__ import annotations

import hashlib
from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor

from muse_presets.evidence_custody import EvidenceLedger, ROLES

TEXT = "A neutral observation.\nFinding: red lantern.\nAll text stays intact.\n"


class PublicEvidenceCustodyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="showcase_evidence_")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.sources = self.root / "sources"
        self.sources.mkdir()
        self.state = self.root / "local_state"
        self.state.mkdir()
        (self.sources / "note.txt").write_bytes(TEXT.encode("utf-8"))

    def ledger(self, role="evidence-finder"):
        return EvidenceLedger(self.state, role_id=role)

    def record(self, case="case_one", query="red lantern", role="evidence-finder"):
        return self.ledger(role).record(
            operation_id=case, source_root=self.sources,
            relative_path="note.txt", query=query,
        )

    def test_full_exact_source_is_locally_recorded_then_reopened_without_file(self):
        first = self.record()
        self.assertEqual(first["status"], "LOCAL_RECEIPT_RECORDED")
        self.assertEqual(first["receipt"]["sequence"], 1)
        self.assertEqual(first["outcome"], "FINDING")
        self.assertEqual(first["finding"]["text"], TEXT)
        self.assertEqual(
            first["finding"]["source_sha256"],
            hashlib.sha256(TEXT.encode("utf-8")).hexdigest(),
        )
        self.assertFalse(first["source_owner_authenticated"])
        self.assertFalse(first["external_effect_performed"])
        self.assertFalse(first["native_muse_invoked"])
        (self.sources / "note.txt").unlink()
        recovered = self.ledger().read("case_one")
        self.assertEqual(recovered["status"], "LOCAL_RECEIPT_REOPENED")
        self.assertEqual(recovered["finding"]["text"], TEXT)
        self.assertTrue(recovered["source_bytes_verified_locally"])
        self.assertEqual(recovered["receipt"]["chain_sha256"], first["receipt"]["chain_sha256"])

    def test_no_hit_is_explicit_and_persists_scope_without_invented_finding(self):
        found = self.record()
        missed = self.record(case="case_two", query="not here")
        self.assertEqual(missed["outcome"], "NOTHING_FOUND")
        self.assertIsNone(missed["finding"])
        self.assertEqual(missed["source_sha256"], found["source_sha256"])
        self.assertEqual(missed["receipt"]["sequence"], 2)
        self.assertEqual(
            missed["receipt"]["previous_chain_sha256"],
            found["receipt"]["chain_sha256"],
        )
        reopened = self.ledger().read("case_two")
        self.assertIsNone(reopened["finding"])
        self.assertEqual(reopened["outcome"], "NOTHING_FOUND")
        self.assertEqual(self.ledger().verify()["receipt_count"], 2)

    def test_identical_replay_preserves_one_entry_changed_query_fails(self):
        original = self.record()
        replay = self.record()
        self.assertEqual(replay["status"], "LOCAL_RECEIPT_PRESERVED")
        self.assertEqual(replay["receipt"]["chain_sha256"], original["receipt"]["chain_sha256"])
        with self.assertRaisesRegex(ValueError, "OPERATION_CONFLICT"):
            self.record(query="other")
        self.assertEqual(self.ledger().verify()["receipt_count"], 1)

    def test_changed_source_bytes_refuse_same_operation_without_overwriting(self):
        one = self.record()
        (self.sources / "note.txt").write_text(TEXT + "modified\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "OPERATION_CONFLICT"):
            self.record()
        self.assertEqual(self.ledger().read("case_one")["receipt"]["chain_sha256"],
                         one["receipt"]["chain_sha256"])

    def test_tampered_sqlite_entry_is_rejected_on_read_verify_and_append(self):
        self.record()
        db = self.state / "evidence-finder" / "receipts.sqlite3"
        with closing(sqlite3.connect(db)) as c:
            c.execute("UPDATE entries SET chain_sha256=? WHERE seq=1", ("0" * 64,))
            c.commit()
        for task in (
            lambda: self.ledger().read("case_one"),
            lambda: self.ledger().verify(),
            lambda: self.record(case="case_next"),
        ):
            with self.assertRaisesRegex(ValueError, "RECEIPT_CHAIN_INVALID"):
                task()

    def test_cross_role_database_copy_is_not_mistaken_for_owner_authorization(self):
        self.record()
        other = self.ledger("coordinator")
        # Establish its distinct local role namespace.
        self.assertFalse(other.verify()["ledger_exists"])
        src = self.state / "evidence-finder" / "receipts.sqlite3"
        target_dir = self.state / "coordinator"
        target_dir.mkdir()
        (target_dir / "receipts.sqlite3").write_bytes(src.read_bytes())
        with self.assertRaisesRegex(ValueError, "ROLE_LEDGER_MISMATCH"):
            other.verify()

    def test_all_public_generic_roles_are_admitted_as_labels_not_real_principals(self):
        self.assertEqual(len(ROLES), 12)
        for role in ROLES:
            result = self.record(role=role)
            self.assertEqual(result["role_id"], role)
            self.assertFalse(result["host_principal_verified"])
            self.assertFalse(result["external_effect_performed"])
            self.assertEqual(self.ledger(role).verify()["receipt_count"], 1)
        with self.assertRaisesRegex(ValueError, "ROLE_NOT_ALLOWED"):
            self.ledger("fictional-intruder")

    def test_traversal_symlink_and_overlarge_source_fail_before_record(self):
        with self.assertRaises(ValueError):
            self.ledger().record(operation_id="x", source_root=self.sources,
                                 relative_path="../note.txt", query="red")
        alias = self.sources / "alias.txt"
        try:
            alias.symlink_to(self.sources / "note.txt")
        except (OSError, NotImplementedError):
            pass
        else:
            with self.assertRaises(ValueError):
                self.ledger().record(operation_id="x", source_root=self.sources,
                                     relative_path="alias.txt", query="red")
        (self.sources / "huge.txt").write_bytes(b"x" * 9000)
        with self.assertRaises(ValueError):
            self.ledger().record(operation_id="x", source_root=self.sources,
                                 relative_path="huge.txt", query="red")
        self.assertFalse(self.ledger().verify()["ledger_exists"])

    def test_does_not_create_on_verify_read_or_invalid_fields(self):
        self.assertFalse(self.ledger().verify()["ledger_exists"])
        with self.assertRaisesRegex(ValueError, "OPERATION_NOT_FOUND"):
            self.ledger().read("missing")
        self.assertFalse((self.state / "evidence-finder").exists())
        with self.assertRaisesRegex(ValueError, "INVALID_OPERATION_ID"):
            self.record(case="../escape")
        with self.assertRaisesRegex(ValueError, "INVALID_QUERY"):
            self.record(query="")
        self.assertFalse((self.state / "evidence-finder").exists())

    def test_symlinked_storage_namespace_refuses(self):
        external = self.root / "outside"
        external.mkdir()
        alias = self.state / "evidence-finder"
        try:
            alias.symlink_to(external, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("Symlink unavailable")
        with self.assertRaisesRegex(ValueError, "STATE_SYMLINK_REFUSED"):
            self.record()

    def test_two_concurrent_writers_produce_valid_chain(self):
        def op(n):
            return self.record(case=f"case_{n}")
        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(op, (2, 3)))
        self.assertEqual(sorted(x["receipt"]["sequence"] for x in outcomes), [1, 2])
        record = self.ledger().verify()
        self.assertEqual(record["receipt_count"], 2)
        self.assertTrue(record["local_chain_verified"])
        self.assertFalse(record["external_anchor_verified"])


if __name__ == "__main__":
    unittest.main()

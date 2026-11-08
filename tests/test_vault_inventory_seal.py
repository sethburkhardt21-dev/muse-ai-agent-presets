"""R32 Provenance Vault read-only inventory/seal acceptance with actual Finder receipts."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from muse_presets.evidence_ledger import EvidenceLedger, EvidenceScope
from muse_presets.provenance_vault import (
    ProvenanceRefused, inventory_tree, make_local_source_seal,
    verify_local_source_seal,
)

NOW = datetime(2026, 11, 7, 17, 0, tzinfo=timezone.utc)


class ReadOnlySourceInventoryTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="local-inventory-")
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name).resolve() / "owned-source"
        self.root.mkdir()
        (self.root / "nested").mkdir()
        (self.root / "a.txt").write_bytes(b"alpha\n")
        (self.root / "nested" / "b.bin").write_bytes(bytes(range(12)))

    def test_deterministic_relative_inventory_with_exact_bytes(self):
        before = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in
                  (self.root / "a.txt", self.root / "nested" / "b.bin")}
        first = inventory_tree(self.root)
        second = inventory_tree(self.root)
        self.assertEqual(first, second)
        self.assertEqual(first["file_count"], 2)
        self.assertEqual(first["total_bytes"], 18)
        self.assertEqual([x["relative_path"] for x in first["records"]],
                         ["a.txt", "nested/b.bin"])
        self.assertEqual(first["records"][0]["sha256"],
                         hashlib.sha256(b"alpha\n").hexdigest())
        self.assertNotIn(str(self.root), json.dumps(first))
        for p, (raw, stamp) in before.items():
            self.assertEqual(p.read_bytes(), raw)
            self.assertEqual(p.stat().st_mtime_ns, stamp)

    def test_refuse_symlinked_ancestor_without_symlink_privilege(self):
        root_parent = self.root.parent
        real_is_symlink = Path.is_symlink

        def artificial_link(path):
            return path == root_parent or real_is_symlink(path)

        with patch.object(Path, "is_symlink", autospec=True,
                          side_effect=artificial_link):
            with self.assertRaisesRegex(ProvenanceRefused, "symlink"):
                inventory_tree(self.root)

    def test_actual_symlinked_ancestor_refused_if_os_supports_it(self):
        alias = self.root.parent / "alternate-root"
        try:
            alias.symlink_to(self.root, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("native directory symlink unavailable")
        with self.assertRaisesRegex(ProvenanceRefused, "symlink"):
            inventory_tree(alias / "nested")

    def test_file_change_changes_inventory_digest(self):
        initial = inventory_tree(self.root)
        (self.root / "a.txt").write_bytes(b"beta!")
        changed = inventory_tree(self.root)
        self.assertNotEqual(initial["inventory_sha256"], changed["inventory_sha256"])

    def test_refuse_missing_root_and_file_count_limit(self):
        with self.assertRaises(ProvenanceRefused):
            inventory_tree(self.root / "missing")
        with self.assertRaisesRegex(ProvenanceRefused, "file count"):
            inventory_tree(self.root, max_files=1)

    def test_refuse_large_source_file(self):
        (self.root / "oversize.bin").write_bytes(b"x" * (1_048_577))
        with self.assertRaisesRegex(ProvenanceRefused, "too large"):
            inventory_tree(self.root)

    def test_refuse_file_or_directory_symlink_where_supported(self):
        alias = self.root / "alias"
        try:
            alias.symlink_to(self.root / "a.txt")
        except (OSError, NotImplementedError):
            self.skipTest("native symlink creation unavailable")
        with self.assertRaisesRegex(ProvenanceRefused, "symlink"):
            inventory_tree(self.root)
        with self.assertRaisesRegex(ProvenanceRefused, "symlink"):
            inventory_tree(alias)


class LocalProvenanceSealTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="local-seal-")
        self.addCleanup(tmp.cleanup)
        self.base = Path(tmp.name).resolve()
        self.sources = self.base / "sources"
        self.sources.mkdir()
        (self.sources / "note.txt").write_bytes(b"synthetic alpha observation\n")
        self.database = self.base / "ledger.sqlite3"
        self.scope = EvidenceScope(owner_id="sample-owner", workspace_id="sample-work",
                                   role_id="evidence-finder", actor_id="sample-researcher")

    def ledger(self):
        return EvidenceLedger(self.database, authority=lambda: self.scope)

    def record(self):
        with self.ledger() as finder:
            finder.capture(self.sources, "note.txt", "alpha", operation_id="op-1")
            return finder.verify()

    def test_real_finder_chain_bound_to_source_snapshot_and_reopen(self):
        original_head = self.record()
        sealed = make_local_source_seal(self.sources, original_head,
                                        version=3, ttl_seconds=3600, now=NOW)
        self.assertEqual(sealed["receipt_count"], 1)
        self.assertEqual(sealed["head_chain_sha256"],
                         original_head["head_chain_sha256"])
        self.assertFalse(sealed["chain_externally_anchored"])
        self.assertFalse(sealed["source_owner_authenticated"])
        self.assertFalse(sealed["redistribution_rights_verified"])
        self.assertFalse(sealed["roles_authenticated"])
        self.assertNotIn(str(self.base), json.dumps(sealed))
        with self.ledger() as reopened:
            fresh_head = reopened.verify()
            response = verify_local_source_seal(
                self.sources, sealed, fresh_head, minimum_version=3, now=NOW + timedelta(seconds=10))
            self.assertEqual(response["status"], "LOCAL_SOURCE_AND_EVIDENCE_CORRELATED")
            self.assertEqual(response["receipt_count"], 1)
            self.assertFalse(response["native_muse_bound"])
            self.assertFalse(response["recipient_acknowledged"])
            self.assertEqual(reopened.verify()["receipt_count"], 1)

    def test_source_edit_refused(self):
        head = self.record()
        seal = make_local_source_seal(self.sources, head, now=NOW)
        (self.sources / "note.txt").write_bytes(b"altered evidence")
        with self.assertRaisesRegex(ProvenanceRefused, "source"):
            verify_local_source_seal(self.sources, seal, head, now=NOW)

    def test_existing_finder_receipt_chain_change_refused(self):
        head = self.record()
        seal = make_local_source_seal(self.sources, head, now=NOW)
        with self.ledger() as finder:
            finder.capture(self.sources, "note.txt", "synthetic", operation_id="op-2")
            new_head = finder.verify()
        self.assertNotEqual(head["head_chain_sha256"], new_head["head_chain_sha256"])
        with self.assertRaisesRegex(ProvenanceRefused, "chain head"):
            verify_local_source_seal(self.sources, seal, new_head, now=NOW)

    def test_expiry_and_version_rollback_refused(self):
        head = self.record()
        seal = make_local_source_seal(self.sources, head, version=2,
                                      ttl_seconds=60, now=NOW)
        with self.assertRaisesRegex(ProvenanceRefused, "expired"):
            verify_local_source_seal(self.sources, seal, head,
                                     now=NOW + timedelta(seconds=61))
        with self.assertRaisesRegex(ProvenanceRefused, "rollback"):
            verify_local_source_seal(self.sources, seal, head,
                                     minimum_version=3, now=NOW + timedelta(seconds=20))
        with self.assertRaisesRegex(ProvenanceRefused, "lifetime"):
            make_local_source_seal(self.sources, head, ttl_seconds=60 * 60 * 24 * 31, now=NOW)

    def test_tampered_seal_rejected_without_trusting_self_authored_claim(self):
        head = self.record()
        seal = make_local_source_seal(self.sources, head, now=NOW)
        seal["version"] = 999
        with self.assertRaisesRegex(ProvenanceRefused, "seal digest"):
            verify_local_source_seal(self.sources, seal, head, now=NOW)

    def test_forged_evidence_verdict_and_native_flag_refused(self):
        head = self.record()
        for name, value in (
            ("status", "SIMULATED"),
            ("chain_verified_locally", False),
            ("source_owner_authenticated", True),
            ("chain_externally_anchored", True),
            ("recipient_acknowledged", True),
            ("native_muse_status", "VERIFIED"),
            ("effect_authorized", True),
        ):
            altered = dict(head)
            altered[name] = value
            with self.subTest(field=name), self.assertRaises(ProvenanceRefused):
                make_local_source_seal(self.sources, altered, now=NOW)

    def test_source_only_seal_refuses_empty_or_unverified_finder_head(self):
        with self.ledger() as finder:
            empty = finder.verify()
        with self.assertRaisesRegex(ProvenanceRefused, "empty"):
            make_local_source_seal(self.sources, empty, now=NOW)

    def test_invalid_issuer_clock_and_unsupported_version_refused(self):
        head = self.record()
        for case in (0, True, -1):
            with self.subTest(version=case), self.assertRaises(ProvenanceRefused):
                make_local_source_seal(self.sources, head, version=case, now=NOW)
        with self.assertRaises(ProvenanceRefused):
            make_local_source_seal(self.sources, head, now=datetime(2026, 11, 7))
        seal = make_local_source_seal(self.sources, head, now=NOW)
        with self.assertRaisesRegex(ProvenanceRefused, "clock"):
            verify_local_source_seal(self.sources, seal, head,
                                     now=NOW - timedelta(hours=2))


if __name__ == "__main__":
    unittest.main()

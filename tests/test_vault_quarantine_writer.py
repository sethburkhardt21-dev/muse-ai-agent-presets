"""R32.1c real local create-only quarantine with deterministic recovery evidence.

Temporary synthetic owner source and destination only. No native Muse, export,
original donor registry, remote provider, or authority elevation.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import muse_presets.provenance_vault as vault
from muse_presets.evidence_ledger import EvidenceLedger, EvidenceScope

NOW = datetime(2026, 11, 7, 18, 0, tzinfo=timezone.utc)


class LocalQuarantineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="r32-local-quarantine-")
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name).resolve()
        self.source = self.base / "source"
        self.source.mkdir()
        (self.source / "nested").mkdir()
        (self.source / "alpha.txt").write_bytes(b"alpha synthetic evidence\n")
        (self.source / "nested" / "beta.bin").write_bytes(bytes(range(20)))
        self.parent = self.base / "quarantine"
        self.parent.mkdir()
        self.dest = self.parent / "candidate-001"
        self.scope = EvidenceScope(owner_id="sample-owner", workspace_id="sample-project",
                                   role_id="evidence-finder", actor_id="sample-operator")
        self.database = self.base / "finder.sqlite3"
        with EvidenceLedger(self.database, authority=lambda:self.scope) as ledger:
            ledger.capture(self.source, "alpha.txt", "alpha", operation_id="original001")
            self.head = ledger.verify()
        self.seal = vault.make_local_source_seal(self.source, self.head, now=NOW)
        self.preview = vault.preview_local_adoption(
            self.source, self.seal, self.head,
            members=["alpha.txt", "nested/beta.bin"], now=NOW)
        self.calls = []

    def authorized(self, src, dst_parent, pin):
        self.calls.append((src, dst_parent, pin))
        return src == self.source and dst_parent == self.parent and pin == self.preview["preview_sha256"]

    def stage(self, *, guard=None, preview=None, parent=None, name="candidate-001"):
        return vault.stage_local_adoption_quarantine(
            self.source, self.preview if preview is None else preview,
            self.seal, self.head, quarantine_parent=self.parent if parent is None else parent,
            adoption_name=name,
            authorize_local_write=self.authorized if guard is None else guard,
            now=NOW)

    def test_create_only_happy_path_and_reopen_after_original_source_removed(self):
        before = {(p.relative_to(self.source).as_posix()): (p.read_bytes(), p.stat().st_mtime_ns)
                  for p in (self.source / "alpha.txt", self.source / "nested" / "beta.bin")}
        result = self.stage()
        self.assertEqual(result["status"], "LOCAL_QUARANTINE_STAGED")
        self.assertFalse(result["native_muse_bound"])
        self.assertFalse(result["release_approved"])
        self.assertFalse(result["external_effect_authorized"])
        self.assertFalse(result["source_owner_authenticated"])
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(self.calls[0], (self.source, self.parent, self.preview["preview_sha256"]))
        self.assertTrue(self.dest.is_dir())
        self.assertFalse((self.dest / "STAGING_INCOMPLETE").exists())
        self.assertFalse((self.parent / "adoptions.json").exists())
        self.assertFalse((self.source / "adoptions.json").exists())
        manifest = json.loads((self.dest / "ADOPTION-MANIFEST.json").read_text())
        self.assertEqual(len(manifest["members"]), 2)
        self.assertEqual(manifest["status"], "LOCAL_QUARANTINED_NOT_ADOPTED")
        self.assertEqual(manifest["source_preview_sha256"], self.preview["preview_sha256"])
        self.assertEqual(manifest["evidence_head_sha256"], self.head["head_chain_sha256"])
        self.assertFalse(manifest["redistribution_rights_verified"])
        for entry in manifest["members"]:
            stored = self.dest / entry["stored_path"]
            self.assertTrue(stored.is_file())
            self.assertEqual(stored.read_bytes(), before[entry["relative_path"]][0])
            self.assertEqual(hashlib.sha256(stored.read_bytes()).hexdigest(), entry["sha256"])
        for rel, (raw, stamp) in before.items():
            path = self.source / rel
            self.assertEqual(path.read_bytes(), raw)
            self.assertEqual(path.stat().st_mtime_ns, stamp)
            path.unlink()
        reopened = vault.inspect_local_adoption_quarantine(self.dest)
        self.assertEqual(reopened["status"], "LOCAL_QUARANTINE_VERIFIED")
        self.assertEqual(reopened["members_verified"], 2)
        self.assertFalse(reopened["source_owner_authenticated"])
        self.assertFalse(reopened["native_muse_bound"])

    def test_actual_staged_vault_module_performs_local_quarantine_only(self):
        from importlib.util import spec_from_file_location, module_from_spec
        from muse_presets.engineering_pack import stage_engineer_pack, inspect_engineer_pack
        pack = self.base / "new-generic-engineer"
        stage_engineer_pack(pack)
        path = pack / "runtime" / "provenance-vault" / "provenance_vault.py"
        spec = spec_from_file_location("r32_staged_quarantine_writer", path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        result = module.stage_local_adoption_quarantine(
            self.source, self.preview, self.seal, self.head,
            quarantine_parent=self.parent, adoption_name="candidate-001",
            authorize_local_write=self.authorized, now=NOW)
        self.assertEqual(result["status"], "LOCAL_QUARANTINE_STAGED")
        self.assertFalse(result["host_authority_authenticated"])
        checked = module.inspect_local_adoption_quarantine(self.dest)
        self.assertEqual(checked["status"], "LOCAL_QUARANTINE_VERIFIED")
        self.assertFalse(checked["release_approved"])
        self.assertEqual(inspect_engineer_pack(pack)["status"], "LOCAL_MATCH")
        self.assertFalse((self.parent / "adoptions.json").exists())

    def test_missing_guard_and_denied_guard_refuse_without_destination(self):
        with self.assertRaisesRegex(vault.ProvenanceRefused, "guard"):
            self.stage(guard=False)
        with self.assertRaisesRegex(vault.ProvenanceRefused, "guard"):
            self.stage(guard=lambda *args: False)
        with self.assertRaisesRegex(vault.ProvenanceRefused, "guard"):
            self.stage(guard=lambda *args: 1)
        with self.assertRaisesRegex(vault.ProvenanceRefused, "guard"):
            self.stage(guard=lambda *args: (_ for _ in ()).throw(RuntimeError("not authorized")))
        self.assertFalse(self.dest.exists())
        self.assertFalse(self.calls)

    def test_existing_directory_refuses_without_modifying_owner_content(self):
        self.dest.mkdir()
        note = self.dest / "MEMORY.md"
        note.write_bytes(b"owner-state")
        with self.assertRaisesRegex(vault.ProvenanceRefused, "exists"):
            self.stage()
        self.assertEqual(note.read_bytes(), b"owner-state")
        self.assertFalse((self.dest / "STAGING_INCOMPLETE").exists())

    def test_changed_source_and_finder_head_refuse_before_write(self):
        (self.source / "alpha.txt").write_bytes(b"changed")
        with self.assertRaisesRegex(vault.ProvenanceRefused, "source"):
            self.stage()
        self.assertFalse(self.dest.exists())
        (self.source / "alpha.txt").write_bytes(b"alpha synthetic evidence\n")
        with EvidenceLedger(self.database, authority=lambda:self.scope) as ledger:
            ledger.capture(self.source, "alpha.txt", "synthetic", operation_id="original002")
            newer = ledger.verify()
        with self.assertRaises(vault.ProvenanceRefused):
            vault.stage_local_adoption_quarantine(
                self.source, self.preview, self.seal, newer,
                quarantine_parent=self.parent, adoption_name="candidate-001",
                authorize_local_write=self.authorized, now=NOW)
        self.assertFalse(self.dest.exists())

    def test_destination_scope_refuses_source_child_or_symlink_parent(self):
        with self.assertRaises(vault.ProvenanceRefused):
            self.stage(parent=self.source)
        self.assertFalse((self.source / "candidate-001").exists())
        with self.assertRaises(vault.ProvenanceRefused):
            self.stage(parent=self.parent / "missing")
        alias = self.base / "link-quarantine"
        try:
            alias.symlink_to(self.parent, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("native directory symlink unavailable")
        with self.assertRaisesRegex(vault.ProvenanceRefused, "symlink"):
            self.stage(parent=alias)
        self.assertFalse(self.dest.exists())

    def test_bad_adoption_names_refuse_without_writes(self):
        for name in ("", "../escape", ".hidden", "one/two", "a\\b",
                     "alpha\nbeta", "x" * 100, "a:b", "candidate.01"):
            with self.subTest(name=name), self.assertRaises(vault.ProvenanceRefused):
                self.stage(name=name)
        self.assertEqual(list(self.parent.iterdir()), [])

    def test_concurrent_same_name_one_wins_and_other_refuses(self):
        with ThreadPoolExecutor(max_workers=2) as workers:
            results = list(workers.map(lambda _: self._try_stage(), range(2)))
        self.assertEqual(sorted(results), ["REFUSED", "STAGED"])
        self.assertEqual(vault.inspect_local_adoption_quarantine(self.dest)["members_verified"], 2)

    def _try_stage(self):
        try:
            self.stage()
            return "STAGED"
        except vault.ProvenanceRefused:
            return "REFUSED"

    def test_write_fault_leaves_incomplete_marker_and_no_overwrite_on_retry(self):
        original = vault._write_quarantine_file
        seen = []

        def fail_second_member(path, raw):
            if path.suffix == ".bin":
                seen.append(path)
                if len(seen) == 2:
                    raise OSError("synthetic storage failure")
            return original(path, raw)

        with patch.object(vault, "_write_quarantine_file", side_effect=fail_second_member):
            with self.assertRaisesRegex(vault.ProvenanceRefused, "incomplete"):
                self.stage()
        self.assertTrue((self.dest / "STAGING_INCOMPLETE").is_file())
        self.assertEqual(vault.inspect_local_adoption_quarantine(self.dest)["status"],
                         "INCOMPLETE_STAGE")
        with self.assertRaisesRegex(vault.ProvenanceRefused, "exists"):
            self.stage()
        self.assertTrue((self.dest / "STAGING_INCOMPLETE").exists())

    def test_marker_create_failure_preserves_unsafe_directory_for_manual_review(self):
        with patch.object(vault, "_write_quarantine_file",
                          side_effect=OSError("simulated disk refused marker")):
            with self.assertRaisesRegex(vault.ProvenanceRefused, "incomplete"):
                self.stage()
        self.assertTrue(self.dest.is_dir())
        self.assertFalse((self.dest / "STAGING_INCOMPLETE").exists())
        with self.assertRaisesRegex(vault.ProvenanceRefused, "unexpected"):
            vault.inspect_local_adoption_quarantine(self.dest)
        with self.assertRaisesRegex(vault.ProvenanceRefused, "exists"):
            self.stage()

    def test_staged_data_tamper_is_refused(self):
        self.stage()
        member = next((self.dest / "members").iterdir())
        member.write_bytes(b"tampered")
        with self.assertRaisesRegex(vault.ProvenanceRefused, "digest"):
            vault.inspect_local_adoption_quarantine(self.dest)

    def test_staged_manifest_or_receipt_tamper_is_refused(self):
        self.stage()
        rec = self.dest / "RECEIPT.json"
        content = json.loads(rec.read_text())
        content["release_approved"] = True
        rec.write_text(json.dumps(content))
        with self.assertRaises(vault.ProvenanceRefused):
            vault.inspect_local_adoption_quarantine(self.dest)

    def test_unexpected_extra_file_refused(self):
        self.stage()
        (self.dest / "unapproved").write_bytes(b"unreviewed")
        with self.assertRaisesRegex(vault.ProvenanceRefused, "unexpected"):
            vault.inspect_local_adoption_quarantine(self.dest)

    def test_symlinked_extra_member_refuses_even_without_native_privilege(self):
        self.stage()
        extra = self.dest / "members" / "unexpected.bin"
        extra.write_bytes(b"unapproved")
        original_is_symlink = Path.is_symlink
        with patch.object(Path, "is_symlink", autospec=True,
                          side_effect=lambda path: path == extra or original_is_symlink(path)):
            with self.assertRaisesRegex(vault.ProvenanceRefused, "symlink"):
                vault.inspect_local_adoption_quarantine(self.dest)

    def test_quarantine_renamed_without_manifest_update_is_refused(self):
        self.stage()
        renamed = self.parent / "different-candidate"
        self.dest.rename(renamed)
        with self.assertRaisesRegex(vault.ProvenanceRefused, "name"):
            vault.inspect_local_adoption_quarantine(renamed)

    def test_symlinked_staged_member_is_refused_where_os_permits(self):
        self.stage()
        member = next((self.dest / "members").iterdir())
        alias = member.with_name("extra.bin")
        try:
            alias.symlink_to(member)
        except (OSError, NotImplementedError):
            self.skipTest("native file symlink unavailable")
        with self.assertRaisesRegex(vault.ProvenanceRefused, "symlink"):
            vault.inspect_local_adoption_quarantine(self.dest)

    def test_no_externals_or_original_private_paths_in_receipt(self):
        self.stage()
        for file in (self.dest / "ADOPTION-MANIFEST.json", self.dest / "RECEIPT.json"):
            text = file.read_text()
            self.assertNotIn(str(self.base), text)
            self.assertNotIn("file://", text)
        report = vault.inspect_local_adoption_quarantine(self.dest)
        for key in ("native_muse_bound", "external_effect_authorized",
                    "redistribution_rights_verified", "source_owner_authenticated"):
            self.assertFalse(report[key])


if __name__ == "__main__":
    unittest.main()

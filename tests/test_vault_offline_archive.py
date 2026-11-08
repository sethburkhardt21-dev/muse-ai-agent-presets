"""R32.1d: offline export and create-only restore of LOCAL quarantine bytes.

Only synthetic source, a disposable owner-approved directory, and existing
source-level Evidence Finder. No original donor or native Muse effects.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch
import hashlib
import io
import json
import tempfile
import unittest
import zipfile

import muse_presets.provenance_vault as vault
from muse_presets.evidence_ledger import EvidenceLedger, EvidenceScope

NOW = datetime(2026, 11, 7, 20, 0, tzinfo=timezone.utc)


class OfflineArchiveTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="r32-offline-archive-")
        self.addCleanup(tmp.cleanup)
        self.base = Path(tmp.name).resolve()
        self.source = self.base / "synthetic-original"
        self.source.mkdir()
        (self.source / "nested").mkdir()
        (self.source / "first.txt").write_bytes(b"first synthetic original item\n")
        (self.source / "nested" / "second.bin").write_bytes(bytes(range(22)))
        self.quarantines = self.base / "quarantines"
        self.quarantines.mkdir()
        self.exports = self.base / "exports"
        self.exports.mkdir()
        self.restored = self.base / "restored"
        self.restored.mkdir()
        self.archive = self.exports / "candidate-1.zip"
        self.source_dir = self.quarantines / "candidate-1"
        self.restored_dir = self.restored / "candidate-1"
        scope = EvidenceScope(owner_id="synthetic-owner",
                              workspace_id="synthetic-work",
                              role_id="evidence-finder",
                              actor_id="synthetic-worker")
        with EvidenceLedger(self.base / "existing.sqlite3", authority=lambda:scope) as finder:
            finder.capture(self.source, "first.txt", "synthetic", operation_id="op1")
            head = finder.verify()
        seal = vault.make_local_source_seal(self.source, head, now=NOW)
        preview = vault.preview_local_adoption(
            self.source, seal, head,
            members=["first.txt", "nested/second.bin"], now=NOW)
        local = vault.stage_local_adoption_quarantine(
            self.source, preview, seal, head,
            quarantine_parent=self.quarantines, adoption_name="candidate-1",
            authorize_local_write=lambda src,parent,pin:src == self.source
                and parent == self.quarantines and pin == preview["preview_sha256"],
            now=NOW)
        self.assertEqual(local["status"], "LOCAL_QUARANTINE_STAGED")
        self.guard_log = []

    def grant_export(self, source, parent, pin):
        self.guard_log.append(("export",source,parent,pin))
        return source == self.source_dir and parent == self.exports and pin == \
            vault.inspect_local_adoption_quarantine(source)["manifest_sha256"]

    def grant_restore(self, archive, parent, pin):
        self.guard_log.append(("restore",archive,parent,pin))
        return archive == self.archive and parent == self.restored and pin == hashlib.sha256(self.archive.read_bytes()).hexdigest()

    def export(self, guard=None):
        return vault.export_local_quarantine_archive(
            self.source_dir, archive_path=self.archive,
            authorize_local_export=self.grant_export if guard is None else guard)

    def restore(self, seal=None, guard=None):
        if seal is None:
            seal = hashlib.sha256(self.archive.read_bytes()).hexdigest()
        return vault.restore_local_quarantine_archive(
            self.archive, restore_parent=self.restored,
            adoption_name="candidate-1", expected_sha256=seal,
            authorize_local_restore=self.grant_restore if guard is None else guard)

    def test_source_only_export_restore_exact_bytes_and_reopen(self):
        exported = self.export()
        self.assertEqual(exported["status"], "LOCAL_ARCHIVE_CREATED")
        self.assertTrue(self.archive.is_file())
        self.assertFalse(exported["native_muse_bound"])
        self.assertFalse(exported["redistribution_rights_verified"])
        self.assertFalse(exported["host_authority_authenticated"])
        self.assertEqual(exported["archive_sha256"],
                         hashlib.sha256(self.archive.read_bytes()).hexdigest())
        self.assertEqual(vault.inspect_local_quarantine_archive(
            self.archive, expected_sha256=exported["archive_sha256"])["status"],
            "LOCAL_ARCHIVE_VERIFIED")
        with zipfile.ZipFile(self.archive) as archive:
            self.assertEqual(len(archive.namelist()), 5)  # export manifest + 4 quarantine files
        # The source may be deleted: restoration is anchored in copied custody.
        (self.source / "first.txt").unlink()
        (self.source / "nested" / "second.bin").unlink()
        restored = self.restore(seal=exported["archive_sha256"])
        self.assertEqual(restored["status"], "LOCAL_QUARANTINE_RESTORED")
        self.assertFalse(restored["native_muse_bound"])
        self.assertFalse(restored["ready_to_install"])
        verified = vault.inspect_local_adoption_quarantine(self.restored_dir)
        self.assertEqual(verified["status"], "LOCAL_QUARANTINE_VERIFIED")
        self.assertEqual(verified["members_verified"], 2)
        orig_manifest = self.source_dir / "ADOPTION-MANIFEST.json"
        self.assertEqual((self.restored_dir / "ADOPTION-MANIFEST.json").read_bytes(),
                         orig_manifest.read_bytes())
        original = (self.source_dir / "members")
        recovered = (self.restored_dir / "members")
        self.assertEqual(sorted(p.name for p in original.iterdir()),
                         sorted(p.name for p in recovered.iterdir()))
        for member in original.iterdir():
            self.assertEqual(member.read_bytes(), (recovered / member.name).read_bytes())
        self.assertFalse((self.exports / "adoptions.json").exists())
        self.assertFalse((self.restored / "adoptions.json").exists())
        self.assertFalse((self.restored_dir / "STAGING_INCOMPLETE").exists())
        self.assertEqual([x[0] for x in self.guard_log], ["export","restore"])

    def test_staged_generic_vault_executes_bounded_export_restore(self):
        from importlib.util import spec_from_file_location, module_from_spec
        from muse_presets.engineering_pack import stage_engineer_pack,inspect_engineer_pack
        pack = self.base / "software-engineer-source-only"
        stage_engineer_pack(pack)
        module_path = pack / "runtime" / "provenance-vault" / "provenance_vault.py"
        spec = spec_from_file_location("r32_staged_archive", module_path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        plugin = module_from_spec(spec)
        spec.loader.exec_module(plugin)
        archived = plugin.export_local_quarantine_archive(
            self.source_dir, archive_path=self.archive,
            authorize_local_export=self.grant_export)
        self.assertEqual(archived["status"], "LOCAL_ARCHIVE_CREATED")
        restored = plugin.restore_local_quarantine_archive(
            self.archive, restore_parent=self.restored,
            adoption_name="candidate-1", expected_sha256=archived["archive_sha256"],
            authorize_local_restore=self.grant_restore)
        self.assertEqual(restored["status"], "LOCAL_QUARANTINE_RESTORED")
        self.assertEqual(plugin.inspect_local_adoption_quarantine(
            self.restored_dir)["status"], "LOCAL_QUARANTINE_VERIFIED")
        self.assertEqual(inspect_engineer_pack(pack)["status"], "LOCAL_MATCH")
        self.assertFalse(restored["ready_to_install"])

    def test_missing_and_deny_guards_refuse_without_files(self):
        for guard in (False, lambda *args:False, lambda *args:1,
                      lambda *args: (_ for _ in ()).throw(RuntimeError("deny"))):
            with self.subTest(guard=repr(guard)), self.assertRaisesRegex(vault.ProvenanceRefused, "guard"):
                self.export(guard)
        self.assertFalse(self.archive.exists())
        self.export()
        for guard in (False, lambda *args:False, lambda *args:1):
            with self.subTest(guard=repr(guard)), self.assertRaisesRegex(vault.ProvenanceRefused, "guard"):
                self.restore(guard=guard)
        self.assertFalse(self.restored_dir.exists())

    def test_existing_archive_and_restore_preserve_original_owner_data(self):
        self.archive.write_bytes(b"owner existing archive")
        with self.assertRaisesRegex(vault.ProvenanceRefused,"exists"):
            self.export()
        self.assertEqual(self.archive.read_bytes(), b"owner existing archive")
        self.archive.unlink()
        self.export()
        self.restored_dir.mkdir()
        owner = self.restored_dir / "MEMORY.md"
        owner.write_bytes(b"owner existing memory")
        with self.assertRaisesRegex(vault.ProvenanceRefused,"exists"):
            self.restore()
        self.assertEqual(owner.read_bytes(), b"owner existing memory")

    def test_wrong_archive_seal_and_tampered_archive_fail_before_restore(self):
        self.export()
        with self.assertRaisesRegex(vault.ProvenanceRefused,"digest"):
            self.restore(seal="f" * 64)
        self.assertFalse(self.restored_dir.exists())
        self.archive.write_bytes(self.archive.read_bytes() + b"changed")
        with self.assertRaises(vault.ProvenanceRefused):
            self.restore()
        self.assertFalse(self.restored_dir.exists())

    def _replace_entries(self, change):
        """Rewrite one synthetic ZIP; caller recomputes its digest to reach parser."""
        raw = {}
        with zipfile.ZipFile(self.archive) as z:
            for name in z.namelist():
                raw[name] = z.read(name)
        change(raw)
        with zipfile.ZipFile(self.archive, "w", compression=zipfile.ZIP_STORED) as out:
            for name, data in raw.items():
                out.writestr(name,data)

    def test_archive_prefix_and_comment_not_accepted_as_canonical(self):
        self.export()
        valid = self.archive.read_bytes()
        for raw in (b"prefix" + valid, valid + b"trailing",
                    valid[:-2] + b"\x01\x00" + b"x"):
            with self.subTest(length=len(raw)):
                self.archive.write_bytes(raw)
                with self.assertRaises(vault.ProvenanceRefused):
                    vault.inspect_local_quarantine_archive(
                        self.archive,
                        expected_sha256=hashlib.sha256(raw).hexdigest())
        self.assertFalse(self.restored_dir.exists())

    def test_forged_custody_metadata_refused_before_restore_destination(self):
        self.export()
        def forge(payload):
            manifest=json.loads(payload["ADOPTION-MANIFEST.json"])
            manifest["ready_to_install"]=True
            payload["ADOPTION-MANIFEST.json"]=(
                json.dumps(manifest,sort_keys=True)+"\n").encode("utf-8")
            exported=json.loads(payload["EXPORT-MANIFEST.json"])
            for entry in exported["files"]:
                if entry["path"]=="ADOPTION-MANIFEST.json":
                    entry["sha256"]=hashlib.sha256(payload["ADOPTION-MANIFEST.json"]).hexdigest()
                    entry["bytes"]=len(payload["ADOPTION-MANIFEST.json"])
            exported["original_manifest_sha256"]=hashlib.sha256(
                payload["ADOPTION-MANIFEST.json"]).hexdigest()
            payload["EXPORT-MANIFEST.json"]=json.dumps(
                exported,sort_keys=True).encode("utf-8")
        self._replace_entries(forge)
        with self.assertRaises(vault.ProvenanceRefused):
            self.restore()
        self.assertFalse(self.restored_dir.exists())

    def test_zip_slip_extra_member_refused_even_with_matching_new_archive_hash(self):
        self.export()
        self._replace_entries(lambda members:members.update({"../escaped.txt":b"unsafe"}))
        with self.assertRaisesRegex(vault.ProvenanceRefused,"unexpected|unsafe"):
            self.restore()
        self.assertFalse((self.base / "escaped.txt").exists())
        self.assertFalse(self.restored_dir.exists())

    def test_missing_unexpected_duplicate_and_symlink_archive_members_refused(self):
        self.export()
        with zipfile.ZipFile(self.archive) as z:
            blobs = [(i.filename, z.read(i)) for i in z.infolist()]
        cases = ["missing", "extra", "duplicate", "symlink", "compressed"]
        for case in cases:
            dest = self.exports / (case + ".zip")
            with zipfile.ZipFile(dest,"w",compression=zipfile.ZIP_STORED) as z:
                for name, raw in blobs:
                    if case == "missing" and name.startswith("members/"):
                        continue
                    info = zipfile.ZipInfo(name)
                    info.compress_type = zipfile.ZIP_DEFLATED if case=="compressed" else zipfile.ZIP_STORED
                    info.external_attr = ((0o120777 if case == "symlink" and name.startswith("members/")
                                           else 0o100600) << 16)
                    z.writestr(info, raw)
                if case == "extra":
                    z.writestr("extra.txt", b"new")
                if case == "duplicate":
                    z.writestr(blobs[0][0], blobs[0][1])
            with self.subTest(case=case), self.assertRaises(vault.ProvenanceRefused):
                vault.inspect_local_quarantine_archive(
                    dest, expected_sha256=hashlib.sha256(dest.read_bytes()).hexdigest())
        self.assertFalse(self.restored_dir.exists())

    def test_source_quarantine_tamper_refused_before_export_write(self):
        (self.source_dir / "members" / next((self.source_dir / "members").iterdir()).name).write_bytes(b"altered")
        with self.assertRaisesRegex(vault.ProvenanceRefused,"digest"):
            self.export()
        self.assertFalse(self.archive.exists())

    def test_concurrent_same_archive_name_only_one_wins(self):
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _:self._attempt_export(), range(2)))
        self.assertEqual(sorted(results), ["REFUSED","SUCCESS"])
        self.assertEqual(vault.inspect_local_quarantine_archive(
            self.archive,expected_sha256=hashlib.sha256(self.archive.read_bytes()).hexdigest())["status"],
                         "LOCAL_ARCHIVE_VERIFIED")

    def _attempt_export(self):
        try:
            self.export()
            return "SUCCESS"
        except vault.ProvenanceRefused:
            return "REFUSED"

    def test_interrupted_export_keeps_partial_archive_and_no_retry(self):
        def bad_write(*args,**kwargs):
            raise OSError("synthetic write interrupted")
        with patch.object(vault, "_archive_write_file", side_effect=bad_write):
            with self.assertRaisesRegex(vault.ProvenanceRefused,"incomplete"):
                self.export()
        self.assertTrue(self.archive.exists())
        with self.assertRaises(vault.ProvenanceRefused):
            self.export()
        with self.assertRaises(vault.ProvenanceRefused):
            vault.inspect_local_quarantine_archive(
                self.archive, expected_sha256=hashlib.sha256(self.archive.read_bytes()).hexdigest())

    def test_interrupted_restore_keeps_marker_without_auto_overwrite(self):
        self.export()
        before=vault._write_quarantine_file
        def broken(path,raw):
            if path.name.endswith(".bin"):
                raise OSError("synthetic restore failure")
            return before(path,raw)
        with patch.object(vault,"_write_quarantine_file",side_effect=broken):
            with self.assertRaisesRegex(vault.ProvenanceRefused,"incomplete"):
                self.restore()
        self.assertTrue((self.restored_dir/"STAGING_INCOMPLETE").is_file())
        self.assertEqual(vault.inspect_local_adoption_quarantine(self.restored_dir)["status"],"INCOMPLETE_STAGE")
        with self.assertRaisesRegex(vault.ProvenanceRefused,"exists"):
            self.restore()

    def test_invalid_archive_parent_symlink_ancestor_refused(self):
        alias = self.base / "linked-exports"
        try:
            alias.symlink_to(self.exports, target_is_directory=True)
        except (OSError,NotImplementedError):
            self.skipTest("native symlink creation restricted")
        with self.assertRaisesRegex(vault.ProvenanceRefused,"symlink"):
            vault.export_local_quarantine_archive(
                self.source_dir, archive_path=alias/"candidate-1.zip",
                authorize_local_export=lambda *args:True)
        self.assertFalse(self.archive.exists())

    def test_restoration_directory_cannot_be_source_quarantine(self):
        self.export()
        with self.assertRaises(vault.ProvenanceRefused):
            vault.restore_local_quarantine_archive(
                self.archive, restore_parent=self.source_dir,
                adoption_name="candidate-1",
                expected_sha256=hashlib.sha256(self.archive.read_bytes()).hexdigest(),
                authorize_local_restore=lambda *args:True)
        self.assertFalse((self.source_dir / "candidate-1").exists())

    def test_archive_manifest_forged_authority_refused(self):
        self.export()
        def mutate(payload):
            manifest=json.loads(payload["EXPORT-MANIFEST.json"])
            manifest["release_approved"]=True
            payload["EXPORT-MANIFEST.json"]=json.dumps(manifest).encode()
        self._replace_entries(mutate)
        with self.assertRaises(vault.ProvenanceRefused):
            self.restore()
        self.assertFalse(self.restored_dir.exists())


if __name__ == "__main__":
    unittest.main()

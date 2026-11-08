"""Local, source-derived Provenance Vault contracts; no native Muse effects."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from muse_presets.provenance_vault import (
    ProvenanceRefused, make_ref, parse_ref, verify_path_against_ref,
    declared_hashes, admit_manifest_pin,
)


class ProvenanceReferenceTests(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory(prefix="vault-port-")
        self.addCleanup(t.cleanup)
        self.base = Path(t.name)

    def test_canonical_pin_reference_roundtrip(self):
        digest = "ab" * 32
        ref = make_ref("release-1.tar.gz", digest.upper())
        self.assertEqual(ref, "release-1.tar.gz@sha256:" + digest)
        self.assertEqual(parse_ref(ref), ("release-1.tar.gz", digest))

    def test_refuse_bad_ref_or_name(self):
        for bad in ("", "release", "release@sha256:" + "f" * 63,
                    "bad/name@sha256:" + "f" * 64,
                    "release@SHA256:" + "f" * 64,
                    "release@sha256:" + "g" * 64):
            with self.subTest(bad=bad), self.assertRaises(ProvenanceRefused):
                parse_ref(bad)
        with self.assertRaises(ProvenanceRefused):
            make_ref("../secret", "a" * 64)

    def test_exact_bytes_match_and_no_mutation(self):
        p = self.base / "artifact.bin"
        p.write_bytes(b"\x00\x01\xff" * 7)
        raw = p.read_bytes()
        mtime = p.stat().st_mtime_ns
        ref = make_ref("artifact.bin", hashlib.sha256(raw).hexdigest())
        self.assertEqual(verify_path_against_ref(p, ref), ("artifact.bin", hashlib.sha256(raw).hexdigest()))
        self.assertEqual(p.read_bytes(), raw)
        self.assertEqual(p.stat().st_mtime_ns, mtime)

    def test_wrong_digest_and_name_are_not_accepted(self):
        p = self.base / "artifact.bin"
        p.write_bytes(b"alpha")
        with self.assertRaisesRegex(ProvenanceRefused, "digest mismatch"):
            verify_path_against_ref(p, make_ref(p.name, "0" * 64))
        ref = make_ref("renamed.bin", hashlib.sha256(b"alpha").hexdigest())
        with self.assertRaisesRegex(ProvenanceRefused, "name mismatch"):
            verify_path_against_ref(p, ref)
        self.assertEqual(verify_path_against_ref(p, ref, allow_name_mismatch=True)[0], "renamed.bin")

    def test_missing_and_directory_refused(self):
        ref = make_ref("artifact.bin", "f" * 64)
        for p in (self.base / "artifact.bin", self.base):
            with self.subTest(p=str(p)), self.assertRaises(ProvenanceRefused):
                verify_path_against_ref(p, ref)

    def test_symlink_artifact_refused_where_supported(self):
        target = self.base / "actual.bin"
        target.write_bytes(b"valid")
        link = self.base / "artifact.bin"
        try:
            link.symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest("OS does not permit test symlink")
        ref = make_ref(link.name, hashlib.sha256(b"valid").hexdigest())
        with self.assertRaisesRegex(ProvenanceRefused, "symlink"):
            verify_path_against_ref(link, ref)


class DonorManifestTests(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory(prefix="vault-manifest-")
        self.addCleanup(t.cleanup)
        self.base = Path(t.name)
        self.digest = hashlib.sha256(b"known donor bytes").hexdigest()
        self.registry = {
            "donors": [{"name": "approved-module", "status": "pinned_verified",
                        "observed_sha256": self.digest},
                       {"name": "not-approved", "status": "identified_not_pinned",
                        "observed_sha256": "b" * 64}]}
        self.manifest = self.base / "manifest.json"

    def _save(self, document):
        self.manifest.write_text(json.dumps(document), encoding="utf-8")

    def test_admit_manifest_against_verified_donor_and_fresh_bytes(self):
        self._save({"nested": {"source_sha256": self.digest}})
        raw = self.manifest.read_bytes()
        result = admit_manifest_pin("generic-manifest", self.manifest, self.registry)
        self.assertEqual(result["status"], "pinned_verified")
        self.assertEqual(result["observed_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(result["declared_bytes"], len(raw))
        self.assertEqual(result["local_path"], "manifest.json")
        self.assertNotIn(str(self.base), json.dumps(result))

    def test_nested_fields_and_unlabeled_values(self):
        self.assertEqual(declared_hashes(
            {"unrelated": self.digest, "members": [{"pin": self.digest}]}),
            [("members[0]/pin", self.digest)])

    def test_refuse_unpinned_donor_or_unknown_pin(self):
        for sha in ("b" * 64, "c" * 64):
            self._save({"source_sha256": sha})
            with self.assertRaisesRegex(ProvenanceRefused, "not resolving"):
                admit_manifest_pin("generic-manifest", self.manifest, self.registry)

    def test_refuse_missing_invalid_and_empty_manifest(self):
        with self.assertRaises(ProvenanceRefused):
            admit_manifest_pin("missing", self.base / "absent.json", self.registry)
        self.manifest.write_text("{", encoding="utf-8")
        with self.assertRaises(ProvenanceRefused):
            admit_manifest_pin("bad", self.manifest, self.registry)
        self._save({"info": "no pins"})
        with self.assertRaises(ProvenanceRefused):
            admit_manifest_pin("none", self.manifest, self.registry)

    def test_malformed_explicit_digest_cannot_be_masked_by_valid_pin(self):
        self._save({"source_sha256": self.digest, "release_sha256": "z" * 64})
        with self.assertRaisesRegex(ProvenanceRefused, "malformed"):
            admit_manifest_pin("generic-manifest", self.manifest, self.registry)

    def test_reject_duplicate_manifest_keys(self):
        self.manifest.write_text(
            '{"source_sha256":"' + self.digest + '",'
            '"source_sha256":"' + self.digest + '"}', encoding="utf-8")
        with self.assertRaisesRegex(ProvenanceRefused, "duplicate"):
            admit_manifest_pin("generic-manifest", self.manifest, self.registry)

    def test_reject_nonstandard_json_constants(self):
        self.manifest.write_text(
            '{"source_sha256":"' + self.digest + '","measure":NaN}', encoding="utf-8")
        with self.assertRaises(ProvenanceRefused):
            admit_manifest_pin("generic-manifest", self.manifest, self.registry)

    def test_reject_bad_explicit_pin_without_masking(self):
        for label in ("sha256", "digest", "pin", "release_pin"):
            with self.subTest(label=label):
                self._save({"source_sha256": self.digest, label: "not-a-digest"})
                with self.assertRaisesRegex(ProvenanceRefused, "malformed"):
                    admit_manifest_pin("generic-manifest", self.manifest, self.registry)

    def test_manifest_symlink_refused_where_supported(self):
        target = self.base / "target.json"
        target.write_text(json.dumps({"source_sha256": self.digest}), encoding="utf-8")
        try:
            self.manifest.symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest("OS does not permit test symlink")
        with self.assertRaisesRegex(ProvenanceRefused, "symlink"):
            admit_manifest_pin("generic-manifest", self.manifest, self.registry)

    def test_unverified_label_is_not_a_signed_rights_grant(self):
        self._save({"source_sha256": self.digest})
        result = admit_manifest_pin("generic-manifest", self.manifest, self.registry)
        self.assertEqual(result["evidence_grade"], "LOCAL_BYTES_ONLY")
        self.assertFalse(result["donor_files_reverified"])
        self.assertFalse(result["registry_authenticated"])
        self.assertFalse(result["source_owner_authenticated"])
        self.assertFalse(result["redistribution_rights_verified"])
        self.assertFalse(result["native_authority_verified"])


if __name__ == "__main__":
    unittest.main()



class VaultPackIntegrationTests(unittest.TestCase):
    def setUp(self):
        from muse_presets import engineering_pack
        self.pack = engineering_pack
        temp = tempfile.TemporaryDirectory(prefix="vault-stage-")
        self.addCleanup(temp.cleanup)
        self.base = Path(temp.name)
        self.target = self.base / "new-software-engineer"

    def test_pack_preflight_pins_vault_source_and_skill_before_creation(self):
        result = self.pack.preview_engineer_pack()
        self.assertEqual(result["provenance_runtime_modules"], 1)
        self.assertEqual(result["provenance_rights_verified"], False)
        self.assertFalse(self.target.exists())

    def test_create_only_pack_stages_executable_vault_and_pinned_skill(self):
        staged = self.pack.stage_engineer_pack(self.target)
        self.assertFalse(staged["native_installed"])
        source = self.target / "runtime" / "provenance-vault" / "provenance_vault.py"
        self.assertTrue(source.is_file())
        skill = self.target / "skills" / "provenance-vault" / "SKILL.md"
        self.assertTrue(skill.is_file())
        receipt = json.loads((self.target / "receipts" / "PACK_RECEIPT.json").read_text())
        self.assertFalse(receipt["provenance_rights_verified"])
        self.assertEqual(receipt["native_muse_status"], "UNBOUND")
        self.assertIn("runtime/provenance-vault/provenance_vault.py", receipt["files_sha256"])
        self.assertEqual(receipt["files_sha256"]["runtime/provenance-vault/provenance_vault.py"],
                         hashlib.sha256(source.read_bytes()).hexdigest())
        self.assertEqual(self.pack.inspect_engineer_pack(self.target)["status"], "LOCAL_MATCH")

    def test_vault_source_tamper_rejected_before_destination_exists(self):
        bad = self.base / "modified_source.py"
        bad.write_text("print('unreviewed source')", encoding="utf-8")
        with patch.object(self.pack, "VAULT_SOURCE", bad):
            with self.assertRaisesRegex(ValueError, "SOURCE_PIN_MISMATCH"):
                self.pack.stage_engineer_pack(self.target)
        self.assertFalse(self.target.exists())

    def test_vault_skill_tamper_rejected_before_destination_exists(self):
        import shutil
        tampered = self.base / "skill"
        shutil.copytree(self.pack.VAULT_SKILL_ROOT, tampered)
        (tampered / "SKILL.md").write_text("Unsafe changed instructions", encoding="utf-8")
        with patch.object(self.pack, "VAULT_SKILL_ROOT", tampered):
            with self.assertRaisesRegex(ValueError, "SOURCE_PIN_MISMATCH"):
                self.pack.stage_engineer_pack(self.target)
        self.assertFalse(self.target.exists())

    def test_staged_vault_policy_change_requires_review(self):
        self.pack.stage_engineer_pack(self.target)
        path = self.target / "runtime" / "provenance-vault" / "provenance_vault.py"
        path.write_bytes(path.read_bytes() + b"\n# changed\n")
        res = self.pack.inspect_engineer_pack(self.target)
        self.assertEqual(res["status"], "REVIEW_REQUIRED")
        self.assertIn("runtime/provenance-vault/provenance_vault.py",
                      res["policy_modified"])

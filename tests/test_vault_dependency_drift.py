"""R32.1e read-only donor drift and dependent quarantine invalidation plan.

Source pin and Evidence Finder receipt are local observations, not authenticated
donor identity, signature, or a native permission. No registry writes.
"""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from pathlib import Path
import hashlib
import json
import tempfile
import unittest
from unittest.mock import patch

import muse_presets.provenance_vault as vault
from muse_presets.evidence_ledger import EvidenceLedger, EvidenceScope

NOW = datetime(2026, 11, 7, 21, 0, tzinfo=timezone.utc)


class LocalDependencyDriftTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="r32-drift-")
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name).resolve()
        self.parent = self.base / "local-quarantines"
        self.parent.mkdir()
        self.src = self.base / "donor-1"
        self.src.mkdir()
        (self.src / "proof.txt").write_bytes(b"original donor one bytes\n")
        self.scope = EvidenceScope(owner_id="demo-owner", workspace_id="demo-work",
                                   role_id="evidence-finder", actor_id="demo-reviewer")
        self.db = self.base / "finder.sqlite3"
        with self.finder() as ledger:
            ledger.capture(self.src, "proof.txt", "original", operation_id="first")
            self.head = ledger.verify()
        self.seal = vault.make_local_source_seal(self.src, self.head,
                                                 ttl_seconds=1800, now=NOW)
        self.preview = vault.preview_local_adoption(
            self.src, self.seal, self.head, members=["proof.txt"], now=NOW)
        self.destination = self.parent / "candidate-1"
        self.stage()

    def finder(self):
        return EvidenceLedger(self.db, authority=lambda:self.scope)

    def stage(self):
        result = vault.stage_local_adoption_quarantine(
            self.src, self.preview, self.seal, self.head,
            quarantine_parent=self.parent, adoption_name="candidate-1",
            authorize_local_write=lambda src, parent, pin:
                src==self.src and parent==self.parent and pin==self.preview["preview_sha256"],
            now=NOW)
        self.assertEqual(result["status"], "LOCAL_QUARANTINE_STAGED")

    def assess(self, **kwargs):
        return vault.assess_local_quarantine_dependency(
            kwargs.get("root", self.src), kwargs.get("preview", self.preview),
            kwargs.get("seal", self.seal), kwargs.get("head", self.head),
            quarantine_destination=kwargs.get("destination", self.destination),
            now=kwargs.get("now", NOW))

    def test_verified_dependency_remains_local_and_does_not_mutate_original(self):
        before = [(p, p.read_bytes(), p.stat().st_mtime_ns) for p in
                  [self.src/"proof.txt", self.db, self.destination/"RECEIPT.json",
                   self.destination/"ADOPTION-MANIFEST.json"]]
        result = self.assess()
        self.assertEqual(result["status"], "LOCAL_DEPENDENCY_CURRENT")
        self.assertEqual(result["reason"], "CURRENT_SOURCE_AND_EVIDENCE")
        self.assertEqual(result["adoption_name"], "candidate-1")
        self.assertEqual(result["quarantine_manifest_sha256"],
                         vault.inspect_local_adoption_quarantine(self.destination)["manifest_sha256"])
        self.assertFalse(result["invalidation_recommended"])
        self.assertFalse(result["hold_required"])
        for flag in ("registry_modified", "native_muse_bound",
                     "owner_authenticated", "external_effect_authorized",
                     "redistribution_rights_verified", "release_approved"):
            self.assertFalse(result[flag])
        self.assertNotIn(str(self.base), json.dumps(result))
        self.assertFalse((self.parent / "adoptions.json").exists())
        for p, contents, stamp in before:
            self.assertEqual(p.read_bytes(), contents)
            self.assertEqual(p.stat().st_mtime_ns, stamp)

    def test_actual_changed_file_detects_local_invalidation_without_registry_write(self):
        copied = (self.destination/"RECEIPT.json").read_bytes()
        (self.src/"proof.txt").write_bytes(b"changed donor one bytes\n")
        result = self.assess()
        self.assertEqual(result["status"], "LOCAL_INVALIDATION_RECOMMENDED")
        self.assertEqual(result["reason"], "SOURCE_CONTENT_CHANGED")
        self.assertTrue(result["invalidation_recommended"])
        self.assertTrue(result["hold_required"])
        self.assertFalse(result["registry_modified"])
        self.assertEqual((self.destination/"RECEIPT.json").read_bytes(), copied)
        self.assertEqual(vault.inspect_local_adoption_quarantine(
            self.destination)["status"], "LOCAL_QUARANTINE_VERIFIED")

    def test_added_source_file_is_conservative_drift(self):
        (self.src/"new.txt").write_bytes(b"new donor context")
        result = self.assess()
        self.assertEqual(result["status"], "LOCAL_INVALIDATION_RECOMMENDED")
        self.assertEqual(result["reason"], "SOURCE_CONTENT_CHANGED")

    def test_missing_or_unreachable_source_is_hold_not_confirmed_drift(self):
        (self.src/"proof.txt").unlink()
        result = self.assess()
        self.assertEqual(result["status"], "LOCAL_REVIEW_REQUIRED")
        self.assertEqual(result["reason"], "SOURCE_UNAVAILABLE_OR_UNVERIFIED")
        self.assertFalse(result["invalidation_recommended"])
        self.assertTrue(result["hold_required"])

    def test_finder_appended_receipt_requires_review_not_false_donor_drift(self):
        with self.finder() as f:
            f.capture(self.src, "proof.txt", "changed-observation", operation_id="second")
            fresh = f.verify()
        result = self.assess(head=fresh)
        self.assertEqual(result["status"], "LOCAL_REVIEW_REQUIRED")
        self.assertEqual(result["reason"], "EVIDENCE_HEAD_CHANGED")
        self.assertFalse(result["invalidation_recommended"])

    def test_forged_or_wrong_evidence_scope_is_hold(self):
        fake = {**self.head, "scope":{**self.head["scope"], "owner_id":"other-owner"}}
        result = self.assess(head=fake)
        self.assertEqual(result["status"], "LOCAL_REVIEW_REQUIRED")
        self.assertEqual(result["reason"], "EVIDENCE_SCOPE_CHANGED")
        fake = {**self.head, "recipient_acknowledged":True}
        result = self.assess(head=fake)
        self.assertEqual(result["status"], "LOCAL_REVIEW_REQUIRED")
        self.assertEqual(result["reason"], "EVIDENCE_UNVERIFIED")

    def test_corrupted_quarantine_holds_even_when_source_has_changed(self):
        (self.src/"proof.txt").write_bytes(b"changed")
        (self.destination/"RECEIPT.json").write_bytes(b"corrupted")
        result = self.assess()
        self.assertEqual(result["status"], "LOCAL_REVIEW_REQUIRED")
        self.assertEqual(result["reason"], "QUARANTINE_UNVERIFIED")
        self.assertFalse(result["invalidation_recommended"])

    def test_missing_and_incomplete_quarantine_hold(self):
        missing = self.parent / "not-present"
        result = self.assess(destination=missing)
        self.assertEqual(result["status"], "LOCAL_REVIEW_REQUIRED")
        self.assertEqual(result["reason"], "QUARANTINE_UNVERIFIED")
        (self.destination/"STAGING_INCOMPLETE").write_bytes(b"held")
        result = self.assess()
        self.assertEqual(result["reason"], "QUARANTINE_UNVERIFIED")

    def test_unrelated_quarantine_and_forged_preview_refuse(self):
        other_preview = vault.preview_local_adoption(
            self.src, self.seal, self.head, members=["proof.txt"], now=NOW)
        forged = {**other_preview, "preview_sha256":"a"*64}
        self.assertEqual(self.assess(preview=forged)["reason"], "PREVIEW_UNVERIFIED")
        forged = {**self.preview, "ready_to_install":True}
        self.assertEqual(self.assess(preview=forged)["reason"], "PREVIEW_UNVERIFIED")
        forged = {**self.seal, "source_owner_authenticated":True}
        self.assertEqual(self.assess(seal=forged)["reason"], "SEAL_UNVERIFIED")

    def test_expiry_and_rollback_seal_refuse_without_invalidation(self):
        out = self.assess(now=NOW+timedelta(hours=3))
        self.assertEqual(out["status"], "LOCAL_REVIEW_REQUIRED")
        self.assertEqual(out["reason"], "SEAL_EXPIRED_OR_INVALID")
        self.assertFalse(out["invalidation_recommended"])
        forged = {**self.seal, "version":-1}
        self.assertEqual(self.assess(seal=forged)["reason"], "SEAL_UNVERIFIED")

    def test_no_untrusted_directory_path_can_leak_or_grant_effect(self):
        result = self.assess(root=self.base/"notfound")
        self.assertNotIn(str(self.base), json.dumps(result))
        for name in ("native_muse_bound", "external_effect_authorized",
                     "registry_modified", "release_approved"):
            self.assertFalse(result[name])

    def test_batch_is_selective_across_separate_donors_and_idempotent(self):
        src2 = self.base/"donor-2"
        src2.mkdir()
        (src2/"other.txt").write_bytes(b"other donor")
        db2 = self.base/"finder-two.sqlite3"
        with EvidenceLedger(db2,authority=lambda:self.scope) as f:
            f.capture(src2,"other.txt","other",operation_id="other1")
            head2 = f.verify()
        seal2 = vault.make_local_source_seal(src2,head2,now=NOW)
        preview2 = vault.preview_local_adoption(src2,seal2,head2,members=["other.txt"],now=NOW)
        dest2 = self.parent/"candidate-2"
        vault.stage_local_adoption_quarantine(
            src2,preview2,seal2,head2,quarantine_parent=self.parent,
            adoption_name="candidate-2",
            authorize_local_write=lambda source,parent,pin:
                source==src2 and parent==self.parent and pin==preview2["preview_sha256"],
            now=NOW)
        (src2/"other.txt").write_bytes(b"drifted donor")
        entries = [
            {"name":"candidate-1", "root":self.src, "preview":self.preview,
             "seal":self.seal,"head":self.head, "destination":self.destination},
            {"name":"candidate-2", "root":src2, "preview":preview2,
             "seal":seal2,"head":head2, "destination":dest2},
        ]
        first = vault.review_local_dependent_quarantines(entries,now=NOW)
        second = vault.review_local_dependent_quarantines(entries,now=NOW)
        self.assertEqual(first,second)
        self.assertEqual(first["status"], "LOCAL_HOLD_REQUIRED")
        self.assertEqual(first["invalidation_recommended"], ["candidate-2"])
        self.assertEqual(first["current"], ["candidate-1"])
        self.assertEqual(first["review_required"], [])
        self.assertFalse(first["registry_modified"])
        self.assertFalse((self.parent/"adoptions.json").exists())
        self.assertEqual(vault.inspect_local_adoption_quarantine(dest2)["status"],
                         "LOCAL_QUARANTINE_VERIFIED")
        with self.assertRaisesRegex(vault.ProvenanceRefused,"duplicate"):
            vault.review_local_dependent_quarantines(entries+[entries[0]],now=NOW)

    def test_batch_rejects_wrong_scope_and_unknown_records_without_effect(self):
        bad = [{"name":"../../x","root":self.src,"seal":self.seal,
                "preview":self.preview,"head":self.head,"destination":self.destination}]
        with self.assertRaises(vault.ProvenanceRefused):
            vault.review_local_dependent_quarantines(bad,now=NOW)
        for value in (None, {}, True, [], "name", list(range(33))):
            with self.subTest(value=repr(value)),self.assertRaises(vault.ProvenanceRefused):
                vault.review_local_dependent_quarantines(value,now=NOW)

    def test_preexisting_registry_is_never_rewritten_even_when_source_drifts(self):
        registry = self.parent / "adoptions.json"
        registry.write_bytes(b'{"existing":"owner-protected","status":"ADOPTED"}')
        previous = registry.read_bytes()
        modified_at = registry.stat().st_mtime_ns
        self.assertEqual(self.assess()["status"], "LOCAL_DEPENDENCY_CURRENT")
        (self.src/"proof.txt").write_bytes(b"changed")
        self.assertEqual(self.assess()["status"], "LOCAL_INVALIDATION_RECOMMENDED")
        self.assertEqual(registry.read_bytes(), previous)
        self.assertEqual(registry.stat().st_mtime_ns, modified_at)

    def test_advanced_evidence_and_changed_source_is_review_hold_not_false_verdict(self):
        (self.src/"proof.txt").write_bytes(b"changed source bytes")
        with self.finder() as f:
            f.capture(self.src,"proof.txt","changed",operation_id="revision")
            advanced=f.verify()
        result=self.assess(head=advanced)
        self.assertEqual(result["status"],"LOCAL_REVIEW_REQUIRED")
        self.assertEqual(result["reason"],"EVIDENCE_HEAD_CHANGED")
        self.assertFalse(result["invalidation_recommended"])

    def test_batch_mismatched_candidate_name_refused_before_state_change(self):
        entry={"name":"candidate-OTHER","root":self.src,
               "seal":self.seal,"preview":self.preview,
               "head":self.head,"destination":self.destination}
        with self.assertRaisesRegex(vault.ProvenanceRefused,"mismatched"):
            vault.review_local_dependent_quarantines([entry],now=NOW)

    def test_symlinked_source_root_is_review_hold_where_supported(self):
        alias=self.base/"source-link"
        try:
            alias.symlink_to(self.src,target_is_directory=True)
        except (OSError,NotImplementedError):
            self.skipTest("symlink privilege unavailable")
        result=self.assess(root=alias)
        self.assertEqual(result["status"],"LOCAL_REVIEW_REQUIRED")
        self.assertEqual(result["reason"],"SOURCE_UNAVAILABLE_OR_UNVERIFIED")
        self.assertFalse(result["invalidation_recommended"])

    def test_staged_vault_exposes_read_only_dependency_review(self):
        from importlib.util import module_from_spec, spec_from_file_location
        from muse_presets.engineering_pack import stage_engineer_pack,inspect_engineer_pack
        dest = self.base/"new-engineer-pack"
        stage_engineer_pack(dest)
        module_path = dest/"runtime/provenance-vault/provenance_vault.py"
        spec = spec_from_file_location("staged_drift",module_path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        mod = module_from_spec(spec)
        spec.loader.exec_module(mod)
        assessment = mod.assess_local_quarantine_dependency(
            self.src,self.preview,self.seal,self.head,
            quarantine_destination=self.destination,now=NOW)
        self.assertEqual(assessment["status"],"LOCAL_DEPENDENCY_CURRENT")
        self.assertEqual(inspect_engineer_pack(dest)["status"],"LOCAL_MATCH")
        self.assertFalse((self.parent/"adoptions.json").exists())


if __name__=="__main__":
    unittest.main()

"""R32.1b: honest unsigned source statements and adoption read-only plans.

Every source and Evidence Finder receipt is synthetic. No native Muse actions.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from muse_presets.evidence_ledger import EvidenceLedger, EvidenceScope
from muse_presets.provenance_vault import (
    ProvenanceRefused,
    make_local_source_seal, make_unsigned_local_statement,
    verify_unsigned_local_statement, preview_local_adoption,
    verify_local_adoption_preview,
)

NOW = datetime(2026, 11, 7, 18, 0, tzinfo=timezone.utc)


class VaultStatementAndAdoptionTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="r32-statement-")
        self.addCleanup(temp.cleanup)
        self.base = Path(temp.name).resolve()
        self.sources = self.base / "sources"
        self.sources.mkdir()
        (self.sources / "nested").mkdir()
        (self.sources / "one.txt").write_bytes(b"first evidence alpha\n")
        (self.sources / "nested" / "two.txt").write_bytes(b"second independent item\n")
        self.db = self.base / "evidence.sqlite3"
        self.scope = EvidenceScope(
            owner_id="synthetic-owner", workspace_id="synthetic-workspace",
            role_id="evidence-finder", actor_id="synthetic-actor"
        )
        with self.ledger() as ledger:
            ledger.capture(self.sources, "one.txt", "alpha", operation_id="read-1")
            self.head = ledger.verify()
        self.seal = make_local_source_seal(self.sources, self.head,
                                           version=2, ttl_seconds=3600, now=NOW)

    def ledger(self):
        return EvidenceLedger(self.db, authority=lambda: self.scope)

    def statement(self):
        return make_unsigned_local_statement(self.sources, self.seal,
                                              self.head, now=NOW)

    def preview(self, members=None):
        return preview_local_adoption(self.sources, self.seal, self.head,
                                      members=["one.txt"] if members is None else members,
                                      now=NOW)

    def test_statement_roundtrip_contains_original_actual_source_digests(self):
        statement = self.statement()
        self.assertEqual(statement["_type"], "https://in-toto.io/Statement/v1")
        self.assertEqual(statement["status"], "UNSIGNED_LOCAL_OBSERVATION")
        self.assertEqual(statement["signature_status"], "UNSIGNED_NOT_DSSE")
        self.assertFalse(statement["issuer_authenticated"])
        self.assertFalse(statement["source_owner_authenticated"])
        self.assertFalse(statement["publication_authorized"])
        self.assertFalse(statement["recipient_acknowledged"])
        self.assertEqual([r["name"] for r in statement["subject"]],
                         ["nested/two.txt", "one.txt"])
        by_name = {r["name"]: r for r in statement["subject"]}
        self.assertEqual(by_name["one.txt"]["digest"]["sha256"],
                         hashlib.sha256(b"first evidence alpha\n").hexdigest())
        self.assertEqual(by_name["one.txt"]["annotations"]["bytes"], 21)
        self.assertEqual(statement["predicate"]["seal_sha256"],
                         self.seal["seal_sha256"])
        self.assertEqual(statement["predicate"]["existing_evidence_head_sha256"],
                         self.head["head_chain_sha256"])
        self.assertNotIn(str(self.base), json.dumps(statement))
        verified = verify_unsigned_local_statement(self.sources, statement,
                                                    self.seal, self.head, now=NOW)
        self.assertEqual(verified["status"], "LOCAL_UNSIGNED_STATEMENT_MATCH")
        self.assertFalse(verified["signatures_verified"])
        self.assertFalse(verified["native_muse_bound"])

    def test_duplicate_missing_unexpected_and_reordered_subject_refused(self):
        value = self.statement()
        for bad_subjects in (
            [value["subject"][0], value["subject"][0]],
            value["subject"][:1],
            value["subject"] + [{"name": "stowaway.txt",
                                   "digest": {"sha256": "a" * 64}}],
            list(reversed(value["subject"])),
        ):
            with self.subTest(count=len(bad_subjects)):
                modified = {**value, "subject": bad_subjects}
                with self.assertRaisesRegex(ProvenanceRefused, "statement"):
                    verify_unsigned_local_statement(self.sources, modified,
                                                    self.seal, self.head, now=NOW)

    def test_forged_signatures_and_attested_role_refused(self):
        statement = self.statement()
        for key, new in (
            ("signature_status", "SIGNED_VERIFIED"),
            ("issuer_authenticated", True),
            ("source_owner_authenticated", True),
            ("publication_authorized", True),
            ("recipient_acknowledged", True),
            ("signatures", ["forged-signature"]),
        ):
            with self.subTest(field=key):
                forged = {**statement, key: new}
                with self.assertRaises(ProvenanceRefused):
                    verify_unsigned_local_statement(self.sources, forged,
                                                    self.seal, self.head, now=NOW)

    def test_statement_payload_mutation_and_forged_local_hash_refused(self):
        statement = self.statement()
        altered = json.loads(json.dumps(statement))
        altered["predicate"]["existing_evidence_head_sha256"] = "f" * 64
        with self.assertRaises(ProvenanceRefused):
            verify_unsigned_local_statement(self.sources, altered,
                                            self.seal, self.head, now=NOW)
        altered = json.loads(json.dumps(statement))
        altered["subject"][0]["digest"]["sha256"] = "f" * 64
        with self.assertRaises(ProvenanceRefused):
            verify_unsigned_local_statement(self.sources, altered,
                                            self.seal, self.head, now=NOW)

    def test_expired_or_changed_source_or_changed_evidence_head_refuses_statement(self):
        statement = self.statement()
        with self.assertRaisesRegex(ProvenanceRefused, "expired"):
            verify_unsigned_local_statement(self.sources, statement,
                self.seal, self.head, now=NOW + timedelta(hours=2))
        (self.sources / "one.txt").write_bytes(b"altered source bytes")
        with self.assertRaisesRegex(ProvenanceRefused, "source"):
            verify_unsigned_local_statement(self.sources, statement,
                                            self.seal, self.head, now=NOW)

    def test_preview_lists_exact_pinned_members_no_copy_and_no_authority(self):
        before = {p: (p.read_bytes(), p.stat().st_mtime_ns)
                  for p in (self.sources / "one.txt", self.sources / "nested" / "two.txt")}
        preview = self.preview(members=["nested/two.txt", "one.txt"])
        self.assertEqual(preview["status"], "LOCAL_ADOPTION_PREVIEW_ONLY")
        self.assertEqual([p["relative_path"] for p in preview["members"]],
                         ["nested/two.txt", "one.txt"])
        self.assertEqual(preview["source_seal_sha256"], self.seal["seal_sha256"])
        self.assertEqual(preview["source_evidence_head_sha256"],
                         self.head["head_chain_sha256"])
        self.assertFalse(preview["ready_to_install"])
        self.assertFalse(preview["owner_authenticated"])
        self.assertFalse(preview["redistribution_rights_verified"])
        self.assertFalse(preview["external_effect_authorized"])
        self.assertNotIn(str(self.base), json.dumps(preview))
        res = verify_local_adoption_preview(self.sources, preview, self.seal,
                                             self.head, now=NOW)
        self.assertEqual(res["status"], "LOCAL_ADOPTION_PREVIEW_MATCH")
        self.assertFalse(res["release_approved"])
        for path, (raw, stamp) in before.items():
            self.assertEqual(path.read_bytes(), raw)
            self.assertEqual(path.stat().st_mtime_ns, stamp)
        self.assertFalse((self.base / "adoptions").exists())
        self.assertFalse((self.sources / "adoptions.json").exists())

    def test_adoption_invalid_relative_paths_and_duplicates_refused(self):
        invalid = [[], ["one.txt", "one.txt"], ["../secret.txt"], ["/absolute"],
                   ["nested\\two.txt"], ["nested//two.txt"], ["nested/../one.txt"],
                   ["missing.txt"], ["."], ["a:b"], ["nested"], ["one.txt", ".hidden"]]
        for members in invalid:
            with self.subTest(members=members), self.assertRaises(ProvenanceRefused):
                self.preview(members)

    def test_forged_preview_fields_and_missing_member_are_refused(self):
        preview = self.preview()
        for key, new in (("ready_to_install", True),
                         ("owner_authenticated", True),
                         ("redistribution_rights_verified", True),
                         ("authorization_status", "APPROVED"),
                         ("source_evidence_head_sha256", "f" * 64)):
            with self.subTest(field=key):
                forged = {**preview, key: new}
                with self.assertRaises(ProvenanceRefused):
                    verify_local_adoption_preview(self.sources, forged,
                                                  self.seal, self.head, now=NOW)
        (self.sources / "one.txt").unlink()
        with self.assertRaises(ProvenanceRefused):
            verify_local_adoption_preview(self.sources, preview,
                                          self.seal, self.head, now=NOW)

    def test_untrusted_finder_scope_cannot_be_spoofed(self):
        altered = dict(self.head)
        altered["scope"] = {**self.head["scope"], "owner_id": "other-owner"}
        with self.assertRaisesRegex(ProvenanceRefused, "scope"):
            make_unsigned_local_statement(self.sources, self.seal, altered, now=NOW)
        with self.assertRaisesRegex(ProvenanceRefused, "scope"):
            preview_local_adoption(self.sources, self.seal, altered,
                                   members=["one.txt"], now=NOW)

    def test_control_characters_and_oversized_member_names_refuse(self):
        from muse_presets.provenance_vault import _adoption_member_name
        for candidate in ("unsafe\nname", "unsafe\rname", "unsafe\tname",
                          "unpaired\ud800", "a" * 600):
            with self.subTest(name_repr=repr(candidate)):
                with self.assertRaisesRegex(ProvenanceRefused, "member"):
                    _adoption_member_name(candidate)

    def test_invalid_preview_types_refuse_before_manifest(self):
        for members in (None, "one.txt", True, 1, [1], ["one.txt", None]):
            with self.subTest(members=members), self.assertRaises(ProvenanceRefused):
                preview_local_adoption(self.sources, self.seal, self.head,
                                       members=members, now=NOW)
        with self.assertRaises(ProvenanceRefused):
            verify_local_adoption_preview(self.sources, {"members": True},
                                          self.seal, self.head, now=NOW)

    def test_staged_vault_exposes_live_local_statement_and_adoption_preview(self):
        from importlib.util import spec_from_file_location, module_from_spec
        from muse_presets.engineering_pack import stage_engineer_pack, inspect_engineer_pack
        destination = self.base / "new-staged-engineer"
        result = stage_engineer_pack(destination)
        self.assertFalse(result["native_installed"])
        module_path = destination / "runtime" / "provenance-vault" / "provenance_vault.py"
        spec = spec_from_file_location("independent_staged_source_provenance", module_path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        statement = module.make_unsigned_local_statement(
            self.sources, self.seal, self.head, now=NOW)
        self.assertEqual(statement["signature_status"], "UNSIGNED_NOT_DSSE")
        adoption = module.preview_local_adoption(self.sources, self.seal, self.head,
                                                   members=["one.txt"], now=NOW)
        checked = module.verify_local_adoption_preview(
            self.sources, adoption, self.seal, self.head, now=NOW)
        self.assertEqual(checked["status"], "LOCAL_ADOPTION_PREVIEW_MATCH")
        self.assertEqual(inspect_engineer_pack(destination)["status"], "LOCAL_MATCH")
        self.assertFalse((destination / "adoptions.json").exists())

    def test_actual_posix_claim_gate_holds_preview_without_executing_it(self):
        import os
        import subprocess
        import sys
        if os.name != "posix":
            self.skipTest("existing Claim Gate requires POSIX fcntl")
        from muse_presets.engineering_pack import stage_engineer_pack
        stage = self.base / "candidate-pack"
        stage_engineer_pack(stage)
        content = self.preview()
        inputs = self.base / "synthetic-claim-input"
        inputs.mkdir()
        (inputs / "preview.json").write_text(
            json.dumps(content, sort_keys=True), encoding="utf-8")
        state = self.base / "claim-state"
        state.mkdir()
        cli = stage / "runtime" / "claim-gate" / "engineering_claim_gate.py"

        def run(action, *args):
            cmd = [sys.executable, "-I", "-B", str(cli), "--state-dir", str(state),
                   "--scope", "engineering", "--claim-id", "preview-only", action, *args]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            return json.loads(result.stdout)

        first = run("claim", "--source-root", str(inputs),
                    "--payload", "preview.json")
        replay = run("claim", "--source-root", str(inputs),
                     "--payload", "preview.json")
        held = run("hold-unknown", "--reason", "no provider recipient observed")
        inspected = run("inspect")
        self.assertEqual(first["status"], "LOCAL_CLAIM_RECORDED")
        self.assertEqual(replay["status"], "LOCAL_CLAIM_REUSED")
        self.assertEqual(held["state"], "UNKNOWN")
        self.assertEqual(inspected["state"], "UNKNOWN")
        self.assertFalse(inspected["external_effect_authorized"])
        self.assertFalse(inspected["native_muse_invoked"])
        self.assertFalse((stage / "adoptions").exists())

    def test_adoption_preview_symlinked_member_refused_on_posix(self):
        alias = self.sources / "alias.txt"
        try:
            alias.symlink_to(self.sources / "one.txt")
        except (OSError, NotImplementedError):
            self.skipTest("host does not permit symlink fixture")
        with self.assertRaisesRegex(ProvenanceRefused, "symlink"):
            self.preview(["alias.txt"])

    def test_evidence_chain_append_invalidates_prior_preview(self):
        preview = self.preview()
        with self.ledger() as reopened:
            reopened.capture(self.sources, "one.txt", "first", operation_id="read-2")
            head = reopened.verify()
        with self.assertRaisesRegex(ProvenanceRefused, "chain head"):
            verify_local_adoption_preview(self.sources, preview,
                                          self.seal, head, now=NOW)


if __name__ == "__main__":
    unittest.main()

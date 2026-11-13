"""R32 generic host gate: source artifacts, not donor/recipient execution."""
import json
import tempfile
import unittest
from pathlib import Path

from muse_presets.catalog import load_registry
from muse_presets.native_canary import (
    make_canary,
    stage_canary,
    inspect_canary,
    assess_fixture_transcript,
    NativeHostUnavailable,
    unsupported_native_invoke,
)

HOSTS = ("personal-hatch", "muse-code")


class GenericHostCanaryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.role = "software-engineer"
        self.spec = make_canary(self.role, "personal-hatch", challenge="ab" * 16)

    def test_all_eleven_roles_have_inert_staged_canaries_for_both_hosts(self):
        roles = load_registry()["presets"]
        self.assertEqual(len(roles), 15)
        for host in HOSTS:
            (self.root / host).mkdir()
            for role in roles:
                with self.subTest(host=host, role=role):
                    location = self.root / host / role
                    self.assertEqual(stage_canary(location, role, host)["status"], "SOURCE_ONLY_STAGED")
                    self.assertEqual(inspect_canary(location)["status"], "SOURCE_ONLY_MATCH")
                    spec = json.loads((location / "GENERIC_CANARY.json").read_text())
                    self.assertEqual(spec["role_id"], role)
                    self.assertEqual(spec["host_kind"], host)
                    self.assertFalse(spec["native_effects_enabled"])
                    self.assertIsNone(spec["provider_session_id"])
                    self.assertFalse(spec["native_authenticated"])
                    self.assertFalse(spec["model_invoked"])
                    self.assertEqual(spec["native_acceptance"], "NOT_RUN")

    def test_pinned_source_hashes_are_real_sha256_digests(self):
        for name, value in self.spec["source_pins"].items():
            self.assertIn(name, ("preset.json", "playbook.json"))
            self.assertRegex(value, r"^[0-9a-f]{64}$")
        self.assertTrue(self.spec["challenge"].startswith("ab"))
        self.assertTrue(self.spec["disposable_only"])

    def test_roles_or_host_kind_cannot_be_conflated(self):
        for role in ("bogus-role", "../escape", "", "UNKNOWN_ROLE"):
            with self.subTest(role=role), self.assertRaises(ValueError):
                make_canary(role, "personal-hatch")
        for kind in ("hatch-or-muse-code", "muse", "", "../personal-hatch"):
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                make_canary(self.role, kind)

    def test_unsupported_port_fails_before_any_native_effect(self):
        with self.assertRaises(NativeHostUnavailable):
            unsupported_native_invoke(self.spec)
        self.assertFalse(self.spec["native_effects_enabled"])

    def test_untrusted_challenge_cannot_be_used_as_a_grant(self):
        spec = make_canary(self.role, "personal-hatch", challenge="cc" * 16)
        self.assertEqual(spec["native_acceptance"], "NOT_RUN")
        self.assertIsNone(spec["owner_grant_id"])
        self.assertFalse(spec["native_authenticated"])
        for invalid in ("", "opaque token", "0" * 10, "../escape", 123):
            with self.subTest(challenge=invalid), self.assertRaises(ValueError):
                make_canary(self.role, "personal-hatch", challenge=invalid)

    def test_create_only_refuses_existing_directory_without_modification(self):
        target = self.root / "existing"
        target.mkdir()
        sentinel = target / "DO_NOT_TOUCH.txt"
        sentinel.write_text("preserved")
        with self.assertRaises((ValueError, FileExistsError)):
            stage_canary(target, self.role, "personal-hatch")
        self.assertEqual(sentinel.read_text(), "preserved")

    def test_create_only_refuses_parent_traversal(self):
        with self.assertRaises(ValueError):
            stage_canary(self.root / "x" / ".." / "out", self.role, "personal-hatch")

    def test_existing_symlinked_ancestor_refused(self):
        real = self.root / "actual"
        real.mkdir()
        alias = self.root / "shortcut"
        try:
            alias.symlink_to(real, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unavailable")
        with self.assertRaises(ValueError):
            stage_canary(alias / "fresh", self.role, "personal-hatch")

    def test_inspection_rejects_added_code_and_forged_authority(self):
        target = self.root / "candidate"
        stage_canary(target, self.role, "personal-hatch")
        (target / "unlisted.py").write_text("print('not approved')")
        self.assertEqual(inspect_canary(target)["status"], "REVIEW_REQUIRED")
        (target / "unlisted.py").unlink()
        record = json.loads((target / "GENERIC_CANARY.json").read_text())
        record["native_authenticated"] = True
        (target / "GENERIC_CANARY.json").write_text(json.dumps(record))
        self.assertEqual(inspect_canary(target)["status"], "REVIEW_REQUIRED")

    def test_inspection_rejects_missing_and_duplicate_keys(self):
        target = self.root / "candidate"
        stage_canary(target, self.role, "personal-hatch")
        file = target / "GENERIC_CANARY.json"
        original = file.read_text()
        file.write_text(original.replace('"native_authenticated": false,', '"native_authenticated": false, "native_authenticated": true,'))
        self.assertEqual(inspect_canary(target)["status"], "REVIEW_REQUIRED")
        file.write_text(original)
        (target / "NATIVE_HANDOFF.md").unlink()
        self.assertEqual(inspect_canary(target)["status"], "REVIEW_REQUIRED")

    def test_fixture_consistent_chain_never_establishes_provider_proof(self):
        result = assess_fixture_transcript(self.spec, self.events())
        self.assertEqual(result["status"], "FIXTURE_CONSISTENT_ONLY")
        self.assertEqual(result["evidence_grade"], "UNATTESTED_FIXTURE")
        self.assertFalse(result["native_authenticated"])
        self.assertFalse(result["native_tool_invoked"])
        self.assertFalse(result["recipient_readback_verified"])
        self.assertFalse(result["wrong_owner_denied_by_provider"])

    def test_wrong_principal_and_nonce_are_rejected(self):
        events = self.events()
        events["invocation"]["owner_principal"] = "wrong-owner"
        self.assertEqual(assess_fixture_transcript(self.spec, events)["status"], "FIXTURE_REJECTED")
        events = self.events()
        events["invocation"]["challenge"] = "00" * 16
        self.assertEqual(assess_fixture_transcript(self.spec, events)["status"], "FIXTURE_REJECTED")

    def test_wrong_session_and_recipient_reference_are_rejected(self):
        events = self.events()
        events["invocation"]["session_id"] = "other-session"
        self.assertEqual(assess_fixture_transcript(self.spec, events)["status"], "FIXTURE_REJECTED")
        events = self.events()
        events["recipient_readback"]["invocation_id"] = "replayed-event"
        self.assertEqual(assess_fixture_transcript(self.spec, events)["status"], "FIXTURE_REJECTED")

    def test_denial_is_not_proof_when_principal_is_same_owner(self):
        events = self.events()
        events["wrong_owner_refusal"]["owner_principal"] = "owner-fixture"
        self.assertEqual(assess_fixture_transcript(self.spec, events)["status"], "FIXTURE_REJECTED")

    def test_missing_denial_or_readback_is_rejected(self):
        for field in ("wrong_owner_refusal", "recipient_readback"):
            events = self.events()
            del events[field]
            with self.subTest(field=field):
                self.assertEqual(assess_fixture_transcript(self.spec, events)["status"], "FIXTURE_REJECTED")

    def test_self_reported_host_authority_is_refused(self):
        events = self.events()
        events["host_authenticated"] = True
        self.assertEqual(assess_fixture_transcript(self.spec, events)["status"], "FIXTURE_REJECTED")

    def test_duplicate_provider_event_ids_are_refused(self):
        events = self.events()
        events["invocation"]["event_id"] = events["discovery"]["event_id"]
        self.assertEqual(assess_fixture_transcript(self.spec, events)["status"], "FIXTURE_REJECTED")

    def events(self):
        return {
            "schema": "r32/native-fixture-events-v1",
            "host_kind": "personal-hatch",
            "discovery": {
                "event_id": "discover-fixture", "owner_principal": "owner-fixture",
                "session_id": "session-fixture", "skill_id": self.spec["skill_id"],
                "status": "found",
            },
            "invocation": {
                "event_id": "invoke-fixture", "owner_principal": "owner-fixture",
                "session_id": "session-fixture", "skill_id": self.spec["skill_id"],
                "challenge": self.spec["challenge"], "status": "completed",
            },
            "recipient_readback": {
                "event_id": "readback-fixture", "invocation_id": "invoke-fixture",
                "owner_principal": "owner-fixture", "challenge": self.spec["challenge"],
                "status": "matched",
            },
            "wrong_owner_refusal": {
                "event_id": "deny-fixture", "owner_principal": "other-fixture",
                "skill_id": self.spec["skill_id"], "status": "denied",
            },
        }


if __name__ == "__main__":
    unittest.main()

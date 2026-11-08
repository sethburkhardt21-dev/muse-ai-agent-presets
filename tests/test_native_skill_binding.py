"""Source-level custom-skill catalog admission; native proof must be external."""
from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from muse_presets.native_skill_binding import inspect_skill_bindings, propose_registry_entries
from muse_presets.cli import main


class NativeSkillBindingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.skills = self.base / "custom-skills"
        self.skills.mkdir()
        self.registry = self.base / "skills.yaml"
        self.registry.write_text("version: 1\nentries:\n  asana:\n    status: connected\n")
        self.descriptor = self.skills / "example-claim-gate"
        self.descriptor.mkdir()
        (self.descriptor / "skill.yaml").write_text(
            "name: example_claim_gate\n"
            "title: Example Claim Gate\n"
            "description: 'Run a scoped, read-only claim status check.'\n"
            "include_in_prompt: true\n"
            "availability:\n  confidential_vm: true\n"
        )
        (self.descriptor / "SKILL.md").write_text(
            "# Example Claim Gate\n\n## When to use\nUse for local claim inspection only.\n"
        )

    def inspect(self, names=("example_claim_gate",)):
        return inspect_skill_bindings(
            custom_root=self.skills, registry_path=self.registry, skill_names=names
        )

    def test_missing_registry_entry_is_reported_without_native_claim(self):
        out = self.inspect()
        row = out["skills"][0]
        self.assertEqual(row["source_status"], "DESCRIPTOR_VALID")
        self.assertEqual(row["catalog_status"], "CATALOG_ENTRY_MISSING")
        self.assertEqual(out["status"], "LOCAL_CATALOG_GAP")
        self.assertEqual(out["evidence_grade"], "UNATTESTED_LOCAL_SOURCE_ONLY")
        self.assertFalse(out["authority"]["provider_invocation_verified"])
        self.assertFalse(out["authority"]["external_effect_authorized"])

    def test_available_entry_does_not_prove_organic_invocation(self):
        self.registry.write_text(
            "version: 1\nentries:\n  asana:\n    status: connected\n"
            "  example_claim_gate:\n    status: available\n"
        )
        out = self.inspect()
        self.assertEqual(out["status"], "LOCAL_CATALOG_ADVERTISED_ONLY")
        self.assertEqual(out["skills"][0]["catalog_status"], "DECLARED_AVAILABLE")
        self.assertEqual(out["skills"][0]["include_in_prompt"], True)
        self.assertFalse(out["authority"]["model_selected_skill_verified"])
        self.assertFalse(out["authority"]["provider_invocation_verified"])
        self.assertFalse(out["authority"]["recipient_readback_verified"])

    def test_registry_proposal_is_not_an_installation(self):
        before = self.registry.read_bytes()
        report = self.inspect()
        proposed = propose_registry_entries(report)
        self.assertEqual(proposed["base_registry_sha256"], report["registry_sha256"])
        self.assertEqual(proposed["missing"], ["example_claim_gate"])
        self.assertEqual(proposed["snippet"], "  example_claim_gate:\n    status: available\n")
        self.assertFalse(proposed["applied"])
        self.assertEqual(self.registry.read_bytes(), before)

    def test_no_entrypoint_is_distinct_from_skill_descriptor(self):
        row = self.inspect()["skills"][0]
        self.assertTrue(row["descriptor_present"])
        self.assertFalse(row["local_entrypoint_observed"])
        self.assertFalse(row["native_tool_registered"])

    def test_local_bin_entrypoint_is_metadata_not_a_provider_receipt(self):
        b = self.descriptor / "bin"
        b.mkdir()
        (b / "claim-gate").write_bytes(b"#!/usr/bin/env python3\nprint('fixture')\n")
        row = self.inspect()["skills"][0]
        self.assertTrue(row["local_entrypoint_observed"])
        self.assertFalse(row["native_tool_registered"])
        self.assertFalse(row["provider_invocation_verified"])

    def test_frontmatter_skill_markdown_is_valid(self):
        (self.descriptor / "SKILL.md").write_text(
            '---\nname: "example-claim-gate"\ndescription: "Metadata only"\n---\n'
            '# Example Claim Gate\n\n## When to use\nLocal read-only inspection.\n'
        )
        self.assertEqual(self.inspect()["skills"][0]["source_status"], "DESCRIPTOR_VALID")

    def test_unclosed_skill_frontmatter_is_rejected(self):
        (self.descriptor / "SKILL.md").write_text(
            '---\nname: "example-claim-gate"\n# No closing delimiter\n'
        )
        self.assertEqual(self.inspect()["skills"][0]["source_status"], "DESCRIPTOR_REVIEW_REQUIRED")

    def test_wrong_descriptor_name_is_held(self):
        file = self.descriptor / "skill.yaml"
        file.write_text(file.read_text().replace("example_claim_gate", "other_claim_gate"))
        row = self.inspect()["skills"][0]
        self.assertEqual(row["source_status"], "DESCRIPTOR_REVIEW_REQUIRED")
        self.assertEqual(row["catalog_status"], "NOT_EVALUATED")

    def test_symlinked_descriptor_refused(self):
        file = self.descriptor / "skill.yaml"
        file.unlink()
        target = self.base / "outside.yaml"
        target.write_text("name: example_claim_gate\ninclude_in_prompt: true\n")
        try:
            file.symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest("symlink fixture unsupported on host")
        self.assertEqual(self.inspect()["skills"][0]["source_status"], "DESCRIPTOR_REVIEW_REQUIRED")

    def test_symlinked_markdown_refused(self):
        file = self.descriptor / "SKILL.md"
        file.unlink()
        target = self.base / "outside.md"
        target.write_text("# unsafe\n")
        try:
            file.symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest("symlink fixture unsupported on host")
        self.assertEqual(self.inspect()["skills"][0]["source_status"], "DESCRIPTOR_REVIEW_REQUIRED")

    def test_duplicate_manifest_name_is_refused(self):
        file = self.descriptor / "skill.yaml"
        file.write_text(file.read_text() + "\nname: example_claim_gate\n")
        self.assertEqual(self.inspect()["skills"][0]["source_status"], "DESCRIPTOR_REVIEW_REQUIRED")

    def test_duplicate_registry_entries_refuse_all_advertisements(self):
        self.registry.write_text(
            "version: 1\nentries:\n  example_claim_gate:\n    status: available\n"
            "  example_claim_gate:\n    status: available\n"
        )
        report = self.inspect()
        self.assertEqual(report["status"], "LOCAL_CATALOG_UNTRUSTED")
        self.assertIsNone(report["registry_sha256"])
        self.assertEqual(propose_registry_entries(report)["missing"], [])
        self.assertFalse(report["authority"]["provider_invocation_verified"])

    def test_duplicate_status_refused(self):
        self.registry.write_text(
            "version: 1\nentries:\n  example_claim_gate:\n"
            "    status: available\n    status: available\n"
        )
        self.assertEqual(self.inspect()["status"], "LOCAL_CATALOG_UNTRUSTED")

    def test_connected_is_not_a_custom_skill_registration(self):
        self.registry.write_text(
            "version: 1\nentries:\n  example_claim_gate:\n    status: connected\n"
        )
        self.assertEqual(self.inspect()["skills"][0]["catalog_status"], "NOT_ADVERTISED_AS_SKILL")

    def test_alias_and_duplicate_directory_are_ambiguous(self):
        other = self.skills / "example_claim_gate"
        other.mkdir()
        (other / "skill.yaml").write_text((self.descriptor / "skill.yaml").read_text())
        (other / "SKILL.md").write_text((self.descriptor / "SKILL.md").read_text())
        self.assertEqual(self.inspect()["skills"][0]["source_status"], "AMBIGUOUS_SKILL_DIRECTORY")

    def test_missing_descriptor_cannot_enter_proposal(self):
        (self.descriptor / "SKILL.md").unlink()
        report = self.inspect()
        self.assertEqual(report["skills"][0]["source_status"], "DESCRIPTOR_REVIEW_REQUIRED")
        self.assertEqual(propose_registry_entries(report)["missing"], [])

    def test_bad_skill_name_refused_before_filesystem_access(self):
        for name in ("../escape", "Example Claim Gate", "x/y", "", "a" * 100):
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.inspect((name,))

    def test_registry_yaml_injection_refused(self):
        self.registry.write_text("version: 1\nentries:\n  example_claim_gate: !python/object\n    status: available\n")
        self.assertEqual(self.inspect()["status"], "LOCAL_CATALOG_UNTRUSTED")

    def test_missing_registry_is_not_assumed_negative(self):
        self.registry.unlink()
        report = self.inspect()
        self.assertEqual(report["status"], "LOCAL_CATALOG_UNTRUSTED")
        self.assertEqual(report["skills"][0]["catalog_status"], "NOT_EVALUATED")

    def test_cli_reports_gaps_but_never_success_authority(self):
        stream = io.StringIO()
        with redirect_stdout(stream):
            code = main([
                "skill-binding-doctor", "--host", "personal-hatch",
                "--custom-root", str(self.skills),
                "--registry", str(self.registry),
                "--skill", "example_claim_gate",
            ])
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(stream.getvalue())["status"], "LOCAL_CATALOG_GAP")
        self.assertFalse(json.loads(stream.getvalue())["authority"]["external_effect_authorized"])


if __name__ == "__main__":
    unittest.main()

"""R32.S2: passive skill catalog must reject owner-controlled symlink ancestors."""
import sys
import tempfile
import unittest
from pathlib import Path

from muse_presets.native_skill_binding import inspect_skill_bindings


class NativeSkillAncestorAdmissionTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.real = self.root / "real"
        skill = self.real / "custom" / "example-claim-gate"
        skill.mkdir(parents=True)
        (skill / "skill.yaml").write_text(
            "name: example_claim_gate\ntitle: Example Claim Gate\n"
            "description: Scoped local inspection only\ninclude_in_prompt: true\n"
        )
        (skill / "SKILL.md").write_text("# Example Claim Gate\n\nSource body.\n")
        config = self.real / "config"
        config.mkdir()
        (config / "skills.yaml").write_text(
            "version: 1\nentries:\n  example_claim_gate:\n    status: available\n"
        )
        self.alias = self.root / "alias"

    def make_alias(self):
        try:
            self.alias.symlink_to(self.real, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("symlink fixture unsupported")

    def inspect(self, custom_root=None, registry_path=None):
        return inspect_skill_bindings(
            custom_root=custom_root or self.real / "custom",
            registry_path=registry_path or self.real / "config" / "skills.yaml",
            skill_names=["example_claim_gate"],
        )

    def test_user_symlinked_ancestor_of_custom_root_is_refused(self):
        self.make_alias()
        report = self.inspect(custom_root=self.alias / "custom")
        self.assertEqual(report["status"], "LOCAL_SOURCE_REVIEW_REQUIRED")
        self.assertFalse(report["skills"][0]["descriptor_present"])
        self.assertFalse(report["authority"]["external_effect_authorized"])

    def test_user_symlinked_ancestor_of_registry_is_refused(self):
        self.make_alias()
        report = self.inspect(registry_path=self.alias / "config" / "skills.yaml")
        self.assertEqual(report["status"], "LOCAL_CATALOG_UNTRUSTED")
        self.assertIsNone(report["registry_sha256"])
        self.assertFalse(report["authority"]["owner_grant_verified"])

    def test_explicit_parent_traversal_in_source_root_is_refused(self):
        report = self.inspect(custom_root=self.real / "custom" / ".." / "custom")
        self.assertEqual(report["status"], "LOCAL_SOURCE_REVIEW_REQUIRED")
        self.assertFalse(report["skills"][0]["descriptor_present"])

    def test_normal_sources_under_macos_root_alias_remain_readable(self):
        if sys.platform != "darwin" or not Path("/var").is_symlink():
            self.skipTest("macOS system root alias is required")
        self.assertTrue(str(self.root).startswith("/var/"))
        report = self.inspect()
        self.assertEqual(report["status"], "LOCAL_CATALOG_ADVERTISED_ONLY")
        self.assertFalse(report["authority"]["native_skill_search_verified"])


if __name__ == "__main__":
    unittest.main()

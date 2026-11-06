"""Fail-closed privacy checks on the ENTIRE public source distribution.

Use synthetic fixtures only; no private person, original agent or host names
appear in this test source. Historical Git blob review is a separate gate.
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from muse_presets.neutrality import audit_public_tree


class EntirePublicTreePrivacyTests(unittest.TestCase):
    def setUp(self):
        self.owned=tempfile.TemporaryDirectory(prefix="neutral-check-")
        self.addCleanup(self.owned.cleanup)
        self.root=Path(self.owned.name)

    def put(self,relative,text):
        target=self.root/relative
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(text,encoding="utf-8")
        return target

    def findings(self):
        return audit_public_tree(self.root)

    def test_application_sources_are_not_exempt(self):
        self.put("src/package/extension.py", "token='sk-proj-" + "X"*32 + "'")
        self.assertEqual(
            self.findings(),
            [{"path":"src/package/extension.py","reason":"POSSIBLE_SECRET"}])

    def test_examples_scripts_and_workflows_are_checked(self):
        self.put("examples/demo.py","const example = 'Bearer " + "A"*42 + "'")
        self.put("scripts/launch.sh","AWS_ACCESS_KEY_ID=AKIA" + "Z"*16)
        self.put(".github/workflows/ci.yml","secret: " + "sk-proj-" + "J"*40)
        rows=self.findings()
        self.assertEqual({r["path"] for r in rows},
                         {"examples/demo.py","scripts/launch.sh",".github/workflows/ci.yml"})
        self.assertTrue(all(r["reason"]=="POSSIBLE_SECRET" for r in rows))

    def test_root_markdown_and_shell_metadata_not_ignored(self):
        private="/"+"home/"+"sample-owner"+"/work"
        self.put("README.md","setup with "+private)
        self.put(".gitattributes","private_path="+private)
        rows=self.findings()
        self.assertEqual(len(rows),2)
        self.assertTrue(all(r["reason"]=="PRIVATE_HOST_PATH" for r in rows))

    def test_sensitive_binary_and_database_files_fail_closed(self):
        raw=self.root/"payload.exe"
        raw.write_bytes(b"\x00MZ synthetic machine bytes")
        db=self.root/"example.sqlite3"
        db.write_bytes(b"\x00synthetic test database")
        rows=self.findings()
        self.assertEqual({r["path"] for r in rows},{"payload.exe","example.sqlite3"})
        self.assertEqual({r["reason"] for r in rows},
                         {"UNREVIEWED_BINARY_ASSET","SENSITIVE_FILE"})

    def test_untracked_text_and_sensitive_files_in_distribution_are_scanned(self):
        self.put("templates/profile/owner-editable.md","Generic empty profile.")
        self.put("examples/credentials.json","synthetic content that must not ship")
        self.assertEqual(self.findings(),
            [{"path":"examples/credentials.json","reason":"SENSITIVE_FILE"}])

    def test_secret_redaction_never_echoes_the_input(self):
        private="ghp_"+"A"*36
        self.put("scripts/config.sh","token="+private)
        report=self.findings()
        self.assertTrue(report)
        self.assertNotIn(private,str(report))

    def test_custom_private_name_screen_can_be_injected_without_publishing_list(self):
        self.put("docs/howto.md","This document refers to demo-private-label.")
        self.assertEqual(self.findings(),[])
        result=audit_public_tree(self.root,forbidden_terms=("demo-private-label",))
        self.assertEqual(result,[{"path":"docs/howto.md","reason":"FORBIDDEN_IDENTITY_LABEL"}])

    def test_source_symlink_to_outside_is_not_followed(self):
        outside=self.root.parent/("private-external-file-"+self.root.name+".txt")
        outside.write_text("private data")
        self.addCleanup(lambda:outside.unlink(missing_ok=True))
        linked=self.root/"src"/"shortcut"
        linked.parent.mkdir()
        try:linked.symlink_to(outside)
        except (OSError,NotImplementedError):self.skipTest("Symlink unsupported")
        self.assertEqual(self.findings(),
            [{"path":"src/shortcut","reason":"SYMLINK_REFUSED"}])

    def test_unrelated_git_internal_objects_not_treated_as_distribution(self):
        self.put(".git/objects/test-blob","token='sk-proj-"+"X"*32+"'")
        self.put("src/neutral.py","def valid(): return True")
        self.assertEqual(self.findings(),[])


    def test_ci_uses_read_only_permissions_and_full_privacy_gate(self):
        workflow=(Path(__file__).resolve().parents[1]/
                  ".github/workflows/checks.yml").read_text(encoding="utf8")
        self.assertIn("permissions:\n  contents: read",workflow)
        self.assertIn("python -m muse_presets.cli audit-neutrality",workflow)

if __name__=="__main__":
    unittest.main()

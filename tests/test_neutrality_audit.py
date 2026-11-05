"""The public preset intake must reject host-specific configuration and secrets."""
import tempfile
import unittest
from pathlib import Path

from muse_presets.neutrality import audit_public_tree
from muse_presets.catalog import ROOT


class NeutralityAuditTests(unittest.TestCase):
    def test_current_distributable_assets_are_generic(self):
        self.assertEqual(audit_public_tree(ROOT), [])

    def test_concrete_windows_and_linux_home_paths_are_refused(self):
        for bad in (r'C:\Users\someone\AppData\secret', '/home/jane/workspace/agent'):
            with self.subTest(value=bad), tempfile.TemporaryDirectory() as temp:
                doc = Path(temp)/'templates'/'profile'/'TOOLS.md'
                doc.parent.mkdir(parents=True)
                doc.write_text('path: '+bad, encoding='utf-8')
                results = audit_public_tree(Path(temp))
                self.assertEqual(len(results), 1)
                self.assertEqual(results[0]['reason'], 'PRIVATE_HOST_PATH')
                self.assertNotIn('someone', str(results))
                self.assertNotIn('jane', str(results))

    def test_secrets_and_sensitive_files_are_refused_without_printing_content(self):
        with tempfile.TemporaryDirectory() as temp:
            profile = Path(temp)/'presets'/'safe'
            profile.mkdir(parents=True)
            (profile/'preset.json').write_text('token="sk-proj-'+('Z'*32)+'"')
            (profile/'.env').write_text('SAMPLE_SECRET=sensitive')
            result = audit_public_tree(Path(temp))
            self.assertIn('POSSIBLE_SECRET', [x['reason'] for x in result])
            self.assertIn('SENSITIVE_FILE', [x['reason'] for x in result])
            self.assertNotIn('sensitive', str(result))
            self.assertNotIn('sk-proj-', str(result))

    def test_symlink_to_external_source_is_refused_without_reading_target(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            data = root/'unrelated.txt'
            data.write_text('a private file')
            templ = root/'templates'/'profile'
            templ.mkdir(parents=True)
            try:
                (templ/'AGENTS.md').symlink_to(data)
            except (OSError, NotImplementedError):
                self.skipTest('symlinks unavailable')
            result=audit_public_tree(root)
            self.assertEqual(result[0]['reason'],'SYMLINK_REFUSED')
            self.assertEqual(data.read_text(),'a private file')


if __name__ == '__main__':
    unittest.main()

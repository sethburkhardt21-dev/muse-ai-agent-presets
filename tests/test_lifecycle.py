"""Red/green safeguards for source-only rendered profile inspection."""
import io
import json
import os
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from muse_presets.catalog import render_preset
from muse_presets.cli import main
from muse_presets.lifecycle import inspect_render


class LifecycleInspectionTests(unittest.TestCase):
    def create_profile(self, root):
        profile = Path(root) / 'profile'
        render_preset('garden-companion', profile, display_name='Garden Guide')
        return profile

    def test_fresh_profile_has_local_match_without_native_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            profile = self.create_profile(tmp)
            before = {p.name: p.read_bytes() for p in profile.iterdir()}
            result = inspect_render(profile)
            self.assertEqual(result['status'], 'LOCAL_MATCH')
            self.assertEqual(result['native_muse_status'], 'NOT_CHECKED')
            self.assertEqual(result['evidence_grade'], 'UNAUTHENTICATED_LOCAL_ONLY')
            self.assertEqual(before, {p.name: p.read_bytes() for p in profile.iterdir()})

    def test_owner_customization_is_detected_and_never_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            profile = self.create_profile(tmp)
            for name in ('SOUL.md', 'MEMORY.md'):
                (profile / name).write_text('owner personal changes', encoding='utf-8')
            result = inspect_render(profile)
            self.assertEqual(result['status'], 'OWNER_CUSTOMIZED')
            self.assertEqual(result['owner_modified'], ['MEMORY.md', 'SOUL.md'])
            self.assertEqual((profile / 'MEMORY.md').read_text(), 'owner personal changes')

    def test_family_link_policy_change_requires_separate_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            profile = self.create_profile(tmp)
            (profile/'FAMILY_LINK.json').write_text('{"enabled":true,"transport":"unbound"}')
            result = inspect_render(profile)
            self.assertEqual(result['status'], 'REVIEW_REQUIRED')
            self.assertEqual(result['policy_modified'], ['FAMILY_LINK.json'])
            self.assertEqual(result['native_muse_status'], 'NOT_CHECKED')

    def test_missing_managed_file_requires_review_not_restoration(self):
        with tempfile.TemporaryDirectory() as tmp:
            profile = self.create_profile(tmp)
            (profile / 'TOOLS.md').unlink()
            result = inspect_render(profile)
            self.assertEqual(result['status'], 'REVIEW_REQUIRED')
            self.assertEqual(result['missing'], ['TOOLS.md'])
            self.assertFalse((profile / 'TOOLS.md').exists())

    def test_legacy_render_receipt_is_not_silently_trusted(self):
        with tempfile.TemporaryDirectory() as tmp:
            profile = self.create_profile(tmp)
            receipt = json.loads((profile/'RECEIPT.json').read_text())
            receipt['schema'] = 'muse-presets/render-v1'
            receipt.pop('rendered_sha256', None)
            (profile/'RECEIPT.json').write_text(json.dumps(receipt), encoding='utf-8')
            result = inspect_render(profile)
            self.assertEqual(result['status'], 'LEGACY_UNVERIFIABLE')

    def test_symlink_to_external_memory_is_refused_without_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            profile = self.create_profile(tmp)
            secret = Path(tmp) / 'secret.txt'
            secret.write_text('private', encoding='utf-8')
            (profile / 'MEMORY.md').unlink()
            try:
                (profile / 'MEMORY.md').symlink_to(secret)
            except (OSError, NotImplementedError):
                self.skipTest('symlinks unavailable on this Windows host')
            with self.assertRaisesRegex(ValueError, 'UNSAFE_SYMLINK'):
                inspect_render(profile)
            self.assertEqual(secret.read_text(), 'private')

    def test_unsafe_receipt_membership_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            profile = self.create_profile(tmp)
            receipt = json.loads((profile/'RECEIPT.json').read_text())
            receipt['rendered_sha256']['../sneak'] = '0' * 64
            (profile/'RECEIPT.json').write_text(json.dumps(receipt))
            with self.assertRaisesRegex(ValueError, 'INVALID_RECEIPT_MANIFEST'):
                inspect_render(profile)

    def test_upstream_template_changed_is_detected_not_applied(self):
        from muse_presets import lifecycle
        with tempfile.TemporaryDirectory() as tmp:
            profile = self.create_profile(tmp)
            isolated_root = Path(tmp) / 'source'
            (isolated_root/'presets'/'garden-companion').mkdir(parents=True)
            (isolated_root/'templates').mkdir()
            shutil.copytree(lifecycle.ROOT/'templates'/'profile', isolated_root/'templates'/'profile')
            shutil.copy2(lifecycle.ROOT/'presets'/'garden-companion'/'preset.json', isolated_root/'presets'/'garden-companion'/'preset.json')
            shutil.copy2(lifecycle.ROOT/'presets'/'garden-companion'/'playbook.json', isolated_root/'presets'/'garden-companion'/'playbook.json')
            (isolated_root/'templates'/'profile'/'AGENTS.md').write_text('upstream revised')
            with patch.object(lifecycle, 'ROOT', isolated_root):
                result = inspect_render(profile)
            self.assertEqual(result['status'], 'REVIEW_REQUIRED')
            self.assertEqual(result['source_changed'], ['templates/AGENTS.md'])
            self.assertNotEqual((profile/'AGENTS.md').read_text(), 'upstream revised')

    def test_cli_inspect_returns_clean_and_review_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            profile = self.create_profile(tmp)
            output = io.StringIO()
            with redirect_stdout(output):
                code = main(['inspect', '--path', str(profile)])
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(output.getvalue())['status'], 'LOCAL_MATCH')
            (profile/'FAMILY_LINK.json').write_text('changed')
            output = io.StringIO()
            with redirect_stdout(output):
                code = main(['inspect', '--path', str(profile)])
            self.assertEqual(code, 2)
            self.assertEqual(json.loads(output.getvalue())['status'], 'REVIEW_REQUIRED')


if __name__ == '__main__':
    unittest.main()

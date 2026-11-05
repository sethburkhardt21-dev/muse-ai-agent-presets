"""Red-first contract tests: every neutral specialist must have distinct methods."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from muse_presets.catalog import load_registry, load_preset, render_preset, validate_catalog
from muse_presets.lifecycle import inspect_render
from muse_presets.playbooks import load_playbook, validate_playbook


class RolePlaybookTests(unittest.TestCase):
    def test_all_eleven_presets_have_distinct_valid_playbooks(self):
        signatures = set()
        for slug in load_registry()['presets']:
            with self.subTest(role=slug):
                preset = load_preset(slug)
                book = load_playbook(slug)
                self.assertEqual(validate_playbook(book, preset), [])
                self.assertEqual(len(book['methods']), 3)
                signature = tuple(m['id'] for m in book['methods'])
                self.assertNotIn(signature, signatures)
                signatures.add(signature)
                self.assertEqual(book['first_canary']['grade'], 'SOURCE_ONLY')
        self.assertEqual(validate_catalog(), [])

    def test_all_handoffs_are_policy_allowlisted(self):
        for slug in load_registry()['presets']:
            preset = load_preset(slug)
            for method in load_playbook(slug)['methods']:
                with self.subTest(role=slug, method=method['id']):
                    self.assertIn(method['handoff_to'], preset['family_link']['suggested_receivers'])
                    self.assertGreaterEqual(len(method['steps']), 3)
                    self.assertGreaterEqual(len(method['evidence']), 2)
                    self.assertTrue(method['stop_rule'])

    def test_every_role_renders_distinct_reinspectable_local_profile(self):
        with tempfile.TemporaryDirectory() as work:
            documents = set()
            for slug in load_registry()['presets']:
                with self.subTest(role=slug):
                    dest = render_preset(slug, Path(work)/slug, display_name='Test Role')
                    content = (dest/'ROLE_PLAYBOOK.md').read_text(encoding='utf-8')
                    self.assertNotIn(content, documents)
                    documents.add(content)
                    self.assertEqual(inspect_render(dest)['status'], 'LOCAL_MATCH')
                    self.assertIn('SOURCE-ONLY', content)
                    self.assertFalse(json.loads((dest/'FAMILY_LINK.json').read_text())['enabled'])
                    self.assertIn('blank user-owned', (dest/'MEMORY.md').read_text().lower())

    def test_fake_native_grade_or_unapproved_receiver_is_rejected(self):
        preset = load_preset('model-builder')
        good = load_playbook('model-builder')
        forged = json.loads(json.dumps(good))
        forged['first_canary']['grade'] = 'NATIVE_PROVEN'
        self.assertIn('INVALID_CANARY_GRADE', validate_playbook(forged, preset))
        forged = json.loads(json.dumps(good))
        forged['methods'][0]['handoff_to'] = 'not-registered'
        self.assertIn('BAD_HANDOFF_RECEIVER', validate_playbook(forged, preset))

    def test_render_uses_role_specific_methods_and_v3_receipt(self):
        with tempfile.TemporaryDirectory() as work:
            garden = render_preset('garden-companion', Path(work)/'garden', display_name='My Garden Helper')
            model = render_preset('model-builder', Path(work)/'model', display_name='My Model Helper')
            garden_doc = (garden/'ROLE_PLAYBOOK.md').read_text(encoding='utf-8')
            model_doc = (model/'ROLE_PLAYBOOK.md').read_text(encoding='utf-8')
            self.assertNotEqual(garden_doc, model_doc)
            self.assertIn('My Garden Helper', garden_doc)
            self.assertIn('revision', garden_doc.lower())
            self.assertIn('QLoRA', model_doc)
            self.assertIn('ROLE_PLAYBOOK.md', (garden/'AGENTS.md').read_text(encoding='utf-8'))
            self.assertEqual(json.loads((garden/'RECEIPT.json').read_text())['schema'], 'muse-presets/render-v3')
            self.assertEqual(inspect_render(garden)['status'], 'LOCAL_MATCH')

    def test_playbook_edit_requires_policy_review_without_overwriting(self):
        with tempfile.TemporaryDirectory() as work:
            dest = render_preset('claims-adjudicator', Path(work)/'claims')
            (dest/'ROLE_PLAYBOOK.md').write_text('altered verdict policy', encoding='utf-8')
            outcome = inspect_render(dest)
            self.assertEqual(outcome['status'], 'REVIEW_REQUIRED')
            self.assertIn('ROLE_PLAYBOOK.md', outcome['policy_modified'])
            self.assertEqual((dest/'ROLE_PLAYBOOK.md').read_text(), 'altered verdict policy')

    def test_playbook_source_drift_is_detected_without_rewrite(self):
        with tempfile.TemporaryDirectory() as work:
            dest = render_preset('coordinator', Path(work)/'coord')
            original = (dest/'ROLE_PLAYBOOK.md').read_bytes()
            from muse_presets import lifecycle
            import shutil
            fake_root = Path(work)/'fake'
            shutil.copytree(lifecycle.ROOT/'presets', fake_root/'presets')
            shutil.copytree(lifecycle.ROOT/'templates', fake_root/'templates')
            src = fake_root/'presets'/'coordinator'/'playbook.json'
            src.write_text(src.read_text()+' ', encoding='utf-8')
            with patch.object(lifecycle, 'ROOT', fake_root):
                result = inspect_render(dest)
            self.assertEqual(result['status'], 'REVIEW_REQUIRED')
            self.assertIn('playbook.json', result['source_changed'])
            self.assertEqual((dest/'ROLE_PLAYBOOK.md').read_bytes(), original)

    def test_legacy_v2_render_inspection_remains_supported(self):
        with tempfile.TemporaryDirectory() as work:
            dest = render_preset('learning-coach', Path(work)/'learn')
            receipt = json.loads((dest/'RECEIPT.json').read_text())
            receipt['schema'] = 'muse-presets/render-v2'
            receipt.pop('playbook_sha256')
            del receipt['rendered_sha256']['ROLE_PLAYBOOK.md']
            (dest/'ROLE_PLAYBOOK.md').unlink()
            (dest/'RECEIPT.json').write_text(json.dumps(receipt))
            result = inspect_render(dest)
            self.assertEqual(result['status'], 'LOCAL_MATCH')
            self.assertEqual(result['role_playbook_status'], 'NOT_IN_LEGACY_RENDER')

    def test_no_public_operational_contract_has_private_machine_bindings(self):
        for slug in load_registry()['presets']:
            book = load_playbook(slug)
            data = json.dumps(book).lower()
            self.assertNotIn('/home/', data)
            self.assertNotIn('c:\\users\\', data)
            self.assertNotIn('https://github.com/sethburkhardt21-dev/', data)
            self.assertNotIn('muse://auth', data)


if __name__ == '__main__':
    unittest.main()

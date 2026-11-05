import json
import tempfile
import unittest
from pathlib import Path

from muse_presets.catalog import load_registry, load_preset, validate_catalog, render_preset
from muse_presets.family import propose_handoff, verify_finding, FamilyLinkRefusal

class PresetCatalogTests(unittest.TestCase):
    def test_eleven_unique_specialists_and_one_service(self):
        reg = load_registry()
        self.assertEqual(len(reg['presets']), 11)
        self.assertEqual(len(set(reg['presets'])), 11)
        self.assertEqual(reg['services'], ['evidence-finder'])

    def test_every_preset_has_default_denied_family_link(self):
        for slug in load_registry()['presets']:
            with self.subTest(slug=slug):
                p = load_preset(slug)
                self.assertEqual(p['id'], slug)
                self.assertFalse(p['family_link']['enabled'])
                self.assertEqual(p['family_link']['transport'], 'unbound')

    def test_catalog_validation(self):
        self.assertEqual(validate_catalog(), [])

    def test_reject_traversal_slug(self):
        with self.assertRaises(ValueError):
            load_preset('../memory')

    def test_render_creates_all_user_editable_docs_in_a_new_destination(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / 'installed'
            render_preset('garden-companion', target, display_name='My Garden Guide')
            expected = {'AGENTS.md', 'SOUL.md', 'IDENTITY.md', 'USER.md', 'TOOLS.md', 'MEMORY.md', 'HEARTBEAT.md', 'PROACTIVE_PREFERENCES.md', 'SYSTEM_INSTRUCTIONS.md', 'SUBCHATS.md', 'HOOKS.md', 'FAMILY_LINK.json', 'ROLE_PLAYBOOK.md', 'RECEIPT.json'}
            self.assertEqual({x.name for x in target.iterdir()}, expected)
            self.assertIn('My Garden Guide', (target/'IDENTITY.md').read_text())
            self.assertEqual(json.loads((target/'FAMILY_LINK.json').read_text())['enabled'], False)
            self.assertIn('NOT an installed Muse runtime', (target/'RECEIPT.json').read_text())

    def test_render_does_not_overwrite_private_user_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp)/'existing'
            dest.mkdir()
            (dest/'MEMORY.md').write_text('private owner memory')
            with self.assertRaises(FileExistsError):
                render_preset('learning-coach', dest)
            self.assertEqual((dest/'MEMORY.md').read_text(), 'private owner memory')

    def test_invalid_display_name_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                render_preset('coordinator', Path(tmp)/'target', display_name='hi\nESCAPE')

class FamilyLinkTests(unittest.TestCase):
    def test_all_presets_have_a_preview_only_adapter(self):
        for slug in load_registry()['presets']:
            p = load_preset(slug)
            to = p['family_link']['suggested_receivers'][0]
            with self.subTest(slug=slug):
                preview = propose_handoff(slug, to, request_id=f'{slug}-001', capability='review')
                self.assertEqual(preview['state'], 'PROPOSAL_ONLY_NOT_SENT')
                self.assertFalse(preview['native_receipt'])
                self.assertFalse(preview['recipient_acknowledged'])

    def test_unknown_receiver_refused(self):
        with self.assertRaises(FamilyLinkRefusal):
            propose_handoff('coordinator', 'private-gateway', request_id='test-1', capability='review')

    def test_disallowed_receiver_refused(self):
        with self.assertRaises(FamilyLinkRefusal):
            propose_handoff('garden-companion', 'model-builder', request_id='test-1', capability='review')

    def test_self_route_refused(self):
        with self.assertRaises(FamilyLinkRefusal):
            propose_handoff('learning-coach', 'learning-coach', request_id='test-1', capability='review')

    def test_request_id_requires_safe_shape(self):
        with self.assertRaises(FamilyLinkRefusal):
            propose_handoff('coordinator', 'software-engineer', request_id='../oops', capability='review')

    def test_finder_finding_never_contains_a_verdict(self):
        finding = {'source_uri':'fixture://example', 'source_sha256':'a'*64, 'observation':'sample', 'result':'FOUND'}
        self.assertEqual(verify_finding(finding)['status'], 'VALID_FINDING_ONLY')
        with self.assertRaises(FamilyLinkRefusal):
            verify_finding({**finding, 'verdict':'PASS'})

    def test_finder_source_digest_is_required(self):
        with self.assertRaises(FamilyLinkRefusal):
            verify_finding({'source_uri':'fixture://example', 'observation':'no source digest','result':'FOUND'})

    def test_finding_rejects_fabricated_null_as_found(self):
        with self.assertRaises(FamilyLinkRefusal):
            verify_finding({'source_uri':'fixture://example','source_sha256':'a'*64,'observation':'','result':'FOUND'})

    def test_not_even_preview_claims_native_sender_or_effect(self):
        preview = propose_handoff('claims-adjudicator','evidence-finder',request_id='claim-1',capability='find')
        self.assertEqual(preview['admission'], 'HOST_AND_RECIPIENT_REQUIRED')
        self.assertNotIn('execute', preview)
        self.assertNotIn('sent_at', preview)

if __name__ == '__main__':
    unittest.main()

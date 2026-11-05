"""Acceptance cases for five offline, non-native priority specialist slices.

All inputs are synthetic and scoped to disposable test paths.
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from muse_presets.finder import find_exact_text
from muse_presets.claims import assess_scope
from muse_presets.garden import preview_date_shift
from muse_presets.learning import draft_supported_card
from muse_presets.reverse import compare_observed_flows


class FinderSliceTests(unittest.TestCase):
    def test_exact_match_and_full_bounded_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'receipt.txt').write_text('Case A\nFinding: alpha\nSecond observation\n', encoding='utf-8')
            result = find_exact_text(root, 'receipt.txt', 'Finding: alpha')
            self.assertEqual(result['result'], 'FOUND')
            self.assertEqual(result['observation'], (root / 'receipt.txt').read_bytes().decode('utf-8'))
            self.assertEqual(result['source_uri'], 'receipt.txt')
            self.assertEqual(len(result['source_sha256']), 64)
            self.assertNotIn('verdict', result)

    def test_honest_null(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'receipt.txt').write_text('No matching record', encoding='utf-8')
            out = find_exact_text(root, 'receipt.txt', 'never existed')
            self.assertEqual(out['result'], 'NOT_FOUND')
            self.assertEqual(out['observation'], '')

    def test_parent_escape_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                find_exact_text(Path(tmp), '../secret.txt', 'needle')

    def test_symlink_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'valid.txt').write_text('x', encoding='utf-8')
            link = root / 'alias.txt'
            try:
                link.symlink_to(root / 'valid.txt')
            except (OSError, NotImplementedError):
                self.skipTest('OS symlink creation unavailable')
            with self.assertRaises(ValueError):
                find_exact_text(root, 'alias.txt', 'x')

    def test_oversized_source_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'huge.txt').write_text('x' * 9000, encoding='utf-8')
            with self.assertRaises(ValueError):
                find_exact_text(root, 'huge.txt', 'x')


class ClaimsSliceTests(unittest.TestCase):
    def test_narrow_local_test_cannot_prove_native_use(self):
        result = assess_scope('The assistant is fully operational.', 'NATIVE_USED', 'LOCAL_TESTED',
                              conditions=('Source regression only',))
        self.assertEqual(result['disposition'], 'OVERCLAIM')
        self.assertEqual(result['conditions'], ['Source regression only'])
        self.assertFalse(result['independent_verified'])

    def test_narrow_claim_preserves_both_conditions(self):
        result = assess_scope('A local source parser passed.', 'LOCAL_TESTED', 'LOCAL_TESTED',
                              conditions=('No host execution', 'No credential grant'))
        self.assertEqual(result['disposition'], 'WITHIN_DECLARED_SCOPE_UNAUTHENTICATED')
        self.assertEqual(result['conditions'], ['No host execution', 'No credential grant'])

    def test_missing_conditions_refused(self):
        with self.assertRaises(ValueError):
            assess_scope('claim', 'LOCAL_TESTED', 'LOCAL_TESTED', conditions=())

    def test_unknown_grade_refused(self):
        with self.assertRaises(ValueError):
            assess_scope('claim', 'ALL_POWERFUL', 'LOCAL_TESTED', conditions=('test',))


class GardenSliceTests(unittest.TestCase):
    EVENT = {'id': 'planting-1', 'owner_id': 'demo-owner', 'revision': 7, 'date': '2026-11-10'}

    def test_date_shift_is_proposal_not_mutation(self):
        event = dict(self.EVENT)
        out = preview_date_shift(event, owner_id='demo-owner', expected_revision=7, days=5)
        self.assertEqual(out['proposed_date'], '2026-11-15')
        self.assertEqual(out['original_date'], '2026-11-10')
        self.assertEqual(event, self.EVENT)
        self.assertFalse(out['committed'])

    def test_wrong_owner_refused(self):
        with self.assertRaises(ValueError):
            preview_date_shift(self.EVENT, owner_id='other', expected_revision=7, days=1)

    def test_stale_revision_refused(self):
        with self.assertRaises(ValueError):
            preview_date_shift(self.EVENT, owner_id='demo-owner', expected_revision=6, days=1)

    def test_unbounded_shift_refused(self):
        with self.assertRaises(ValueError):
            preview_date_shift(self.EVENT, owner_id='demo-owner', expected_revision=7, days=400)


class LearningSliceTests(unittest.TestCase):
    def test_quoted_answer_must_exist_in_exact_source(self):
        out = draft_supported_card('Plants absorb light through chlorophyll.',
                                   source_id='lesson-1', question='What pigment absorbs light?',
                                   answer='chlorophyll')
        self.assertEqual(out['status'], 'DRAFT_REVIEW_REQUIRED')
        self.assertEqual(out['source_span'], [28, 39])
        self.assertFalse(out['reviewed'])

    def test_invented_answer_is_refused(self):
        with self.assertRaises(ValueError):
            draft_supported_card('The source states only water.', source_id='lesson-2',
                                 question='What is mentioned?', answer='calcium')

    def test_empty_source_id_is_refused(self):
        with self.assertRaises(ValueError):
            draft_supported_card('Clear source.', source_id='', question='What?', answer='source')


class ReverseSliceTests(unittest.TestCase):
    def test_detects_add_remove_and_change_from_supplied_fixtures(self):
        before = [
            {'action': 'click', 'target': 'save', 'outcome': 'modal'},
            {'action': 'click', 'target': 'help', 'outcome': 'page'},
        ]
        after = [
            {'action': 'click', 'target': 'save', 'outcome': 'toast'},
            {'action': 'click', 'target': 'export', 'outcome': 'file'},
        ]
        out = compare_observed_flows(before, after)
        self.assertEqual(out['changed'], ['click:save'])
        self.assertEqual(out['added'], ['click:export'])
        self.assertEqual(out['removed'], ['click:help'])
        self.assertFalse(out['network_activity'])
        self.assertFalse(out['target_accessed'])

    def test_duplicate_observation_refused(self):
        repeated = [{'action': 'click', 'target': 'save', 'outcome': 'a'}] * 2
        with self.assertRaises(ValueError):
            compare_observed_flows(repeated, [])

    def test_external_url_target_refused(self):
        with self.assertRaises(ValueError):
            compare_observed_flows([{'action': 'click', 'target': 'https://some.site', 'outcome': 'ok'}], [])

    def test_no_effect_for_identical_fixtures(self):
        a = [{'action': 'view', 'target': 'welcome', 'outcome': 'shown'}]
        out = compare_observed_flows(a, a)
        self.assertEqual(out['changed'], [])
        self.assertEqual(out['added'], [])
        self.assertEqual(out['removed'], [])


if __name__ == '__main__':
    unittest.main()

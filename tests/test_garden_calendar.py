"""Offline SQLite acceptance: host auth is simulated by explicit trusted fixtures.

Never interpret these tests as a Muse-native principal or calendar write grant.
"""
from __future__ import annotations

import sqlite3
from contextlib import closing
import tempfile
import unittest
from pathlib import Path

from muse_presets.garden_calendar import GardenCalendar, GardenScope


class GardenCalendarTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.database = Path(self.folder.name) / 'private-test-calendar.sqlite3'
        self.time_ms = 1_800_000_000_000
        self.authorized_owner = GardenScope('owner-one', 'space-one', 'garden-one', 'owner-one', True)
        self.authorized_specialist = GardenScope('owner-one', 'space-one', 'garden-one', 'garden-worker', False)
        self.calendar = GardenCalendar(self.database, authority=lambda: self.authorized_owner,
                                       clock_ms=lambda: self.time_ms)
        self.addCleanup(self.calendar.close)

    def _add(self, event_id='seed-one', date='2026-11-10'):
        return self.calendar.add_event(event_id=event_id, title='Plant bulbs', on_date=date)

    def _propose(self, proposal_id='proposal-one', changes=None):
        if changes is None:
            changes = [{'event_id': 'seed-one', 'expected_revision': 1, 'days': 3}]
        return self.calendar.propose_shift_batch(proposal_id=proposal_id, changes=changes)

    def _approve(self, proposal, operation_id='op-one', decision='approve'):
        return self.calendar.decide_batch(proposal_id=proposal['proposal_id'], digest=proposal['digest'],
                                          operation_id=operation_id, decision=decision)

    def test_host_authority_is_explicitly_required(self):
        absent = self.database.with_name('unbound.sqlite3')
        with self.assertRaisesRegex(ValueError, 'HOST_AUTHORITY_UNBOUND'):
            GardenCalendar(absent)
        self.assertFalse(absent.exists())

    def test_owner_creates_scoped_event_and_retrieves_it(self):
        created = self._add()
        self.assertEqual(created['revision'], 1)
        self.assertEqual(created['on_date'], '2026-11-10')
        self.assertEqual(created['state'], 'active')
        self.assertEqual(self.calendar.event('seed-one'), created)

    def test_cross_owner_event_and_proposal_invisible(self):
        self._add()
        other = GardenCalendar(self.database, authority=lambda: GardenScope('owner-two', 'space-one', 'garden-one', 'owner-two', True), clock_ms=lambda: self.time_ms)
        self.addCleanup(other.close)
        self.assertIsNone(other.event('seed-one'))
        with self.assertRaisesRegex(ValueError, 'EVENT_NOT_FOUND'):
            other.propose_shift_batch(proposal_id='owner-two-proposal', changes=[{'event_id': 'seed-one', 'expected_revision': 1, 'days': 1}])
        other.add_event(event_id='seed-one', title='Owner two', on_date='2026-12-01')
        self.assertEqual(self.calendar.event('seed-one')['title'], 'Plant bulbs')
        self.assertEqual(other.event('seed-one')['title'], 'Owner two')

    def test_unauthenticated_scope_and_specialist_owner_boundary(self):
        self._add()
        specialist = GardenCalendar(self.database, authority=lambda: self.authorized_specialist, clock_ms=lambda: self.time_ms)
        self.addCleanup(specialist.close)
        with self.assertRaisesRegex(ValueError, 'OWNER_APPROVAL_REQUIRED'):
            specialist.add_event(event_id='x', title='Fail', on_date='2026-11-01')
        proposed = specialist.propose_shift_batch(proposal_id='specialist-1', changes=[{'event_id': 'seed-one', 'expected_revision': 1, 'days': 1}])
        with self.assertRaisesRegex(ValueError, 'OWNER_APPROVAL_REQUIRED'):
            specialist.decide_batch(proposal_id='specialist-1', digest=proposed['digest'], operation_id='o1', decision='approve')
        with self.assertRaisesRegex(ValueError, 'OWNER_APPROVAL_REQUIRED'):
            specialist.receipt('o1')
        invalid = GardenCalendar(self.database, authority=lambda: {'owner_id': 'owner-one'}, clock_ms=lambda: self.time_ms)
        self.addCleanup(invalid.close)
        with self.assertRaisesRegex(ValueError, 'HOST_AUTHORITY_UNVERIFIED'):
            invalid.event('seed-one')

    def test_proposal_replay_returns_same_digest_and_conflicts_refused(self):
        self._add()
        proposed = self._propose()
        self.assertEqual(self._propose(), proposed)
        with self.assertRaisesRegex(ValueError, 'PROPOSAL_CONFLICT'):
            self._propose(changes=[{'event_id': 'seed-one', 'expected_revision': 1, 'days': 4}])
        self.assertEqual(self.calendar.event('seed-one')['revision'], 1)

    def test_review_is_read_only_and_uses_authoritative_records(self):
        self._add()
        proposed = self._propose()
        reviewed = self.calendar.review_batch('proposal-one')
        self.assertTrue(reviewed['ready'])
        self.assertEqual(reviewed['digest'], proposed['digest'])
        self.assertEqual(reviewed['changes'][0]['before_date'], '2026-11-10')
        self.assertEqual(reviewed['changes'][0]['after_date'], '2026-11-13')
        self.assertEqual(self.calendar.event('seed-one')['revision'], 1)

    def test_approval_is_atomic_and_receipt_persists_through_reopen(self):
        self._add()
        self._add('seed-two', '2026-11-11')
        changes = [
            {'event_id': 'seed-one', 'expected_revision': 1, 'days': 3},
            {'event_id': 'seed-two', 'expected_revision': 1, 'days': -2},
        ]
        proposal = self._propose('batch-2', changes)
        result = self._approve(proposal, operation_id='op-2')
        self.assertEqual(result['state'], 'approved')
        self.assertEqual(len(result['events']), 2)
        self.assertEqual(self.calendar.event('seed-one')['on_date'], '2026-11-13')
        self.assertEqual(self.calendar.event('seed-two')['on_date'], '2026-11-09')
        self.assertEqual(self.calendar.event('seed-two')['revision'], 2)
        self.assertEqual(self.calendar.receipt('op-2'), result)
        reopened = GardenCalendar(self.database, authority=lambda: self.authorized_owner, clock_ms=lambda: self.time_ms)
        self.addCleanup(reopened.close)
        self.assertEqual(reopened.receipt('op-2'), result)
        self.assertEqual(reopened.decide_batch(proposal_id='batch-2', digest=proposal['digest'], operation_id='op-2', decision='approve'), result)
        self.assertEqual(reopened.event('seed-one')['revision'], 2)

    def test_stale_item_refuses_whole_batch_without_partial_effect(self):
        self._add()
        self._add('seed-two', '2026-11-11')
        batch = self._propose('many', [
            {'event_id': 'seed-one', 'expected_revision': 1, 'days': 1},
            {'event_id': 'seed-two', 'expected_revision': 1, 'days': 1},
        ])
        fresher = self._propose('other', [{'event_id': 'seed-two', 'expected_revision': 1, 'days': 2}])
        self._approve(fresher, operation_id='op-other')
        review = self.calendar.review_batch('many')
        self.assertFalse(review['ready'])
        self.assertIn('STALE_REVISION', review['issues'])
        with self.assertRaisesRegex(ValueError, 'STALE_REVISION'):
            self._approve(batch, operation_id='op-many')
        self.assertEqual(self.calendar.event('seed-one')['on_date'], '2026-11-10')
        self.assertIsNone(self.calendar.receipt('op-many'))

    def test_decline_is_durable_without_event_mutation(self):
        self._add()
        proposed = self._propose()
        receipt = self._approve(proposed, operation_id='decline-1', decision='decline')
        self.assertEqual(receipt['state'], 'declined')
        self.assertEqual(receipt['events'], [])
        self.assertEqual(self.calendar.event('seed-one')['revision'], 1)
        self.assertEqual(self._approve(proposed, operation_id='decline-1', decision='decline'), receipt)
        with self.assertRaisesRegex(ValueError, 'PROPOSAL_NOT_PENDING'):
            self._approve(proposed, operation_id='decline-2', decision='decline')

    def test_operation_id_cannot_be_reused_for_changed_decision(self):
        self._add()
        proposal = self._propose()
        self._approve(proposal, operation_id='op-same')
        with self.assertRaisesRegex(ValueError, 'OPERATION_CONFLICT'):
            self._approve(proposal, operation_id='op-same', decision='decline')

    def test_expired_batch_rejected_and_bad_clock_fails_closed(self):
        self._add()
        proposal = self._propose()
        self.time_ms += 3_600_001
        with self.assertRaisesRegex(ValueError, 'PROPOSAL_EXPIRED'):
            self._approve(proposal, operation_id='late')
        self.assertIsNone(self.calendar.receipt('late'))
        badclock = GardenCalendar(self.database, authority=lambda: self.authorized_owner, clock_ms=lambda: -5)
        self.addCleanup(badclock.close)
        with self.assertRaisesRegex(ValueError, 'SERVER_CLOCK_INVALID'):
            badclock.propose_shift_batch(proposal_id='bad-clock', changes=[{'event_id': 'seed-one', 'expected_revision': 1, 'days': 1}])

    def test_owner_cancellation_prevents_proposal_approval(self):
        self._add()
        proposed = self._propose()
        self.calendar.cancel_event('seed-one', expected_revision=1)
        self.assertFalse(self.calendar.review_batch('proposal-one')['ready'])
        with self.assertRaisesRegex(ValueError, 'EVENT_NOT_ACTIVE'):
            self._approve(proposed)
        self.assertEqual(self.calendar.event('seed-one')['state'], 'cancelled')
        self.assertIsNone(self.calendar.receipt('op-one'))

    def test_bad_inputs_rejected_without_saving_effects(self):
        self._add()
        invalid = [
            [{'event_id': 'seed-one', 'expected_revision': True, 'days': 1}],
            [{'event_id': 'seed-one', 'expected_revision': 1, 'days': 31}],
            [{'event_id': 'seed-one', 'expected_revision': 1, 'days': 0}],
            [{'event_id': 'seed-one', 'expected_revision': 1, 'days': 1, 'owner_id': 'other'}],
            [{'event_id': 'seed-one', 'expected_revision': 1, 'days': 1}]*2,
            [],
            [{'event_id': 'seed-one', 'expected_revision': 1, 'days': 1}]*22,
        ]
        for n, changes in enumerate(invalid):
            with self.subTest(n=n), self.assertRaises(ValueError):
                self._propose('reject-'+str(n), changes)
        self.assertEqual(self.calendar.event('seed-one')['revision'], 1)
        with self.assertRaises(ValueError):
            self.calendar.add_event(event_id='bad/../path', title='Oops', on_date='2026-11-10')
        with self.assertRaises(ValueError):
            self.calendar.add_event(event_id='x', title='Bad\u202e', on_date='2026-11-10')
        with self.assertRaises(ValueError):
            self.calendar.add_event(event_id='x', title='okay', on_date='2026-02-30')

    def test_sql_failure_after_first_update_rolls_back_all(self):
        self._add()
        self._add('seed-two', '2026-11-11')
        proposed = self._propose('should-rollback', [
            {'event_id': 'seed-one', 'expected_revision': 1, 'days': 1},
            {'event_id': 'seed-two', 'expected_revision': 1, 'days': 2},
        ])
        with closing(sqlite3.connect(self.database)) as conn:
            with conn:
                conn.execute("CREATE TRIGGER abort_second BEFORE UPDATE ON garden_events WHEN NEW.event_key='seed-two' BEGIN SELECT RAISE(ABORT, 'inject'); END")
        with self.assertRaisesRegex(ValueError, 'OUTCOME_UNKNOWN'):
            self._approve(proposed, operation_id='failpoint')
        self.assertEqual(self.calendar.event('seed-one')['on_date'], '2026-11-10')
        self.assertEqual(self.calendar.event('seed-two')['on_date'], '2026-11-11')
        self.assertIsNone(self.calendar.receipt('failpoint'))

    def test_two_independent_connections_replay_same_operation_not_twice(self):
        import threading
        self._add()
        proposal = self._propose('concurrent')
        barrier = threading.Barrier(2)
        outcomes: list = []
        def attempt():
            with GardenCalendar(self.database, authority=lambda: self.authorized_owner, clock_ms=lambda: self.time_ms) as calendar:
                barrier.wait(timeout=5)
                try:
                    outcomes.append(calendar.decide_batch(proposal_id='concurrent', digest=proposal['digest'],
                                                          operation_id='concurrent-op', decision='approve'))
                except Exception as exc:
                    outcomes.append(exc)
        threads = [threading.Thread(target=attempt) for _ in range(2)]
        for thread in threads: thread.start()
        for thread in threads: thread.join(timeout=8)
        self.assertFalse(any(t.is_alive() for t in threads))
        self.assertEqual(len(outcomes), 2)
        self.assertEqual(outcomes[0], outcomes[1])
        self.assertIsInstance(outcomes[0], dict)
        self.assertEqual(self.calendar.event('seed-one')['revision'], 2)

    def test_owner_browser_flag_cannot_claim_another_actor(self):
        invalid = GardenCalendar(self.database,
                                 authority=lambda: GardenScope('one', 'space', 'site', 'different', True))
        self.addCleanup(invalid.close)
        with self.assertRaisesRegex(ValueError, 'HOST_AUTHORITY_UNVERIFIED'):
            invalid.list_events()

    def test_existing_site_with_same_identifiers_is_separate_in_another_space(self):
        self._add()
        other = GardenCalendar(self.database, authority=lambda: GardenScope('owner-one', 'space-two', 'garden-one', 'owner-one', True))
        self.addCleanup(other.close)
        self.assertIsNone(other.event('seed-one'))
        self.assertEqual(other.list_events()['events'], [])

    def test_bounded_list_explicitly_reports_omitted_events(self):
        for n in range(101):
            self._add(f'plant-{n:03d}')
        result = self.calendar.list_events()
        self.assertEqual(len(result['events']), 100)
        self.assertTrue(result['truncated'])
        self.assertEqual(result['scope'], 'LOCAL_SCOPED_REFERENCE')

    def test_expiry_is_exclusive_at_exact_deadline(self):
        self._add()
        proposal = self._propose()
        self.time_ms += 3_600_000
        with self.assertRaisesRegex(ValueError, 'PROPOSAL_EXPIRED'):
            self._approve(proposal, operation_id='exact-expiry')
        self.assertIsNone(self.calendar.receipt('exact-expiry'))

    def test_active_pending_quota_counts_only_active_proposals(self):
        self._add()
        limited = GardenCalendar(self.database, authority=lambda: self.authorized_owner,
                                 clock_ms=lambda: self.time_ms, pending_limit=1)
        self.addCleanup(limited.close)
        p1 = limited.propose_shift_batch(proposal_id='first', changes=[{'event_id':'seed-one','expected_revision':1,'days':1}])
        with self.assertRaisesRegex(ValueError, 'PROPOSAL_LIMIT'):
            limited.propose_shift_batch(proposal_id='second', changes=[{'event_id':'seed-one','expected_revision':1,'days':2}])
        limited.decide_batch(proposal_id='first', digest=p1['digest'], operation_id='op-first', decision='decline')
        p2 = limited.propose_shift_batch(proposal_id='second', changes=[{'event_id':'seed-one','expected_revision':1,'days':2}])
        self.assertEqual(p2['state'], 'pending')

    def test_proposal_ttl_overflow_fails_before_write(self):
        self._add()
        unsafe = GardenCalendar(self.database, authority=lambda: self.authorized_owner,
                                clock_ms=lambda: 2**53-1000)
        self.addCleanup(unsafe.close)
        with self.assertRaisesRegex(ValueError, 'SERVER_CLOCK_INVALID'):
            unsafe.propose_shift_batch(proposal_id='overflow', changes=[{'event_id':'seed-one','expected_revision':1,'days':1}])

    def test_symlink_database_parent_refused_if_supported(self):
        root = Path(self.folder.name)
        actual = root / 'real-folder'
        actual.mkdir()
        alias = root / 'alias-folder'
        try:
            alias.symlink_to(actual, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest('OS symlink creation unavailable')
        with self.assertRaisesRegex(ValueError, 'INVALID_DATABASE'):
            GardenCalendar(alias/'other.sqlite3', authority=lambda: self.authorized_owner)
        self.assertFalse((actual/'other.sqlite3').exists())

    def test_proposal_and_receipt_scope_include_site(self):
        self._add()
        other = GardenCalendar(self.database, authority=lambda: GardenScope('owner-one', 'space-one', 'garden-other', 'owner-one', True), clock_ms=lambda: self.time_ms)
        self.addCleanup(other.close)
        self.assertIsNone(other.event('seed-one'))
        self.assertIsNone(other.receipt('op-one'))
        with self.assertRaisesRegex(ValueError, 'PROPOSAL_NOT_FOUND'):
            other.review_batch('proposal-one')


if __name__ == '__main__':
    unittest.main()

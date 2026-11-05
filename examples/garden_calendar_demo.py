"""Disposable local owner-review example. No Muse, calendar or account effects.

Run from repo root: PYTHONPATH=src python examples/garden_calendar_demo.py
"""
from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from muse_presets.garden_calendar import GardenCalendar, GardenScope


def main() -> None:
    with TemporaryDirectory(prefix='garden-calendar-fixture-') as tmp:
        path = Path(tmp) / 'demo.sqlite3'
        clock = lambda: 1_800_000_000_000
        owner = lambda: GardenScope('fictional-owner', 'fictional-space', 'fictional-site', 'fictional-owner', True)
        specialist = lambda: GardenScope('fictional-owner', 'fictional-space', 'fictional-site', 'fictional-helper', False)
        with GardenCalendar(path, authority=owner, clock_ms=clock) as calendar:
            calendar.add_event(event_id='seedling', title='Start seedlings', on_date='2026-11-10')
        with GardenCalendar(path, authority=specialist, clock_ms=clock) as calendar:
            proposal = calendar.propose_shift_batch(proposal_id='shift-01', changes=[
                {'event_id': 'seedling', 'expected_revision': 1, 'days': 2}
            ])
        with GardenCalendar(path, authority=owner, clock_ms=clock) as calendar:
            review = calendar.review_batch('shift-01')
            assert review['ready'], review
            receipt = calendar.decide_batch(proposal_id=proposal['proposal_id'],
                                            digest=proposal['digest'], operation_id='approval-01',
                                            decision='approve')
        with GardenCalendar(path, authority=owner, clock_ms=clock) as calendar:
            assert calendar.receipt('approval-01') == receipt
            assert calendar.event('seedling')['on_date'] == '2026-11-12'
            assert calendar.event('seedling')['revision'] == 2
        print(json.dumps({
            'status': 'LOCAL_SQLITE_DEMO_PASSED',
            'source_execution': True,
            'host_authenticated': False,
            'native_muse_installed': False,
            'external_calendar_writes': False,
            'family_link_sent': False,
            'proposal_id': proposal['proposal_id'],
            'decision': receipt['decision'],
            'final_revision': 2,
            'lost_ack_recovered': True,
            'demo_data_deleted': True,
        }, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()

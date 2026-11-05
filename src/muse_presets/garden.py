"""Read-only garden calendar scenario preview; no persistent effects."""
from __future__ import annotations

from datetime import date, timedelta
import re

_ISO_DATE = re.compile(r'^\d{4}-\d{2}-\d{2}$')


def preview_date_shift(event: dict, *, owner_id: str, expected_revision: int, days: int) -> dict:
    """Propose a bounded date shift with owner and revision checks."""
    if not isinstance(event, dict) or not isinstance(owner_id, str) or not owner_id:
        raise ValueError('INVALID_EVENT_OR_OWNER')
    if event.get('owner_id') != owner_id:
        raise ValueError('WRONG_OWNER')
    revision = event.get('revision')
    if (type(revision) is not int or type(expected_revision) is not int
            or revision != expected_revision or revision < 0):
        raise ValueError('STALE_OR_INVALID_REVISION')
    if type(days) is not int or not -30 <= days <= 30:
        raise ValueError('SHIFT_OUTSIDE_BOUND')
    if not isinstance(event.get('id'), str) or not event['id']:
        raise ValueError('EVENT_ID_REQUIRED')
    value = event.get('date')
    if not isinstance(value, str) or not _ISO_DATE.fullmatch(value):
        raise ValueError('INVALID_DATE')
    try:
        original = date.fromisoformat(value)
        proposed = original + timedelta(days=days)
    except (ValueError, OverflowError) as exc:
        raise ValueError('INVALID_OR_OUT_OF_RANGE_DATE') from exc
    return {
        'schema': 'muse-presets/garden-date-preview-v1',
        'state': 'PROPOSAL_ONLY',
        'event_id': event['id'],
        'owner_id': owner_id,
        'expected_revision': expected_revision,
        'original_date': original.isoformat(),
        'proposed_date': proposed.isoformat(),
        'committed': False,
        'host_authorized': False,
    }

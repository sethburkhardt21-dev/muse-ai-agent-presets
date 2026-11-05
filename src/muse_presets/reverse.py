"""Static comparison of explicitly supplied, benign UI-observation fixtures.

This module does not open applications, capture traffic, attach debuggers,
inspect live hosts, probe remote agents, or execute untrusted samples.
"""
from __future__ import annotations

import re

_TARGET = re.compile(r'^[a-z][a-z0-9_-]{0,63}$')
_ACTIONS = frozenset({'view', 'click', 'scroll', 'hover'})


def _index_observations(items: list[dict]) -> dict[str, str]:
    if not isinstance(items, list) or len(items) > 256:
        raise ValueError('INVALID_OBSERVATIONS')
    indexed: dict[str, str] = {}
    for item in items:
        if not isinstance(item, dict) or set(item) != {'action', 'target', 'outcome'}:
            raise ValueError('INVALID_OBSERVATION_SHAPE')
        action, target, outcome = item['action'], item['target'], item['outcome']
        if not isinstance(action, str) or action not in _ACTIONS or not isinstance(target, str) or not _TARGET.fullmatch(target):
            raise ValueError('UNSUPPORTED_ACTION_OR_TARGET')
        if not isinstance(outcome, str) or not outcome or len(outcome) > 256:
            raise ValueError('INVALID_OUTCOME')
        key = f'{action}:{target}'
        if key in indexed:
            raise ValueError('DUPLICATE_ACTION_TARGET')
        indexed[key] = outcome
    return indexed


def compare_observed_flows(before: list[dict], after: list[dict]) -> dict:
    """Report fixture-only changes, preserving no pretended access to targets."""
    old = _index_observations(before)
    new = _index_observations(after)
    return {
        'schema': 'muse-presets/reverse-fixture-diff-v1',
        'changed': sorted(k for k in old.keys() & new.keys() if old[k] != new[k]),
        'added': sorted(new.keys() - old.keys()),
        'removed': sorted(old.keys() - new.keys()),
        'network_activity': False,
        'target_accessed': False,
        'native_invoked': False,
    }

"""Inspect schema changes, versioned events and supplied SQLite plan details.

All functions operate on supplied JSON and return new data. They do not connect
to a database, execute SQL, apply a migration or claim distributed delivery.
"""
from __future__ import annotations
import copy
from .common import boolean, canonical, fields, identifier, integer, require, rows, text


def _columns(raw):
    result = {}
    for col in rows(raw, 256):
        fields(col, {'name', 'type', 'nullable'})
        name = identifier(col['name'])
        require(name not in result, 'DUPLICATE_COLUMN')
        kind = text(col['type'], 64)
        require(kind in {'integer', 'text', 'real', 'boolean', 'decimal', 'timestamp', 'json', 'blob'},
                'UNSUPPORTED_LOGICAL_TYPE')
        result[name] = {'name': name, 'type': kind, 'nullable': boolean(col['nullable'])}
    return result


def schema_evolution(inputs: dict) -> dict:
    fields(inputs, {'current', 'proposed', 'row_count'})
    before, after = _columns(inputs['current']), _columns(inputs['proposed'])
    count = integer(inputs['row_count'])
    added, removed = sorted(after.keys() - before.keys()), sorted(before.keys() - after.keys())
    type_changes = sorted(name for name in before.keys() & after.keys()
                          if before[name]['type'] != after[name]['type'])
    tightened = sorted(name for name in before.keys() & after.keys()
                       if before[name]['nullable'] and not after[name]['nullable'])
    backfill = sorted(name for name in added if not after[name]['nullable'] and count > 0)
    migration = bool(removed or type_changes or tightened or backfill)
    return {'status': 'migration_required' if migration else 'compatible',
            'added': added, 'removed': removed, 'type_changes': type_changes,
            'nullability_tightened': tightened, 'backfill_required': backfill,
            'row_count': count, 'database_modified': False,
            'scope': 'logical_contract_only; database locks, defaults, indexes and constraints require engine-specific review'}


def _event(raw):
    fields(raw, {'key', 'version', 'value', 'deleted'})
    identifier(raw['key']); integer(raw['version']); boolean(raw['deleted'])
    require(not raw['deleted'] or raw['value'] is None, 'TOMBSTONE_VALUE_MUST_BE_NULL')
    canonical(raw['value'])
    return copy.deepcopy(raw)


def incremental_pipeline(inputs: dict) -> dict:
    fields(inputs, {'state', 'events'})
    before = [_event(v) for v in rows(inputs['state'], 1000)]
    events = [_event(v) for v in rows(inputs['events'], 5000)]
    state = {r['key']: r for r in before}
    require(len(state) == len(before), 'DUPLICATE_STATE_KEY')
    grouped = {}
    for item in [*before, *events]:
        pair = (item['key'], item['version'])
        grouped.setdefault(pair, {})[canonical(item)] = item
    conflicts = sorted({key for (key, _), variants in grouped.items() if len(variants) > 1})
    if conflicts:
        return {'status': 'conflict', 'state': before,
                'conflicting_keys': conflicts, 'stale_events': 0, 'duplicate_events': 0,
                'applied_keys': [], 'external_writes': False}
    final = dict(state)
    for (key, version), variants in sorted(grouped.items()):
        item = next(iter(variants.values()))
        if key not in final or version > final[key]['version']:
            final[key] = item
    # Counters describe the batch independent of arrival order. Repetitions are
    # counted against the initial state and earlier identical batch records.
    seen = {canonical(x) for x in before}
    duplicates = 0
    unique_events = {}
    for item in events:
        encoded = canonical(item)
        if encoded in seen:
            duplicates += 1
        seen.add(encoded)
        unique_events[encoded] = item
    stale = sum(item['version'] < final[item['key']]['version'] for item in unique_events.values())
    changed = sorted(key for key, item in final.items() if key not in state or item != state[key])
    return {'status': 'applied', 'state': [final[k] for k in sorted(final)],
            'conflicting_keys': [], 'stale_events': stale, 'duplicate_events': duplicates,
            'applied_keys': changed, 'external_writes': False}


def query_plan_review(inputs: dict) -> dict:
    """Classify supplied SQLite EXPLAIN QUERY PLAN detail strings, not timing.

    SQLite warns that its textual plan format may change between releases.
    Unknown detail rows are retained, never interpreted as efficient execution.
    Reference: https://www.sqlite.org/eqp.html
    """
    fields(inputs, {'details'})
    details = [text(v, 4000) for v in rows(inputs['details'], 1000, 1)]
    result = {'table_scans': [], 'index_scans': [], 'searches': [],
              'temporary_sorts': [], 'unclassified': []}
    for original in details:
        line = original.strip().upper()
        if line.startswith('SCAN '):
            key = 'index_scans' if 'USING ' in line and 'INDEX ' in line else 'table_scans'
        elif line.startswith('SEARCH '):
            key = 'searches'
        elif line.startswith('USE TEMP B-TREE'):
            key = 'temporary_sorts'
        else:
            key = 'unclassified'
        result[key].append(original)
    result.update({'performance_proven': False, 'query_executed': False,
                   'review': 'measure_cardinality_and_runtime_before_changing_indexes'})
    return result

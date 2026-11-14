"""Review automation plans and supplied observations; never dispatch effects.

Approval fields are declarations to check, not authenticated permission grants.
These tools do not replace the host's existing task, identity or effect authority.
"""
from __future__ import annotations
import re
from .common import boolean, canonical, fields, identifier, integer, require, rows, unique_ids


def automation_contract(inputs: dict) -> dict:
    fields(inputs, {'allowed_targets', 'steps'})
    targets = set(unique_ids(inputs['allowed_targets'], 100))
    require(bool(targets), 'TARGET_SCOPE_REQUIRED')
    steps = {}
    for item in rows(inputs['steps'], 200, 1):
        fields(item, {'id', 'depends_on', 'kind', 'target', 'approval', 'idempotency_key'})
        name = identifier(item['id'])
        require(name not in steps, 'DUPLICATE_STEP')
        deps = unique_ids(item['depends_on'], 200)
        require(name not in deps, 'SELF_DEPENDENCY')
        require(item['kind'] in ('read', 'draft', 'write', 'send', 'publish', 'delete'), 'UNKNOWN_STEP_KIND')
        identifier(item['target']); boolean(item['approval'])
        key = item['idempotency_key']
        require(key is None or (type(key) is str and bool(key.strip()) and len(key) <= 128),
                'INVALID_IDEMPOTENCY_KEY')
        steps[name] = item
    require(all(set(s['depends_on']) <= steps.keys() for s in steps.values()), 'MISSING_DEPENDENCY')
    pending, order = set(steps), []
    while pending:
        ready = sorted(k for k in pending if set(steps[k]['depends_on']) <= set(order))
        require(bool(ready), 'CYCLIC_DEPENDENCIES')
        order.extend(ready); pending.difference_update(ready)
    blocked = []
    blocked_ids = set()
    for name in order:
        step = steps[name]
        reasons = []
        if step['target'] not in targets:
            reasons.append('target_out_of_scope')
        if step['kind'] not in ('read', 'draft'):
            if not step['approval']:
                reasons.append('approval_missing')
            if not step['idempotency_key']:
                reasons.append('idempotency_key_missing')
        if set(step['depends_on']) & blocked_ids:
            reasons.append('dependency_blocked')
        if reasons:
            blocked_ids.add(name); blocked.append({'id': name, 'reasons': reasons})
    return {'order': order, 'blocked_steps': blocked,
            'review': 'blocked' if blocked else 'ready_for_host_review',
            'execution_authorized': False, 'external_actions_performed': False,
            'authority': 'existing host must independently verify actor, target, approval and operation state'}


def selector_resilience(inputs: dict) -> dict:
    fields(inputs, {'target_id', 'candidates'})
    target = identifier(inputs['target_id'])
    seen, eligible, rejected = set(), [], []
    priority = {'role': 0, 'testid': 1, 'label': 2, 'css': 3}
    for candidate in rows(inputs['candidates'], 100):
        fields(candidate, {'id', 'strategy', 'matches', 'visible', 'stable', 'target_id'})
        name = identifier(candidate['id'])
        require(name not in seen, 'DUPLICATE_SELECTOR_ID'); seen.add(name)
        require(type(candidate['strategy']) is str and candidate['strategy'] in priority, 'UNSUPPORTED_SELECTOR_STRATEGY')
        count = integer(candidate['matches'], maximum=1000000)
        visible, stable = boolean(candidate['visible']), boolean(candidate['stable'])
        bound = identifier(candidate['target_id'])
        reasons = []
        if bound != target: reasons.append('target_mismatch')
        if count != 1: reasons.append('not_unique')
        if not visible: reasons.append('not_visible')
        if not stable: reasons.append('unstable')
        if reasons: rejected.append({'id': name, 'reasons': reasons})
        else: eligible.append((priority[candidate['strategy']], name))
    eligible.sort()
    return {'selected': eligible[0][1] if eligible else None,
            'eligible': [name for _, name in eligible], 'rejected': rejected,
            'status': 'candidate_identified' if eligible else 'needs_observation',
            'browser_action_performed': False,
            'scope': 'supplied locator observations only; re-observe immediately before an authorized browser action'}


def effect_reconciliation(inputs: dict) -> dict:
    fields(inputs, {'operation', 'evidence'})
    operation = fields(inputs['operation'], {'id', 'request_sha256', 'target'})
    identifier(operation['id']); identifier(operation['target'])
    require(type(operation['request_sha256']) is str and
            re.fullmatch(r'[a-f0-9]{64}', operation['request_sha256']) is not None, 'INVALID_REQUEST_HASH')
    states, receipts, conflicts = set(), set(), False
    seen = set()
    for row in rows(inputs['evidence'], 1000):
        fields(row, {'operation_id', 'request_sha256', 'target', 'state', 'receipt_id'})
        identifier(row['operation_id']); identifier(row['target'])
        require(type(row['request_sha256']) is str and re.fullmatch(r'[a-f0-9]{64}', row['request_sha256']) is not None,
                'INVALID_EVIDENCE_REQUEST_HASH')
        require(row['state'] in ('unknown', 'started', 'success', 'failure', 'not_started'), 'INVALID_EFFECT_STATE')
        require(row['receipt_id'] is None or type(row['receipt_id']) is str, 'INVALID_RECEIPT_ID')
        if row['receipt_id'] is not None: identifier(row['receipt_id'])
        encoded = canonical(row)
        if encoded in seen: continue
        seen.add(encoded)
        if (row['operation_id'], row['request_sha256'], row['target']) != (
                operation['id'], operation['request_sha256'], operation['target']):
            conflicts = True
            continue
        if row['state'] in ('success', 'failure', 'not_started'):
            if row['receipt_id'] is None:
                states.add('unknown')
            else:
                states.add(row['state']); receipts.add(row['receipt_id'])
        else:
            states.add('unknown')
    terminal = states & {'success', 'failure', 'not_started'}
    if conflicts or len(terminal) > 1:
        observation = 'conflict'
    elif 'unknown' in states or not terminal:
        observation = 'unknown'
    else:
        observation = next(iter(terminal))
    return {'observation': observation, 'receipt_ids': sorted(receipts),
            'requires_provider_readback': True, 'provider_evidence_authenticated': False,
            'retry_authorized': False, 'external_actions_performed': False,
            'scope': 'consistency review only; retain original provider records and never infer effect permission'}

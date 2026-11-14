"""Read-only reliability calculations from explicit event and load measurements."""
from __future__ import annotations
from decimal import Decimal, ROUND_CEILING
from .common import decimal_text, decimal_value, fields, identifier, integer, require, rows, timestamp


def service_objectives(inputs: dict) -> dict:
    fields(inputs, {'good_events', 'total_events', 'target', 'window_minutes'})
    good, total = integer(inputs['good_events']), integer(inputs['total_events'])
    require(good <= total, 'GOOD_EVENTS_EXCEED_TOTAL')
    target = decimal_value(inputs['target'], maximum='1', lower_open=True, upper_open=True)
    window = integer(inputs['window_minutes'], 1, 525600)
    bad = total - good
    allowed = Decimal(total) * (1 - target)
    remaining = allowed - bad
    sli = Decimal(good) / total if total else None
    burn = Decimal(bad) / allowed if total else None
    return {'status': 'no_traffic' if not total else ('exhausted' if remaining <= 0 else 'within_budget'),
            'sli': decimal_text(sli) if sli is not None else None,
            'bad_events': bad, 'allowed_bad_events': decimal_text(allowed),
            'remaining_bad_events': decimal_text(remaining),
            'burn_rate': decimal_text(burn) if burn is not None else None,
            'window_minutes': window, 'monitoring_configured': False,
            'scope': 'event_ratio_for_supplied_window; not a time-based uptime or multi-window paging policy'}


def capacity_planning(inputs: dict) -> dict:
    fields(inputs, {'demand_rps', 'per_instance_rps', 'target_utilization', 'instances', 'reserve_instances'})
    demand = decimal_value(inputs['demand_rps'])
    capacity = decimal_value(inputs['per_instance_rps'], lower_open=True)
    utilization = decimal_value(inputs['target_utilization'], maximum='1', lower_open=True)
    current = integer(inputs['instances'], maximum=1000000)
    reserve = integer(inputs['reserve_instances'], maximum=1000000)
    per_node = capacity * utilization
    serving = int((demand / per_node).to_integral_value(rounding=ROUND_CEILING))
    required = serving + reserve
    require(required <= 1000000, 'CAPACITY_RESULT_EXCEEDS_BUDGET')
    return {'required_serving_instances': serving, 'required_instances': required,
            'additional_instances': max(0, required - current),
            'effective_rps_per_instance': decimal_text(per_node),
            'available_rps_after_reserve': decimal_text(max(0, current - reserve) * per_node),
            'scale_actions_performed': False,
            'assumptions': ['measured per-instance capacity applies to this workload',
                            'load is evenly distributable', 'reserve instances do not serve normal demand']}


def incident_triage(inputs: dict) -> dict:
    fields(inputs, {'events', 'as_of'})
    now = timestamp(inputs['as_of'])
    ordered = []
    ids = set()
    for raw in rows(inputs['events'], 1000, 1):
        fields(raw, {'id', 'at', 'kind'})
        name = identifier(raw['id'])
        require(name not in ids, 'DUPLICATE_INCIDENT_EVENT')
        ids.add(name)
        require(raw['kind'] in ('start', 'detected', 'mitigation', 'resolved', 'observation'),
                'UNKNOWN_INCIDENT_EVENT')
        at = timestamp(raw['at'])
        require(at <= now, 'EVENT_AFTER_OBSERVATION_TIME')
        ordered.append((at, name, raw['kind']))
    ordered.sort()
    starts = [at for at, _, kind in ordered if kind == 'start']
    ends = [at for at, _, kind in ordered if kind == 'resolved']
    require(len(starts) == 1 and len(ends) <= 1, 'SINGLE_INCIDENT_BOUNDARY_REQUIRED')
    start = starts[0]
    require(all(at >= start for at, _, _ in ordered), 'EVENT_BEFORE_INCIDENT_START')
    end = ends[0] if ends else None
    mitigations = [at for at, _, kind in ordered if kind == 'mitigation']
    mitigation = min(mitigations) if mitigations else None
    require(end is None or all(at <= end for at in mitigations), 'MITIGATION_AFTER_RESOLUTION')
    return {'status': 'resolved' if end else 'open',
            'event_order': [name for _, name, _ in ordered],
            'time_to_mitigate_seconds': (mitigation-start).total_seconds() if mitigation else None,
            'time_to_resolve_seconds': (end-start).total_seconds() if end else None,
            'elapsed_seconds': ((end or now)-start).total_seconds(),
            'source': 'supplied_event_records', 'remediation_performed': False,
            'scope': 'one incident; durations are not population-average reliability metrics'}

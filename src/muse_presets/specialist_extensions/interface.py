"""Inspect declared interface tokens and state graphs, not browser conformance."""
from __future__ import annotations
import re
from decimal import Decimal
from .common import decimal_value, fields, identifier, require, rows, unique_ids


def _luminance(color: str) -> float:
    require(type(color) is str and re.fullmatch(r'#[0-9a-fA-F]{6}', color) is not None,
            'OPAQUE_SRGB_HEX_REQUIRED')
    channels = [int(color[i:i+2], 16)/255 for i in (1, 3, 5)]
    linear = [c/12.92 if c <= 0.04045 else ((c+0.055)/1.055)**2.4 for c in channels]
    return sum(c*w for c, w in zip(linear, (0.2126, 0.7152, 0.0722)))


def design_token_audit(inputs: dict) -> dict:
    """Apply the W3C sRGB luminance/contrast formula without rounding to pass.

    Reference: https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html
    Only opaque 6-digit sRGB token values are admitted. Typography, compositing,
    focus, interaction, semantics and actual rendering remain separate checks.
    """
    fields(inputs, {'tokens', 'pairs'})
    tokens = inputs['tokens']
    require(type(tokens) is dict and 1 <= len(tokens) <= 500, 'TOKEN_SET_REQUIRED')
    luminance = {identifier(name): _luminance(color) for name, color in tokens.items()}
    seen, results = set(), []
    for pair in rows(inputs['pairs'], 1000, 1):
        fields(pair, {'id', 'foreground', 'background', 'minimum_ratio'})
        name = identifier(pair['id'])
        require(name not in seen, 'DUPLICATE_COLOR_PAIR'); seen.add(name)
        front, back = identifier(pair['foreground']), identifier(pair['background'])
        require(front in tokens and back in tokens, 'MISSING_COLOR_TOKEN')
        threshold = decimal_value(pair['minimum_ratio'], minimum='1', maximum='21')
        high, low = sorted((luminance[front], luminance[back]), reverse=True)
        ratio = (high+0.05)/(low+0.05)
        results.append({'id': name, 'foreground': front, 'background': back,
                        'ratio': round(ratio, 6), 'minimum_ratio': float(threshold),
                        'passed': Decimal.from_float(ratio) >= threshold})
    return {'status': 'pass' if all(r['passed'] for r in results) else 'fail',
            'pairs': results, 'conformance_certified': False, 'rendered_ui_inspected': False,
            'scope': 'opaque_srgb_token_pair_calculation_only'}


def interaction_state_coverage(inputs: dict) -> dict:
    fields(inputs, {'states', 'initial', 'terminal_states', 'required_states', 'transitions'})
    states = set(unique_ids(inputs['states'], 500))
    require(bool(states), 'STATE_SET_REQUIRED')
    initial = identifier(inputs['initial'])
    require(initial in states, 'INITIAL_STATE_MISSING')
    terminal = set(unique_ids(inputs['terminal_states'], 500))
    required = set(unique_ids(inputs['required_states'], 500))
    require(terminal <= states, 'TERMINAL_STATE_MISSING')
    links = {s: set() for s in states}
    rules = set()
    for transition in rows(inputs['transitions'], 2000):
        fields(transition, {'from', 'event', 'to'})
        origin, event, target = (identifier(transition[k]) for k in ('from', 'event', 'to'))
        require(origin in states and target in states, 'UNKNOWN_TRANSITION_STATE')
        key = (origin, event)
        require(key not in rules, 'DUPLICATE_OR_NONDETERMINISTIC_TRANSITION')
        rules.add(key); links[origin].add(target)
    reached, todo = {initial}, [initial]
    while todo:
        origin = todo.pop()
        for target in links[origin] - reached:
            reached.add(target); todo.append(target)
    dead = sorted(s for s in reached if not links[s] and s not in terminal)
    missing, unreachable = sorted(required-states), sorted(states-reached)
    return {'status': 'complete_declared_graph' if not (dead or missing or unreachable) else 'incomplete',
            'reachable': sorted(reached), 'unreachable': unreachable,
            'missing_required': missing, 'dead_ends': dead,
            'browser_tested': False, 'scope': 'declared_states_and_transitions_only'}

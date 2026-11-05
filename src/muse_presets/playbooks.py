"""Structured specialist work methods, not installed skills or host authority.

The source contracts are newly authored neutral guidance. They cannot grant tools,
start jobs, authenticate reviewers, or substitute for native Muse execution.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

_ID = re.compile(r'^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$')
_METHOD_FIELDS = frozenset({'id', 'trigger', 'steps', 'evidence', 'stop_rule', 'handoff_to'})
_CANARY_FIELDS = frozenset({'grade', 'task', 'observable_result', 'negative_test'})
_ROOT_FIELDS = frozenset({'schema', 'role_id', 'purpose', 'optional_tool_categories',
                          'hard_boundaries', 'methods', 'first_canary'})


def _plain(value: object, *, limit: int = 1000) -> bool:
    return (isinstance(value, str) and 0 < len(value.strip()) <= limit
            and all((ch.isprintable() or ch == '\t') for ch in value)
            and not any(ch in value for ch in ('\r', '\n')))


def _bounded_strings(value: object, minimum: int, maximum: int) -> bool:
    return (isinstance(value, list) and minimum <= len(value) <= maximum
            and all(_plain(x) for x in value) and len(value) == len(set(value)))


def load_playbook(slug: str, *, source_root: Path | None = None) -> dict:
    """Read only the canonical per-role playbook; reject source-path indirection."""
    if not isinstance(slug, str) or not _ID.fullmatch(slug):
        raise ValueError('INVALID_PRESET_ID')
    if source_root is None:
        source_root = Path(__file__).resolve().parents[2]
    path = source_root / 'presets' / slug / 'playbook.json'
    if path.is_symlink() or not path.is_file():
        raise ValueError('MISSING_OR_SYMLINK_PLAYBOOK')
    try:
        parsed = json.loads(path.read_text(encoding='utf-8'))
    except json.JSONDecodeError as exc:
        raise ValueError('INVALID_PLAYBOOK_JSON') from exc
    if not isinstance(parsed, dict):
        raise ValueError('INVALID_PLAYBOOK_TYPE')
    return parsed


def validate_playbook(book: object, preset: dict) -> list[str]:
    """Validate method shape and role routing; independent execution is separate."""
    if not isinstance(book, dict) or set(book) != _ROOT_FIELDS:
        return ['INVALID_PLAYBOOK_SHAPE']
    if book['schema'] != 'muse-presets/playbook-v1':
        return ['INVALID_PLAYBOOK_SCHEMA']
    if book['role_id'] != preset['id']:
        return ['ROLE_ID_MISMATCH']
    if not _plain(book['purpose'], limit=350):
        return ['INVALID_PURPOSE']
    if (not _bounded_strings(book['optional_tool_categories'], 2, 8)
            or not all(_ID.fullmatch(x) for x in book['optional_tool_categories'])):
        return ['INVALID_TOOL_CATEGORIES']
    if not _bounded_strings(book['hard_boundaries'], 2, 8):
        return ['INVALID_BOUNDARIES']
    canary = book['first_canary']
    if not isinstance(canary, dict) or set(canary) != _CANARY_FIELDS:
        return ['INVALID_CANARY_SHAPE']
    if canary['grade'] != 'SOURCE_ONLY':
        return ['INVALID_CANARY_GRADE']
    if not all(_plain(canary[field], limit=600) for field in ('task', 'observable_result', 'negative_test')):
        return ['INVALID_CANARY_CONTENT']
    methods = book['methods']
    if not isinstance(methods, list) or len(methods) != 3:
        return ['INVALID_METHOD_COUNT']
    allowed = preset['family_link']['suggested_receivers']
    if not isinstance(allowed, list) or any(not isinstance(x,str) for x in allowed):
        return ['INVALID_RECEIVER_POLICY']
    seen: set[str] = set()
    for method in methods:
        if not isinstance(method, dict) or set(method) != _METHOD_FIELDS:
            return ['INVALID_METHOD_SHAPE']
        name = method['id']
        if not isinstance(name, str) or not _ID.fullmatch(name) or name in seen:
            return ['INVALID_OR_DUPLICATE_METHOD_ID']
        seen.add(name)
        if method['handoff_to'] not in allowed:
            return ['BAD_HANDOFF_RECEIVER']
        if not _plain(method['trigger'], limit=400) or not _plain(method['stop_rule'], limit=450):
            return ['INVALID_TRIGGER_OR_STOP_RULE']
        if not _bounded_strings(method['steps'], 3, 6):
            return ['INVALID_STEPS']
        if not _bounded_strings(method['evidence'], 2, 5):
            return ['INVALID_EVIDENCE']
    return []


def render_playbook(book: dict, *, display_name: str, role_title: str) -> str:
    """Generate a human-readable local policy document, not an executable hook."""
    lines = [f'# Operational playbook — {display_name}', '',
             f'**Preset:** {role_title} (`{book["role_id"]}`)',
             '**Grade:** SOURCE-ONLY guidance; no native Muse tool, subchat, model or connector is installed.', '',
             '## Mission', '', book['purpose'], '', '## Preferred optional tool categories', '',
             ', '.join(f'`{x}`' for x in book['optional_tool_categories']),
             '', 'These are capability categories, not tool registrations. Discover real permissions and schemas before use.',
             '', '## Required limits', '']
    lines.extend(f'- {entry}' for entry in book['hard_boundaries'])
    lines.extend(['', '## Specialist methods', ''])
    for i, method in enumerate(book['methods'], 1):
        lines.extend([f'### {i}. {method["id"]}', '', f'**When:** {method["trigger"]}', '', '**Procedure:**'])
        lines.extend(f'{j}. {step}' for j, step in enumerate(method['steps'], 1))
        lines.extend(['', '**Evidence to return:**'])
        lines.extend(f'- {entry}' for entry in method['evidence'])
        lines.extend(['', f'**Stop condition:** {method["stop_rule"]}',
                      f'**Suggested handoff:** `{method["handoff_to"]}` (proposal only, never an automatic send)', ''])
    canary = book['first_canary']
    lines.extend(['## First acceptance exercise', '',
                  f'**Toy task:** {canary["task"]}',
                  f'**Expected observable result:** {canary["observable_result"]}',
                  f'**Negative case:** {canary["negative_test"]}',
                  '', 'Passing a local example does not establish the role is wired, used, useful, or independently verified in Muse.',
                  'Family Link is off unless a real receiving account separately grants it.', ''])
    return '\n'.join(lines)

"""Portable T04 profiles and read-only change previews; never a host installer.

Reuse existing neutral templates and role playbook rendering. Freeze source
bytes before writing, preserve partial stages, and compare against trusted
repository source rather than trusting a candidate's editable manifest.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from string import Template
from typing import Any

from .catalog import DISPLAY, DOCUMENTS, ROOT, SLUG
from .native_canary import _no_duplicate_json, _reject_constant
from .native_skill_binding import _regular_bytes, _unsafe_source_path
from .playbooks import render_playbook, validate_playbook

SOURCE_ROOT = ROOT
SCHEMA = 'r40/system-profile-v1'
EXTRA_DOCUMENTS = ('CONNECTORS.md', 'BROWSER.md', 'VOICE.md')
OWNER_FILES = frozenset({'IDENTITY.md', 'SOUL.md', 'USER.md', 'MEMORY.md',
                         'PROACTIVE_PREFERENCES.md'})
MANIFEST = 'PROFILE_MANIFEST.json'
MAX_FILE_BYTES = 131072
_SHA = re.compile(r'^[0-9a-f]{64}$')


def _json(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + '\n').encode('utf-8')


def _parse(data: bytes) -> Any:
    return json.loads(data.decode('utf-8'), object_pairs_hook=_no_duplicate_json,
                      parse_constant=_reject_constant)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _source(role: str) -> dict[str, bytes]:
    if not isinstance(role, str) or not SLUG.fullmatch(role):
        raise ValueError('INVALID_PROFILE_ROLE')
    paths = ['presets/catalog.json', f'presets/{role}/preset.json',
             f'presets/{role}/playbook.json']
    paths += ['templates/profile/' + name for name in DOCUMENTS]
    paths += ['templates/system-profile/' + name for name in EXTRA_DOCUMENTS]
    frozen = {name: _regular_bytes(SOURCE_ROOT / name, MAX_FILE_BYTES) for name in paths}
    catalog = _parse(frozen['presets/catalog.json'])
    roles = catalog.get('presets') if isinstance(catalog, dict) else None
    if (not isinstance(roles, list) or len(roles) != 11 or
            any(not isinstance(x, str) for x in roles) or len(set(roles)) != 11 or role not in roles):
        raise ValueError('INVALID_PROFILE_CATALOG')
    return frozen


def _binding(role: str) -> dict:
    return {
        'schema': 'r40/profile-host-binding-v1', 'role': role,
        'target_host': 'RECEIVING_OWNER_SELECTS_SUPPORTED_HOST',
        'owner_id': None, 'agent_id': None, 'provider_session_id': None,
        'native_loaded': False, 'native_registered': False,
        'model_invocation_verified': False, 'recipient_readback_verified': False,
        'external_effect_authorized': False,
        'schedule_enabled': False, 'hooks_enabled': False,
        'family_link_enabled': False, 'voice_enabled': False,
        'instruction_precedence': 'DECLARED_ONLY_HOST_POLICY_ALWAYS_PRECEDES_DRAFT',
        'profile_directory': 'profile',
        'host_apply': 'NOT_IMPLEMENTED_REQUIRES_SUPPORTED_OWNER_SCOPED_PROVIDER',
        'state_policy': 'PRESERVE_RECEIVING_OWNER_MEMORY_AND_PREFERENCES',
    }


def _build(role: str, display_name: str | None) -> tuple[dict[str, bytes], dict, dict[str, bytes]]:
    frozen = _source(role)
    preset = _parse(frozen[f'presets/{role}/preset.json'])
    book = _parse(frozen[f'presets/{role}/playbook.json'])
    if not isinstance(preset, dict) or preset.get('id') != role:
        raise ValueError('PROFILE_PRESET_MISMATCH')
    family = preset.get('family_link')
    if (preset.get('native_muse_status') != 'UNBOUND' or not isinstance(family, dict)
            or family.get('enabled') is not False or family.get('transport') != 'unbound'
            or family.get('trusted_signer') is not None or family.get('native_recipient') is not None):
        raise ValueError('PROFILE_POLICY_NOT_DEFAULT_DENY')
    if validate_playbook(book, preset):
        raise ValueError('INVALID_PROFILE_PLAYBOOK')
    name = role.replace('-', ' ').title() if display_name is None else display_name
    if not isinstance(name, str) or not DISPLAY.fullmatch(name):
        raise ValueError('INVALID_PROFILE_DISPLAY_NAME')
    values = {'display_name': name, 'role_id': role, 'role_title': preset['title'],
              'role_description': preset['description']}
    content = {}
    for filename in (*DOCUMENTS, *EXTRA_DOCUMENTS):
        folder = 'profile' if filename in DOCUMENTS else 'system-profile'
        template = frozen[f'templates/{folder}/{filename}'].decode('utf-8')
        text = Template(template).substitute(values)
        if '\x00' in text or len(text.encode('utf-8')) > MAX_FILE_BYTES:
            raise ValueError('INVALID_PROFILE_TEMPLATE')
        content['profile/' + filename] = text.encode('utf-8')
    content['profile/ROLE_PLAYBOOK.md'] = render_playbook(
        book, display_name=name, role_title=preset['title']).encode('utf-8')
    content['profile/FAMILY_LINK.json'] = _json(family)
    content['config/host-binding.json'] = _json(_binding(role))
    pins = {path: _sha(data) for path, data in frozen.items()}
    receipt = {
        'schema': SCHEMA, 'role': role, 'display_name': name,
        'source_pins': pins, 'source_sha256': _sha(_json(pins)),
        'files': {path: _sha(data) for path, data in content.items()},
        'owner_files': ['profile/' + path for path in sorted(OWNER_FILES)],
        'native_loaded': False, 'native_registered': False,
        'external_effect_authorized': False, 'recipient_readback_verified': False,
        'grade': 'LOCAL_SOURCE_PROFILE_ONLY',
    }
    return content, receipt, frozen


def plan_system_profile(role: str, *, display_name: str | None = None) -> dict:
    """Resolve source pins and relative output names without creating any file."""
    content, receipt, _ = _build(role, display_name)
    return {'status': 'SOURCE_PLAN_ONLY', 'role': role,
            'display_name': receipt['display_name'], 'files': sorted(content),
            'source_sha256': receipt['source_sha256'], 'native_loaded': False,
            'can_apply': False}


def _new_destination(dest: Path) -> None:
    if _unsafe_source_path(dest):
        raise ValueError('UNSAFE_PROFILE_DESTINATION')
    if dest.exists():
        raise FileExistsError('PROFILE_DESTINATION_EXISTS')
    if not dest.parent.is_dir():
        raise FileNotFoundError('PROFILE_PARENT_REQUIRED')


def _write_new(path: Path, data: bytes) -> None:
    with path.open('xb') as output:
        output.write(data)


def stage_system_profile(destination: Path, role: str, *, display_name: str | None = None,
                         expected_source_sha256: str | None = None) -> dict:
    """Create a new source draft only. Keep interrupted work fenced, never erase it."""
    dest = Path(destination)
    _new_destination(dest)
    content, receipt, frozen = _build(role, display_name)
    if expected_source_sha256 is not None and (
            not isinstance(expected_source_sha256, str) or not _SHA.fullmatch(expected_source_sha256)
            or expected_source_sha256 != receipt['source_sha256']):
        raise ValueError('PROFILE_SOURCE_PIN_MISMATCH')
    dest.mkdir(exist_ok=False)
    marker = dest / 'STAGING_INCOMPLETE'
    _write_new(marker, b'LOCAL_ONLY_RECONCILE_PARTIAL_STAGE_BEFORE_RETRY\n')
    (dest / 'profile').mkdir()
    (dest / 'config').mkdir()
    for relative, data in content.items():
        _write_new(dest / relative, data)
    # All outputs came from frozen bytes. If the source changes, retain the
    # explicit incomplete marker instead of issuing a successful manifest.
    if _source(role) != frozen:
        raise ValueError('PROFILE_SOURCE_CHANGED_DURING_STAGE')
    _write_new(dest / MANIFEST, _json(receipt))
    marker.unlink()
    return {'status': 'LOCAL_SYSTEM_PROFILE_STAGED', 'role': role,
            'file_count': len(content), 'source_sha256': receipt['source_sha256'],
            'native_loaded': False, 'external_effect_authorized': False}


def _closed_tree(dest: Path, expected: set[str]) -> bool:
    if {p.name for p in dest.iterdir()} != {'profile', 'config', MANIFEST}:
        return False
    found = {MANIFEST}
    for folder in ('profile', 'config'):
        root = dest / folder
        if _unsafe_source_path(root) or not root.is_dir():
            return False
        entries = list(root.iterdir())
        if len(entries) > 40:
            return False
        for member in entries:
            if _unsafe_source_path(member) or not member.is_file():
                return False
            found.add(folder + '/' + member.name)
    return found == expected | {MANIFEST}


def inspect_system_profile(destination: Path) -> dict:
    """Compare source and draft bytes; do not trust editable receipt assertions."""
    dest = Path(destination)
    base = {'status': 'REVIEW_REQUIRED', 'native_loaded': False,
            'external_effect_authorized': False, 'owner_modified': [],
            'policy_modified': [], 'files_changed': False}
    try:
        if _unsafe_source_path(dest) or not dest.is_dir():
            return base
        if (dest / 'STAGING_INCOMPLETE').exists() or (dest / 'STAGING_INCOMPLETE').is_symlink():
            return {**base, 'status': 'INCOMPLETE_STAGE'}
        raw = _regular_bytes(dest / MANIFEST, MAX_FILE_BYTES)
        receipt = _parse(raw)
        if not isinstance(receipt, dict) or receipt.get('schema') != SCHEMA:
            return base
        content, expected, _ = _build(receipt.get('role'), receipt.get('display_name'))
        if receipt.get('source_pins') != expected['source_pins']:
            return {**base, 'status': 'SOURCE_DRIFT'}
        if raw != _json(expected) or not _closed_tree(dest, set(content)):
            return base
        owner_modified, policy_modified = [], []
        for relative, data in content.items():
            observed = _regular_bytes(dest / relative, MAX_FILE_BYTES)
            if observed != data:
                bucket = owner_modified if relative in expected['owner_files'] else policy_modified
                bucket.append(relative)
        status = ('REVIEW_REQUIRED' if policy_modified else
                  'OWNER_CUSTOMIZED' if owner_modified else 'LOCAL_SYSTEM_PROFILE_MATCH')
        return {**base, 'status': status, 'role': receipt['role'],
                'owner_modified': sorted(owner_modified), 'policy_modified': sorted(policy_modified),
                'source_sha256': expected['source_sha256']}
    except (OSError, ValueError, TypeError, KeyError):
        return base


def preview_system_profile(candidate: Path, target: Path) -> dict:
    """Read-only per-file change proposal. This function has no apply operation."""
    candidate, target = Path(candidate), Path(target)
    result = inspect_system_profile(candidate)
    if result['status'] != 'LOCAL_SYSTEM_PROFILE_MATCH':
        raise ValueError('PROFILE_CANDIDATE_NOT_PRISTINE')
    if _unsafe_source_path(target) or (target.exists() and not target.is_dir()):
        raise ValueError('UNSAFE_PROFILE_TARGET')
    plan = []
    for source in sorted((candidate / 'profile').iterdir(), key=lambda p: p.name):
        current = target / source.name
        if _unsafe_source_path(current):
            raise ValueError('UNSAFE_PROFILE_TARGET_MEMBER')
        if current.exists():
            existing = _regular_bytes(current, MAX_FILE_BYTES)
            new = _regular_bytes(source, MAX_FILE_BYTES)
            action = ('UNCHANGED' if existing == new else
                      'PRESERVE_OWNER_EDIT' if source.name in OWNER_FILES else 'REVIEW_CONFLICT')
        else:
            action = 'CREATE'
        plan.append({'name': source.name, 'action': action})
    return {'status': 'PREVIEW_ONLY', 'files': plan, 'can_apply': False,
            'native_loaded': False, 'effects_performed': False,
            'host_binding_required': True, 'unlisted_owner_files': 'UNTOUCHED'}

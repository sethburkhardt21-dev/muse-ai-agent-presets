"""Read-only, self-reported comparison of an offline rendered Muse draft.

This is not native Muse loading, authentication, a safe auto-merge or a signature.
Never opens a symlinked managed path or writes to the destination.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from .catalog import DOCUMENTS, ROOT, load_preset

_HEX_SHA = re.compile(r'^[0-9a-f]{64}$')
_MANAGED_V2 = tuple(DOCUMENTS) + ('FAMILY_LINK.json',)
_MANAGED_V3 = _MANAGED_V2 + ('ROLE_PLAYBOOK.md',)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def inspect_render(destination: Path) -> dict:
    """Classify a local draft against its original, unauthenticated receipt.

    User-modified identity and memory files are expected customizations. Changed
    Family Link policy, missing files and changed upstream template source need
    owner review. This method never installs, reconciles or regenerates files.
    """
    path = Path(destination)
    if path.is_symlink() or not path.is_dir():
        raise ValueError('INVALID_OR_SYMLINKED_PROFILE')
    receipt_path = path / 'RECEIPT.json'
    if receipt_path.is_symlink() or not receipt_path.is_file():
        raise ValueError('MISSING_OR_UNSAFE_RECEIPT')
    receipt = json.loads(receipt_path.read_text(encoding='utf-8'))
    if not isinstance(receipt, dict):
        raise ValueError('INVALID_RECEIPT')

    base = {
        'native_muse_status': 'NOT_CHECKED',
        'evidence_grade': 'UNAUTHENTICATED_LOCAL_ONLY',
        'effects_performed': False,
        'owner_modified': [],
        'policy_modified': [],
        'missing': [],
        'source_changed': [],
        'warning': 'Self-reported hashes are not signatures or native admission; no files were changed',
    }
    if receipt.get('schema') == 'muse-presets/render-v1':
        return {**base, 'status': 'LEGACY_UNVERIFIABLE'}
    version = receipt.get('schema')
    if version not in ('muse-presets/render-v2', 'muse-presets/render-v3'):
        raise ValueError('UNKNOWN_RECEIPT_SCHEMA')
    managed_names = _MANAGED_V3 if version == 'muse-presets/render-v3' else _MANAGED_V2
    base['role_playbook_status'] = ('MANAGED_POLICY' if version == 'muse-presets/render-v3'
                                    else 'NOT_IN_LEGACY_RENDER')

    hashes = receipt.get('rendered_sha256')
    templates = receipt.get('template_sha256')
    if (not isinstance(hashes, dict) or set(hashes) != set(managed_names)
            or not all(isinstance(v, str) and _HEX_SHA.fullmatch(v) for v in hashes.values())
            or not isinstance(templates, dict) or set(templates) != set(DOCUMENTS)
            or not all(isinstance(v, str) and _HEX_SHA.fullmatch(v) for v in templates.values())):
        raise ValueError('INVALID_RECEIPT_MANIFEST')
    if version == 'muse-presets/render-v3' and not _HEX_SHA.fullmatch(str(receipt.get('playbook_sha256', ''))):
        raise ValueError('INVALID_RECEIPT_MANIFEST')
    preset_id = receipt.get('preset_id')
    if not isinstance(preset_id, str) or not _HEX_SHA.fullmatch(str(receipt.get('preset_sha256', ''))):
        raise ValueError('INVALID_RECEIPT_MANIFEST')
    # load_preset rejects traversal or unknown names; nothing is executed.
    load_preset(preset_id)

    for filename in managed_names:
        managed = path / filename
        if managed.is_symlink():
            raise ValueError('UNSAFE_SYMLINK:' + filename)
        if not managed.is_file():
            base['missing'].append(filename)
        elif _sha(managed.read_bytes()) != hashes[filename]:
            key = 'policy_modified' if filename in ('FAMILY_LINK.json', 'ROLE_PLAYBOOK.md') else 'owner_modified'
            base[key].append(filename)

    original = ROOT / 'presets' / preset_id / 'preset.json'
    if _sha(original.read_bytes()) != receipt['preset_sha256']:
        base['source_changed'].append('preset.json')
    if version == 'muse-presets/render-v3':
        playbook = ROOT / 'presets' / preset_id / 'playbook.json'
        if not playbook.is_file() or playbook.is_symlink() or _sha(playbook.read_bytes()) != receipt['playbook_sha256']:
            base['source_changed'].append('playbook.json')
    for filename in DOCUMENTS:
        template = ROOT / 'templates' / 'profile' / filename
        if not template.is_file() or _sha(template.read_bytes()) != templates[filename]:
            base['source_changed'].append('templates/' + filename)

    for field in ('owner_modified', 'policy_modified', 'missing', 'source_changed'):
        base[field].sort()
    if base['policy_modified'] or base['missing'] or base['source_changed']:
        status = 'REVIEW_REQUIRED'
    elif base['owner_modified']:
        status = 'OWNER_CUSTOMIZED'
    else:
        status = 'LOCAL_MATCH'
    return {**base, 'status': status, 'preset_id': preset_id}

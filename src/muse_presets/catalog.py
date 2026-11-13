"""Validate and render neutral, create-only Muse assistant profile templates.

This module never reads private Muse state or changes an installed account.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from string import Template

from .playbooks import load_playbook, validate_playbook, render_playbook
from .neutrality import audit_public_tree

ROOT = Path(__file__).resolve().parents[2]
SLUG = re.compile(r'^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$')
DISPLAY = re.compile(r'^[A-Za-z0-9][A-Za-z0-9 ._\-]{0,79}$')
DOCUMENTS = ('AGENTS.md', 'SOUL.md', 'IDENTITY.md', 'USER.md', 'TOOLS.md',
             'MEMORY.md', 'HEARTBEAT.md', 'PROACTIVE_PREFERENCES.md',
             'SYSTEM_INSTRUCTIONS.md', 'SUBCHATS.md', 'HOOKS.md',
             'OPINION.md', 'SYSTEM_PROMPT.md', 'DOORS.md',
             'ENGINE_MATRIX.md', 'VOICE.md')


def _check_slug(slug: str) -> None:
    if not isinstance(slug, str) or not SLUG.fullmatch(slug):
        raise ValueError('INVALID_PRESET_ID')


def load_registry() -> dict:
    return json.loads((ROOT / 'presets' / 'catalog.json').read_text(encoding='utf-8'))


def load_preset(slug: str) -> dict:
    _check_slug(slug)
    item = ROOT / 'presets' / slug / 'preset.json'
    if not item.is_file():
        raise ValueError('UNKNOWN_PRESET_ID')
    return json.loads(item.read_text(encoding='utf-8'))


def validate_catalog() -> list[str]:
    errors: list[str] = []
    try:
        cat = load_registry()
        ids = cat['presets']
        all_ids = set(ids + cat['services'])
        if len(ids) != len(set(ids)) or len(all_ids) != len(ids) + len(cat['services']):
            errors.append('DUPLICATE_IDS')
        for slug in ids:
            try:
                config = load_preset(slug)
                fam = config['family_link']
                if config['id'] != slug: errors.append(f'{slug}:ID_MISMATCH')
                if config.get('schema') != 'muse-presets/preset-v1' or config.get('maturity') != 'SOURCE_TEMPLATE_ONLY' or config.get('native_muse_status') != 'UNBOUND':
                    errors.append(f'{slug}:UNSUPPORTED_NATIVE_CLAIM')
                if (config.get('requirements') != {'permissions': [], 'external_services': [], 'secret_values': []}
                        or fam.get('mode') != 'proposal-only' or fam.get('trusted_signer') is not None
                        or fam.get('native_recipient') is not None):
                    errors.append(f'{slug}:NON_NEUTRAL_DEFAULT_POLICY')
                if fam['enabled'] is not False or fam['transport'] != 'unbound':
                    errors.append(f'{slug}:FAMILY_NOT_DEFAULT_DENY')
                if not fam['suggested_receivers']:
                    errors.append(f'{slug}:NO_RECEIVER_PREVIEW')
                for to in fam['suggested_receivers']:
                    if to not in all_ids or to == slug: errors.append(f'{slug}:BAD_RECEIVER:{to}')
                contract = load_playbook(slug, source_root=ROOT)
                errors.extend(f'{slug}:{reason}' for reason in validate_playbook(contract, config))
            except (KeyError, ValueError, OSError, json.JSONDecodeError) as err:
                errors.append(f'{slug}:INVALID:{type(err).__name__}')
        for name in DOCUMENTS:
            if not (ROOT/'templates'/'profile'/name).is_file():
                errors.append(f'MISSING_TEMPLATE:{name}')
        for violation in audit_public_tree(ROOT):
            errors.append(f"NEUTRALITY:{violation['path']}:{violation['reason']}")
    except (OSError, KeyError, json.JSONDecodeError) as err:
        errors.append(f'INVALID_CATALOG:{type(err).__name__}')
    return errors


def render_preset(slug: str, destination: Path, *, display_name: str | None = None) -> Path:
    """Create a new offline draft only. Never install, merge or overwrite Muse files."""
    config = load_preset(slug)
    name = display_name or config['title']
    if not isinstance(name, str) or not DISPLAY.fullmatch(name):
        raise ValueError('INVALID_DISPLAY_NAME')
    playbook = load_playbook(slug, source_root=ROOT)
    problems = validate_playbook(playbook, config)
    if problems:
        raise ValueError('INVALID_ROLE_PLAYBOOK:' + ','.join(problems))
    destination = Path(destination)
    if destination.exists() or destination.is_symlink():
        raise FileExistsError('DESTINATION_EXISTS_REFUSING_OVERWRITE')
    if not destination.parent.is_dir():
        raise FileNotFoundError('PARENT_DIRECTORY_MUST_EXIST')
    template_data = {'display_name':name,'role_id':slug,'role_title':config['title'],
                     'role_description':config['description']}
    destination.mkdir(exist_ok=False)
    try:
        for filename in DOCUMENTS:
            tmpl = (ROOT/'templates'/'profile'/filename).read_text(encoding='utf-8')
            output = Template(tmpl).substitute(template_data)
            (destination/filename).write_text(output,encoding='utf-8')
        (destination/'ROLE_PLAYBOOK.md').write_text(
            render_playbook(playbook, display_name=name, role_title=config['title']), encoding='utf-8')
        (destination/'FAMILY_LINK.json').write_text(
            json.dumps(config['family_link'],indent=2,sort_keys=True)+'\n',encoding='utf-8')
        receipt = {'schema':'muse-presets/render-v3','preset_id':slug,
                   'display_name':name,
                   'preset_sha256': hashlib.sha256((ROOT/'presets'/slug/'preset.json').read_bytes()).hexdigest(),
                   'template_sha256': {filename:hashlib.sha256((ROOT/'templates'/'profile'/filename).read_bytes()).hexdigest() for filename in DOCUMENTS},
                   'playbook_sha256': hashlib.sha256((ROOT/'presets'/slug/'playbook.json').read_bytes()).hexdigest(),
                   'rendered_sha256': {filename:hashlib.sha256((destination/filename).read_bytes()).hexdigest() for filename in (*DOCUMENTS,'FAMILY_LINK.json','ROLE_PLAYBOOK.md')},
                   'grade':'LOCAL_DRAFT_ONLY',
                   'warning':'NOT an installed Muse runtime; no host identity, connector, hook, scheduler or native tool is bound',
                   'source':'local source-controlled preset'}
        (destination/'RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    except Exception:
        # The destination was created by this function; remove only our own outputs.
        for member in destination.iterdir():
            if member.is_file() and not member.is_symlink(): member.unlink()
        destination.rmdir()
        raise
    return destination

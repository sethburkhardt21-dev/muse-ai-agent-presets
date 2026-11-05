"""Bounded read-only audit of publicly distributed preset/configuration assets.

This is a heuristic release check, not a complete secret scan, rights audit,
license adjudication, or history validation. Never emit suspect file contents.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

_AREAS = ('presets', 'templates', 'services', 'docs')
_TEXT_SUFFIXES = frozenset(('.md', '.json', '.yaml', '.yml', '.txt', '.toml', '.py', '.sh'))
_SENSITIVE_NAMES = frozenset(('.env', '.env.local', 'id_rsa', 'id_ed25519', 'credentials.json'))
_SENSITIVE_SUFFIXES = frozenset(('.pem', '.p12', '.pfx', '.key', '.sqlite', '.sqlite3', '.db'))
_PRIVATE_HOST_PATH = re.compile(r'(?i)(?:[a-z]:[\\/]Users[\\/][^\\/\s]+[\\/]|/home/[^/\s]+/)')
_POSSIBLE_SECRET = re.compile(r'(?i)(?:\bsk-(?:proj|live)-[A-Za-z0-9_-]{12,}\b|\bAKIA[A-Z0-9]{16}\b|-----BEGIN (?:OPENSSH|RSA |EC |)PRIVATE KEY-----)')


def audit_public_tree(root: Path) -> list[dict[str, str]]:
    """Check public role/config/docs surfaces without network or filesystem writes.

    The report contains only relative paths and reason codes, never the matched
    secret or path string. Symlinks are refused without reading their targets.
    """
    root = Path(root)
    if root.is_symlink() or not root.is_dir():
        raise ValueError('INVALID_PUBLIC_ROOT')
    findings: list[dict[str, str]] = []
    for area in _AREAS:
        base = root / area
        if not base.exists():
            continue
        if base.is_symlink():
            findings.append({'path': area, 'reason': 'SYMLINK_REFUSED'})
            continue
        if not base.is_dir():
            findings.append({'path': area, 'reason': 'NOT_A_DIRECTORY'})
            continue
        for location, dirs, files in os.walk(base, followlinks=False):
            parent = Path(location)
            for child in list(dirs):
                path = parent / child
                if path.is_symlink():
                    findings.append({'path': path.relative_to(root).as_posix(), 'reason': 'SYMLINK_REFUSED'})
                    dirs.remove(child)
            for child in files:
                path = parent / child
                rel = path.relative_to(root).as_posix()
                if path.is_symlink():
                    findings.append({'path': rel, 'reason': 'SYMLINK_REFUSED'})
                    continue
                if child.lower() in _SENSITIVE_NAMES or path.suffix.lower() in _SENSITIVE_SUFFIXES:
                    findings.append({'path': rel, 'reason': 'SENSITIVE_FILE'})
                    continue
                if path.suffix.lower() not in _TEXT_SUFFIXES:
                    # Non-text assets require separate explicit license and malware review.
                    continue
                try:
                    # Bounded: do not process giant accidental vendor files as templates.
                    if path.stat().st_size > 2_000_000:
                        findings.append({'path': rel, 'reason': 'OVERSIZED_ASSET'})
                        continue
                    data = path.read_text(encoding='utf-8')
                except (OSError, UnicodeError):
                    findings.append({'path': rel, 'reason': 'UNREADABLE_OR_NON_UTF8'})
                    continue
                if _PRIVATE_HOST_PATH.search(data):
                    findings.append({'path': rel, 'reason': 'PRIVATE_HOST_PATH'})
                if _POSSIBLE_SECRET.search(data):
                    findings.append({'path': rel, 'reason': 'POSSIBLE_SECRET'})
    return sorted(findings, key=lambda row: (row['path'], row['reason']))

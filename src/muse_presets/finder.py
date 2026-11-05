"""Bounded, read-only evidence-finding primitive for user-supplied files.

This does not authenticate source material, grant access, or make a verdict.
"""
from __future__ import annotations

import hashlib
from pathlib import Path, PurePosixPath

MAX_FILE_BYTES = 8192


def find_exact_text(root: Path, relative_path: str, needle: str) -> dict:
    """Locate an exact literal in a bounded UTF-8 file, preserving its full text.

    Only one explicit file under an existing owned directory is read. There is
    no recursive crawler, network request, model operation, or external effect.
    """
    if not isinstance(relative_path, str) or not relative_path:
        raise ValueError('INVALID_RELATIVE_PATH')
    path = PurePosixPath(relative_path)
    if path.is_absolute() or '..' in path.parts or path.as_posix() != relative_path or ':' in relative_path:
        raise ValueError('INVALID_RELATIVE_PATH')
    if not isinstance(needle, str) or not 1 <= len(needle) <= 256:
        raise ValueError('INVALID_QUERY')
    base = Path(root)
    if not base.is_dir() or base.is_symlink():
        raise ValueError('INVALID_ROOT')
    base = base.resolve(strict=True)
    target = base
    for part in path.parts:
        target = target / part
        if target.is_symlink():
            raise ValueError('SYMLINK_REFUSED')
    resolved = target.resolve(strict=True)
    if not resolved.is_relative_to(base) or not resolved.is_file():
        raise ValueError('SOURCE_OUTSIDE_ALLOWED_ROOT')
    if resolved.stat().st_size > MAX_FILE_BYTES:
        raise ValueError('SOURCE_TOO_LARGE')
    raw = resolved.read_bytes()
    if len(raw) > MAX_FILE_BYTES:
        raise ValueError('SOURCE_CHANGED_OR_TOO_LARGE')
    try:
        text = raw.decode('utf-8')
    except UnicodeDecodeError as exc:
        raise ValueError('UTF8_SOURCE_REQUIRED') from exc
    found = needle in text
    return {
        'source_uri': relative_path,
        'source_sha256': hashlib.sha256(raw).hexdigest(),
        'observation': text if found else '',
        'result': 'FOUND' if found else 'NOT_FOUND',
    }

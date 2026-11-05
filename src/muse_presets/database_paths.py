"""Source-only SQLite path admission shared by local specialist engines.

Do not treat a valid local path as authorized host storage. Files remain
unencrypted and subject to the host filesystem's own access controls.
"""
from __future__ import annotations

import sys
from pathlib import Path

_DARWIN_ROOT_ALIASES={'/var':'/private/var','/tmp':'/private/tmp','/etc':'/private/etc'}


def _trusted_darwin_alias(part: Path) -> bool:
    """Permit only the standard root-owned macOS /var,/tmp,/etc aliases.

    A symlink named ``var`` below an owner directory is *not* a system alias.
    The destination, fixed location and root ownership must all match.
    """
    expected=_DARWIN_ROOT_ALIASES.get(str(part))
    if sys.platform!='darwin' or expected is None:
        return False
    try:
        return (part.is_symlink() and part.lstat().st_uid==0 and
                part.resolve(strict=True)==Path(expected) and
                Path(expected).is_dir())
    except (OSError, RuntimeError):
        return False


def validated_database_path(raw: str | Path, *, error: str,
                            absolute: bool = False) -> Path:
    """Reject symlinked user paths, missing parent and directory targets.

    Requiring an absolute path is opt-in to preserve the older garden caller
    contract. No symlink exception applies outside three fixed macOS roots.
    This is not an atomic openat sandbox and does not authenticate a caller.
    """
    if not isinstance(raw,(str,Path)) or not str(raw).strip():
        raise ValueError(error)
    file=Path(raw).expanduser()
    if (absolute and not file.is_absolute()) or '..' in file.parts or not file.parent.is_dir():
        raise ValueError(error)
    if file.exists() and not file.is_file():
        raise ValueError(error)
    if any(part.is_symlink() and not _trusted_darwin_alias(part)
           for part in (file,*file.parents)):
        raise ValueError(error)
    return file

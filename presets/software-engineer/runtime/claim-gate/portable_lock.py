"""Local exclusive file locks for the neutral Claim Gate runtime.

On Windows use a one-byte kernel file lock (msvcrt), on POSIX flock.
Lock files are never unlinked. This is a LOCAL filesystem protocol, not
multi-host consensus, an independent fencing witness or a power-loss proof.
"""
from __future__ import annotations

import errno
import os
import stat
import time
from contextlib import contextmanager
from pathlib import Path

if os.name == "nt":
    import msvcrt
elif os.name == "posix":
    import fcntl
else:
    raise RuntimeError("UNSUPPORTED_LOCAL_LOCK_PLATFORM")


class PortableLockUnavailable(OSError):
    """Lock path/owner unusable or unavailable; no state mutation is allowed."""


def sync_directory(path: str | os.PathLike[str]) -> bool:
    """Durably sync a directory on POSIX; explicitly report lack on Windows.

    On Windows, file fsync plus same-volume atomic replace is used, but
    a power-loss-durable directory-entry witness is NOT promised.
    """
    directory = os.fspath(path)
    if not os.path.isdir(directory):
        raise PortableLockUnavailable("DIRECTORY_SYNC_PATH_REFUSED")
    if os.name != "posix":
        return False
    fd = os.open(directory, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(fd)
    finally:
        os.close(fd)
    return True


@contextmanager
def exclusive_lock(path: str | os.PathLike[str], *, timeout_seconds: float = 30.0):
    """Hold one exclusive OS lock until exit; refuse unsafe lock paths.

    The same byte-0 lock file must be shared by approval and composite.
    Never nest two acquisitions of the same path from separate descriptors.
    A Windows busy lock times out fail-closed rather than granting access.
    """
    if isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, (int, float)):
        raise PortableLockUnavailable("INVALID_LOCK_TIMEOUT")
    if not 0 <= timeout_seconds <= 120:
        raise PortableLockUnavailable("INVALID_LOCK_TIMEOUT")
    name = os.fspath(path)
    if os.path.islink(name) or (os.path.lexists(name) and not os.path.isfile(name)):
        raise PortableLockUnavailable("UNSAFE_LOCKFILE_TYPE")
    flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_BINARY", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(name, flags, 0o600)
    except OSError as exc:
        raise PortableLockUnavailable("LOCKFILE_OPEN_REFUSED") from exc
    locked = False
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise PortableLockUnavailable("LOCKFILE_NOT_REGULAR")
        if os.name == "nt":
            # Windows kernel byte-range lock needs a real byte at offset zero.
            # Two initial writers may write the same sentinel; neither may
            # modify consequential state until the OS lock is held.
            if os.fstat(fd).st_size == 0:
                os.lseek(fd, 0, os.SEEK_SET)
                os.write(fd, b"\x00")
                os.fsync(fd)
            deadline = time.monotonic() + float(timeout_seconds)
            while True:
                os.lseek(fd, 0, os.SEEK_SET)
                try:
                    msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
                    locked = True
                    break
                except OSError as exc:
                    busy = (exc.errno in (errno.EACCES, errno.EAGAIN)
                            or getattr(exc, "winerror", None) in (33, 36))
                    if not busy:
                        raise PortableLockUnavailable("WINDOWS_LOCK_ERROR") from exc
                    if time.monotonic() >= deadline:
                        raise PortableLockUnavailable("WINDOWS_LOCK_BUSY_TIMEOUT") from exc
                    time.sleep(min(0.03, max(0.0, deadline - time.monotonic())))
        else:
            # Preserve the original POSIX flock behavior and lock location.
            fcntl.flock(fd, fcntl.LOCK_EX)
            locked = True
        try:
            yield
        finally:
            if locked:
                if os.name == "nt":
                    os.lseek(fd, 0, os.SEEK_SET)
                    msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(fd, fcntl.LOCK_UN)
                locked = False
    finally:
        os.close(fd)

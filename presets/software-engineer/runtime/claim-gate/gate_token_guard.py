"""Token guard — downstream fencing enforcement (P2).

Design: evidence/GATE-DESIGN-MULTIHOST.md (P2), Kleppmann's fencing rule.

A fencing token protects nothing by itself. The gate can order tokens
perfectly — one authority, strictly increasing — and a stale holder can
still destroy the work: paused past its lease, preempted by a takeover,
it wakes up and writes to the guarded resource with its old token. The
only place that write can be stopped is at the resource itself.

``TokenGuard`` is that resource-side check, supplied by this module for
consuming modules to place in front of their effect:

- honor(scope, claim_id, token): atomically, if ``token`` is strictly
  greater than the greatest token ever honored for that claim, record it
  and return True (apply the effect). Otherwise return False (refuse:
  the caller is stale, or is replaying an effect already applied).
- The greatest-honored table is durable (atomic write + fsync per honor),
  survives restarts, and is NEVER reset by this component. There is
  deliberately no forget/reset: the guard's memory IS the enforcement,
  and amnesia would reopen every window it ever closed.
- Corrupt guard state fails closed with a typed error — validated per
  entry, not just at the top level: any malformed entry (non-object,
  missing/wrong-typed/non-finite token) refuses the whole load. It is
  never silently reinitialized — a wiped table would re-honor every
  stale token ever issued. (Per-entry validation and the strict JSON
  parser are Challenger G repairs, GATE-BUILD-009.)
- Equal tokens are refused. A holder whose effect response was lost
  holds an UNKNOWN, and this house's doctrine is that UNKNOWN is
  reconciled read-only, never re-effected. Strict ``>`` gives
  at-most-once per token at the resource.

The guard is local to one resource: the resource is the single writer of
its own guard state, which is exactly the assumption P2 requires. It
complements the gate (which refuses stale holders at claim time) —
defense in depth: a holder must pass BOTH to land an effect after a
takeover, and passing the resource requires being the current maximum.

State layout: ``<guard_dir>/token-guard.json`` plus a lockfile. The
guard dir belongs to the resource, not to the gate's claims dir.
"""

from __future__ import annotations

import fcntl
import json
import os
import re
import sys
import tempfile
import time
from contextlib import contextmanager

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from claim_gate import ClaimGateError

_COMPONENT = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")
_STATE_NAME = "token-guard.json"
_LOCK_NAME = ".token-guard.lock"


def _utcnow() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _check_component(kind: str, value: str) -> str:
    # fullmatch, not a $-anchored match: "$" also matches before a trailing
    # newline, which once let "abc\n" slip past this validator (Challenger G).
    if not isinstance(value, str) or not _COMPONENT.fullmatch(value):
        raise ValueError("unsafe %s: %r" % (kind, value))
    return value


def _check_token(token) -> int:
    if isinstance(token, bool) or not isinstance(token, int) or token <= 0:
        raise ValueError("fencing token must be a positive int: %r" % (token,))
    if token.bit_length() > 1024:
        # Challenger G (NEW-2): an absurd programmatic token passed input
        # validation, then json.dump failed on it mid-store with an
        # untyped ValueError (interpreter int->str limit). Real fencing
        # issuers mint small counters; cap the input at a generous bound.
        raise ValueError("fencing token exceeds 1024 bits: %r..." % (token,))
    return token


class TokenGuard:
    """Greatest-token enforcement for one guarded resource."""

    def __init__(self, guard_dir: str):
        self._dir = guard_dir
        try:
            os.makedirs(self._dir, exist_ok=True)
        except OSError as exc:
            raise ClaimGateError(
                "token guard dir %r is unusable: %s" % (guard_dir, exc))
        if not os.path.isdir(self._dir):
            raise ClaimGateError(
                "token guard dir %r exists and is not a directory"
                % (guard_dir,))
        self._state_path = os.path.join(self._dir, _STATE_NAME)
        self._lock_path = os.path.join(self._dir, _LOCK_NAME)

    # -- internals ---------------------------------------------------------

    @contextmanager
    def _locked(self):
        # Challenger G (NEW-1): the lock path got the same planted-path
        # treatment as the state path — a directory planted there crashed
        # every public method with a bare IsADirectoryError.
        if os.path.exists(self._lock_path) and not os.path.isfile(
                self._lock_path):
            raise ClaimGateError(
                "token guard lock path %s exists and is not a regular "
                "file; refusing" % self._lock_path)
        try:
            fd = os.open(self._lock_path, os.O_CREAT | os.O_RDWR, 0o644)
        except OSError as exc:
            raise ClaimGateError(
                "token guard lock at %s cannot be opened: %s"
                % (self._lock_path, exc))
        try:
            fcntl.flock(fd, fcntl.LOCK_EX)
            yield
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)
            os.close(fd)

    @staticmethod
    def _bad_constant(name):
        # json accepts NaN / Infinity / -Infinity by default. A non-finite
        # token poisons every comparison (NaN) or locks the claim forever
        # (Infinity) — Challenger G seeded both. They must never parse.
        raise ValueError("non-finite JSON constant in guard state: %s" % name)

    @classmethod
    def _validate_table(cls, data: dict, path: str) -> dict:
        """Every entry must be exactly the shape _store writes.

        Challenger G's root finding: entry-level corruption was silently
        read as "greatest = 0" (non-dict entry), as a bare TypeError
        (string/null token), or not at all (missing token) — three ways
        for one malformed line to edit the guard's memory into amnesia.
        Now: any malformed entry fails the whole load, closed and typed.
        Absence of a key is the ONLY way a claim reads as never-honored.
        """
        for key, entry in data.items():
            where = "token guard state at %s, entry %r" % (path, key)
            if not isinstance(entry, dict):
                raise ClaimGateError(
                    "%s: entry is not an object; refusing rather than "
                    "treating it as never-honored" % where)
            token = entry.get("token")
            if (isinstance(token, bool) or not isinstance(token, int)
                    or token < 1):
                raise ClaimGateError(
                    "%s: token is not a positive int (%r); refusing"
                    % (where, token))
            digest = entry.get("effect_digest")
            if digest is not None and not isinstance(digest, str):
                raise ClaimGateError(
                    "%s: effect_digest is not a string or null; refusing"
                    % where)
        return data

    def _load(self) -> dict:
        if not os.path.exists(self._state_path):
            return {}
        if not os.path.isfile(self._state_path):
            # A directory, FIFO, or device planted at the state path must
            # refuse, never wedge open() forever (Challenger G).
            raise ClaimGateError(
                "token guard state at %s exists and is not a regular "
                "file; refusing" % self._state_path)
        try:
            with open(self._state_path, "r", encoding="utf-8") as fh:
                data = json.load(fh, parse_constant=self._bad_constant)
        except (OSError, ValueError, RecursionError) as exc:
            # Fail closed: a corrupt table is preserved and reported,
            # never silently reset — resetting would re-honor stale tokens.
            raise ClaimGateError(
                "token guard state at %s is unreadable (%s); refusing "
                "rather than resetting enforcement" % (self._state_path, exc))
        if not isinstance(data, dict):
            raise ClaimGateError(
                "token guard state at %s is not a JSON object; refusing"
                % self._state_path)
        return self._validate_table(data, self._state_path)

    def _store(self, data: dict) -> None:
        fd, tmp = tempfile.mkstemp(dir=self._dir, prefix=".tg-", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(data, fh, indent=2, sort_keys=True)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp, self._state_path)
        except BaseException:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise
        dfd = os.open(self._dir, os.O_RDONLY)
        try:
            os.fsync(dfd)
        finally:
            os.close(dfd)

    @staticmethod
    def _key(scope: str, claim_id: str) -> str:
        return "%s/%s" % (scope, claim_id)

    @staticmethod
    def _entry_token(data: dict, key: str) -> int:
        """The one interpretation of the table, shared by honor() and the
        read API (Challenger G found them disagreeing on malformed state).
        _load has already validated every present entry, so a present key
        yields its strict positive int; only absence reads as 0."""
        entry = data.get(key)
        return entry["token"] if entry is not None else 0

    # -- public API ---------------------------------------------------------

    def honor(self, scope: str, claim_id: str, fencing_token: int,
              effect_digest: str | None = None) -> bool:
        """Try to honor ``fencing_token`` for a claim.

        Returns True exactly when the token is a new maximum for the
        claim — the caller may apply its effect, once. Returns False for
        stale tokens (a higher token was already honored) and for equal
        tokens (this token's effect already landed; a retry is a replay).
        """
        scope = _check_component("scope", scope)
        claim_id = _check_component("claim_id", claim_id)
        token = _check_token(fencing_token)
        if effect_digest is not None and not isinstance(effect_digest, str):
            raise ValueError("effect_digest must be a string or None")
        key = self._key(scope, claim_id)
        with self._locked():
            data = self._load()
            greatest = self._entry_token(data, key)
            if token <= greatest:
                return False
            data[key] = {"token": token, "effect_digest": effect_digest,
                         "honored_ts": _utcnow()}
            try:
                self._store(data)
            except (OSError, ValueError) as exc:
                raise ClaimGateError(
                    "failed to persist honored token for %s: %s"
                    % (key, exc))
            return True

    def greatest(self, scope: str, claim_id: str) -> int:
        """The greatest token honored for the claim (0 if none). Read-only."""
        scope = _check_component("scope", scope)
        claim_id = _check_component("claim_id", claim_id)
        with self._locked():
            data = self._load()
        return self._entry_token(data, self._key(scope, claim_id))

    def was_honored(self, scope: str, claim_id: str,
                    fencing_token: int) -> bool:
        """True iff this exact token is the greatest honored. Read-only."""
        return self.greatest(scope, claim_id) == _check_token(fencing_token)

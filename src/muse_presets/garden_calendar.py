"""Local, source-tested garden calendar transaction reference (not a Muse adapter).

The host must supply an authenticated authority resolver. The resolver in local
examples is a test fixture: no token, signed grant, Muse account or native
identity can be proven by this library itself. Never expose the resolver as a
model/browser parameter. No external calendar or task is contacted.
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Callable, Iterator

_ID = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_-]{0,79}$')
_DIGEST = re.compile(r'^[a-f0-9]{64}$')
_DATE = re.compile(r'^\d{4}-\d{2}-\d{2}$')
_BIDI = re.compile('[\u061c\u200e\u200f\u202a-\u202e\u2066-\u2069\u200b\u2060\ufeff]')
_MAX_MS = 2**53 - 1
_MAX_CHANGES = 21
_DEFAULT_TTL = 3_600_000


def _id(value: str) -> str:
    if not isinstance(value, str) or not _ID.fullmatch(value):
        raise ValueError('INVALID_ID')
    return value


def _time_ms(value: int) -> int:
    if type(value) is not int or not 0 <= value < _MAX_MS:
        raise ValueError('SERVER_CLOCK_INVALID')
    return value


def _text(value: str, *, size: int = 160) -> str:
    if not isinstance(value, str) or len(value) > size or '\0' in value or _BIDI.search(value):
        raise ValueError('INVALID_TEXT')
    result = value.strip()
    if not result:
        raise ValueError('INVALID_TEXT')
    return result


def _day(value: str) -> date:
    if not isinstance(value, str) or not _DATE.fullmatch(value):
        raise ValueError('INVALID_DATE')
    try:
        d = date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError('INVALID_DATE') from exc
    if d.year < 1900 or d.year > 2200:
        raise ValueError('INVALID_DATE')
    return d


def _hash_dict(data: dict) -> str:
    wire = json.dumps(data, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    return hashlib.sha256(wire.encode('utf-8')).hexdigest()


@dataclass(frozen=True)
class GardenScope:
    """Host-supplied scope; constructing this alone does NOT authenticate anyone."""

    owner_id: str
    space_id: str
    garden_id: str
    actor_id: str
    owner_browser: bool = False

    def checked(self) -> 'GardenScope':
        for key in (self.owner_id, self.space_id, self.garden_id, self.actor_id):
            _id(key)
        if type(self.owner_browser) is not bool:
            raise ValueError('HOST_AUTHORITY_UNVERIFIED')
        if self.owner_browser and self.actor_id != self.owner_id:
            raise ValueError('HOST_AUTHORITY_UNVERIFIED')
        return self

    def key(self) -> tuple[str, str, str]:
        return self.owner_id, self.space_id, self.garden_id


class GardenCalendar:
    """Atomic SQLite-only calendar workflow, for disposable/local instances.

    `authority` MUST be an injected host-side verifier that checks the current
    principal every call. Do not construct it from client-supplied identity. This
    repo does not implement the Muse authenticated verifier or installation.
    """

    def __init__(self, database: str | Path, *,
                 authority: Callable[[], GardenScope] | None = None,
                 clock_ms: Callable[[], int] | None = None,
                 proposal_ttl_ms: int = _DEFAULT_TTL,
                 pending_limit: int = 1000):
        if not callable(authority):
            raise ValueError('HOST_AUTHORITY_UNBOUND')
        if clock_ms is not None and not callable(clock_ms):
            raise ValueError('SERVER_CLOCK_INVALID')
        if type(proposal_ttl_ms) is not int or not 60_000 <= proposal_ttl_ms <= 86_400_000:
            raise ValueError('SERVER_POLICY_INVALID')
        if type(pending_limit) is not int or not 1 <= pending_limit <= 10_000:
            raise ValueError('SERVER_POLICY_INVALID')
        if not isinstance(database, (str, Path)) or not str(database):
            raise ValueError('INVALID_DATABASE')
        file = Path(database)
        if file.is_symlink() or any(part.is_symlink() for part in (file.parent, *file.parent.parents)) or not file.parent.is_dir():
            raise ValueError('INVALID_DATABASE')
        self._authority = authority
        self._clock_ms = clock_ms or (lambda: int(time.time() * 1000))
        self._ttl_ms = proposal_ttl_ms
        self._pending_limit = pending_limit
        self._db = sqlite3.connect(file, timeout=5.0, isolation_level=None)
        self._db.row_factory = sqlite3.Row
        self._db.execute('PRAGMA foreign_keys = ON')
        self._db.executescript('''
            CREATE TABLE IF NOT EXISTS garden_events (
                owner_key TEXT NOT NULL, space_key TEXT NOT NULL, garden_key TEXT NOT NULL,
                event_key TEXT NOT NULL, title TEXT NOT NULL, on_date TEXT NOT NULL,
                revision INTEGER NOT NULL CHECK (revision >= 1), state TEXT NOT NULL,
                PRIMARY KEY(owner_key,space_key,garden_key,event_key));
            CREATE TABLE IF NOT EXISTS garden_batch_proposals (
                owner_key TEXT NOT NULL, space_key TEXT NOT NULL, garden_key TEXT NOT NULL,
                proposal_key TEXT NOT NULL, digest TEXT NOT NULL, created_by TEXT NOT NULL,
                changes_json TEXT NOT NULL, state TEXT NOT NULL, created_ms INTEGER NOT NULL,
                expires_ms INTEGER NOT NULL,
                PRIMARY KEY(owner_key,space_key,garden_key,proposal_key));
            CREATE TABLE IF NOT EXISTS garden_batch_receipts (
                owner_key TEXT NOT NULL, space_key TEXT NOT NULL, garden_key TEXT NOT NULL,
                operation_key TEXT NOT NULL, proposal_key TEXT NOT NULL,
                digest TEXT NOT NULL, decision TEXT NOT NULL, state TEXT NOT NULL,
                decided_ms INTEGER NOT NULL, events_json TEXT NOT NULL,
                PRIMARY KEY(owner_key,space_key,garden_key,operation_key));
        ''')

    def close(self) -> None:
        self._db.close()

    def __enter__(self) -> 'GardenCalendar':
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def _scope(self, *, owner_only: bool = False) -> GardenScope:
        try:
            candidate = self._authority()
            if type(candidate) is not GardenScope:
                raise ValueError('HOST_AUTHORITY_UNVERIFIED')
            candidate.checked()
        except Exception as exc:
            raise ValueError('HOST_AUTHORITY_UNVERIFIED') from exc
        if owner_only and not candidate.owner_browser:
            raise ValueError('OWNER_APPROVAL_REQUIRED')
        return candidate

    def _now(self) -> int:
        try:
            return _time_ms(self._clock_ms())
        except Exception as exc:
            raise ValueError('SERVER_CLOCK_INVALID') from exc

    @contextmanager
    def _transaction(self) -> Iterator[None]:
        try:
            self._db.execute('BEGIN IMMEDIATE')
        except sqlite3.Error as exc:
            raise ValueError('OUTCOME_UNKNOWN_RECONCILE_BY_OPERATION_ID') from exc
        try:
            yield
            self._db.execute('COMMIT')
        except sqlite3.Error as exc:
            self._db.execute('ROLLBACK')
            raise ValueError('OUTCOME_UNKNOWN_RECONCILE_BY_OPERATION_ID') from exc
        except BaseException:
            self._db.execute('ROLLBACK')
            raise

    def _event_row(self, scope: GardenScope, event_id: str):
        return self._db.execute('''SELECT event_key,title,on_date,revision,state
            FROM garden_events WHERE owner_key=? AND space_key=? AND garden_key=? AND event_key=?''',
            (*scope.key(), event_id)).fetchone()

    @staticmethod
    def _event_payload(row: sqlite3.Row) -> dict:
        return {'event_id': row['event_key'], 'title': row['title'], 'on_date': row['on_date'],
                'revision': row['revision'], 'state': row['state']}

    def event(self, event_id: str) -> dict | None:
        scope = self._scope()
        row = self._event_row(scope, _id(event_id))
        return self._event_payload(row) if row else None

    def list_events(self) -> dict:
        scope = self._scope()
        rows = self._db.execute('''SELECT event_key,title,on_date,revision,state FROM garden_events
            WHERE owner_key=? AND space_key=? AND garden_key=? ORDER BY on_date,event_key LIMIT 101''', scope.key()).fetchall()
        return {'events':[self._event_payload(r) for r in rows[:100]],
                'truncated':len(rows)>100,'scope':'LOCAL_SCOPED_REFERENCE'}

    def add_event(self, *, event_id: str, title: str, on_date: str) -> dict:
        scope = self._scope(owner_only=True)
        event_id = _id(event_id)
        title = _text(title)
        on_date = _day(on_date).isoformat()
        with self._transaction():
            if self._event_row(scope, event_id):
                raise ValueError('EVENT_EXISTS')
            self._db.execute('''INSERT INTO garden_events
                (owner_key,space_key,garden_key,event_key,title,on_date,revision,state)
                VALUES(?,?,?,?,?,?,1,'active')''', (*scope.key(),event_id,title,on_date))
        return self.event(event_id)  # type: ignore[return-value]

    def cancel_event(self, event_id: str, *, expected_revision: int) -> dict:
        scope = self._scope(owner_only=True)
        event_id = _id(event_id)
        if type(expected_revision) is not int or expected_revision < 1:
            raise ValueError('INVALID_REVISION')
        with self._transaction():
            row = self._event_row(scope, event_id)
            if row is None:
                raise ValueError('EVENT_NOT_FOUND')
            if row['state'] != 'active':
                raise ValueError('EVENT_NOT_ACTIVE')
            if row['revision'] != expected_revision:
                raise ValueError('STALE_REVISION')
            cursor = self._db.execute('''UPDATE garden_events SET state='cancelled',revision=revision+1
                WHERE owner_key=? AND space_key=? AND garden_key=? AND event_key=?
                AND state='active' AND revision=?''', (*scope.key(),event_id,expected_revision))
            if cursor.rowcount != 1:
                raise ValueError('STALE_REVISION')
        return self.event(event_id)  # type: ignore[return-value]

    @staticmethod
    def _normalized_changes(changes: list) -> list[dict]:
        if type(changes) is not list or not 1 <= len(changes) <= _MAX_CHANGES:
            raise ValueError('BATCH_LIMIT')
        normalized: list[dict] = []
        ids: set[str] = set()
        for item in changes:
            if type(item) is not dict or set(item) != {'event_id', 'expected_revision', 'days'}:
                raise ValueError('INVALID_CHANGE')
            event_id = _id(item['event_id'])
            rev = item['expected_revision']
            shift = item['days']
            if type(rev) is not int or rev < 1 or rev >= _MAX_MS:
                raise ValueError('INVALID_REVISION')
            if type(shift) is not int or shift == 0 or not -30 <= shift <= 30:
                raise ValueError('SHIFT_OUTSIDE_BOUND')
            if event_id in ids:
                raise ValueError('DUPLICATE_EVENT')
            ids.add(event_id)
            normalized.append({'event_id': event_id, 'expected_revision': rev, 'days': shift})
        return normalized

    def _proposal_row(self, scope: GardenScope, proposal_id: str):
        return self._db.execute('''SELECT * FROM garden_batch_proposals
            WHERE owner_key=? AND space_key=? AND garden_key=? AND proposal_key=?''',
            (*scope.key(),proposal_id)).fetchone()

    @staticmethod
    def _proposal_payload(row: sqlite3.Row) -> dict:
        return {'proposal_id':row['proposal_key'],'digest':row['digest'],
                'state':row['state'],'created_ms':row['created_ms'],
                'expires_ms':row['expires_ms'],
                'changes':json.loads(row['changes_json']),
                'host_authenticated':False,'native_installed':False}

    def propose_shift_batch(self, *, proposal_id: str, changes: list) -> dict:
        scope = self._scope()
        proposal_id = _id(proposal_id)
        normalized = self._normalized_changes(changes)
        digest = _hash_dict({'scope':scope.key(),'proposal_id':proposal_id,'changes':normalized})
        now = self._now()
        if now > _MAX_MS - self._ttl_ms:
            raise ValueError('SERVER_CLOCK_INVALID')
        with self._transaction():
            old = self._proposal_row(scope,proposal_id)
            if old:
                if old['digest'] != digest or old['created_by'] != scope.actor_id:
                    raise ValueError('PROPOSAL_CONFLICT')
                return self._proposal_payload(old)
            active = self._db.execute('''SELECT count(*) AS n FROM garden_batch_proposals
                WHERE owner_key=? AND space_key=? AND garden_key=? AND state='pending'
                AND expires_ms>?''', (*scope.key(),now)).fetchone()
            if active['n'] >= self._pending_limit:
                raise ValueError('PROPOSAL_LIMIT')
            previews = []
            for change in normalized:
                row = self._event_row(scope,change['event_id'])
                if row is None:
                    raise ValueError('EVENT_NOT_FOUND')
                if row['state'] != 'active':
                    raise ValueError('EVENT_NOT_ACTIVE')
                if row['revision'] != change['expected_revision']:
                    raise ValueError('STALE_REVISION')
                original = _day(row['on_date'])
                try:
                    new_date = original + timedelta(days=change['days'])
                except OverflowError as exc:
                    raise ValueError('INVALID_DATE') from exc
                if not 1900 <= new_date.year <= 2200:
                    raise ValueError('INVALID_DATE')
                previews.append({**change,'before_date':original.isoformat(),
                                 'after_date':new_date.isoformat()})
            self._db.execute('''INSERT INTO garden_batch_proposals
                (owner_key,space_key,garden_key,proposal_key,digest,created_by,
                changes_json,state,created_ms,expires_ms) VALUES(?,?,?,?,?,?,?,?,?,?)''',
                (*scope.key(),proposal_id,digest,scope.actor_id,json.dumps(previews,sort_keys=True),
                 'pending',now,now+self._ttl_ms))
            row = self._proposal_row(scope,proposal_id)
            return self._proposal_payload(row)

    def review_batch(self, proposal_id: str) -> dict:
        scope = self._scope(owner_only=True)
        proposal_id = _id(proposal_id)
        row = self._proposal_row(scope,proposal_id)
        if not row:
            raise ValueError('PROPOSAL_NOT_FOUND')
        problems: list[str] = []
        if row['state'] != 'pending':
            problems.append('PROPOSAL_NOT_PENDING')
        if self._now() >= row['expires_ms']:
            problems.append('PROPOSAL_EXPIRED')
        changes = json.loads(row['changes_json'])
        for change in changes:
            before = self._event_row(scope, change['event_id'])
            if before is None:
                problems.append('EVENT_NOT_FOUND')
            elif before['state'] != 'active':
                problems.append('EVENT_NOT_ACTIVE')
            elif before['revision'] != change['expected_revision'] or before['on_date'] != change['before_date']:
                problems.append('STALE_REVISION')
        return {'proposal_id':proposal_id,'digest':row['digest'],'ready':not problems,
                'issues':list(dict.fromkeys(problems)),'changes':changes,
                'state':row['state'],'committed':False,'native_installed':False}

    def _receipt_row(self, scope: GardenScope, operation_id: str):
        return self._db.execute('''SELECT * FROM garden_batch_receipts
            WHERE owner_key=? AND space_key=? AND garden_key=? AND operation_key=?''',
            (*scope.key(),operation_id)).fetchone()

    @staticmethod
    def _receipt_payload(row: sqlite3.Row) -> dict:
        return {'operation_id':row['operation_key'],'proposal_id':row['proposal_key'],
                'digest':row['digest'],'decision':row['decision'],'state':row['state'],
                'decided_ms':row['decided_ms'],'events':json.loads(row['events_json']),
                'effect_scope':'LOCAL_SQLITE_ONLY','host_authenticated':False,'native_installed':False}

    def receipt(self, operation_id: str) -> dict | None:
        scope = self._scope(owner_only=True)
        row = self._receipt_row(scope,_id(operation_id))
        return self._receipt_payload(row) if row else None

    def decide_batch(self, *, proposal_id: str, digest: str, operation_id: str,
                     decision: str) -> dict:
        scope = self._scope(owner_only=True)
        proposal_id,operation_id = _id(proposal_id),_id(operation_id)
        if not isinstance(digest,str) or not _DIGEST.fullmatch(digest):
            raise ValueError('INVALID_DIGEST')
        if decision not in ('approve','decline'):
            raise ValueError('INVALID_DECISION')
        now = self._now()
        with self._transaction():
            existing = self._receipt_row(scope,operation_id)
            if existing is not None:
                if (existing['proposal_key']!=proposal_id or existing['digest']!=digest
                        or existing['decision']!=decision):
                    raise ValueError('OPERATION_CONFLICT')
                return self._receipt_payload(existing)
            proposal = self._proposal_row(scope,proposal_id)
            if proposal is None:
                raise ValueError('PROPOSAL_NOT_FOUND')
            if proposal['digest'] != digest:
                raise ValueError('PROPOSAL_DIGEST_MISMATCH')
            if proposal['state'] != 'pending':
                raise ValueError('PROPOSAL_NOT_PENDING')
            if now >= proposal['expires_ms']:
                raise ValueError('PROPOSAL_EXPIRED')
            events: list[dict] = []
            if decision == 'approve':
                for change in json.loads(proposal['changes_json']):
                    event = self._event_row(scope,change['event_id'])
                    if event is None:
                        raise ValueError('EVENT_NOT_FOUND')
                    if event['state'] != 'active':
                        raise ValueError('EVENT_NOT_ACTIVE')
                    if event['revision'] != change['expected_revision'] or event['on_date'] != change['before_date']:
                        raise ValueError('STALE_REVISION')
                    # Preserve the original revision and date as an additional SQL fence.
                    updated = self._db.execute('''UPDATE garden_events
                        SET on_date=?,revision=revision+1
                        WHERE owner_key=? AND space_key=? AND garden_key=? AND event_key=?
                        AND state='active' AND revision=? AND on_date=?''',
                        (change['after_date'],*scope.key(),change['event_id'],
                         change['expected_revision'],change['before_date']))
                    if updated.rowcount != 1:
                        raise ValueError('STALE_REVISION')
                    events.append({'event_id':change['event_id'],'before_date':change['before_date'],
                                   'after_date':change['after_date'],'revision':change['expected_revision']+1})
            outcome = 'approved' if decision == 'approve' else 'declined'
            updated = self._db.execute('''UPDATE garden_batch_proposals SET state=?
                WHERE owner_key=? AND space_key=? AND garden_key=? AND proposal_key=? AND state='pending' ''',
                (outcome,*scope.key(),proposal_id))
            if updated.rowcount != 1:
                raise ValueError('PROPOSAL_NOT_PENDING')
            self._db.execute('''INSERT INTO garden_batch_receipts
                (owner_key,space_key,garden_key,operation_key,proposal_key,digest,decision,
                state,decided_ms,events_json) VALUES(?,?,?,?,?,?,?,?,?,?)''',
                (*scope.key(),operation_id,proposal_id,digest,decision,outcome,now,
                 json.dumps(events,sort_keys=True)))
            return self._receipt_payload(self._receipt_row(scope,operation_id))

"""Public-neutral, local Evidence Finder custody and recovery reference.

Stores *original* bounded findings from the existing exact-text finder.
Receipts survive process restarts and have a SHA-256-linked SQLite chain.
Neither host identity, native Muse invocation, genuine source ownership,
independent truth, external delivery nor cryptographic immutability is proven.

This is newly authored portable standard-library source, not a copy of a
private agent engine, platform SDK, or anyone's memory or medical material.
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Iterator

from .catalog import load_registry
from .database_paths import validated_database_path
from .finder import MAX_FILE_BYTES, find_exact_text

_ID = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_-]{0,79}$')
_SHA = re.compile(r'^[a-f0-9]{64}$')
_ZERO = '0' * 64
_MAX_RECORDS = 512


def _id(value: str) -> str:
    if not isinstance(value, str) or not _ID.fullmatch(value):
        raise ValueError('INVALID_ID')
    return value


def _wire(payload: object) -> str:
    return json.dumps(payload, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _digest(payload: object) -> str:
    return _sha(_wire(payload).encode('utf-8'))


@dataclass(frozen=True)
class EvidenceScope:
    """Host-supplied scope SHAPE, not an independently authenticated identity."""

    owner_id: str
    workspace_id: str
    role_id: str
    actor_id: str

    def checked(self) -> 'EvidenceScope':
        for field in (self.owner_id, self.workspace_id, self.role_id, self.actor_id):
            _id(field)
        registry = load_registry()
        allowed = set(registry['presets']) | set(registry['services'])
        if self.role_id not in allowed:
            raise ValueError('HOST_AUTHORITY_UNVERIFIED')
        return self

    def key(self) -> tuple[str, str, str, str]:
        return self.owner_id, self.workspace_id, self.role_id, self.actor_id


class EvidenceLedger:
    """Bounded local finding custody shared by all eleven presets + Evidence Finder.

    Every public method requires an injected host-side authority resolver,
    including reads. The demonstration callback is synthetic: this library
    DOES NOT verify tokens, recognize Muse principals, or enforce OS ACLs.
    The same host identity and source permissions must be verified separately.

    Receipt chains detect accidental/partial edits, not deliberate rewriting
    by someone who can modify both SQLite rows and the local head.
    """

    def __init__(self, database: str | Path, *,
                 authority: Callable[[], EvidenceScope] | None = None):
        if not callable(authority):
            raise ValueError('HOST_AUTHORITY_UNBOUND')
        path = validated_database_path(database, error='UNSAFE_DATABASE_PATH',
                                       absolute=True)
        self._authority = authority
        self._db = sqlite3.connect(path, timeout=8.0, isolation_level=None,
                                   check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._db.execute('PRAGMA busy_timeout=8000')
        self._db.execute('''
            CREATE TABLE IF NOT EXISTS evidence_records(
                owner_key TEXT NOT NULL, workspace_key TEXT NOT NULL,
                role_key TEXT NOT NULL, actor_key TEXT NOT NULL,
                operation_key TEXT NOT NULL, request_sha256 TEXT NOT NULL,
                sequence INTEGER NOT NULL CHECK(sequence >= 1),
                record_json TEXT NOT NULL, record_sha256 TEXT NOT NULL,
                previous_chain_sha256 TEXT NOT NULL, chain_sha256 TEXT NOT NULL,
                PRIMARY KEY(owner_key,workspace_key,role_key,actor_key,operation_key),
                UNIQUE(owner_key,workspace_key,role_key,actor_key,sequence)
            )''')
        self._db.execute('''
            CREATE TABLE IF NOT EXISTS evidence_heads(
                owner_key TEXT NOT NULL, workspace_key TEXT NOT NULL,
                role_key TEXT NOT NULL, actor_key TEXT NOT NULL,
                sequence INTEGER NOT NULL, chain_sha256 TEXT NOT NULL,
                PRIMARY KEY(owner_key,workspace_key,role_key,actor_key)
            )''')

    def close(self) -> None:
        self._db.close()

    def __enter__(self) -> 'EvidenceLedger':
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()

    def _scope(self) -> EvidenceScope:
        try:
            scope = self._authority()
            if type(scope) is not EvidenceScope:
                raise ValueError('HOST_AUTHORITY_UNVERIFIED')
            return scope.checked()
        except Exception as exc:
            raise ValueError('HOST_AUTHORITY_UNVERIFIED') from exc

    @contextmanager
    def _transaction(self, *, write: bool = False) -> Iterator[None]:
        try:
            self._db.execute('BEGIN IMMEDIATE' if write else 'BEGIN')
        except sqlite3.Error as exc:
            raise ValueError('LOCAL_DATABASE_OUTCOME_UNKNOWN_RECONCILE') from exc
        try:
            yield
            self._db.execute('COMMIT')
        except sqlite3.Error as exc:
            self._db.execute('ROLLBACK')
            raise ValueError('LOCAL_DATABASE_OUTCOME_UNKNOWN_RECONCILE') from exc
        except BaseException:
            self._db.execute('ROLLBACK')
            raise

    @staticmethod
    def _finding_valid(finding: object, query: str) -> bool:
        if type(finding) is not dict or set(finding) != {
            'source_uri', 'source_sha256', 'observation', 'result'
        }:
            return False
        if not isinstance(finding['source_uri'], str) or not finding['source_uri']:
            return False
        if not isinstance(finding['source_sha256'], str) or not _SHA.fullmatch(finding['source_sha256']):
            return False
        value = finding['observation']
        if not isinstance(value, str) or finding['result'] not in ('FOUND', 'NOT_FOUND'):
            return False
        if finding['result'] == 'NOT_FOUND':
            return value == ''
        try:
            raw = value.encode('utf-8')
        except UnicodeEncodeError:
            return False
        return (0 < len(raw) <= MAX_FILE_BYTES and _sha(raw) == finding['source_sha256']
                and isinstance(query, str) and query in value)

    def _verify_rows(self, scope: EvidenceScope) -> tuple[int, str]:
        rows = self._db.execute('''
            SELECT sequence,operation_key,request_sha256,record_json,record_sha256,
                   previous_chain_sha256,chain_sha256 FROM evidence_records
            WHERE owner_key=? AND workspace_key=? AND role_key=? AND actor_key=?
            ORDER BY sequence''', scope.key()).fetchall()
        head = self._db.execute('''
            SELECT sequence,chain_sha256 FROM evidence_heads
            WHERE owner_key=? AND workspace_key=? AND role_key=? AND actor_key=?''',
            scope.key()).fetchone()
        if len(rows) > _MAX_RECORDS:
            raise ValueError('EVIDENCE_CHAIN_INVALID')
        previous = _ZERO
        for index, row in enumerate(rows, start=1):
            try:
                record = json.loads(row['record_json'])
                if (type(record) is not dict or
                    set(record) != {'schema', 'scope', 'operation_id', 'query', 'finding'} or
                    record['schema'] != 'muse-presets/evidence-ledger-entry-v1' or
                    record['scope'] != asdict(scope) or
                    record['operation_id'] != row['operation_key'] or
                    not self._finding_valid(record['finding'], record['query'])):
                    raise ValueError('EVIDENCE_CHAIN_INVALID')
                if row['sequence'] != index or row['request_sha256'] != _digest({
                    'scope': asdict(scope), 'operation_id': row['operation_key'],
                    'relative_path': record['finding']['source_uri'], 'query': record['query']
                }):
                    raise ValueError('EVIDENCE_CHAIN_INVALID')
                digest = _digest(record)
                if (digest != row['record_sha256'] or
                    previous != row['previous_chain_sha256'] or
                    _sha((previous + ':' + digest).encode('ascii')) != row['chain_sha256']):
                    raise ValueError('EVIDENCE_CHAIN_INVALID')
                previous = row['chain_sha256']
            except (TypeError, KeyError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
                raise ValueError('EVIDENCE_CHAIN_INVALID') from exc
        if ((head is None and rows) or
            (head is not None and (head['sequence'] != len(rows) or
                                   head['chain_sha256'] != previous))):
            raise ValueError('EVIDENCE_CHAIN_INVALID')
        return len(rows), previous

    def _existing(self, scope: EvidenceScope, operation_id: str,
                  request_digest: str) -> sqlite3.Row | None:
        row = self._db.execute('''
            SELECT sequence,operation_key,request_sha256,record_json,record_sha256,
                   previous_chain_sha256,chain_sha256 FROM evidence_records
            WHERE owner_key=? AND workspace_key=? AND role_key=? AND actor_key=?
              AND operation_key=?''', (*scope.key(), operation_id)).fetchone()
        if row is not None and row['request_sha256'] != request_digest:
            raise ValueError('OPERATION_CONFLICT')
        return row

    @staticmethod
    def _response(scope: EvidenceScope, row: sqlite3.Row, *, status: str) -> dict:
        entry = json.loads(row['record_json'])
        return {
            'status': status, 'scope': asdict(scope),
            'finding': entry['finding'],
            'receipt': {
                'operation_id': row['operation_key'],
                'sequence': row['sequence'],
                'record_sha256': row['record_sha256'],
                'previous_chain_sha256': row['previous_chain_sha256'],
                'chain_sha256': row['chain_sha256'],
            },
            'source_text_persisted_locally': entry['finding']['result'] == 'FOUND',
            'source_owner_authenticated': False,
            'independent_truth_verified': False,
            'effect_authorized': False,
            'recipient_acknowledged': False,
            'chain_externally_anchored': False,
            'native_muse_status': 'NOT_INVOKED',
        }

    def capture(self, root: str | Path, relative_path: str, query: str, *,
                operation_id: str) -> dict:
        """Locate and store one bounded source snapshot; never send or judge."""
        scope = self._scope()
        _id(operation_id)
        if not isinstance(relative_path, str) or not relative_path:
            raise ValueError('INVALID_RELATIVE_PATH')
        if not isinstance(query, str) or not 1 <= len(query) <= 256:
            raise ValueError('INVALID_QUERY')
        request_sha = _digest({
            'scope': asdict(scope), 'operation_id': operation_id,
            'relative_path': relative_path, 'query': query,
        })
        with self._transaction():
            self._verify_rows(scope)
            existing = self._existing(scope, operation_id, request_sha)
            if existing:
                return self._response(scope, existing, status='LOCAL_EVIDENCE_PRESERVED')

        # Reuse the original public Finder's bounded file admission. The
        # evidence is a snapshot of that call, not a live source ownership
        # assertion. No cross-user permissions are inferred from role labels.
        finding = find_exact_text(Path(root), relative_path, query)
        if not self._finding_valid(finding, query):
            raise ValueError('FINDER_RESULT_INVALID')
        entry = {
            'schema': 'muse-presets/evidence-ledger-entry-v1',
            'scope': asdict(scope),
            'operation_id': operation_id,
            'query': query,
            'finding': finding,
        }
        record_sha = _digest(entry)
        with self._transaction(write=True):
            count, previous = self._verify_rows(scope)
            existing = self._existing(scope, operation_id, request_sha)
            if existing:
                return self._response(scope, existing, status='LOCAL_EVIDENCE_PRESERVED')
            if count >= _MAX_RECORDS:
                raise ValueError('EVIDENCE_LEDGER_FULL')
            sequence = count + 1
            chain_sha = _sha((previous + ':' + record_sha).encode('ascii'))
            self._db.execute('''
                INSERT INTO evidence_records VALUES(?,?,?,?,?,?,?,?,?,?,?)''',
                (*scope.key(), operation_id, request_sha, sequence, _wire(entry),
                 record_sha, previous, chain_sha))
            self._db.execute('''
                INSERT INTO evidence_heads VALUES(?,?,?,?,?,?)
                ON CONFLICT(owner_key,workspace_key,role_key,actor_key)
                DO UPDATE SET sequence=excluded.sequence,
                              chain_sha256=excluded.chain_sha256''',
                (*scope.key(), sequence, chain_sha))
            row = self._existing(scope, operation_id, request_sha)
            return self._response(scope, row, status='LOCAL_EVIDENCE_RECORDED')

    def read(self, operation_id: str) -> dict:
        """Reopen one verified receipt without requiring its original source."""
        scope = self._scope()
        _id(operation_id)
        with self._transaction():
            self._verify_rows(scope)
            row = self._db.execute('''
                SELECT sequence,operation_key,request_sha256,record_json,record_sha256,
                       previous_chain_sha256,chain_sha256 FROM evidence_records
                WHERE owner_key=? AND workspace_key=? AND role_key=? AND actor_key=?
                  AND operation_key=?''', (*scope.key(), operation_id)).fetchone()
            if row is None:
                raise ValueError('OPERATION_NOT_FOUND')
            return self._response(scope, row, status='LOCAL_EVIDENCE_REOPENED')

    def verify(self) -> dict:
        """Verify scoped chain/head without modifying any receipt record."""
        scope = self._scope()
        with self._transaction():
            count, head = self._verify_rows(scope)
        return {
            'status': 'LOCAL_EVIDENCE_CHAIN_VERIFIED',
            'scope': asdict(scope),
            'receipt_count': count,
            'head_chain_sha256': head,
            'chain_verified_locally': True,
            'chain_externally_anchored': False,
            'source_owner_authenticated': False,
            'independent_truth_verified': False,
            'effect_authorized': False,
            'recipient_acknowledged': False,
            'native_muse_status': 'NOT_INVOKED',
        }

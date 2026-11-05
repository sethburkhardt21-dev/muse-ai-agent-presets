"""Local, nonclinical source-to-review study ledger. No Muse/identity authority.

Callers MUST inject a host-authenticated authority callback; the public scope
shape is not a token and the example callback is only a fictional fixture.
Source sentences are owner-supplied *claims*, not independently true facts.
Questions use a deliberately limited ``Term :: literal definition`` grammar.
No automatic clinical approval, external study content, model inference, or
native scheduling is performed. Local SQLite files are not tamper-proof.
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterator

from .database_paths import validated_database_path

_ID = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_-]{0,79}$')
_SOURCE_ID = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$')
_DIGEST = re.compile(r'^[a-f0-9]{64}$')
_FACT = re.compile(r'^([A-Za-z][A-Za-z0-9 -]{2,70}?) :: ([A-Za-z0-9][^<>\r\n]{4,260})$')
_CONTROLS = re.compile('[\u061c\u200e\u200f\u202a-\u202e\u2066-\u2069\u200b\u2060\ufeff\x00]')
_MAX_CLOCK = 2**53 - 1
_DAY_MS = 86_400_000
_DEFAULT_TTL_MS = 900_000


def _id(value: str, *, source: bool = False) -> str:
    if not isinstance(value, str) or not (_SOURCE_ID if source else _ID).fullmatch(value):
        raise ValueError('INVALID_SOURCE_ID' if source else 'INVALID_ID')
    return value


def _text(value: str, *, max_size: int, kind: str, blank: bool = False) -> str:
    if not isinstance(value, str) or len(value) > max_size or _CONTROLS.search(value):
        raise ValueError('INVALID_' + kind)
    try:
        value.encode('utf-8')
    except UnicodeEncodeError as exc:
        raise ValueError('INVALID_' + kind) from exc
    if not blank and not value.strip():
        raise ValueError('INVALID_' + kind)
    return value


def _now_ms(value: int) -> int:
    if type(value) is not int or not 0 <= value < _MAX_CLOCK:
        raise ValueError('SERVER_CLOCK_INVALID')
    return value


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def _wire(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)


def _answer_key(value: str) -> str:
    return ' '.join(value.split()).casefold()




@dataclass(frozen=True)
class LearningScope:
    """A host-injected identity *shape*, not an independently proven principal."""

    owner_id: str
    space_id: str
    learner_id: str
    actor_id: str
    session_id: str
    role: str

    def checked(self) -> 'LearningScope':
        for part in (self.owner_id, self.space_id, self.learner_id,
                     self.actor_id, self.session_id):
            _id(part)
        if self.role not in ('owner', 'specialist', 'learner'):
            raise ValueError('HOST_AUTHORITY_UNVERIFIED')
        if self.role == 'owner' and self.actor_id != self.owner_id:
            raise ValueError('HOST_AUTHORITY_UNVERIFIED')
        if self.role == 'learner' and self.actor_id != self.learner_id:
            raise ValueError('HOST_AUTHORITY_UNVERIFIED')
        return self

    def source_scope(self) -> tuple[str, str]:
        return (self.owner_id, self.space_id)

    def learner_scope(self) -> tuple[str, str, str]:
        return (self.owner_id, self.space_id, self.learner_id)


class LearningSession:
    def __init__(self, database: str | Path, *,
                 authority: Callable[[], LearningScope] | None = None,
                 clock_ms: Callable[[], int] | None = None,
                 challenge_ttl_ms: int = _DEFAULT_TTL_MS):
        if authority is None or not callable(authority):
            raise ValueError('HOST_AUTHORITY_UNBOUND')
        if type(challenge_ttl_ms) is not int or not 60_000 <= challenge_ttl_ms <= _DAY_MS:
            raise ValueError('INVALID_CHALLENGE_TTL')
        self._authority = authority
        self._clock_ms = clock_ms or (lambda: time.time_ns() // 1_000_000)
        self._ttl_ms = challenge_ttl_ms
        self.path = validated_database_path(database, error='UNSAFE_DATABASE_PATH', absolute=True)
        self._db = sqlite3.connect(self.path, timeout=8.0, isolation_level=None,
                                   check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._db.execute('PRAGMA busy_timeout=8000')
        self._db.execute('PRAGMA foreign_keys=ON')
        self._db.executescript('''
            CREATE TABLE IF NOT EXISTS study_source_versions (
                owner_key TEXT NOT NULL, space_key TEXT NOT NULL,
                source_key TEXT NOT NULL, version TEXT NOT NULL,
                body TEXT NOT NULL, digest TEXT NOT NULL, admitted_ms INTEGER NOT NULL,
                PRIMARY KEY(owner_key,space_key,source_key,version));
            CREATE TABLE IF NOT EXISTS study_source_registry (
                owner_key TEXT NOT NULL, space_key TEXT NOT NULL,
                source_key TEXT NOT NULL, active_version TEXT NOT NULL,
                PRIMARY KEY(owner_key,space_key,source_key));
            CREATE TABLE IF NOT EXISTS study_drafts (
                owner_key TEXT NOT NULL, space_key TEXT NOT NULL,
                draft_key TEXT NOT NULL, source_key TEXT NOT NULL,
                version TEXT NOT NULL, source_digest TEXT NOT NULL,
                source_line INTEGER NOT NULL, sentence TEXT NOT NULL,
                question TEXT NOT NULL, answer TEXT NOT NULL, digest TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'held',
                PRIMARY KEY(owner_key,space_key,draft_key));
            CREATE TABLE IF NOT EXISTS study_review_receipts (
                owner_key TEXT NOT NULL,space_key TEXT NOT NULL,
                operation_key TEXT NOT NULL,draft_key TEXT NOT NULL,
                digest TEXT NOT NULL,decision TEXT NOT NULL,payload_json TEXT NOT NULL,
                PRIMARY KEY(owner_key,space_key,operation_key));
            CREATE TABLE IF NOT EXISTS study_challenges (
                owner_key TEXT NOT NULL,space_key TEXT NOT NULL,learner_key TEXT NOT NULL,
                challenge_key TEXT NOT NULL,session_key TEXT NOT NULL,
                draft_key TEXT NOT NULL,question_digest TEXT NOT NULL,
                expires_ms INTEGER NOT NULL,state TEXT NOT NULL,
                PRIMARY KEY(owner_key,space_key,learner_key,challenge_key));
            CREATE TABLE IF NOT EXISTS study_attempts (
                owner_key TEXT NOT NULL,space_key TEXT NOT NULL,learner_key TEXT NOT NULL,
                operation_key TEXT NOT NULL,challenge_key TEXT NOT NULL,
                draft_key TEXT NOT NULL,question_digest TEXT NOT NULL,
                correct INTEGER NOT NULL,occurred_ms INTEGER NOT NULL,
                PRIMARY KEY(owner_key,space_key,learner_key,operation_key));
            CREATE TABLE IF NOT EXISTS study_score_receipts (
                owner_key TEXT NOT NULL,space_key TEXT NOT NULL,learner_key TEXT NOT NULL,
                operation_key TEXT NOT NULL,challenge_key TEXT NOT NULL,
                session_key TEXT NOT NULL,answer_digest TEXT NOT NULL,payload_json TEXT NOT NULL,
                PRIMARY KEY(owner_key,space_key,learner_key,operation_key));
            CREATE INDEX IF NOT EXISTS study_attempts_by_draft
                ON study_attempts(owner_key,space_key,learner_key,draft_key,occurred_ms);
        ''')

    def __enter__(self) -> 'LearningSession':
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def close(self) -> None:
        self._db.close()

    def _scope(self, roles: tuple[str, ...]) -> LearningScope:
        try:
            scope = self._authority()
            if type(scope) is not LearningScope:
                raise ValueError('BAD_AUTHORITY')
            scope.checked()
        except Exception as exc:
            raise ValueError('HOST_AUTHORITY_UNVERIFIED') from exc
        if scope.role not in roles:
            raise ValueError('OWNER_APPROVAL_REQUIRED' if roles == ('owner',) else
                             'REVIEWER_SCOPE_REQUIRED' if roles == ('owner', 'specialist') else
                             'LEARNER_SCOPE_REQUIRED')
        return scope

    def _now(self) -> int:
        try:
            return _now_ms(self._clock_ms())
        except Exception as exc:
            raise ValueError('SERVER_CLOCK_INVALID') from exc

    @contextmanager
    def _tx(self) -> Iterator[None]:
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

    def _source_row(self, scope: LearningScope, source_id: str):
        return self._db.execute('''SELECT v.* FROM study_source_registry r
            JOIN study_source_versions v ON v.owner_key=r.owner_key
                AND v.space_key=r.space_key AND v.source_key=r.source_key
                AND v.version=r.active_version
            WHERE r.owner_key=? AND r.space_key=? AND r.source_key=?''',
            (*scope.source_scope(), source_id)).fetchone()

    @staticmethod
    def _verified_source(row: sqlite3.Row) -> None:
        if _sha(row['body']) != row['digest']:
            raise ValueError('SOURCE_DIGEST_MISMATCH')

    @staticmethod
    def _source_info(row: sqlite3.Row) -> dict:
        return {'source_id':row['source_key'], 'version':row['version'],
                'sha256':row['digest'], 'lines':len(row['body'].splitlines()),
                'trust':'OWNER_SUPPLIED_UNVERIFIED_CONTENT', 'clinical_release_ready':False}

    def register_source(self, *, source_id: str, version: str, text: str) -> dict:
        scope = self._scope(('owner',))
        source_id,version=_id(source_id,source=True),_id(version,source=True)
        body=_text(text,max_size=32768,kind='SOURCE')
        now=self._now()
        digest=_sha(body)
        with self._tx():
            previous=self._db.execute('''SELECT body,digest FROM study_source_versions
                WHERE owner_key=? AND space_key=? AND source_key=? AND version=?''',
                (*scope.source_scope(),source_id,version)).fetchone()
            if previous and (previous['digest']!=digest or previous['body']!=body):
                raise ValueError('SOURCE_VERSION_CONFLICT')
            current=self._source_row(scope,source_id)
            if previous and current and current['version']!=version:
                raise ValueError('SOURCE_VERSION_STALE')
            if not previous:
                self._db.execute('''INSERT INTO study_source_versions
                  (owner_key,space_key,source_key,version,body,digest,admitted_ms)
                  VALUES(?,?,?,?,?,?,?)''',(*scope.source_scope(),source_id,version,body,digest,now))
            self._db.execute('''INSERT INTO study_source_registry
                (owner_key,space_key,source_key,active_version) VALUES(?,?,?,?)
                ON CONFLICT(owner_key,space_key,source_key)
                DO UPDATE SET active_version=excluded.active_version''',
                (*scope.source_scope(),source_id,version))
        return {'source_id':source_id,'version':version,'sha256':digest,
                'lines':len(body.splitlines()),'trust':'OWNER_SUPPLIED_UNVERIFIED_CONTENT',
                'clinical_release_ready':False}

    def source(self, source_id: str) -> dict | None:
        scope=self._scope(('owner','specialist'))
        row=self._source_row(scope,_id(source_id,source=True))
        if row is None:return None
        self._verified_source(row)
        return self._source_info(row)

    @staticmethod
    def _parse_fact(sentence: str) -> tuple[str, str] | None:
        match=_FACT.fullmatch(sentence)
        if not match:return None
        term,answer=(x.strip() for x in match.groups())
        if len(term)<3 or len(answer)<6 or not answer.endswith(('.', '?', '!')):
            return None
        return term,answer

    @staticmethod
    def _draft_payload(row: sqlite3.Row) -> dict:
        return {'draft_id':row['draft_key'],'source_id':row['source_key'],
                'source_version':row['version'],
                'source_locator':f"{row['source_key']}@{row['version']}:line-{row['source_line']}",
                'source_sha256':row['source_digest'],'quote':row['sentence'],
                'question':row['question'],'answer':row['answer'],
                'digest':row['digest'],
                'status':'HELD_FOR_OWNER_REVIEW' if row['status']=='held' else row['status'].upper(),
                'clinically_validated':False,'host_authorized':False}

    def propose_source_facts(self, source_id: str, *, limit: int = 20) -> dict:
        scope=self._scope(('owner','specialist'))
        if type(limit) is not int or not 1<=limit<=100:
            raise ValueError('INVALID_LIMIT')
        row=self._source_row(scope,_id(source_id,source=True))
        if row is None:raise ValueError('SOURCE_NOT_FOUND')
        self._verified_source(row)
        lines=row['body'].splitlines()
        all_facts=[]
        seen_terms=set()
        for n,line in enumerate(lines,1):
            parsed=self._parse_fact(line)
            if parsed is None:continue
            term,answer=parsed
            if term.casefold() in seen_terms:continue
            seen_terms.add(term.casefold())
            fields={'source_id':source_id,'version':row['version'],
                    'source_sha256':row['digest'],'source_line':n,
                    'sentence':line,'question':f'What is {term}?','answer':answer}
            digest=_sha(_wire(fields))
            draft_id=_sha(_wire([scope.owner_id,scope.space_id,digest]))[:32]
            all_facts.append((draft_id,digest,fields))
        with self._tx():
            for draft_id,digest,fields in all_facts[:limit]:
                existing=self._db.execute('''SELECT digest FROM study_drafts WHERE
                    owner_key=? AND space_key=? AND draft_key=?''',
                    (*scope.source_scope(),draft_id)).fetchone()
                if existing:
                    if existing['digest']!=digest:
                        raise ValueError('DRAFT_CONFLICT')
                    continue
                self._db.execute('''INSERT INTO study_drafts
                    (owner_key,space_key,draft_key,source_key,version,source_digest,
                    source_line,sentence,question,answer,digest) VALUES(?,?,?,?,?,?,?,?,?,?,?)''',
                    (*scope.source_scope(),draft_id,source_id,fields['version'],row['digest'],
                     fields['source_line'],fields['sentence'],fields['question'],fields['answer'],digest))
        cards=[]
        for draft_id,_,_ in all_facts[:limit]:
            entry=self._db.execute('''SELECT * FROM study_drafts WHERE
                owner_key=? AND space_key=? AND draft_key=?''',
                (*scope.source_scope(),draft_id)).fetchone()
            cards.append(self._draft_payload(entry))
        return {'drafts':cards,'counts':{'lines':len(lines),'generated':len(all_facts),
                'skipped':len(lines)-len(all_facts)},'truncated':len(all_facts)>limit,
                'status':'UNREVIEWED_SOURCE_EXTRACTIVE_PROPOSALS'}

    def _draft_row(self, scope: LearningScope, draft_id: str):
        return self._db.execute('''SELECT * FROM study_drafts WHERE
            owner_key=? AND space_key=? AND draft_key=?''',
            (*scope.source_scope(),draft_id)).fetchone()

    def _check_draft(self, scope: LearningScope, row: sqlite3.Row) -> None:
        current=self._source_row(scope,row['source_key'])
        if current is None or current['version']!=row['version']:
            raise ValueError('SOURCE_VERSION_STALE')
        self._verified_source(current)
        if current['digest']!=row['source_digest']:
            raise ValueError('SOURCE_DIGEST_MISMATCH')
        lines=current['body'].splitlines()
        n=row['source_line']
        if n>len(lines) or n<=0 or lines[n-1]!=row['sentence']:
            raise ValueError('SOURCE_QUOTE_MISMATCH')
        if row['answer'] not in row['sentence']:
            raise ValueError('SOURCE_QUOTE_MISMATCH')
        term_answer=self._parse_fact(row['sentence'])
        if term_answer is None or f'What is {term_answer[0]}?'!=row['question'] or term_answer[1]!=row['answer']:
            raise ValueError('SOURCE_QUOTE_MISMATCH')
        fields={'source_id':row['source_key'],'version':row['version'],
                'source_sha256':row['source_digest'],'source_line':n,
                'sentence':row['sentence'],'question':row['question'],'answer':row['answer']}
        if _sha(_wire(fields))!=row['digest']:
            raise ValueError('DRAFT_DIGEST_MISMATCH')

    def draft(self, draft_id: str) -> dict | None:
        scope=self._scope(('owner','specialist'))
        row=self._draft_row(scope,_id(draft_id))
        if row is None:return None
        self._check_draft(scope,row)
        return self._draft_payload(row)

    def review(self, *, draft_id: str, digest: str, operation_id: str, decision: str) -> dict:
        scope=self._scope(('owner',))
        draft_id,operation_id=_id(draft_id),_id(operation_id)
        if not isinstance(digest,str) or not _DIGEST.fullmatch(digest):raise ValueError('INVALID_DIGEST')
        if decision not in ('approve','decline'):raise ValueError('INVALID_DECISION')
        now=self._now()
        with self._tx():
            existing=self._db.execute('''SELECT * FROM study_review_receipts WHERE
                owner_key=? AND space_key=? AND operation_key=?''',
                (*scope.source_scope(),operation_id)).fetchone()
            if existing:
                if (existing['draft_key'],existing['digest'],existing['decision'])!=(draft_id,digest,decision):
                    raise ValueError('OPERATION_CONFLICT')
                return json.loads(existing['payload_json'])
            row=self._draft_row(scope,draft_id)
            if row is None:raise ValueError('DRAFT_NOT_FOUND')
            self._check_draft(scope,row)
            if row['digest']!=digest:raise ValueError('DRAFT_DIGEST_MISMATCH')
            if row['status']!='held':raise ValueError('DRAFT_NOT_HELD')
            new_state='approved' if decision=='approve' else 'declined'
            self._db.execute('''UPDATE study_drafts SET status=? WHERE
                owner_key=? AND space_key=? AND draft_key=?''',
                (new_state,*scope.source_scope(),draft_id))
            payload={'status':'OWNER_REVIEW_RECORDED_LOCAL_ONLY','operation_id':operation_id,
                     'draft_id':draft_id,'digest':digest,'decision':decision,
                     'decided_ms':now,'host_authorized':False}
            self._db.execute('''INSERT INTO study_review_receipts
                (owner_key,space_key,operation_key,draft_key,digest,decision,payload_json)
                VALUES(?,?,?,?,?,?,?)''',
                (*scope.source_scope(),operation_id,draft_id,digest,decision,_wire(payload)))
        return payload

    def receipt(self, operation_id: str) -> dict | None:
        scope=self._scope(('owner',))
        row=self._db.execute('''SELECT payload_json FROM study_review_receipts WHERE
            owner_key=? AND space_key=? AND operation_key=?''',
            (*scope.source_scope(),_id(operation_id))).fetchone()
        return json.loads(row['payload_json']) if row else None

    @staticmethod
    def _challenge_payload(row: sqlite3.Row, draft: sqlite3.Row) -> dict:
        return {'status':'CHALLENGE_OPEN','challenge_id':row['challenge_key'],
                'question':draft['question'],
                'source_locator':f"{draft['source_key']}@{draft['version']}:line-{draft['source_line']}",
                'source_sha256':draft['source_digest'],
                'question_digest':draft['digest'],'expires_ms':row['expires_ms'],
                'clinical_release_ready':False,'host_authorized':False}

    def issue(self, *, draft_id: str, challenge_id: str) -> dict:
        scope=self._scope(('learner',))
        draft_id,challenge_id=_id(draft_id),_id(challenge_id)
        now=self._now()
        with self._tx():
            existing=self._db.execute('''SELECT * FROM study_challenges WHERE
                owner_key=? AND space_key=? AND learner_key=? AND challenge_key=?''',
                (*scope.learner_scope(),challenge_id)).fetchone()
            if existing:
                if existing['draft_key']!=draft_id or existing['session_key']!=scope.session_id:
                    raise ValueError('CHALLENGE_CONFLICT')
                if existing['state']!='open':raise ValueError('CHALLENGE_ALREADY_ANSWERED')
                if now>=existing['expires_ms']:raise ValueError('CHALLENGE_EXPIRED')
                row=self._draft_row(scope,draft_id)
                if row is None:raise ValueError('QUESTION_NOT_APPROVED')
                self._check_draft(scope,row)
                if row['digest']!=existing['question_digest']:
                    raise ValueError('QUESTION_CHANGED')
                return self._challenge_payload(existing,row)
            row=self._draft_row(scope,draft_id)
            if row is None or row['status']!='approved':
                raise ValueError('QUESTION_NOT_APPROVED')
            self._check_draft(scope,row)
            expires=now+self._ttl_ms
            if expires>=_MAX_CLOCK:raise ValueError('SERVER_CLOCK_INVALID')
            self._db.execute('''INSERT INTO study_challenges
                (owner_key,space_key,learner_key,challenge_key,session_key,draft_key,
                 question_digest,expires_ms,state) VALUES(?,?,?,?,?,?,?,?,?)''',
                (*scope.learner_scope(),challenge_id,scope.session_id,draft_id,row['digest'],expires,'open'))
            inserted=self._db.execute('''SELECT * FROM study_challenges WHERE
                owner_key=? AND space_key=? AND learner_key=? AND challenge_key=?''',
                (*scope.learner_scope(),challenge_id)).fetchone()
        return self._challenge_payload(inserted,row)

    def submit(self, *, challenge_id: str, operation_id: str, answer: str) -> dict:
        scope=self._scope(('learner',))
        challenge_id,operation_id=_id(challenge_id),_id(operation_id)
        answer=_text(answer,max_size=512,kind='ANSWER')
        digest=_sha(answer)
        now=self._now()
        with self._tx():
            old=self._db.execute('''SELECT * FROM study_score_receipts WHERE
                owner_key=? AND space_key=? AND learner_key=? AND operation_key=?''',
                (*scope.learner_scope(),operation_id)).fetchone()
            if old:
                if old['session_key']!=scope.session_id:
                    raise ValueError('CHALLENGE_SESSION_MISMATCH')
                if old['challenge_key']!=challenge_id or old['answer_digest']!=digest:
                    raise ValueError('OPERATION_CONFLICT')
                return json.loads(old['payload_json'])
            challenge=self._db.execute('''SELECT * FROM study_challenges WHERE
                owner_key=? AND space_key=? AND learner_key=? AND challenge_key=?''',
                (*scope.learner_scope(),challenge_id)).fetchone()
            if challenge is None:raise ValueError('CHALLENGE_NOT_FOUND')
            if challenge['session_key']!=scope.session_id:raise ValueError('CHALLENGE_SESSION_MISMATCH')
            if challenge['state']!='open':raise ValueError('CHALLENGE_ALREADY_ANSWERED')
            if now>=challenge['expires_ms']:raise ValueError('CHALLENGE_EXPIRED')
            draft=self._draft_row(scope,challenge['draft_key'])
            if draft is None or draft['status']!='approved':raise ValueError('QUESTION_NOT_APPROVED')
            self._check_draft(scope,draft)
            if draft['digest']!=challenge['question_digest']:
                raise ValueError('QUESTION_CHANGED')
            correct=_answer_key(answer)==_answer_key(draft['answer'])
            payload={'status':'RECORDED_NOT_MASTERY_PROOF','operation_id':operation_id,
                     'challenge_id':challenge_id,'correct':bool(correct),'answer':draft['answer'],
                     'source_locator':f"{draft['source_key']}@{draft['version']}:line-{draft['source_line']}",
                     'source_sha256':draft['source_digest'],'recorded_ms':now,
                     'clinical_release_ready':False,'host_authorized':False}
            self._db.execute('''INSERT INTO study_attempts
                (owner_key,space_key,learner_key,operation_key,challenge_key,draft_key,
                 question_digest,correct,occurred_ms) VALUES(?,?,?,?,?,?,?,?,?)''',
                (*scope.learner_scope(),operation_id,challenge_id,challenge['draft_key'],
                 draft['digest'],int(correct),now))
            self._db.execute('''INSERT INTO study_score_receipts
                (owner_key,space_key,learner_key,operation_key,challenge_key,session_key,answer_digest,payload_json)
                VALUES(?,?,?,?,?,?,?,?)''',
                (*scope.learner_scope(),operation_id,challenge_id,scope.session_id,digest,_wire(payload)))
            self._db.execute('''UPDATE study_challenges SET state='answered'
                WHERE owner_key=? AND space_key=? AND learner_key=? AND challenge_key=?''',
                (*scope.learner_scope(),challenge_id))
        return payload

    def score_receipt(self, operation_id: str) -> dict | None:
        scope=self._scope(('learner',))
        row=self._db.execute('''SELECT payload_json,session_key FROM study_score_receipts WHERE
            owner_key=? AND space_key=? AND learner_key=? AND operation_key=?''',
            (*scope.learner_scope(),_id(operation_id))).fetchone()
        if row and row['session_key']!=scope.session_id:
            raise ValueError('CHALLENGE_SESSION_MISMATCH')
        return json.loads(row['payload_json']) if row else None

    def review_queue(self, *, limit: int = 20) -> dict:
        scope=self._scope(('learner',))
        if type(limit) is not int or not 1<=limit<=100:
            raise ValueError('INVALID_LIMIT')
        now=self._now()
        rows=self._db.execute('''SELECT d.* FROM study_drafts d JOIN study_source_registry s
            ON s.owner_key=d.owner_key AND s.space_key=d.space_key
            AND s.source_key=d.source_key AND s.active_version=d.version
            WHERE d.owner_key=? AND d.space_key=? AND d.status='approved'
            ORDER BY d.source_key,d.source_line,d.draft_key''',scope.source_scope()).fetchall()
        queue=[]
        for d in rows:
            self._check_draft(scope,d)
            last=self._db.execute('''SELECT correct,occurred_ms FROM study_attempts WHERE
                owner_key=? AND space_key=? AND learner_key=? AND draft_key=?
                ORDER BY occurred_ms DESC,operation_key DESC LIMIT 1''',
                (*scope.learner_scope(),d['draft_key'])).fetchone()
            count=self._db.execute('''SELECT count(*) n FROM study_attempts WHERE
                owner_key=? AND space_key=? AND learner_key=? AND draft_key=?''',
                (*scope.learner_scope(),d['draft_key'])).fetchone()['n']
            basis='NOT_ATTEMPTED' if not last else 'CORRECT' if last['correct'] else 'INCORRECT'
            due_at=now if not last else last['occurred_ms']+(_DAY_MS if last['correct'] else 0)
            queue.append({'draft_id':d['draft_key'],'question':d['question'],
                          'source_locator':f"{d['source_key']}@{d['version']}:line-{d['source_line']}",
                          'basis':basis,'last_attempt_at':last['occurred_ms'] if last else None,
                          'due_ms':due_at,'due':due_at<=now,'attempts':count})
        queue.sort(key=lambda x:(not x['due'],x['due_ms'],x['draft_id']))
        return {'policy':'HEURISTIC_V1_NOT_FSRS','status':'LOCAL_REVIEW_PROJECTION_ONLY',
                'eligible':len(queue),'queue':queue[:limit],
                'truncated':len(queue)>limit,'clinical_release_ready':False}

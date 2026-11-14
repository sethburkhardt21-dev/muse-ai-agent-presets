"""Owner-scoped local notebook, preferences and reminder records.

This is offline SQLite code, not an authenticated host, scheduler or notifier.
The host must inject authority on every operation; constructing a scope is not
identity proof. SQLite is unencrypted, and logical forgetting is not secure
physical erasure. Filesystem admission is not an atomic OS sandbox.
"""
from __future__ import annotations
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Callable,Iterator
import re,sqlite3,time
from .database_paths import validated_database_path

_ID=re.compile(r'^[A-Za-z0-9][A-Za-z0-9_-]{0,79}$')
_BAD=re.compile('[\x00\u061c\u200e\u200f\u202a-\u202e\u2066-\u2069\u200b\u2060\ufeff]')
_MAX_MS=2**53
_LIMIT=256
_DEFAULTS={'tone':'neutral','large_text':False,'reminders_enabled':False,
           'paused':False,'quiet_start_minute_utc':-1,'quiet_end_minute_utc':-1}

def _id(value: str) -> str:
    if type(value) is not str or not _ID.fullmatch(value):raise ValueError('INVALID_ID')
    return value

def _text(value: str,limit: int=8000) -> str:
    if type(value) is not str or not value.strip() or len(value)>limit or _BAD.search(value):
        raise ValueError('INVALID_TEXT')
    return value.strip()

def _integer(value: int,*,minimum: int=0,maximum: int=_MAX_MS) -> int:
    if type(value) is not int or not minimum<=value<maximum:raise ValueError('INVALID_INTEGER')
    return value

@dataclass(frozen=True)
class CompanionScope:
    """Host-provided access scope. This value alone never authenticates a user."""
    owner_id: str
    space_id: str
    actor_id: str
    owner_present: bool=False
    def checked(self) -> 'CompanionScope':
        for value in (self.owner_id,self.space_id,self.actor_id):_id(value)
        if type(self.owner_present) is not bool or (self.owner_present and self.owner_id!=self.actor_id):
            raise ValueError('AUTHORITY_UNVERIFIED')
        return self
    def key(self) -> tuple[str,str]:
        return self.owner_id,self.space_id

class PersonalCompanion:
    """Local source reference with injected owner authority and explicit clock.

    Methods never contact a provider, execute arbitrary text, send notifications
    or spawn processes. Due reminders are a foreground read-only projection.
    Acknowledge changes local records only and binds an idempotency key to one
    reminder revision. On an uncertain database outcome, reopen and inspect the
    original receipt rather than infer that a notification was delivered.
    """
    def __init__(self,database: str|Path,*,authority: Callable[[],CompanionScope]|None=None,
                 clock_ms: Callable[[],int]|None=None):
        if not callable(authority):raise ValueError('AUTHORITY_UNBOUND')
        if clock_ms is not None and not callable(clock_ms):raise ValueError('CLOCK_INVALID')
        path=validated_database_path(database,error='DATABASE_PATH_UNSAFE',absolute=True)
        for part in (path,*path.parents):
            junction=getattr(part,'is_junction',None)
            if callable(junction) and junction():raise ValueError('DATABASE_PATH_UNSAFE')
        if path.exists() and path.stat().st_nlink!=1:raise ValueError('DATABASE_PATH_UNSAFE')
        self._authority=authority
        self._clock=clock_ms or (lambda:time.time_ns()//1_000_000)
        self._closed=False
        self._db=sqlite3.connect(path,timeout=5,isolation_level=None)
        self._db.row_factory=sqlite3.Row
        try:
            self._db.executescript('''
            CREATE TABLE IF NOT EXISTS companion_preferences (
              owner_key TEXT NOT NULL,space_key TEXT NOT NULL,revision INTEGER NOT NULL,
              tone TEXT NOT NULL,large_text INTEGER NOT NULL,reminders_enabled INTEGER NOT NULL,
              paused INTEGER NOT NULL,quiet_start INTEGER NOT NULL,quiet_end INTEGER NOT NULL,
              PRIMARY KEY(owner_key,space_key));
            CREATE TABLE IF NOT EXISTS companion_notes (
              owner_key TEXT NOT NULL,space_key TEXT NOT NULL,note_key TEXT NOT NULL,
              text TEXT NOT NULL,revision INTEGER NOT NULL,state TEXT NOT NULL,
              PRIMARY KEY(owner_key,space_key,note_key));
            CREATE TABLE IF NOT EXISTS companion_reminders (
              owner_key TEXT NOT NULL,space_key TEXT NOT NULL,reminder_key TEXT NOT NULL,
              title TEXT NOT NULL,due_ms INTEGER NOT NULL,revision INTEGER NOT NULL,state TEXT NOT NULL,
              PRIMARY KEY(owner_key,space_key,reminder_key));
            CREATE TABLE IF NOT EXISTS companion_acks (
              owner_key TEXT NOT NULL,space_key TEXT NOT NULL,operation_key TEXT NOT NULL,
              reminder_key TEXT NOT NULL,expected_revision INTEGER NOT NULL,
              resulting_revision INTEGER NOT NULL,ack_ms INTEGER NOT NULL,
              PRIMARY KEY(owner_key,space_key,operation_key));
            ''')
        except BaseException:
            self.close();raise
    def close(self) -> None:
        if not self._closed:
            self._closed=True;self._db.close()
    def __enter__(self) -> 'PersonalCompanion':return self
    def __exit__(self,*_exc: object) -> None:self.close()
    def _scope(self,owner_only: bool=False) -> CompanionScope:
        try:
            scope=self._authority()
            if type(scope) is not CompanionScope:raise ValueError('AUTHORITY_UNVERIFIED')
            scope.checked()
        except Exception as exc:raise ValueError('AUTHORITY_UNVERIFIED') from exc
        if owner_only and not scope.owner_present:raise ValueError('OWNER_APPROVAL_REQUIRED')
        return scope
    def _now(self) -> int:
        try:return _integer(self._clock())
        except Exception as exc:raise ValueError('CLOCK_INVALID') from exc
    @contextmanager
    def _transaction(self) -> Iterator[None]:
        try:
            self._db.execute('BEGIN IMMEDIATE')
            yield
            self._db.execute('COMMIT')
        except BaseException as exc:
            if self._db.in_transaction:
                try:self._db.execute('ROLLBACK')
                except sqlite3.Error:pass
            if isinstance(exc,sqlite3.Error):
                raise ValueError('LOCAL_TRANSACTION_UNCONFIRMED_REOPEN_RECEIPT') from exc
            raise
    def _prefs(self,scope: CompanionScope) -> dict:
        row=self._db.execute('SELECT * FROM companion_preferences WHERE owner_key=? AND space_key=?',scope.key()).fetchone()
        if row is None:return dict(_DEFAULTS,revision=0)
        return {'revision':row['revision'],'tone':row['tone'],'large_text':bool(row['large_text']),
                'reminders_enabled':bool(row['reminders_enabled']),'paused':bool(row['paused']),
                'quiet_start_minute_utc':row['quiet_start'],'quiet_end_minute_utc':row['quiet_end']}
    def preferences(self) -> dict:return self._prefs(self._scope())
    def configure(self,*,expected_revision: int,changes: dict) -> dict:
        scope=self._scope(True);_integer(expected_revision)
        if type(changes) is not dict or not changes or not set(changes)<=set(_DEFAULTS):
            raise ValueError('INVALID_PREFERENCE_FIELDS')
        with self._transaction():
            old=self._prefs(scope)
            if old['revision']!=expected_revision:raise ValueError('STALE_REVISION')
            data=dict(old,**changes)
            if data['tone'] not in ('neutral','gentle','direct'):raise ValueError('INVALID_TONE')
            for key in ('large_text','reminders_enabled','paused'):
                if type(data[key]) is not bool:raise ValueError('INVALID_PREFERENCE_BOOLEAN')
            start,end=data['quiet_start_minute_utc'],data['quiet_end_minute_utc']
            if type(start) is not int or type(end) is not int:raise ValueError('INVALID_QUIET_HOURS')
            if (start,end)!=(-1,-1) and not (0<=start<1440 and 0<=end<1440 and start!=end):
                raise ValueError('INVALID_QUIET_HOURS')
            revision=_integer(expected_revision+1,minimum=1)
            self._db.execute('''INSERT INTO companion_preferences VALUES(?,?,?,?,?,?,?,?,?)
                ON CONFLICT(owner_key,space_key) DO UPDATE SET revision=excluded.revision,
                tone=excluded.tone,large_text=excluded.large_text,reminders_enabled=excluded.reminders_enabled,
                paused=excluded.paused,quiet_start=excluded.quiet_start,quiet_end=excluded.quiet_end''',
                (*scope.key(),revision,data['tone'],int(data['large_text']),int(data['reminders_enabled']),int(data['paused']),start,end))
            return self._prefs(scope)
    def _note_row(self,scope: CompanionScope,key: str):
        return self._db.execute('SELECT note_key,text,revision,state FROM companion_notes WHERE owner_key=? AND space_key=? AND note_key=?',(*scope.key(),key)).fetchone()
    @staticmethod
    def _note_payload(row) -> dict:
        return {'note_id':row['note_key'],'text':row['text'],'revision':row['revision']}
    def note(self,note_id: str) -> dict|None:
        row=self._note_row(self._scope(),_id(note_id))
        return self._note_payload(row) if row is not None and row['state']=='active' else None
    def _notes(self,scope: CompanionScope) -> list[dict]:
        rows=self._db.execute("SELECT note_key,text,revision FROM companion_notes WHERE owner_key=? AND space_key=? AND state='active' ORDER BY note_key LIMIT ?",(*scope.key(),_LIMIT+1)).fetchall()
        if len(rows)>_LIMIT:raise ValueError('NOTE_LIMIT_EXCEEDED')
        return [self._note_payload(row) for row in rows]
    def notes(self) -> list[dict]:return self._notes(self._scope())
    def put_note(self,note_id: str,text: str,*,expected_revision: int=0) -> dict:
        scope=self._scope(True);key=_id(note_id);text=_text(text);_integer(expected_revision)
        with self._transaction():
            row=self._note_row(scope,key)
            current=row['revision'] if row is not None else 0
            if current!=expected_revision:raise ValueError('STALE_REVISION')
            if row is None:
                count=self._db.execute('SELECT COUNT(*) FROM companion_notes WHERE owner_key=? AND space_key=?',scope.key()).fetchone()[0]
                if count>=_LIMIT:raise ValueError('NOTE_LIMIT')
            revision=_integer(current+1,minimum=1)
            self._db.execute('''INSERT INTO companion_notes VALUES(?,?,?,?,?,'active')
              ON CONFLICT(owner_key,space_key,note_key) DO UPDATE SET text=excluded.text,
              revision=excluded.revision,state='active' ''',(*scope.key(),key,text,revision))
            return self._note_payload(self._note_row(scope,key))
    def forget_note(self,note_id: str,*,expected_revision: int) -> dict:
        scope=self._scope(True);key=_id(note_id);_integer(expected_revision,minimum=1)
        with self._transaction():
            row=self._note_row(scope,key)
            if row is None or row['state']!='active':raise ValueError('NOTE_NOT_FOUND')
            if row['revision']!=expected_revision:raise ValueError('STALE_REVISION')
            revision=_integer(expected_revision+1,minimum=1)
            self._db.execute("UPDATE companion_notes SET text='',state='deleted',revision=? WHERE owner_key=? AND space_key=? AND note_key=?",(revision,*scope.key(),key))
            return {'note_id':key,'revision':revision,'state':'deleted','secure_erasure':False}
    def _reminder_row(self,scope: CompanionScope,key: str):
        return self._db.execute('SELECT reminder_key,title,due_ms,revision,state FROM companion_reminders WHERE owner_key=? AND space_key=? AND reminder_key=?',(*scope.key(),key)).fetchone()
    @staticmethod
    def _reminder_payload(row) -> dict:
        return {'reminder_id':row['reminder_key'],'title':row['title'],'due_ms':row['due_ms'],
                'revision':row['revision'],'state':row['state']}
    def reminder(self,reminder_id: str) -> dict|None:
        row=self._reminder_row(self._scope(),_id(reminder_id))
        return self._reminder_payload(row) if row is not None else None
    def add_reminder(self,*,reminder_id: str,title: str,due_ms: int) -> dict:
        scope=self._scope(True);key=_id(reminder_id);title=_text(title,160);_integer(due_ms)
        with self._transaction():
            if self._reminder_row(scope,key) is not None:raise ValueError('REMINDER_EXISTS')
            count=self._db.execute('SELECT COUNT(*) FROM companion_reminders WHERE owner_key=? AND space_key=?',scope.key()).fetchone()[0]
            if count>=_LIMIT:raise ValueError('REMINDER_LIMIT')
            self._db.execute("INSERT INTO companion_reminders VALUES(?,?,?,?,?,1,'pending')",(*scope.key(),key,title,due_ms))
            return self._reminder_payload(self._reminder_row(scope,key))
    @staticmethod
    def _policy(prefs: dict,now: int) -> str:
        if not prefs['reminders_enabled']:return 'REMINDERS_DISABLED'
        if prefs['paused']:return 'PAUSED'
        start,end=prefs['quiet_start_minute_utc'],prefs['quiet_end_minute_utc']
        minute=(now//60000)%1440
        if start>=0 and ((start<end and start<=minute<end) or (start>end and (minute>=start or minute<end))):
            return 'QUIET_HOURS'
        return 'LOCAL_DUE_RECORDS'
    def _due(self,scope: CompanionScope,now: int) -> dict:
        status=self._policy(self._prefs(scope),now)
        items=[]
        if status=='LOCAL_DUE_RECORDS':
            rows=self._db.execute("SELECT reminder_key,title,due_ms,revision,state FROM companion_reminders WHERE owner_key=? AND space_key=? AND state='pending' AND due_ms<=? ORDER BY due_ms,reminder_key LIMIT ?",(*scope.key(),now,_LIMIT+1)).fetchall()
            if len(rows)>_LIMIT:raise ValueError('REMINDER_LIMIT_EXCEEDED')
            items=[self._reminder_payload(row) for row in rows]
        return {'status':status,'items':items,'clock_basis':'UTC_EPOCH_MILLISECONDS',
                'notification_sent':False,'native_installed':False}
    def due_reminders(self) -> dict:return self._due(self._scope(),self._now())
    def cancel_reminder(self,reminder_id: str,*,expected_revision: int) -> dict:
        scope=self._scope(True);key=_id(reminder_id);_integer(expected_revision,minimum=1)
        with self._transaction():
            row=self._reminder_row(scope,key)
            if row is None:raise ValueError('REMINDER_NOT_FOUND')
            if row['revision']!=expected_revision:raise ValueError('STALE_REVISION')
            if row['state']!='pending':raise ValueError('REMINDER_NOT_PENDING')
            revision=_integer(expected_revision+1,minimum=1)
            self._db.execute("UPDATE companion_reminders SET state='cancelled',revision=? WHERE owner_key=? AND space_key=? AND reminder_key=?",(revision,*scope.key(),key))
            return self._reminder_payload(self._reminder_row(scope,key))
    def _receipt_row(self,scope: CompanionScope,key: str):
        return self._db.execute('SELECT * FROM companion_acks WHERE owner_key=? AND space_key=? AND operation_key=?',(*scope.key(),key)).fetchone()
    @staticmethod
    def _receipt_payload(row) -> dict:
        return {'operation_id':row['operation_key'],'reminder_id':row['reminder_key'],
                'expected_revision':row['expected_revision'],'revision':row['resulting_revision'],
                'ack_ms':row['ack_ms'],'status':'LOCALLY_ACKNOWLEDGED',
                'effect_scope':'LOCAL_SQLITE_ONLY','notification_sent':False,
                'host_authenticated':False,'native_installed':False}
    def receipt(self,operation_id: str) -> dict|None:
        row=self._receipt_row(self._scope(True),_id(operation_id))
        return self._receipt_payload(row) if row is not None else None
    def acknowledge(self,reminder_id: str,*,expected_revision: int,operation_id: str) -> dict:
        scope=self._scope(True);key=_id(reminder_id);op=_id(operation_id)
        _integer(expected_revision,minimum=1);now=self._now()
        with self._transaction():
            existing=self._receipt_row(scope,op)
            if existing is not None:
                if existing['reminder_key']!=key or existing['expected_revision']!=expected_revision:
                    raise ValueError('OPERATION_CONFLICT')
                return self._receipt_payload(existing)
            policy=self._policy(self._prefs(scope),now)
            if policy!='LOCAL_DUE_RECORDS':raise ValueError(policy)
            row=self._reminder_row(scope,key)
            if row is None:raise ValueError('REMINDER_NOT_FOUND')
            if row['revision']!=expected_revision:raise ValueError('STALE_REVISION')
            if row['state']!='pending':raise ValueError('REMINDER_NOT_PENDING')
            if row['due_ms']>now:raise ValueError('REMINDER_NOT_DUE')
            revision=_integer(expected_revision+1,minimum=1)
            self._db.execute("UPDATE companion_reminders SET state='acknowledged',revision=? WHERE owner_key=? AND space_key=? AND reminder_key=?",(revision,*scope.key(),key))
            self._db.execute('INSERT INTO companion_acks VALUES(?,?,?,?,?,?,?)',(*scope.key(),op,key,expected_revision,revision,now))
            return self._receipt_payload(self._receipt_row(scope,op))
    def day_plan(self) -> dict:
        scope=self._scope();now=self._now()
        return {'status':'LOCAL_PERSONAL_PLAN','preferences':self._prefs(scope),
                'notes':self._notes(scope),'due':self._due(scope,now),
                'notification_sent':False,'native_installed':False,'host_authenticated':False}

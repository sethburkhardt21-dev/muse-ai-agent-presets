"""First-party, SDK-independent local Space request/callback adapter (protocol v1).

An injected scope/verifier is a host integration boundary, not proof of Muse
identity. No network, model, provider job or background timer is started here.
Claim reserves durable state BEFORE a host attempts an effect. Unknown effects
are never retried by this adapter. SQLite is not encrypted or an OS sandbox.
"""
from __future__ import annotations
from contextlib import contextmanager
from pathlib import Path
from typing import Callable
import copy,hashlib,json,re,sqlite3,time
from .database_paths import validated_database_path
from .personal_companion import CompanionScope

_ID=re.compile(r'^[A-Za-z0-9][A-Za-z0-9_-]{0,79}$')
_BAD=re.compile('[\x00-\x08\x0b-\x1f\x7f\u061c\u200e\u200f\u202a-\u202e\u2066-\u2069\u200b\u2060\ufeff]')
_FIELDS={'request_id','operation_id','request_sha256','event_id','status','result'}
_MAX=2**53

def _id(x):
 if type(x) is not str or not _ID.fullmatch(x):raise ValueError('INVALID_ID')
 return x

def _text(x):
 if type(x) is not str or not x.strip() or len(x)>8000 or _BAD.search(x):raise ValueError('INVALID_TEXT')
 return x

def _int(x,low=0,high=_MAX):
 if type(x) is not int or not low<=x<high:raise ValueError('INVALID_INTEGER')
 return x

def _sha(x):return hashlib.sha256(x.encode('utf-8')).hexdigest()

class SpaceCompanion:
 """Persistent local requests with explicit host-authenticated callback injection.

 Reopening does not issue work. The foreground host must explicitly claim once,
 handle the returned intent, authenticate a callback and inspect actual effects.
 The loopback UI exposes neither claim nor callback authority.
 """
 def __init__(self,database:str|Path,*,authority:Callable[[],CompanionScope]|None=None,
              clock_ms:Callable[[],int]|None=None,callback_verifier:Callable[[dict],bool]|None=None):
  if not callable(authority):raise ValueError('AUTHORITY_UNBOUND')
  if clock_ms is not None and not callable(clock_ms):raise ValueError('CLOCK_INVALID')
  if callback_verifier is not None and not callable(callback_verifier):raise ValueError('VERIFIER_INVALID')
  path=validated_database_path(database,error='DATABASE_PATH_UNSAFE',absolute=True)
  if any(callable(getattr(p,'is_junction',None)) and p.is_junction() for p in (path,*path.parents)):
   raise ValueError('DATABASE_PATH_UNSAFE')
  if path.exists() and path.stat().st_nlink!=1:raise ValueError('DATABASE_PATH_UNSAFE')
  self._authority=authority;self._clock=clock_ms or (lambda:time.time_ns()//1_000_000)
  self._verifier=callback_verifier;self._closed=False
  self._db=sqlite3.connect(path,timeout=5,isolation_level=None);self._db.row_factory=sqlite3.Row
  try:
   self._db.executescript('''
    CREATE TABLE IF NOT EXISTS space_policy(owner_key TEXT NOT NULL,space_key TEXT NOT NULL,
      enabled INTEGER NOT NULL,revision INTEGER NOT NULL,PRIMARY KEY(owner_key,space_key));
    CREATE TABLE IF NOT EXISTS space_requests(owner_key TEXT NOT NULL,space_key TEXT NOT NULL,
      request_key TEXT NOT NULL,prompt TEXT NOT NULL,request_sha256 TEXT NOT NULL,state TEXT NOT NULL,
      revision INTEGER NOT NULL,operation_key TEXT,deadline_ms INTEGER,result TEXT NOT NULL,
      created_ms INTEGER NOT NULL,PRIMARY KEY(owner_key,space_key,request_key),
      UNIQUE(owner_key,space_key,operation_key));
    CREATE TABLE IF NOT EXISTS space_callbacks(owner_key TEXT NOT NULL,space_key TEXT NOT NULL,
      event_key TEXT NOT NULL,request_key TEXT NOT NULL,event_sha256 TEXT NOT NULL,
      PRIMARY KEY(owner_key,space_key,event_key));
   ''')
  except BaseException:self.close();raise
 def close(self):
  if not self._closed:self._closed=True;self._db.close()
 def __enter__(self):return self
 def __exit__(self,*_):self.close()
 def _scope(self):
  try:
   s=self._authority()
   if type(s) is not CompanionScope:raise ValueError('AUTHORITY_UNVERIFIED')
   s.checked()
  except Exception as exc:raise ValueError('AUTHORITY_UNVERIFIED') from exc
  if not s.owner_present:raise ValueError('OWNER_APPROVAL_REQUIRED')
  return s
 def _now(self):
  try:return _int(self._clock())
  except Exception as exc:raise ValueError('CLOCK_INVALID') from exc
 @contextmanager
 def _tx(self):
  try:
   self._db.execute('BEGIN IMMEDIATE');yield;self._db.execute('COMMIT')
  except BaseException as exc:
   if self._db.in_transaction:
    try:self._db.execute('ROLLBACK')
    except sqlite3.Error:pass
   if isinstance(exc,sqlite3.Error):raise ValueError('TRANSACTION_UNCONFIRMED_REOPEN_ORIGINAL_STATE') from exc
   raise
 def _policy(self,s):
  r=self._db.execute('SELECT enabled,revision FROM space_policy WHERE owner_key=? AND space_key=?',s.key()).fetchone()
  return {'enabled':bool(r['enabled']),'revision':r['revision']} if r else {'enabled':False,'revision':0}
 def _enabled(self,s):
  if not self._policy(s)['enabled']:raise ValueError('ADAPTER_DISABLED')
 def _row(self,s,key):return self._db.execute('SELECT * FROM space_requests WHERE owner_key=? AND space_key=? AND request_key=?',(*s.key(),key)).fetchone()
 @staticmethod
 def _payload(r):
  if r is None:return None
  return {'request_id':r['request_key'],'prompt':r['prompt'],'request_sha256':r['request_sha256'],
          'state':r['state'],'revision':r['revision'],'operation_id':r['operation_key'],
          'deadline_ms':r['deadline_ms'],'result':r['result'],'created_ms':r['created_ms'],
          'provider_dispatched':False,'native_installed':False,'effect_scope':'LOCAL_STATE_ONLY'}
 def configure(self,*,enabled:bool,expected_revision:int):
  s=self._scope();_int(expected_revision)
  if type(enabled) is not bool:raise ValueError('INVALID_BOOLEAN')
  with self._tx():
   p=self._policy(s)
   if p['revision']!=expected_revision:raise ValueError('STALE_REVISION')
   revision=_int(expected_revision+1,1)
   self._db.execute('INSERT INTO space_policy VALUES(?,?,?,?) ON CONFLICT(owner_key,space_key) DO UPDATE SET enabled=excluded.enabled,revision=excluded.revision',(*s.key(),int(enabled),revision))
   return self._policy(s)
 def request(self,request_id:str,prompt:str):
  s=self._scope();key=_id(request_id);text=_text(prompt);now=self._now()
  with self._tx():
   self._enabled(s);row=self._row(s,key)
   if row:
    if row['prompt']!=text:raise ValueError('REQUEST_CONFLICT')
    return self._payload(row)
   if self._db.execute('SELECT COUNT(*) FROM space_requests WHERE owner_key=? AND space_key=?',s.key()).fetchone()[0]>=128:raise ValueError('REQUEST_LIMIT')
   self._db.execute("INSERT INTO space_requests VALUES(?,?,?,?,?,'queued',1,NULL,NULL,'',?)",(*s.key(),key,text,_sha(text),now))
   return self._payload(self._row(s,key))
 def get(self,request_id:str):return self._payload(self._row(self._scope(),_id(request_id)))
 def snapshot(self):
  s=self._scope()
  rows=self._db.execute('SELECT * FROM space_requests WHERE owner_key=? AND space_key=? ORDER BY created_ms,request_key LIMIT 129',s.key()).fetchall()
  if len(rows)>128:raise ValueError('REQUEST_LIMIT')
  return dict(self._policy(s),requests=[self._payload(r) for r in rows],native_installed=False,
              provider_connected=False,callback_endpoint_exposed=False,protocol='space-starter/1')
 def claim(self,request_id:str,*,expected_revision:int,operation_id:str,timeout_ms:int=60000):
  s=self._scope();key=_id(request_id);op=_id(operation_id);_int(expected_revision,1);_int(timeout_ms,1,300001)
  now=self._now();deadline=_int(now+timeout_ms)
  with self._tx():
   self._enabled(s);r=self._row(s,key)
   if r is None:raise ValueError('REQUEST_NOT_FOUND')
   if r['revision']!=expected_revision:raise ValueError('STALE_REVISION')
   if r['state']!='queued':raise ValueError('REQUEST_NOT_QUEUED')
   if self._db.execute('SELECT 1 FROM space_requests WHERE owner_key=? AND space_key=? AND operation_key=?',(*s.key(),op)).fetchone():raise ValueError('OPERATION_CONFLICT')
   rev=_int(expected_revision+1,1)
   self._db.execute("UPDATE space_requests SET state='dispatching',revision=?,operation_key=?,deadline_ms=? WHERE owner_key=? AND space_key=? AND request_key=?",(rev,op,deadline,*s.key(),key))
   return self._payload(self._row(s,key))
 def expire(self):
  s=self._scope();now=self._now()
  with self._tx():
   rows=self._db.execute("SELECT request_key,revision FROM space_requests WHERE owner_key=? AND space_key=? AND state='dispatching' AND deadline_ms<=?",(*s.key(),now)).fetchall()
   for row in rows:
    rev=_int(row['revision']+1,1)
    self._db.execute("UPDATE space_requests SET state='unknown',revision=? WHERE owner_key=? AND space_key=? AND request_key=?",(rev,*s.key(),row['request_key']))
   return len(rows)
 def cancel(self,request_id:str,*,expected_revision:int):
  s=self._scope();key=_id(request_id);_int(expected_revision)
  with self._tx():
   r=self._row(s,key)
   if r is None:raise ValueError('REQUEST_NOT_FOUND')
   if r['revision']!=expected_revision:raise ValueError('STALE_REVISION')
   if r['state'] in ('completed','failed','cancelled'):raise ValueError('REQUEST_TERMINAL')
   self._db.execute("UPDATE space_requests SET state='cancelled',revision=? WHERE owner_key=? AND space_key=? AND request_key=?",(_int(expected_revision+1,1),*s.key(),key))
   return self._payload(self._row(s,key))
 def callback(self,event:dict):
  s=self._scope()
  if type(event) is not dict or set(event)!=_FIELDS:raise ValueError('CALLBACK_FIELDS')
  e=dict(event)
  for field in ('request_id','operation_id','event_id'):_id(e[field])
  if type(e['request_sha256']) is not str or not re.fullmatch('[0-9a-f]{64}',e['request_sha256']):raise ValueError('CALLBACK_DIGEST')
  if type(e['status']) is not str or e['status'] not in ('SUCCEEDED','FAILED'):raise ValueError('CALLBACK_STATUS')
  _text(e['result']);now=self._now()
  try:verified=self._verifier is not None and self._verifier(copy.deepcopy(e)) is True
  except Exception as exc:raise ValueError('CALLBACK_UNVERIFIED') from exc
  if not verified:raise ValueError('CALLBACK_UNVERIFIED')
  digest=_sha(json.dumps(e,sort_keys=True,ensure_ascii=False,separators=(',',':')))
  with self._tx():
   prior=self._db.execute('SELECT request_key,event_sha256 FROM space_callbacks WHERE owner_key=? AND space_key=? AND event_key=?',(*s.key(),e['event_id'])).fetchone()
   if prior:
    if prior['event_sha256']!=digest:raise ValueError('CALLBACK_CONFLICT')
    return self._payload(self._row(s,prior['request_key']))
   r=self._row(s,e['request_id'])
   if r is None:raise ValueError('REQUEST_NOT_FOUND')
   if r['operation_key']!=e['operation_id'] or r['request_sha256']!=e['request_sha256']:raise ValueError('CALLBACK_BINDING_MISMATCH')
   if r['state']!='dispatching':raise ValueError('REQUEST_NOT_DISPATCHING')
   if now>=r['deadline_ms']:raise ValueError('CALLBACK_LATE')
   state='completed' if e['status']=='SUCCEEDED' else 'failed'
   self._db.execute('UPDATE space_requests SET state=?,revision=?,result=? WHERE owner_key=? AND space_key=? AND request_key=?',(state,_int(r['revision']+1,1),e['result'],*s.key(),e['request_id']))
   self._db.execute('INSERT INTO space_callbacks VALUES(?,?,?,?,?)',(*s.key(),e['event_id'],e['request_id'],digest))
   return self._payload(self._row(s,e['request_id']))

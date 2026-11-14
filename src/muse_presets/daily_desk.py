"""Daily Desk records on the existing PersonalCompanion SQLite backend.

Local task/note transactions only: no model, scheduler, notification or native
provider. An injected scope is the host boundary, not proof of Muse identity.
Backups contain plaintext notes and operation receipts; hashes check consistency,
not authorship. Filesystem checks assume an owner-controlled parent directory.
"""
from __future__ import annotations
import hashlib,hmac,json,os,re,secrets,sqlite3,tempfile
from pathlib import Path
from typing import Callable
from .personal_companion import PersonalCompanion,CompanionScope,_id,_text,_integer
from .database_paths import validated_database_path

FORMAT='daily-desk/1'
MAX_RECORDS=256
MAX_OPERATIONS=1024
MAX_ARCHIVE_BYTES=16*1024*1024
HEX=re.compile(r'^[0-9a-f]{64}$')
CONTROL=re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]')
TASK_KEYS={'task_id','title','status','due_ms','revision','created_ms','updated_ms'}
NOTE_KEYS={'note_id','text','revision'}
REQUEST_KEYS={'kind','item_id','expected_revision','fields'}
OP_KEYS={'operation_id','request','request_sha256','result','at_ms'}


def canonical(value:object)->bytes:
    try:
        return json.dumps(value,sort_keys=True,ensure_ascii=False,
                          allow_nan=False,separators=(',',':')).encode('utf-8')
    except (ValueError,TypeError,UnicodeError,RecursionError) as exc:
        raise ValueError('INVALID_JSON_VALUE') from exc


def _digest(value:object)->str:return hashlib.sha256(canonical(value)).hexdigest()


def _pairs(pairs):
    result={}
    for key,value in pairs:
        if key in result:raise ValueError('DUPLICATE_JSON_KEY')
        result[key]=value
    return result


def _reject_constant(_):raise ValueError('NONFINITE_JSON')


def _parse(raw:bytes):
    try:return json.loads(raw.decode('utf-8'),object_pairs_hook=_pairs,
                          parse_constant=_reject_constant)
    except (ValueError,UnicodeError,RecursionError) as exc:
        raise ValueError('ARCHIVE_INVALID_JSON') from exc


def _exact(value,fields:set[str],code='ARCHIVE_FIELDS'):
    if type(value) is not dict or set(value)!=fields:raise ValueError(code)


def _clean_text(value,limit=8000):
    value=_text(value,limit)
    if CONTROL.search(value):raise ValueError('INVALID_TEXT')
    # Refuse lone surrogates before any SQLite or filesystem effect.
    try:value.encode('utf-8')
    except UnicodeError as exc:raise ValueError('INVALID_TEXT') from exc
    return value


def _scope_from(authority:Callable[[],CompanionScope])->CompanionScope:
    if not callable(authority):raise ValueError('AUTHORITY_UNBOUND')
    try:
        scope=authority()
        if type(scope) is not CompanionScope:raise ValueError('AUTHORITY_UNVERIFIED')
        scope.checked()
    except Exception as exc:raise ValueError('AUTHORITY_UNVERIFIED') from exc
    if not scope.owner_present:raise ValueError('OWNER_APPROVAL_REQUIRED')
    return scope


def _task_fields(title,status,due_ms):
    title=_clean_text(title,160)
    if type(status) is not str or status not in ('pending','done'):
        raise ValueError('INVALID_TASK_STATUS')
    if due_ms is not None:_integer(due_ms)
    return {'title':title,'status':status,'due_ms':due_ms}


def _task_record(row):
    _exact(row,TASK_KEYS)
    _id(row['task_id']);fields=_task_fields(row['title'],row['status'],row['due_ms'])
    if any(row[k]!=v for k,v in fields.items()):raise ValueError('ARCHIVE_TEXT_NOT_CANONICAL')
    _integer(row['revision'],minimum=1);_integer(row['created_ms']);_integer(row['updated_ms'])
    if row['updated_ms']<row['created_ms']:raise ValueError('ARCHIVE_TIME_ORDER')


def _note_record(row,*,state=False):
    _exact(row,NOTE_KEYS|({'state'} if state else set()))
    _id(row['note_id']);_integer(row['revision'],minimum=1)
    if state and row['state']=='deleted':
        if row['text']!='':raise ValueError('ARCHIVE_DELETED_NOTE')
    else:
        if state and row['state']!='active':raise ValueError('ARCHIVE_NOTE_STATE')
        if _clean_text(row['text'])!=row['text']:raise ValueError('ARCHIVE_TEXT_NOT_CANONICAL')


def _request(value):
    _exact(value,REQUEST_KEYS);_id(value['item_id']);_integer(value['expected_revision'])
    if value['kind']=='task':
        _exact(value['fields'],{'title','status','due_ms'})
        fields=_task_fields(**value['fields'])
    elif value['kind']=='note':
        _exact(value['fields'],{'text'});fields={'text':_clean_text(value['fields']['text'])}
    else:raise ValueError('ARCHIVE_OPERATION_KIND')
    if fields!=value['fields']:raise ValueError('ARCHIVE_OPERATION_TEXT')


def _operation(row):
    _exact(row,OP_KEYS);_id(row['operation_id']);_integer(row['at_ms']);_request(row['request'])
    if type(row['request_sha256']) is not str or not HEX.fullmatch(row['request_sha256']):
        raise ValueError('ARCHIVE_OPERATION_DIGEST')
    if not hmac.compare_digest(row['request_sha256'],_digest(row['request'])):
        raise ValueError('ARCHIVE_OPERATION_DIGEST')
    req=row['request'];result=row['result']
    if req['kind']=='task':
        _task_record(result)
        if result['task_id']!=req['item_id'] or result['updated_ms']!=row['at_ms']:
            raise ValueError('ARCHIVE_OPERATION_BINDING')
    else:
        _note_record(result)
        if result['note_id']!=req['item_id']:raise ValueError('ARCHIVE_OPERATION_BINDING')
    if result['revision']!=req['expected_revision']+1:
        raise ValueError('ARCHIVE_OPERATION_REVISION')
    if any(result[k]!=v for k,v in req['fields'].items()):
        raise ValueError('ARCHIVE_OPERATION_BINDING')


def _payload(value):
    _exact(value,{'scope','tasks','notes','operations'})
    _exact(value['scope'],{'owner_id','space_id'})
    for v in value['scope'].values():_id(v)
    indexed={}
    for key,idkey,limit,validate in [('tasks','task_id',MAX_RECORDS,_task_record),
          ('notes','note_id',MAX_RECORDS,lambda r:_note_record(r,state=True)),
          ('operations','operation_id',MAX_OPERATIONS,_operation)]:
        rows=value[key]
        if type(rows) is not list or len(rows)>limit:raise ValueError('ARCHIVE_COUNT')
        ids=[]
        for row in rows:validate(row);ids.append(row[idkey])
        if len(ids)!=len(set(ids)) or ids!=sorted(ids):raise ValueError('ARCHIVE_ORDER_OR_DUPLICATE')
        indexed[key]={row[idkey]:row for row in rows}
    for row in value['operations']:
        req=row['request'];records=indexed['tasks' if req['kind']=='task' else 'notes']
        current=records.get(req['item_id'])
        if current is None or row['result']['revision']>current['revision']:
            raise ValueError('ARCHIVE_OPERATION_ORPHAN')
        if row['result']['revision']==current['revision']:
            fields=TASK_KEYS if req['kind']=='task' else NOTE_KEYS
            if (any(current[k]!=row['result'][k] for k in fields)
                or (req['kind']=='note' and current['state']!='active')):
                raise ValueError('ARCHIVE_LATEST_RESULT_MISMATCH')


def _collect(db,scope):
    tasks=[dict(row) for row in db.execute('SELECT task_key AS task_id,title,status,due_ms,revision,created_ms,updated_ms FROM daily_tasks WHERE owner_key=? AND space_key=? ORDER BY task_key LIMIT ?',(*scope.key(),MAX_RECORDS+1))]
    notes=[dict(row) for row in db.execute('SELECT note_key AS note_id,text,revision,state FROM companion_notes WHERE owner_key=? AND space_key=? ORDER BY note_key LIMIT ?',(*scope.key(),MAX_RECORDS+1))]
    operations=[]
    for row in db.execute('SELECT operation_key,request_json,request_sha256,result_json,at_ms FROM daily_operations WHERE owner_key=? AND space_key=? ORDER BY operation_key LIMIT ?',(*scope.key(),MAX_OPERATIONS+1)):
        operations.append({'operation_id':row['operation_key'],'request':_parse(row['request_json'].encode()),'request_sha256':row['request_sha256'],'result':_parse(row['result_json'].encode()),'at_ms':row['at_ms']})
    data={'scope':{'owner_id':scope.owner_id,'space_id':scope.space_id},'tasks':tasks,'notes':notes,'operations':operations}
    _payload(data);return data


def inspect_desk(database:str|Path,*,authority:Callable[[],CompanionScope])->dict:
    """Read an existing restore without creating/migrating any tables or records."""
    scope=_scope_from(authority)
    path=validated_database_path(database,error='RESTORE_PATH_UNSAFE',absolute=True)
    if any(callable(getattr(p,'is_junction',None)) and p.is_junction() for p in (path,*path.parents)):
        raise ValueError('RESTORE_PATH_UNSAFE')
    if not path.exists():return {'status':'RESTORE_NOT_FOUND','native_installed':False}
    if path.stat().st_nlink!=1:raise ValueError('RESTORE_PATH_UNSAFE')
    try:
        db=sqlite3.connect(path.as_uri()+'?mode=ro',uri=True,isolation_level=None,timeout=5)
        try:
            db.row_factory=sqlite3.Row;db.execute('BEGIN')
            row=db.execute('SELECT version FROM daily_schema WHERE singleton=1').fetchone()
            if row is None or row['version']!=1:raise ValueError('SCHEMA_VERSION_UNSUPPORTED')
            payload=_collect(db,scope);db.execute('COMMIT')
        finally:db.close()
    except sqlite3.Error as exc:raise ValueError('RESTORE_READBACK_UNCONFIRMED') from exc
    return {'status':'RESTORED_STORE_VERIFIED','database':str(path),'tasks':len(payload['tasks']),
            'notes':sum(x['state']=='active' for x in payload['notes']),
            'payload_sha256':_digest(payload),'native_installed':False,'read_only':True}


def read_archive(raw:bytes)->dict:
    """Strict bounded parsing; no SQL, paths, authentication or executable content."""
    if type(raw) is not bytes or not 1<=len(raw)<=MAX_ARCHIVE_BYTES:
        raise ValueError('ARCHIVE_SIZE')
    envelope=_parse(raw);_exact(envelope,{'format','payload','sha256'})
    if envelope['format']!=FORMAT:raise ValueError('ARCHIVE_VERSION')
    digest=envelope['sha256']
    if type(digest) is not str or not HEX.fullmatch(digest) or not hmac.compare_digest(digest,_digest(envelope['payload'])):
        raise ValueError('ARCHIVE_DIGEST_MISMATCH')
    _payload(envelope['payload'])
    return envelope['payload']


class DailyDesk(PersonalCompanion):
    """A bounded domain extension: same connection, scope and transaction machinery."""
    def __init__(self,database:str|Path,*,authority:Callable[[],CompanionScope],clock_ms=None):
        _scope_from(authority)
        super().__init__(database,authority=authority,clock_ms=clock_ms)
        try:
            with self._transaction():
                self._db.execute('CREATE TABLE IF NOT EXISTS daily_schema(singleton INTEGER PRIMARY KEY CHECK(singleton=1),version INTEGER NOT NULL,store_key TEXT NOT NULL)')
                row=self._db.execute('SELECT version,store_key FROM daily_schema WHERE singleton=1').fetchone()
                if row is not None and row['version']!=1:raise ValueError('SCHEMA_VERSION_UNSUPPORTED')
                if row is None:
                    self._store_key=secrets.token_hex(16)
                    self._db.execute('INSERT INTO daily_schema VALUES(1,1,?)',(self._store_key,))
                else:
                    self._store_key=row['store_key']
                    if type(self._store_key) is not str or not re.fullmatch('[a-f0-9]{32}',self._store_key):
                        raise ValueError('SCHEMA_STORE_ID_INVALID')
                self._db.execute('''CREATE TABLE IF NOT EXISTS daily_tasks(
                  owner_key TEXT NOT NULL,space_key TEXT NOT NULL,task_key TEXT NOT NULL,
                  title TEXT NOT NULL,status TEXT NOT NULL,due_ms INTEGER,revision INTEGER NOT NULL,
                  created_ms INTEGER NOT NULL,updated_ms INTEGER NOT NULL,
                  PRIMARY KEY(owner_key,space_key,task_key))''')
                self._db.execute('''CREATE TABLE IF NOT EXISTS daily_operations(
                  owner_key TEXT NOT NULL,space_key TEXT NOT NULL,operation_key TEXT NOT NULL,
                  request_json TEXT NOT NULL,request_sha256 TEXT NOT NULL,
                  result_json TEXT NOT NULL,at_ms INTEGER NOT NULL,
                  PRIMARY KEY(owner_key,space_key,operation_key))''')
        except BaseException:self.close();raise

    def _scope(self,owner_only=True):return super()._scope(True)

    def _task(self,scope,key):
        row=self._db.execute('SELECT task_key AS task_id,title,status,due_ms,revision,created_ms,updated_ms FROM daily_tasks WHERE owner_key=? AND space_key=? AND task_key=?',(*scope.key(),key)).fetchone()
        return dict(row) if row is not None else None

    def _receipt(self,scope,key):
        row=self._db.execute('SELECT * FROM daily_operations WHERE owner_key=? AND space_key=? AND operation_key=?',(*scope.key(),key)).fetchone()
        if row is None:return None
        value={'operation_id':row['operation_key'],'request':_parse(row['request_json'].encode()),
               'request_sha256':row['request_sha256'],'result':_parse(row['result_json'].encode()),'at_ms':row['at_ms']}
        _operation(value);return value

    def receipt(self,operation_id:str)->dict|None:
        return self._receipt(self._scope(),_id(operation_id))

    def _mutate(self,kind,key,fields,expected_revision,operation_id):
        scope=self._scope();_id(key);_id(operation_id);_integer(expected_revision)
        request={'kind':kind,'item_id':key,'fields':fields,'expected_revision':expected_revision}
        _request(request);request_hash=_digest(request)
        with self._transaction():
            old=self._receipt(scope,operation_id)
            if old is not None:
                if old['request_sha256']!=request_hash or old['request']!=request:
                    raise ValueError('OPERATION_CONFLICT')
                return old['result']
            count=self._db.execute('SELECT COUNT(*) FROM daily_operations WHERE owner_key=? AND space_key=?',scope.key()).fetchone()[0]
            if count>=MAX_OPERATIONS:raise ValueError('OPERATION_LIMIT')
            row=self._task(scope,key) if kind=='task' else self._note_row(scope,key)
            revision=row['revision'] if row is not None else 0
            if revision!=expected_revision:raise ValueError('STALE_REVISION')
            new_revision=_integer(revision+1,minimum=1);now=self._now()
            if row is None:
                table='daily_tasks' if kind=='task' else 'companion_notes'
                # Table choice is a fixed local enum, never supplied SQL.
                count=self._db.execute('SELECT COUNT(*) FROM '+table+' WHERE owner_key=? AND space_key=?',scope.key()).fetchone()[0]
                if count>=MAX_RECORDS:raise ValueError('RECORD_LIMIT')
            if kind=='task':
                created=row['created_ms'] if row is not None else now
                if row is not None and now<row['updated_ms']:raise ValueError('CLOCK_REGRESSION')
                self._db.execute('''INSERT INTO daily_tasks VALUES(?,?,?,?,?,?,?,?,?)
                  ON CONFLICT(owner_key,space_key,task_key) DO UPDATE SET title=excluded.title,
                  status=excluded.status,due_ms=excluded.due_ms,revision=excluded.revision,updated_ms=excluded.updated_ms''',
                  (*scope.key(),key,fields['title'],fields['status'],fields['due_ms'],new_revision,created,now))
                result=self._task(scope,key)
            else:
                self._db.execute('''INSERT INTO companion_notes VALUES(?,?,?,?,?,'active')
                  ON CONFLICT(owner_key,space_key,note_key) DO UPDATE SET text=excluded.text,
                  revision=excluded.revision,state='active' ''',(*scope.key(),key,fields['text'],new_revision))
                result=self._note_payload(self._note_row(scope,key))
            self._db.execute('INSERT INTO daily_operations VALUES(?,?,?,?,?,?,?)',
                (*scope.key(),operation_id,canonical(request).decode(),request_hash,canonical(result).decode(),now))
            return result

    def put_task(self,*,task_id:str,title:str,status:str='pending',due_ms:int|None=None,
                 expected_revision:int=0,operation_id:str)->dict:
        return self._mutate('task',task_id,_task_fields(title,status,due_ms),expected_revision,operation_id)

    def put_note(self,note_id:str,text:str,*,expected_revision:int=0,operation_id:str)->dict:
        return self._mutate('note',note_id,{'text':_clean_text(text)},expected_revision,operation_id)

    def _snapshot(self,scope):
        tasks=[dict(row) for row in self._db.execute('SELECT task_key AS task_id,title,status,due_ms,revision,created_ms,updated_ms FROM daily_tasks WHERE owner_key=? AND space_key=? ORDER BY task_key LIMIT ?',(*scope.key(),MAX_RECORDS+1))]
        if len(tasks)>MAX_RECORDS:raise ValueError('RECORD_LIMIT')
        for row in tasks:_task_record(row)
        return {'protocol':FORMAT,'scope_key':_digest([*scope.key(),self._store_key]),
                'tasks':tasks,'notes':self._notes(scope),'local_only':True,
                'native_installed':False,'provider_connected':False}

    def snapshot(self)->dict:
        scope=self._scope()
        with self._transaction():return self._snapshot(scope)

    def export_archive(self)->bytes:
        scope=self._scope()
        with self._transaction():
            payload=_collect(self._db,scope)
            raw=canonical({'format':FORMAT,'payload':payload,'sha256':_digest(payload)})
            if len(raw)>MAX_ARCHIVE_BYTES:raise ValueError('ARCHIVE_SIZE')
            return raw


def _new_target(destination:str|Path)->Path:
    path=validated_database_path(destination,error='RESTORE_PATH_UNSAFE',absolute=True)
    for part in (path,*path.parents):
        if callable(getattr(part,'is_junction',None)) and part.is_junction():raise ValueError('RESTORE_PATH_UNSAFE')
    if path.exists():raise ValueError('RESTORE_EXISTS')
    for suffix in ('-wal','-shm','-journal'):
        sidecar=Path(str(path)+suffix)
        if sidecar.exists() or sidecar.is_symlink():raise ValueError('RESTORE_SIDECAR_EXISTS')
    return path


def restore_desk(destination:str|Path,archive:bytes,*,authority:Callable[[],CompanionScope])->dict:
    """Validate fully, build a closed staging DB, then publish without replacement.

    Requires an owner-controlled same-filesystem parent. A crash after hard-link
    publication but before temporary-name removal may leave a second link; normal
    store admission then refuses it for explicit recovery rather than replaying.
    """
    scope=_scope_from(authority);data=read_archive(archive)
    if data['scope']!={'owner_id':scope.owner_id,'space_id':scope.space_id}:
        raise ValueError('RESTORE_SCOPE_MISMATCH')
    target=_new_target(destination)
    fd,name=tempfile.mkstemp(prefix='.'+target.name+'.restore-',suffix='.sqlite',dir=target.parent)
    os.close(fd);staging=Path(name);published=False
    try:
        with DailyDesk(staging,authority=lambda:scope) as store:
            with store._transaction():
                for row in data['tasks']:
                    store._db.execute('INSERT INTO daily_tasks VALUES(?,?,?,?,?,?,?,?,?)',
                        (*scope.key(),row['task_id'],row['title'],row['status'],row['due_ms'],row['revision'],row['created_ms'],row['updated_ms']))
                for row in data['notes']:
                    store._db.execute('INSERT INTO companion_notes VALUES(?,?,?,?,?,?)',
                        (*scope.key(),row['note_id'],row['text'],row['revision'],row['state']))
                for row in data['operations']:
                    store._db.execute('INSERT INTO daily_operations VALUES(?,?,?,?,?,?,?)',
                        (*scope.key(),row['operation_id'],canonical(row['request']).decode(),row['request_sha256'],canonical(row['result']).decode(),row['at_ms']))
            if read_archive(store.export_archive())!=data:raise ValueError('RESTORE_READBACK_MISMATCH')
        with staging.open('r+b') as f:os.fsync(f.fileno())
        _new_target(target)
        try:os.link(staging,target)
        except FileExistsError as exc:raise ValueError('RESTORE_EXISTS') from exc
        published=True
        staging.unlink()
        with DailyDesk(target,authority=lambda:scope) as reopened:
            if read_archive(reopened.export_archive())!=data:raise ValueError('RESTORE_READBACK_MISMATCH')
        return {'status':'RESTORED_LOCAL_DESK','database':str(target),
                'tasks':len(data['tasks']),'notes':sum(x['state']=='active' for x in data['notes']),
                'payload_sha256':_digest(data),'native_installed':False,'original_store_changed':False}
    except (OSError,sqlite3.Error) as exc:
        if published:raise ValueError('RESTORE_PUBLISHED_READBACK_UNCONFIRMED') from exc
        raise ValueError('RESTORE_FAILED_NO_PUBLISHED_STORE') from exc
    finally:
        # Clean only the owned staging name; never delete a published destination.
        if staging.exists():staging.unlink()

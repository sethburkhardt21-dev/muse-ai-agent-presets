"""Loopback-only development HTTP/UI adapter; never deploy this as a public service.

No native SDK is bundled. The caller binds an owner scope and an ephemeral
session token outside request data. Browser routes cannot claim provider work
or submit callbacks. Use a production host's original authentication/transport
when implementing the separately unqualified native Space integration.
"""
from __future__ import annotations
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from typing import Callable
import hmac,json,re,sqlite3
from .personal_companion import PersonalCompanion,CompanionScope
from .space_companion import SpaceCompanion
from .daily_desk import DailyDesk,restore_desk,inspect_desk,canonical,MAX_ARCHIVE_BYTES
from .database_paths import validated_database_path

class RequestRefused(ValueError):
 def __init__(self,status:int,code:str):self.status=status;self.code=code;super().__init__(code)

def _pairs(pairs):
 out={}
 for k,v in pairs:
  if k in out:raise ValueError('DUPLICATE_JSON_KEY')
  out[k]=v
 return out

def _bad_constant(_):raise ValueError('NONFINITE_JSON')

def make_server(database:str|Path,*,token:str,authority:Callable[[],CompanionScope],port:int=0,
                daily_desk:bool=False,restore_directory:str|Path|None=None):
 """Bind only 127.0.0.1; caller explicitly serves/closes the returned server.

 Token is an OS-user-controlled local demo session, not Muse identity proof.
 Keep database in owner-protected storage; SQLite is not encrypted.
 """
 if type(token) is not str or not re.fullmatch('[A-Za-z0-9_-]{32,128}',token):raise ValueError('INVALID_SESSION_TOKEN')
 if not callable(authority):raise ValueError('AUTHORITY_UNBOUND')
 if type(port) is not int or not 0<=port<=65535:raise ValueError('INVALID_PORT')
 if type(daily_desk) is not bool:raise ValueError('INVALID_DESK_MODE')
 if restore_directory is not None:
  if not daily_desk:raise ValueError('RESTORE_REQUIRES_DESK_MODE')
  restore_directory=Path(restore_directory)
  if not restore_directory.is_dir():raise ValueError('RESTORE_DIRECTORY_REQUIRED')
  # Storage root is bound by the local launcher, never selected by browser JSON.
  validated_database_path(restore_directory/'.validation-only',error='RESTORE_PATH_UNSAFE',absolute=True)
  if any(callable(getattr(p,'is_junction',None)) and p.is_junction() for p in (restore_directory,*restore_directory.parents)):
   raise ValueError('RESTORE_PATH_UNSAFE')
 database=Path(database)
 # Validate storage using the accepted services before opening a listener.
 with PersonalCompanion(database,authority=authority) as store:store.preferences()
 with SpaceCompanion(database,authority=authority) as store:store.snapshot()
 if daily_desk:
  with DailyDesk(database,authority=authority) as store:store.snapshot()
 assets=Path(__file__).parent/('desk_assets' if daily_desk else 'space_assets')
 pages={}
 for path,name,mime in [('/','index.html','text/html; charset=utf-8'),('/app.js','app.js','text/javascript; charset=utf-8'),('/app.css','app.css','text/css; charset=utf-8')]:
  p=assets/name
  if p.is_symlink() or not p.is_file() or p.stat().st_size>131072:raise ValueError('UI_ASSET_INVALID')
  pages[path]=(mime,p.read_bytes())
 class Handler(BaseHTTPRequestHandler):
  server_version='LocalSpace/1';sys_version='';protocol_version='HTTP/1.0'
  def setup(self):
   super().setup();self.connection.settimeout(3)
  def log_message(self,*_):pass # Do not log paths, prompts, credentials or responses.
  def _reply(self,status,data,mime='application/json; charset=utf-8'):
   raw=data if isinstance(data,bytes) else json.dumps(data,ensure_ascii=False,allow_nan=False).encode('utf-8')
   self.send_response(status);self.send_header('Content-Type',mime);self.send_header('Content-Length',str(len(raw)))
   self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff')
   self.send_header('Referrer-Policy','no-referrer');self.send_header('X-Frame-Options','DENY')
   self.send_header('Content-Security-Policy',"default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'")
   self.end_headers()
   try:self.wfile.write(raw)
   except (BrokenPipeError,ConnectionResetError):pass
  def _headers(self,api:bool):
   expected='127.0.0.1:'+str(self.server.server_address[1]);origin='http://'+expected
   if self.headers.get_all('Host',[])!=[expected]:raise RequestRefused(403,'HOST_DENIED')
   origins=self.headers.get_all('Origin',[])
   if origins and origins!=[origin]:raise RequestRefused(403,'ORIGIN_DENIED')
   if self.headers.get('Sec-Fetch-Site','')=='cross-site':raise RequestRefused(403,'ORIGIN_DENIED')
   if api:
    values=self.headers.get_all('Authorization',[])
    if len(values)!=1 or not hmac.compare_digest(values[0],'Bearer '+token):raise RequestRefused(401,'SESSION_REQUIRED')
  def _body(self,limit=32768):
   if self.headers.get_all('Transfer-Encoding',[]):raise RequestRefused(400,'TRANSFER_ENCODING_REFUSED')
   lengths=self.headers.get_all('Content-Length',[])
   if len(lengths)!=1 or not re.fullmatch('[0-9]{1,8}',lengths[0]):raise RequestRefused(400,'CONTENT_LENGTH_REQUIRED')
   n=int(lengths[0])
   if n>limit:raise RequestRefused(413,'BODY_TOO_LARGE')
   if self.headers.get_all('Content-Type',[])!=['application/json']:raise RequestRefused(415,'JSON_REQUIRED')
   raw=self.rfile.read(n)
   if len(raw)!=n:raise RequestRefused(400,'BODY_INCOMPLETE')
   data=json.loads(raw.decode('utf-8'),object_pairs_hook=_pairs,parse_constant=_bad_constant)
   if type(data) is not dict:raise ValueError('JSON_OBJECT_REQUIRED')
   return data
  def _desk(self,method):
   routes={'/api/desk/state':set(),'/api/desk/export':set(),
           '/api/desk/task':{'task_id','title','status','due_ms','expected_revision','operation_id'},
           '/api/desk/note':{'note_id','text','expected_revision','operation_id'},
           '/api/desk/receipt':{'operation_id'},'/api/desk/restore':{'name','archive'},'/api/desk/restore-status':{'name'}}
   readonly=self.path in ('/api/desk/state','/api/desk/export')
   if self.path not in routes or (method=='GET')!=readonly:raise RequestRefused(404,'ROUTE_NOT_FOUND')
   self._headers(True)
   data={} if readonly else self._body(MAX_ARCHIVE_BYTES+4096 if self.path=='/api/desk/restore' else 32768)
   if set(data)!=routes[self.path]:raise ValueError('REQUEST_FIELDS')
   with DailyDesk(database,authority=authority) as desk:
    if self.path=='/api/desk/state':result=desk.snapshot()
    elif self.path=='/api/desk/export':result=desk.export_archive()
    elif self.path=='/api/desk/task':result=desk.put_task(**data)
    elif self.path=='/api/desk/note':result=desk.put_note(**data)
    elif self.path=='/api/desk/receipt':result={'receipt':desk.receipt(data['operation_id'])}
    else:
     desk.snapshot() # Require the original injected owner scope before file effects.
     if restore_directory is None:raise RequestRefused(403,'RESTORE_NOT_CONFIGURED')
     name=data['name']
     if type(name) is not str or not re.fullmatch('[A-Za-z][A-Za-z0-9_-]{0,63}',name):raise ValueError('RESTORE_NAME_INVALID')
     if name.lower() in {'con','prn','aux','nul',*('com'+str(i) for i in range(10)),*('lpt'+str(i) for i in range(10))}:raise ValueError('RESTORE_NAME_INVALID')
     if self.path=='/api/desk/restore-status':
      result=inspect_desk(restore_directory/(name+'.sqlite'),authority=authority)
     else:
      raw=data['archive'].encode('utf-8') if type(data['archive']) is str else canonical(data['archive'])
      result=restore_desk(restore_directory/(name+'.sqlite'),raw,authority=authority)
     result['name']=name
   return self._reply(200,result)

  def _handle(self,method):
   try:
    self._headers(False)
    if method=='GET' and self.path in pages:
     mime,data=pages[self.path];return self._reply(200,data,mime)
    if daily_desk:return self._desk(method)
    allowed={'/api/state':set(),'/api/config':{'enabled','expected_revision'},'/api/note':{'note_id','text','expected_revision'},'/api/request':{'request_id','prompt'},'/api/cancel':{'request_id','expected_revision'}}
    if self.path not in allowed or (method=='GET')!=(self.path=='/api/state'):raise RequestRefused(404,'ROUTE_NOT_FOUND')
    self._headers(True)
    data={} if method=='GET' else self._body()
    if set(data)!=allowed[self.path]:raise ValueError('REQUEST_FIELDS')
    with SpaceCompanion(database,authority=authority) as jobs,PersonalCompanion(database,authority=authority) as notes:
     if self.path=='/api/state':result={'adapter':jobs.snapshot(),'notes':notes.notes(),'provider_connected':False,'native_installed':False}
     elif self.path=='/api/config':result=jobs.configure(**data)
     elif self.path=='/api/note':
      jobs.snapshot() # Enforce owner-present access for all browser mutations.
      result=notes.put_note(**data)
     elif self.path=='/api/request':result=jobs.request(**data)
     else:result=jobs.cancel(**data)
    self._reply(200,result)
   except RequestRefused as exc:self._reply(exc.status,{'error':exc.code})
   except (ValueError,TypeError,UnicodeError,RecursionError) as exc:
    code=str(exc) if str(exc) in {'AUTHORITY_UNVERIFIED','OWNER_APPROVAL_REQUIRED','STALE_REVISION','REQUEST_CONFLICT','ADAPTER_DISABLED','REQUEST_TERMINAL','REQUEST_NOT_FOUND','OPERATION_CONFLICT','RESTORE_EXISTS','RESTORE_SCOPE_MISMATCH','ARCHIVE_DIGEST_MISMATCH','RECORD_LIMIT','OPERATION_LIMIT','RESTORE_PUBLISHED_READBACK_UNCONFIRMED','RESTORE_READBACK_UNCONFIRMED','LOCAL_TRANSACTION_UNCONFIRMED_REOPEN_RECEIPT','TRANSACTION_UNCONFIRMED_REOPEN_ORIGINAL_STATE'} else 'INVALID_REQUEST'
    status=503 if 'UNCONFIRMED' in code else 403 if code in {'AUTHORITY_UNVERIFIED','OWNER_APPROVAL_REQUIRED'} else 409 if code in {'STALE_REVISION','REQUEST_CONFLICT','ADAPTER_DISABLED','REQUEST_TERMINAL','OPERATION_CONFLICT','RESTORE_EXISTS'} else 400
    self._reply(status,{'error':code})
   except (TimeoutError,OSError,sqlite3.Error):self._reply(503,{'error':'LOCAL_STATE_UNCONFIRMED_REOPEN'})
  def do_GET(self):self._handle('GET')
  def do_POST(self):self._handle('POST')
 return ThreadingHTTPServer(('127.0.0.1',port),Handler)

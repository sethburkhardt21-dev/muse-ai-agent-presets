"""Exercise Daily Desk through the original loopback server and real sockets."""
from pathlib import Path
import http.client,json,tempfile,threading,unittest
from muse_presets.personal_companion import CompanionScope
from muse_presets.daily_desk import DailyDesk
from muse_presets.space_server import make_server

class DeskHTTP(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name).resolve();self.db=self.root/'desk.sqlite';self.restores=self.root/'restores';self.restores.mkdir()
  self.scope=CompanionScope('owner','desk','owner',True);self.token='localtestsessiontokenonly'+'a'*20
  self.server=make_server(self.db,token=self.token,authority=lambda:self.scope,port=0,daily_desk=True,restore_directory=self.restores)
  self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
 def tearDown(self):self.server.shutdown();self.thread.join(5);self.server.server_close();self.tmp.cleanup()
 def call(self,path,body=None,*,auth=True,extra=None,raw=None):
  c=http.client.HTTPConnection('127.0.0.1',self.server.server_address[1],timeout=5)
  headers={'Authorization':'Bearer '+self.token} if auth else {}
  if extra:headers.update(extra)
  if body is not None or raw is not None:headers['Content-Type']='application/json'
  data=raw if raw is not None else json.dumps(body).encode() if body is not None else None
  c.request('POST' if data is not None else 'GET',path,body=data,headers=headers);r=c.getresponse();b=r.read();status=r.status;hs=dict(r.getheaders());c.close()
  if 'application/json' in hs.get('Content-Type',''):return status,json.loads(b),hs
  return status,b.decode(),hs
 def create(self):return self.call('/api/desk/task',{'task_id':'t1','title':'A useful task','status':'pending','due_ms':None,'expected_revision':0,'operation_id':'op1'})
 def test_workspace_assets_are_daily_desk_and_have_safe_headers(self):
  status,body,headers=self.call('/',auth=False);self.assertEqual(status,200);self.assertIn('Daily Desk',body)
  for marker in ['task-form','note-form','backup-form','token','status']:self.assertIn(marker,body)
  self.assertIn("default-src 'none'",headers['Content-Security-Policy']);self.assertEqual(headers['X-Frame-Options'],'DENY')
  self.assertNotIn(self.token,body)
 def test_authenticated_create_edit_refuse_stale_and_reopen(self):
  self.assertEqual(self.create()[0],200)
  code,result,_=self.call('/api/desk/task',{'task_id':'t1','title':'Edited','status':'done','due_ms':None,'expected_revision':1,'operation_id':'op2'})
  self.assertEqual(code,200);self.assertEqual(result['revision'],2)
  code,error,_=self.call('/api/desk/task',{'task_id':'t1','title':'Stale','status':'pending','due_ms':None,'expected_revision':1,'operation_id':'op3'})
  self.assertEqual(code,409);self.assertEqual(error['error'],'STALE_REVISION')
  with DailyDesk(self.db,authority=lambda:self.scope) as reopened:self.assertEqual(reopened.snapshot()['tasks'][0]['title'],'Edited')
 def test_exact_http_replay_and_receipt_readback(self):
  a=self.create();b=self.create();self.assertEqual(a[1],b[1])
  code,r,_=self.call('/api/desk/receipt',{'operation_id':'op1'});self.assertEqual(code,200);self.assertEqual(r['receipt']['result'],a[1])
  self.assertEqual(self.call('/api/desk/state')[1]['tasks'][0]['revision'],1)
 def test_no_or_wrong_token_cannot_mutate(self):
  args={'task_id':'t1','title':'test','status':'pending','due_ms':None,'expected_revision':0,'operation_id':'op1'}
  for auth,extra in [(False,None),(False,{'Authorization':'Bearer '+('b'*40)})]:
   self.assertEqual(self.call('/api/desk/task',args,auth=auth,extra=extra)[0],401)
  self.assertEqual(self.call('/api/desk/state')[1]['tasks'],[])
 def test_host_and_origin_denials_preserved(self):
  self.assertEqual(self.call('/api/desk/state',extra={'Origin':'https://unrelated.invalid'})[0],403)
  self.assertEqual(self.call('/api/desk/state',extra={'Host':'unrelated.invalid'})[0],403)
 def test_client_cannot_supply_owner_or_provider_authority(self):
  body={'note_id':'n','text':'test','expected_revision':0,'operation_id':'o','owner_id':'other'}
  self.assertEqual(self.call('/api/desk/note',body)[0],400)
  for path in ['/api/config','/api/request','/api/claim','/api/callback']:
   self.assertEqual(self.call(path,{} )[0],404)
 def test_actual_injected_owner_absence_denied(self):
  self.scope=CompanionScope('owner','desk','owner',False)
  self.assertEqual(self.call('/api/desk/state')[0],403)
  self.assertEqual(self.create()[0],403)
 def test_note_script_text_is_data_not_executed_html(self):
  text='<img src=x onerror=alert(1)>'
  status,r,_=self.call('/api/desk/note',{'note_id':'n','text':text,'expected_revision':0,'operation_id':'note-op'})
  self.assertEqual(status,200);self.assertEqual(r['text'],text)
  self.assertNotIn(text,self.call('/',auth=False)[1])
 def test_restore_creates_only_in_server_approved_root(self):
  self.create();raw=self.call('/api/desk/export')[1]
  status,r,_=self.call('/api/desk/restore',{'name':'restored','archive':raw})
  self.assertEqual(status,200);self.assertTrue((self.restores/'restored.sqlite').is_file())
  self.assertFalse(r['original_store_changed']);self.assertFalse(r['native_installed'])
  self.assertEqual(self.call('/api/desk/restore',{'name':'restored','archive':raw})[0],409)
  self.assertEqual(len(self.call('/api/desk/state')[1]['tasks']),1)
 def test_restore_bad_digest_or_path_refuses_without_files(self):
  raw=self.call('/api/desk/export')[1]
  self.assertEqual(self.call('/api/desk/restore',{'name':'../escape','archive':raw})[0],400)
  raw['sha256']='0'*64;self.assertEqual(self.call('/api/desk/restore',{'name':'bad','archive':raw})[0],400)
  self.assertEqual(list(self.restores.iterdir()),[])
 def test_duplicate_json_and_unknown_fields_refused(self):
  for raw in [b'{"name":"x","name":"y"}',b'{"x":NaN}',b'[]']:
   self.assertEqual(self.call('/api/desk/receipt',raw=raw)[0],400)
 def test_restore_readback_is_not_a_second_restore(self):
  self.create();archive=json.dumps(self.call('/api/desk/export')[1])
  self.assertEqual(self.call('/api/desk/restore',{'name':'copy','archive':archive})[0],200)
  first=(self.restores/'copy.sqlite').read_bytes()
  status,r,_=self.call('/api/desk/restore-status',{'name':'copy'})
  self.assertEqual(status,200);self.assertEqual(r['tasks'],1);self.assertEqual((self.restores/'copy.sqlite').read_bytes(),first)
  self.assertEqual(self.call('/api/desk/restore-status',{'name':'missing'})[1]['status'],'RESTORE_NOT_FOUND')
 def test_duplicate_keys_in_uploaded_raw_archive_are_refused(self):
  raw='{"format":"daily-desk/1","format":"daily-desk/1"}'
  self.assertEqual(self.call('/api/desk/restore',{'name':'bad','archive':raw})[0],400)
  self.assertEqual(list(self.restores.iterdir()),[])
 def test_existing_default_server_route_is_not_replaced(self):
  other=make_server(self.root/'old.sqlite',token=self.token,authority=lambda:self.scope)
  thread=threading.Thread(target=other.serve_forever,daemon=True);thread.start()
  try:
   c=http.client.HTTPConnection('127.0.0.1',other.server_address[1]);c.request('GET','/',headers={});r=c.getresponse();text=r.read().decode();self.assertEqual(r.status,200);self.assertIn('Local companion',text);self.assertNotIn('task-form',text);c.close()
  finally:other.shutdown();thread.join(5);other.server_close()

if __name__=='__main__':unittest.main(verbosity=2)

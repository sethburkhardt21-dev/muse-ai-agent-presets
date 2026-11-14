"""Optional fullstack local Space starter. No server starts without --serve."""
from __future__ import annotations
from pathlib import Path
import argparse,json,secrets,sys,tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from muse_presets.personal_companion import PersonalCompanion,CompanionScope
from muse_presets.space_companion import SpaceCompanion
from muse_presets.space_server import make_server

def demo():
 scope=CompanionScope('demo-owner','demo-space','demo-owner',True);clock=[1000]
 with tempfile.TemporaryDirectory() as directory:
  path=Path(directory)/'example.db';authority=lambda:scope
  with PersonalCompanion(path,authority=authority) as notes:
   notes.put_note('plan','A disposable local planning note')
  with SpaceCompanion(path,authority=authority,clock_ms=lambda:clock[0],callback_verifier=lambda _:True) as store:
   assert not store.snapshot()['enabled'];store.configure(enabled=True,expected_revision=0)
   store.request('first','Review the example note');job=store.claim('first',expected_revision=1,operation_id='demo-op')
   event=dict(request_id='first',operation_id='demo-op',request_sha256=job['request_sha256'],event_id='demo-event',status='SUCCEEDED',result='Fixture result: local notebook reviewed.')
   assert store.callback(event)['state']=='completed';assert store.callback(event)['revision']==3
   store.request('cancelled','Do not perform');pending=store.claim('cancelled',expected_revision=1,operation_id='cancel-op')
   store.cancel('cancelled',expected_revision=2)
   try:store.callback(dict(event,request_id='cancelled',operation_id='cancel-op',request_sha256=pending['request_sha256'],event_id='cancel-event'))
   except ValueError as exc:assert str(exc)=='REQUEST_NOT_DISPATCHING'
   else:raise AssertionError('CANCEL_RESURRECTED')
   store.request('interrupted','Original outcome must be inspected');store.claim('interrupted',expected_revision=1,operation_id='unknown-op',timeout_ms=1)
   clock[0]+=2;assert store.expire()==1
  with SpaceCompanion(path,authority=authority) as reopened,PersonalCompanion(path,authority=authority) as notes:
   assert reopened.get('interrupted')['state']=='unknown';assert notes.note('plan')['text']=='A disposable local planning note'
  return {'status':'OFFLINE_SPACE_STARTER_DEMO_PASS','scope':'DISPOSABLE_LOCAL_SQLITE_ONLY','default_off_verified':True,'notebook_reopened':True,'request_callback_database_loop':True,'duplicate_callback_no_new_effect':True,'late_callback_cannot_undo_cancel':True,'unknown_survives_restart':True,'callback_authentication':'SYNTHETIC_TEST_VERIFIER_ONLY','provider_jobs_created':0,'native_muse_installed':False,'server_started':False}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--serve',action='store_true');p.add_argument('--database',type=Path);p.add_argument('--port',type=int,default=0);args=p.parse_args()
 if not args.serve:print(json.dumps(demo(),indent=2,sort_keys=True));return
 if args.database is None:p.error('--serve requires --database with an absolute path in an owner-protected directory')
 # The local session is a development fixture, not an authenticated Muse owner.
 scope=CompanionScope('local-owner','local-space','local-owner',True);token=secrets.token_urlsafe(36)
 server=make_server(args.database,token=token,authority=lambda:scope,port=args.port)
 print('LOCAL DEVELOPMENT ONLY / NO NATIVE PROVIDER',flush=True)
 print('Open http://127.0.0.1:'+str(server.server_address[1]),flush=True)
 print('Session token (keep local): '+token,flush=True)
 try:server.serve_forever()
 except KeyboardInterrupt:pass
 finally:server.server_close()
if __name__=='__main__':main()

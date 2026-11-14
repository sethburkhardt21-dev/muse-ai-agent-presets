"""Daily Desk persistence, atomic mutations and create-only archive recovery."""
from __future__ import annotations
import concurrent.futures,copy,hashlib,json,os,sqlite3,subprocess,sys,tempfile,threading,unittest
from pathlib import Path
from muse_presets.personal_companion import PersonalCompanion,CompanionScope
from muse_presets.space_companion import SpaceCompanion
from muse_presets.daily_desk import DailyDesk,restore_desk,read_archive,canonical

SCOPE=CompanionScope('owner','desk','owner',True)

class DeskCase(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name).resolve();self.path=self.root/'desk.sqlite';self.scope=SCOPE;self.clock=1000
  self.authority=lambda:self.scope
  self.store=DailyDesk(self.path,authority=self.authority,clock_ms=lambda:self.clock)
 def tearDown(self):self.store.close();self.tmp.cleanup()
 def task(self,key='one',title='First task',rev=0,op='op-one',status='pending'):
  return self.store.put_task(task_id=key,title=title,status=status,due_ms=None,expected_revision=rev,operation_id=op)
 def note(self,key='note',text='First note',rev=0,op='op-note'):
  return self.store.put_note(note_id=key,text=text,expected_revision=rev,operation_id=op)
 def test_exact_vertical_slice_preserves_ids_content_revisions_on_restore(self):
  for n in range(3):self.task('task'+str(n),'Task '+str(n),op='create-task'+str(n))
  for n in range(2):self.note('note'+str(n),'Note '+str(n),op='create-note'+str(n))
  self.clock=2000;self.task('task1','Edited task',rev=1,op='edit-task1',status='done');self.note('note0','Edited note',rev=1,op='edit-note0')
  before=self.store.snapshot();self.assertEqual((len(before['tasks']),len(before['notes'])),(3,2))
  self.store.close();self.store=DailyDesk(self.path,authority=self.authority)
  self.assertEqual(self.store.snapshot(),before)
  raw=self.store.export_archive();self.assertEqual(raw,self.store.export_archive())
  restored=self.root/'restored.sqlite';receipt=restore_desk(restored,raw,authority=self.authority)
  self.assertFalse(receipt['native_installed']);self.assertEqual(receipt['tasks'],3);self.assertEqual(receipt['notes'],2)
  with DailyDesk(restored,authority=self.authority) as copy_store:
   self.assertEqual({k:v for k,v in copy_store.snapshot().items() if k!='scope_key'},{k:v for k,v in before.items() if k!='scope_key'})
   self.assertNotEqual(copy_store.snapshot()['scope_key'],before['scope_key'])
   self.assertEqual(copy_store.export_archive(),raw)
  self.assertEqual(self.store.export_archive(),raw)
 def test_note_table_is_the_existing_personal_store(self):
  self.note()
  with PersonalCompanion(self.path,authority=self.authority) as original:
   self.assertEqual(original.note('note'),self.store.note('note'))
   original.put_note('external','From original service')
  self.assertEqual(len(self.store.snapshot()['notes']),2)
 def test_original_preferences_reminders_and_requests_are_preserved_not_exported(self):
  with PersonalCompanion(self.path,authority=self.authority) as p:
   p.configure(expected_revision=0,changes={'tone':'gentle'});p.add_reminder(reminder_id='r',title='local',due_ms=0)
  with SpaceCompanion(self.path,authority=self.authority) as jobs:
   jobs.configure(enabled=True,expected_revision=0);jobs.request('queued','Keep original request')
  self.task();archive=read_archive(self.store.export_archive());self.assertEqual(set(archive),{'scope','tasks','notes','operations'})
  with PersonalCompanion(self.path,authority=self.authority) as p:self.assertEqual(p.preferences()['tone'],'gentle');self.assertEqual(p.reminder('r')['state'],'pending')
  with SpaceCompanion(self.path,authority=self.authority) as jobs:self.assertEqual(jobs.get('queued')['state'],'queued')
 def test_stale_task_and_note_refuse_without_changing_any_bytes_of_logical_state(self):
  self.task();self.note();before=self.store.export_archive()
  for fn in [lambda:self.task(rev=0,op='stale-task'),lambda:self.note(rev=0,op='stale-note')]:
   with self.assertRaisesRegex(ValueError,'STALE_REVISION'):fn()
   self.assertEqual(self.store.export_archive(),before)
 def test_identical_replay_returns_original_receipt_even_after_later_edit(self):
  first=self.task();self.task(title='Later title',rev=1,op='later')
  self.assertEqual(self.task(),first);self.assertEqual(self.store.receipt('op-one')['result'],first)
  self.assertEqual(self.store.snapshot()['tasks'][0]['revision'],2)
  self.assertEqual(len(read_archive(self.store.export_archive())['operations']),2)
 def test_replay_works_after_process_reopen(self):
  first=self.note();self.store.close();self.store=DailyDesk(self.path,authority=self.authority)
  self.assertEqual(self.note(),first);self.assertEqual(len(self.store.notes()),1)
 def test_operation_id_reuse_with_changed_kind_payload_or_revision_refuses(self):
  self.task();before=self.store.export_archive()
  for fn in [lambda:self.task(title='changed'),lambda:self.task(rev=1),lambda:self.note(op='op-one'),lambda:self.task(key='other')]:
   with self.assertRaisesRegex(ValueError,'OPERATION_CONFLICT'):fn()
  self.assertEqual(self.store.export_archive(),before)
 def test_receipt_missing_is_explicit_not_permission_to_retry_blindly(self):self.assertIsNone(self.store.receipt('unknown'))
 def test_owner_absent_or_wrong_actor_refuses_every_operation(self):
  self.task()
  for bad in [CompanionScope('owner','desk','owner',False),CompanionScope('owner','desk','other',True)]:
   self.scope=bad
   for fn in [self.store.snapshot,self.store.export_archive,lambda:self.task(key='denied',op='bad'),lambda:self.store.receipt('op-one')]:
    with self.assertRaises(ValueError):fn()
 def test_other_owner_and_space_cannot_read_current_records(self):
  self.task();self.note()
  for scope in [CompanionScope('other','desk','other',True),CompanionScope('owner','other','owner',True)]:
   self.scope=scope;self.assertEqual(self.store.snapshot()['tasks'],[]);self.assertEqual(self.store.snapshot()['notes'],[]);self.assertIsNone(self.store.receipt('op-one'))
 def test_atomic_rollback_when_receipt_insert_fails(self):
  self.store._db.execute("CREATE TRIGGER fail_receipt BEFORE INSERT ON daily_operations BEGIN SELECT RAISE(ABORT,'fixture'); END")
  with self.assertRaisesRegex(ValueError,'UNCONFIRMED'):self.task()
  self.assertEqual(self.store.snapshot()['tasks'],[]);self.assertIsNone(self.store.receipt('op-one'))
 def test_two_concurrent_writers_only_one_revision_wins(self):
  self.task();barrier=threading.Barrier(2)
  def edit(n):
   with DailyDesk(self.path,authority=lambda:SCOPE) as d:
    barrier.wait()
    try:return d.put_task(task_id='one',title='Edit'+str(n),status='pending',due_ms=None,expected_revision=1,operation_id='edit'+str(n))
    except ValueError as e:return str(e)
  with concurrent.futures.ThreadPoolExecutor(2) as pool:results=list(pool.map(edit,[1,2]))
  self.assertEqual(sum(type(x) is dict for x in results),1);self.assertIn('STALE_REVISION',results);self.assertEqual(self.store.snapshot()['tasks'][0]['revision'],2)
 def test_concurrent_duplicate_operation_does_not_create_second_revision(self):
  barrier=threading.Barrier(2)
  def create(_):
   with DailyDesk(self.path,authority=lambda:SCOPE) as d:
    barrier.wait();return d.put_note(note_id='same',text='same',expected_revision=0,operation_id='same-op')
  with concurrent.futures.ThreadPoolExecutor(2) as pool:results=list(pool.map(create,[1,2]))
  self.assertEqual(results[0],results[1]);self.assertEqual(results[0]['revision'],1)
 def test_invalid_inputs_are_refused_without_new_records(self):
  inputs=[{'task_id':'../escape'},{'title':''},{'title':'x\x00y'},{'status':'executing'},{'due_ms':True},{'expected_revision':True},{'operation_id':'..'},{'title':'x'*161},{'due_ms':-1}]
  for bad in inputs:
   args=dict(task_id='t',title='test',status='pending',due_ms=None,expected_revision=0,operation_id='op');args.update(bad)
   with self.subTest(bad=bad),self.assertRaises(ValueError):self.store.put_task(**args)
  self.assertEqual(self.store.snapshot()['tasks'],[])
 def test_bad_clock_refused_without_write(self):
  self.clock=True
  with self.assertRaisesRegex(ValueError,'CLOCK_INVALID'):self.task()
  self.clock=1000;self.assertEqual(self.store.snapshot()['tasks'],[])
 def test_future_migration_version_is_refused(self):
  self.store._db.execute('UPDATE daily_schema SET version=99')
  with self.assertRaisesRegex(ValueError,'SCHEMA_VERSION'):DailyDesk(self.path,authority=self.authority)
 def test_archive_is_scoped_and_does_not_grant_authority(self):
  self.task();raw=self.store.export_archive();target=self.root/'other.sqlite'
  for scope in [CompanionScope('other','desk','other',True),CompanionScope('owner','other','owner',True),CompanionScope('owner','desk','owner',False)]:
   with self.assertRaises(ValueError):restore_desk(target,raw,authority=lambda:scope)
   self.assertFalse(target.exists())
 def test_existing_destination_refused_and_preserved(self):
  self.task();raw=self.store.export_archive();target=self.root/'existing.sqlite';target.write_bytes(b'KEEP')
  with self.assertRaisesRegex(ValueError,'RESTORE_EXISTS'):restore_desk(target,raw,authority=self.authority)
  self.assertEqual(target.read_bytes(),b'KEEP')
 def test_corrupt_digest_does_not_create_target(self):
  raw=json.loads(self.store.export_archive());raw['sha256']='0'*64;target=self.root/'bad.sqlite'
  with self.assertRaisesRegex(ValueError,'ARCHIVE_DIGEST'):restore_desk(target,canonical(raw),authority=self.authority)
  self.assertFalse(target.exists())
 def test_duplicate_json_unknown_fields_future_schema_and_nonfinite_refused(self):
  for raw in [b'{"format":"x","format":"y"}',b'{"a":NaN}',b'[]',b'null',b'{']:
   with self.subTest(raw=raw),self.assertRaises(ValueError):read_archive(raw)
  v=json.loads(self.store.export_archive());v['native_installed']=True
  with self.assertRaises(ValueError):read_archive(canonical(v))
  del v['native_installed'];v['format']='daily-desk/99'
  with self.assertRaises(ValueError):read_archive(canonical(v))
 def test_semantically_bad_archive_still_refused_with_recomputed_digest(self):
  self.task();base=json.loads(self.store.export_archive())
  for change in ['duplicate','state','revision','owner','operation','extra']:
   v=copy.deepcopy(base);data=v['payload']
   if change=='duplicate':data['tasks']*=2
   elif change=='state':data['tasks'][0]['status']='dispatched'
   elif change=='revision':data['tasks'][0]['revision']=True
   elif change=='owner':data['scope']['owner_id']='../x'
   elif change=='operation':data['operations'][0]['result']['native_installed']=True
   else:data['claims_provider_identity']=True
   v['sha256']=hashlib.sha256(canonical(data)).hexdigest()
   with self.subTest(change=change),self.assertRaises(ValueError):read_archive(canonical(v))
 def test_path_traversal_and_missing_parent_restores_refused(self):
  raw=self.store.export_archive()
  for p in [self.root/'missing'/'new.sqlite',self.root/'x'/'..'/'new.sqlite',Path('relative.sqlite')]:
   with self.assertRaises(ValueError):restore_desk(p,raw,authority=self.authority)
 def test_restore_sidecar_collision_refused(self):
  target=self.root/'new.sqlite';(self.root/'new.sqlite-wal').write_bytes(b'KEEP')
  with self.assertRaises(ValueError):restore_desk(target,self.store.export_archive(),authority=self.authority)
  self.assertFalse(target.exists())
 def test_symlink_restore_refused_where_available(self):
  original=self.root/'target';original.write_bytes(b'KEEP');link=self.root/'alias.sqlite'
  try:link.symlink_to(original)
  except OSError:self.skipTest('OS symlink creation unavailable')
  with self.assertRaises(ValueError):restore_desk(link,self.store.export_archive(),authority=self.authority)
  self.assertEqual(original.read_bytes(),b'KEEP')
 def test_restore_reopens_from_another_process(self):
  self.task();self.note();target=self.root/'copy.sqlite';restore_desk(target,self.store.export_archive(),authority=self.authority)
  code='from muse_presets.daily_desk import DailyDesk;from muse_presets.personal_companion import CompanionScope;import json,sys\ns=CompanionScope("owner","desk","owner",True)\nwith DailyDesk(sys.argv[1],authority=lambda:s) as d:print(json.dumps(d.snapshot()))'
  p=subprocess.run([sys.executable,'-B','-c',code,str(target)],capture_output=True,timeout=15)
  self.assertEqual(p.returncode,0,p.stderr);self.assertEqual({k:v for k,v in json.loads(p.stdout).items() if k!='scope_key'},{k:v for k,v in self.store.snapshot().items() if k!='scope_key'})

if __name__=='__main__':unittest.main(verbosity=2)

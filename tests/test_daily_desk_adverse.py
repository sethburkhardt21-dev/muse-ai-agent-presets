"""Additional archive, migration, race and failure-boundary checks."""
from pathlib import Path
from unittest import mock
import concurrent.futures,copy,hashlib,json,os,sqlite3,tempfile,threading,unittest
import muse_presets.daily_desk as module
from muse_presets.daily_desk import DailyDesk,restore_desk,read_archive,canonical,inspect_desk
from muse_presets.personal_companion import CompanionScope,PersonalCompanion
S=CompanionScope('owner','space','owner',True)

class AdverseDesk(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name).resolve();self.db=self.root/'db.sqlite';self.auth=lambda:S
  self.store=DailyDesk(self.db,authority=self.auth)
 def tearDown(self):self.store.close();self.tmp.cleanup()
 def add(self):return self.store.put_task(task_id='t',title='test',expected_revision=0,operation_id='op')
 def test_unknown_scope_does_not_create_store(self):
  path=self.root/'no.sqlite'
  with self.assertRaises(ValueError):DailyDesk(path,authority=lambda:{'owner_id':'owner'})
  self.assertFalse(path.exists())
 def test_restore_empty_desk_and_read_only_inspection(self):
  path=self.root/'empty.sqlite';restore_desk(path,self.store.export_archive(),authority=self.auth);before=path.read_bytes()
  r=inspect_desk(path,authority=self.auth);self.assertEqual((r['tasks'],r['notes']),(0,0));self.assertTrue(r['read_only']);self.assertEqual(path.read_bytes(),before)
 def test_read_only_inspection_does_not_initialize_unknown_database(self):
  path=self.root/'unrelated.sqlite'
  from contextlib import closing
  with closing(sqlite3.connect(path)) as db:
   with db:db.execute('CREATE TABLE unrelated(value TEXT)');db.execute("INSERT INTO unrelated VALUES('KEEP')")
  before=path.read_bytes()
  with self.assertRaises(ValueError):inspect_desk(path,authority=self.auth)
  self.assertEqual(path.read_bytes(),before)
 def test_oversized_and_deep_archive_refused(self):
  for raw in [b' '* (module.MAX_ARCHIVE_BYTES+1),b'['*1500+b']'*1500]:
   with self.assertRaises(ValueError):read_archive(raw)
 def test_deleted_original_note_stays_deleted_after_restore(self):
  with PersonalCompanion(self.db,authority=self.auth) as p:
   p.put_note('n','temporary');p.forget_note('n',expected_revision=1)
  path=self.root/'restored.sqlite';restore_desk(path,self.store.export_archive(),authority=self.auth)
  with DailyDesk(path,authority=self.auth) as d:
   self.assertEqual(d.notes(),[]);self.assertEqual(read_archive(d.export_archive())['notes'][0]['state'],'deleted')
 def test_restore_does_not_reenable_original_external_request_policy(self):
  self.add();path=self.root/'restored.sqlite';restore_desk(path,self.store.export_archive(),authority=self.auth)
  from muse_presets.space_companion import SpaceCompanion
  with SpaceCompanion(path,authority=self.auth) as jobs:
   r=jobs.snapshot();self.assertFalse(r['enabled']);self.assertEqual(r['requests'],[])
 def test_restore_link_failure_has_no_published_file_and_cleans_staging(self):
  path=self.root/'no.sqlite'
  with mock.patch.object(module.os,'link',side_effect=OSError('fixture')):
   with self.assertRaisesRegex(ValueError,'RESTORE_FAILED_NO_PUBLISHED_STORE'):restore_desk(path,self.store.export_archive(),authority=self.auth)
  self.assertFalse(path.exists());self.assertEqual(list(self.root.glob('.*.restore-*')),[])
 def test_two_restore_writers_cannot_overwrite_each_other(self):
  self.add();raw=self.store.export_archive();path=self.root/'race.sqlite';barrier=threading.Barrier(2)
  def restore(_):
   barrier.wait()
   try:return restore_desk(path,raw,authority=self.auth)
   except ValueError as e:return str(e)
  with concurrent.futures.ThreadPoolExecutor(2) as pool:result=list(pool.map(restore,[1,2]))
  self.assertEqual(sum(type(x) is dict for x in result),1);self.assertIn('RESTORE_EXISTS',result)
  with DailyDesk(path,authority=self.auth) as d:self.assertEqual(d.export_archive(),raw)
 def test_receipt_tamper_cannot_be_exported_as_valid(self):
  self.add();self.store._db.execute("UPDATE daily_operations SET request_sha256=?",('0'*64,))
  with self.assertRaisesRegex(ValueError,'ARCHIVE_OPERATION_DIGEST'):self.store.export_archive()
 def test_archive_cannot_smuggle_other_operation_or_provider_fields(self):
  self.add();base=json.loads(self.store.export_archive())
  for mutate in [lambda p:p['operations'][0]['request'].update(owner_id='owner'),lambda p:p['operations'][0]['result'].update(provider_dispatched=True),lambda p:p['operations'][0].update(at_ms=True)]:
   v=copy.deepcopy(base);mutate(v['payload']);v['sha256']=hashlib.sha256(canonical(v['payload'])).hexdigest()
   with self.assertRaises(ValueError):read_archive(canonical(v))
 def test_latest_receipt_cannot_disagree_with_same_revision_record(self):
  self.add();v=json.loads(self.store.export_archive())
  v['payload']['tasks'][0]['title']='Different from recorded receipt'
  v['sha256']=hashlib.sha256(canonical(v['payload'])).hexdigest()
  with self.assertRaisesRegex(ValueError,'ARCHIVE_LATEST_RESULT_MISMATCH'):read_archive(canonical(v))
 def test_clock_regression_preserves_record(self):
  with DailyDesk(self.db,authority=self.auth,clock_ms=lambda:1000) as d:d.put_task(task_id='t',title='first',operation_id='first')
  with DailyDesk(self.db,authority=self.auth,clock_ms=lambda:999) as d:
   with self.assertRaisesRegex(ValueError,'CLOCK_REGRESSION'):d.put_task(task_id='t',title='new',expected_revision=1,operation_id='later')
  self.assertEqual(self.store.snapshot()['tasks'][0]['title'],'first')
 def test_pending_binding_distinguishes_new_same_owner_database(self):
  with DailyDesk(self.root/'separate.sqlite',authority=self.auth) as separate:
   self.assertNotEqual(self.store.snapshot()['scope_key'],separate.snapshot()['scope_key'])
 def test_restore_has_new_store_binding_but_exact_task_and_note_state(self):
  self.add();raw=self.store.export_archive();destination=self.root/'copy.sqlite';restore_desk(destination,raw,authority=self.auth)
  with DailyDesk(destination,authority=self.auth) as restored:
   self.assertNotEqual(restored.snapshot()['scope_key'],self.store.snapshot()['scope_key'])
   self.assertEqual(restored.export_archive(),raw)
 def test_hardlinked_destination_inspection_refused(self):
  path=self.root/'alias.sqlite'
  try:os.link(self.db,path)
  except OSError:self.skipTest('Hardlinks unavailable')
  with self.assertRaisesRegex(ValueError,'PATH_UNSAFE'):inspect_desk(path,authority=self.auth)
  path.unlink()

if __name__=='__main__':unittest.main()

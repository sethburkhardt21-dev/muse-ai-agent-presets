"""Clean-consumer Daily Desk launcher: no server or permanent store by default."""
from pathlib import Path
import json,os,subprocess,sys,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
class DailyDeskCLI(unittest.TestCase):
 def run_cli(self,*args):
  return subprocess.run([sys.executable,'-I','-B',str(ROOT/'examples/daily_desk.py'),*map(str,args)],cwd=ROOT,env={k:v for k,v in os.environ.items() if k!='PYTHONPATH'},capture_output=True,timeout=20)
 def test_disposable_vertical_demo(self):
  p=self.run_cli();self.assertEqual(p.returncode,0,p.stderr)
  r=json.loads(p.stdout);self.assertEqual(r['status'],'DAILY_DESK_VERTICAL_SLICE_PASS');self.assertEqual((r['tasks'],r['notes']),(3,2))
  for key in ['reopened','stale_task_refused','stale_note_refused','restored','exact_operation_replayed_once','source_store_unchanged_by_restore']:self.assertTrue(r[key])
  self.assertFalse(r['server_started']);self.assertFalse(r['native_installed'])
 def test_relative_database_refused_before_listener(self):
  p=self.run_cli('--serve','--database','relative.sqlite');self.assertNotEqual(p.returncode,0)
  self.assertIn(b'REFUSED',p.stdout);self.assertFalse((ROOT/'relative.sqlite').exists())
 def test_restore_cli_rejects_existing_without_overwriting(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);archive=root/'bad.json';archive.write_text('{}');target=root/'keep.sqlite';target.write_bytes(b'KEEP')
   p=self.run_cli('--restore',archive,'--database',target);self.assertNotEqual(p.returncode,0);self.assertEqual(target.read_bytes(),b'KEEP')

if __name__=='__main__':unittest.main()

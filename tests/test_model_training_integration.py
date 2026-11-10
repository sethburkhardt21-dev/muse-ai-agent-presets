"""Integration checks: retain both recovered algorithms in the actual neutral role."""
import hashlib,json,subprocess,sys,tempfile,unittest,zipfile
from pathlib import Path
from muse_presets.model_builder_dropin import stage_model_builder_dropin,inspect_model_builder_dropin
from muse_presets.model_builder_sourcekit import export_model_builder_sourcekit,verify_model_builder_sourcekit

class ModelTrainingIntegration(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory(prefix='r62-model-integration-');self.addCleanup(self.temp.cleanup)
  self.root=Path(self.temp.name).resolve();self.pack=self.root/'role';stage_model_builder_dropin(self.pack)
  self.runner=self.pack/'custom-skills/model_development_metrics/run.py'
 def command(self,*args):
  p=subprocess.run([sys.executable,'-I','-B',str(self.runner),*args],capture_output=True,text=True,timeout=40)
  return p,json.loads(p.stdout) if p.stdout.strip().startswith('{') else {}
 def test_linear_training_requires_explicit_optin(self):
  p,r=self.command('--operation','linear-demo');self.assertEqual(p.returncode,2)
  self.assertEqual(r.get('reason'),'EXPLICIT_LOCAL_TRAINING_OPT_IN_REQUIRED',p.stderr+r.__repr__())
 def test_both_algorithms_and_legacy_are_real_separate_operations(self):
  for operation,status in [('demo','LOCAL_MODEL_BUILDER_DEMO_PASSED'),('toy-demo','LOCAL_TOY_MODEL_DEMO_PASSED'),('linear-demo','LOCAL_LINEAR_MODEL_DEMO_PASSED')]:
   p,r=self.command('--operation',operation,'--allow-local-training');self.assertEqual(p.returncode,0,p.stderr+p.stdout);self.assertEqual(r['status'],status)
   self.assertFalse(r['native_tool_invoked']);self.assertFalse(r['external_effect_authorized'])
   if operation=='linear-demo':
    self.assertEqual(r['optimizer_steps'],64);self.assertTrue(r['bundle_recomputed']);self.assertTrue(r['baseline_restored_byte_exact'])
    self.assertEqual(r['final_status'],'HELD_UNEVALUATED');self.assertFalse(r['promotion_authorized'])
 def test_new_runtime_files_are_staged_and_tamper_refused(self):
  for name in ('model_toy_math.py','model_toy_bundle.py','model_toy_fixture.py','model_training_demo.py'):
   p=self.pack/'runtime'/name;self.assertTrue(p.is_file(),name)
  p=self.pack/'runtime/model_toy_math.py';p.write_bytes(p.read_bytes()+b'\n# drift\n')
  self.assertEqual(inspect_model_builder_dropin(self.pack)['status'],'REVIEW_REQUIRED')
  run,r=self.command('--operation','linear-demo','--allow-local-training');self.assertEqual(run.returncode,2);self.assertEqual(r['reason'],'SOURCE_LINEAR_RUNTIME_DRIFT')
 def test_complete_zip_runs_both_algorithms_without_repository(self):
  target=self.root/'combined.zip';report=export_model_builder_sourcekit(self.pack,target)
  self.assertEqual(verify_model_builder_sourcekit(target,report['sha256'])['status'],'LOCAL_MODEL_SOURCEKIT_VERIFIED')
  fresh=self.root/'fresh';fresh.mkdir()
  with zipfile.ZipFile(target) as z:
   self.assertIn('EXAMPLE_LINEAR_DATASET.json',z.namelist());z.extractall(fresh)
  self.runner=fresh/'model-builder/custom-skills/model_development_metrics/run.py'
  for op in ('toy-demo','linear-demo'):
   p,r=self.command('--operation',op,'--allow-local-training');self.assertEqual(p.returncode,0,p.stderr+p.stdout);self.assertFalse(r['external_effect_authorized'])
 def test_original_model_eval_bytes_unchanged(self):
  source=Path(__file__).resolve().parents[1]/'src/muse_presets/model_eval.py'
  self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),'a7ae164110d08d534c7f2c0340981757d0b4f8de77bf4caef50ef5e87781cfb6')

if __name__=='__main__':unittest.main()

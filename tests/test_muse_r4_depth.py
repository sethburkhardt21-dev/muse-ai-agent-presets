from pathlib import Path
import importlib.util,json,copy,unittest,math
ROOT=Path(__file__).resolve().parents[1]; C=ROOT/'collections/muse-starters-v1/r4'
SELECTED='scope-and-route source-and-custody bounded-review household-project teach-back change-brief visual-reference customer-discovery offer-design content-system service-playbook analysis-notebook chart-story portfolio-story role-fit interview-rehearsal difficult-message negotiation-prep meal-plan garden-observe hobby-practice event-plan purchase-compare appointment-prep accessibility-routine reflection-journal habit-experiment family-archive'.split()
def load():
 spec=importlib.util.spec_from_file_location('r4_checks',C/'r4_checks.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
class Structure(unittest.TestCase):
 def test_exact_existing_28(self):
  d=json.loads((C/'R4_DEPTH.json').read_text(encoding='utf-8'));self.assertEqual(set(d),set(SELECTED));self.assertEqual(len(d),28)
 def test_minimum_depth_is_not_performance_claim(self):
  for sid,d in json.loads((C/'R4_DEPTH.json').read_text(encoding='utf-8')).items():
   with self.subTest(sid=sid):
    self.assertGreaterEqual(len(d['decisions']),5);self.assertEqual(len(d['failure_modes']),3)
    self.assertGreater(len(d['domain_method']),150);self.assertGreater(len(d['output_contract']),80)
    self.assertGreaterEqual(len(d['additional_examples']),1);self.assertEqual(d['comparison_result'],'NOT_RUN')
    self.assertEqual(len(d['case_ids']),3);self.assertEqual(d['revision'],'R4')
 def test_case_ids_and_scope(self):
  cs=json.loads((C/'R4_CASES.json').read_text(encoding='utf-8'));self.assertEqual(len(cs),84);self.assertEqual(len({c['id'] for c in cs}),84)
  for c in cs:
   self.assertIn(c['skill_id'],SELECTED);self.assertIsNone(c['model_results']);self.assertNotEqual(c['reference_output'],c['wrong_output'])
 def test_input_validation(self):
  m=load()
  for bad in (None,[],{},float('nan'),True):self.assertFalse(m.check_case(bad,{})['passed'])
 def test_no_network_or_execution_imports(self):
  import ast
  t=ast.parse((C/'r4_checks.py').read_text(encoding='utf-8'))
  imports={n.names[0].name.split('.')[0] for n in ast.walk(t) if isinstance(n,ast.Import)}|{(n.module or '').split('.')[0] for n in ast.walk(t) if isinstance(n,ast.ImportFrom)}
  self.assertFalse(imports&{'subprocess','socket','requests','urllib','http','pickle'})
 def test_100_starters_are_skill_bundles_not_agent_identity_installs(self):
  spec=importlib.util.spec_from_file_location('r4_catalog',ROOT/'tools/muse_collection.py')
  module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
  collection=module.load_collection(ROOT/'collections/muse-starters-v1')
  self.assertEqual(len(collection['starters']),100)
  forbidden={'identity.md','soul.md','agents.md','memory.md','heartbeat.md','user.md','tools.md'}
  for starter in collection['starters']:
   with self.subTest(starter=starter['id']):
    files=module.package_files(collection,starter['id'])
    names={Path(name).name.casefold() for name in files}
    self.assertFalse(forbidden & names)
    self.assertIn('START_HERE.md',files)
    self.assertIn('PROFILE.md',files)
    self.assertTrue(any(name.startswith('skills/') for name in files))
class Domain(unittest.TestCase):pass
for sid in SELECTED:
 for variant in ('standard','edge','recovery'):
  for positive in (True,False):
   def f(self,sid=sid,variant=variant,positive=positive):
    cs=json.loads((C/'R4_CASES.json').read_text(encoding='utf-8'));c=next(c for c in cs if c['id']==f'{sid}-r4-{variant}')
    result=load().check_case(c,c['reference_output' if positive else 'wrong_output'])
    self.assertIs(result['passed'],positive,result)
   setattr(Domain,f'test_{sid.replace("-","_")}_{variant}_{"positive" if positive else "negative"}',f)
 def gold(self,sid=sid):
  c=next(c for c in json.loads((C/'R4_CASES.json').read_text(encoding='utf-8')) if c['id']==f'{sid}-r4-standard');o=copy.deepcopy(c['reference_output'])
  c['reference_output']={'untrusted':'edited'};c['wrong_output']={'untrusted':'edited'}
  self.assertTrue(load().check_case(c,o)['passed'])
 setattr(Domain,'test_gold_independence_'+sid.replace('-','_'),gold)
if __name__=='__main__':unittest.main()

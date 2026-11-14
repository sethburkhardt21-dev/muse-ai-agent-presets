"""Compatibility and source-bound admission of the existing skill collection."""
from __future__ import annotations
import copy,hashlib,importlib.util,json,os,pathlib,subprocess,sys,tempfile,unittest,zipfile,io
R=pathlib.Path(__file__).resolve().parents[1]
C=R/'collections/muse-starters-v1'

def load_tool():
 spec=importlib.util.spec_from_file_location('promoted_collection',R/'tools/muse_collection.py')
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

class CollectionPromotion(unittest.TestCase):
 def test_existing_inventory_is_available_without_becoming_125_skills(self):
  tool=load_tool();data=tool.load_collection()
  self.assertEqual((len(data['skills']),len(data['starters']),len(data['workflows'])),(75,100,25))
  self.assertEqual(len({s['id'] for s in data['skills']}),75)
  self.assertTrue(all(s['evaluation']==tool.EVALUATION for s in data['skills']))
  report=json.loads((C/'PUBLIC_COMPATIBILITY.json').read_bytes())
  self.assertEqual(report['collection_skill_count'],75)
  self.assertEqual(report['legacy_procedure_count'],50)
  self.assertIsNone(report['combined_unique_capability_count'])
  self.assertEqual(report['native_installation'],'NOT_PERFORMED')
 def test_all_legacy_procedures_have_reviewed_non_destructive_dispositions(self):
  from muse_presets.catalog import load_registry,load_preset
  from muse_presets.role_skills import plan_role_skills,SHARED_SKILLS
  expected=set(SHARED_SKILLS)
  for role in load_registry()['presets']:expected.update(plan_role_skills(role)['skill_ids'])
  report=json.loads((C/'PUBLIC_COMPATIBILITY.json').read_bytes())
  self.assertEqual(set(x['legacy_id'] for x in report['procedure_links']),expected)
  self.assertEqual(len(report['procedure_links']),50)
  skills={s['id'] for s in load_tool().load_collection()['skills']}
  for row in report['procedure_links']:
   self.assertIn(row['disposition'],('KEEP_COMPATIBILITY','KEEP_ROLE_METHOD'))
   self.assertTrue(set(row['related_collection_skills'])<=skills)
   self.assertTrue(row['reason'])
   self.assertFalse(row['claims_behavioral_equivalence'])
  self.assertEqual(len(load_registry()['presets']),15)
 def test_aliases_preserve_both_role_protocols_not_extra_agents(self):
  x=json.loads((C/'PUBLIC_COMPATIBILITY.json').read_bytes())
  self.assertEqual(x['role_aliases'],{'data-engineer':'data-engineering-architect','reliability-engineer':'infrastructure-reliability-engineer'})
  self.assertEqual(x['role_count'],15)
  self.assertEqual(x['starter_configurations'],100)
 def test_existing_public_source_bytes_stay_frozen(self):
  p=json.loads((C/'PUBLIC_BASELINE.json').read_bytes())
  self.assertEqual(p['source_commit'],'b75ef3091b8195dbbc090a8ab308c9d9130fd585')
  self.assertEqual(len(p['files']),198)
  for name,expected in p['files'].items():
   with self.subTest(path=name):self.assertEqual(hashlib.sha256((R/name).read_bytes()).hexdigest(),expected)
 def test_public_projection_has_closed_origin_and_no_private_ledger(self):
  x=json.loads((C/'PROMOTION_PROVENANCE.json').read_bytes())
  self.assertEqual(x['source_kind'],'OWNER_AUTHORIZED_FIRST_PARTY')
  self.assertFalse(x['private_history_included']);self.assertFalse(x['upstream_code_imported'])
  self.assertTrue(x['incoming_files'])
  for name,row in x['incoming_files'].items():
   self.assertEqual(hashlib.sha256((R/name).read_bytes()).hexdigest(),row['sha256'])
   self.assertIn(row['rights'],('PROJECT_MIT_ORIGINAL','REFERENCE_ONLY_PUBLIC_SOURCE_METADATA'))
  self.assertNotIn('private_repository',x)
 def test_invalid_origin_and_false_native_badges_are_rejected(self):
  tool=load_tool();d=tool.load_collection()
  for change in ['license','native','duplicate']:
   x=copy.deepcopy(d)
   if change=='license':x['sources'][0]['reuse']='copy';x['sources'][0]['license']='UNKNOWN'
   elif change=='native':x['skills'][0]['evaluation']='NATIVE_INSTALLED_AND_PROVEN'
   else:x['skills'][1]['steps']=x['skills'][0]['steps']
   with self.subTest(change=change),self.assertRaises(tool.CollectionError):tool.validate(x)
 def test_all_starters_build_and_reopen_with_hashes(self):
  tool=load_tool();d=tool.load_collection()
  for starter in d['starters']:
   with self.subTest(starter=starter['id']):
    raw=tool.build_bytes(d,starter['id'])
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
     self.assertIsNone(z.testzip());m=json.loads(z.read('MANIFEST.json'))
     self.assertEqual(set(z.namelist()),set(m['files'])|{'MANIFEST.json'})
     self.assertFalse(m['automatic_external_actions'])
     for n,h in m['files'].items():self.assertEqual(hashlib.sha256(z.read(n)).hexdigest(),h)
     self.assertFalse(any(n.endswith(('IDENTITY.md','SOUL.md','MEMORY.md')) for n in z.namelist()))
 def test_four_existing_rich_engines_execute_without_native_effects(self):
  tool=load_tool();d=tool.load_collection()
  for role in tool.EXTENSION_ROLES:
   with self.subTest(role=role):
    out=tool.specialist_demo(d,role)
    self.assertFalse(out['external_actions_performed']);self.assertFalse(out['model_called'])
    self.assertGreaterEqual(len(out['results']),2)
    self.assertEqual(out,tool.specialist_demo(d,role))
 def test_five_operating_guides_and_daily_desk_contract_exist(self):
  for name in ['context-loading','skill-setup','subchat-workrooms','durable-documents','source-and-host-capabilities']:
   p=R/'docs/handbook'/f'{name}.md';body=p.read_text(encoding='utf8')
   self.assertGreater(len(body),1700)
   for title in ['## First useful result','## Verify','## Failure and recovery','## Scope and evidence']:self.assertIn(title,body)
  body=(R/'docs/handbook/daily-desk-design.md').read_text(encoding='utf8')
  for word in ['SpaceCompanion','PersonalCompanion','NOT_IMPLEMENTED','stale','restore','3 tasks','2 notes']:
   self.assertIn(word,body)
 def test_documentation_routes_do_not_silently_replace_profile_install(self):
  body=(R/'docs/collection/MUSE_CURATED_COLLECTION.md').read_text(encoding='utf8')
  for s in ['75','100','25','existing','identity','memory','quickstart.py','portable','not 125']:
   self.assertIn(s,body)

if __name__=='__main__':unittest.main(verbosity=2)

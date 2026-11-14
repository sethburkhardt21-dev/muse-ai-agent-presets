"""Negative controls for inventory reconciliation; local metadata is never authority."""
import copy,importlib.util,json,pathlib,tempfile,unittest
R=pathlib.Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('collection_compatibility_guard',R/'tools/collection_compatibility.py')
M=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(M)

class CompatibilityGuards(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.mapping=json.loads((R/'collections/muse-starters-v1/PUBLIC_COMPATIBILITY.json').read_bytes())
  cls.legacy={x['legacy_id'] for x in cls.mapping['procedure_links']}
  cls.skills={x['id'] for x in json.loads((R/'collections/muse-starters-v1/skills.json').read_bytes())}
 def check(self,x):return M.validate_mapping(x,self.legacy,self.skills)
 def test_reviewed_mapping_is_valid(self):self.assertIsNone(self.check(self.mapping))
 def test_library_starts_at_seventy_five(self):
  x=copy.deepcopy(self.mapping);x['collection_skill_count']=125
  with self.assertRaisesRegex(ValueError,'COUNT'):self.check(x)
 def test_no_combined_unique_claim(self):
  x=copy.deepcopy(self.mapping);x['combined_unique_capability_count']=125
  with self.assertRaisesRegex(ValueError,'COUNT'):self.check(x)
 def test_no_native_activation_claim(self):
  x=copy.deepcopy(self.mapping);x['native_installation']='INSTALLED'
  with self.assertRaisesRegex(ValueError,'NATIVE'):self.check(x)
 def test_no_promoted_comparison_claim(self):
  x=copy.deepcopy(self.mapping);x['model_comparisons']='WINNER'
  with self.assertRaisesRegex(ValueError,'NATIVE'):self.check(x)
 def test_missing_legacy_reference_refused(self):
  x=copy.deepcopy(self.mapping);x['procedure_links'].pop()
  with self.assertRaisesRegex(ValueError,'LEGACY'):self.check(x)
 def test_duplicate_legacy_reference_refused(self):
  x=copy.deepcopy(self.mapping);x['procedure_links'][1]=copy.deepcopy(x['procedure_links'][0])
  with self.assertRaisesRegex(ValueError,'LEGACY'):self.check(x)
 def test_unknown_collection_skill_refused(self):
  x=copy.deepcopy(self.mapping);x['procedure_links'][0]['related_collection_skills'].append('imaginary')
  with self.assertRaisesRegex(ValueError,'RELATED'):self.check(x)
 def test_duplicate_related_skill_refused(self):
  x=copy.deepcopy(self.mapping);x['procedure_links'][0]['related_collection_skills']*=2
  with self.assertRaisesRegex(ValueError,'RELATED'):self.check(x)
 def test_false_equivalence_refused(self):
  x=copy.deepcopy(self.mapping);x['procedure_links'][0]['claims_behavioral_equivalence']=True
  with self.assertRaisesRegex(ValueError,'EQUIVALENCE'):self.check(x)
 def test_renamed_role_alias_refused(self):
  x=copy.deepcopy(self.mapping);x['role_aliases']['automation-engineer']='new-agent'
  with self.assertRaisesRegex(ValueError,'ALIAS'):self.check(x)
 def test_destructive_disposition_refused(self):
  x=copy.deepcopy(self.mapping);x['procedure_links'][0]['disposition']='REPLACE_AGENT'
  with self.assertRaisesRegex(ValueError,'DISPOSITION'):self.check(x)
 def test_unknown_acceptance_field_refused(self):
  x=copy.deepcopy(self.mapping);x['approved']=True
  with self.assertRaisesRegex(ValueError,'SCHEMA'):self.check(x)
 def test_semantic_equivalence_not_implied_by_shared_name(self):
  x=copy.deepcopy(self.mapping);x['procedure_links'][0]['reason']=''
  with self.assertRaisesRegex(ValueError,'REASON'):self.check(x)
 def test_duplicate_json_refused(self):
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d)/'data.json';p.write_text('{"count":75,"count":125}',encoding='utf8')
   with self.assertRaises(ValueError):M.read_json(p)
 def test_whole_public_repository_checks(self):
  x=M.check_repository(R)
  self.assertEqual(x['status'],'COLLECTION_COMPATIBILITY_VERIFIED')
  self.assertEqual(x['collection_skills'],75)
  self.assertEqual(x['legacy_procedures'],50)
  self.assertIsNone(x['combined_unique_capabilities'])
  self.assertFalse(x['native_installed'])
 def test_original_history_remains_snapshot_not_catalog_downgrade(self):
  original=json.loads((R/'collections/muse-starters-v1/r5/baseline/legacy_catalog.json').read_bytes())
  current=json.loads((R/'presets/catalog.json').read_bytes())
  self.assertEqual(current['presets'][:11],original['presets'])
  self.assertEqual(len(current['presets']),15)

class ExportNamespaceGuards(unittest.TestCase):
 def test_unapproved_tools_path_refused(self):
  from muse_presets.public_export import select_public_files,PublicExportError
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d);(root/'tools').mkdir();(root/'tools/new_dispatcher.py').write_text('x=1\n')
   with self.assertRaisesRegex(PublicExportError,'UNAPPROVED_COLLECTION_PATH'):select_public_files(root,verify_manifest=False)
 def test_unapproved_collection_path_refused(self):
  from muse_presets.public_export import select_public_files,PublicExportError
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d);(root/'collections/owner-private').mkdir(parents=True);(root/'collections/owner-private/notes.md').write_text('test')
   with self.assertRaisesRegex(PublicExportError,'UNAPPROVED_COLLECTION_PATH'):select_public_files(root,verify_manifest=False)

if __name__=='__main__':unittest.main(verbosity=2)

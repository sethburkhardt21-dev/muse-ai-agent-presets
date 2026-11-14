"""V1 connector catalog: complete, source-pinned, useful and never an authority grant."""
from pathlib import Path
import copy,hashlib,importlib.util,json,re,subprocess,sys,tempfile,unittest,zipfile
R=Path(__file__).resolve().parents[1]

def tool():
 spec=importlib.util.spec_from_file_location('connector_catalog',R/'scripts/connector_catalog.py')
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

class ConnectorCatalogTests(unittest.TestCase):
 def test_all151_have_source_setup_and_specialist_relevance(self):
  m=tool();doc=m.load_catalog();self.assertEqual(len(doc['connectors']),151)
  self.assertEqual(doc['source']['repository'],'bluman1/muse-connectors')
  self.assertEqual(doc['source']['commit'],'73f302c2d8569fdc65e0e57c26b244c547fcd40e')
  roles=set(json.loads((R/'presets/catalog.json').read_bytes())['presets'])
  self.assertEqual(len({c['id'] for c in doc['connectors']}),151)
  for c in doc['connectors']:
   with self.subTest(connector=c['id']):
    self.assertTrue(set(c['specialists'])<=roles);self.assertTrue(c['specialists'])
    self.assertIn(doc['source']['commit'],c['source_url'])
    self.assertTrue(c['setup_prompt']);self.assertIn(c['source_url'],c['setup_prompt'])
    self.assertIn('credentials',c['setup_prompt']);self.assertIn('approval',c['setup_prompt'])
    self.assertRegex(c['source_sha256'],r'^[a-f0-9]{64}$')
    self.assertTrue(c['auth']);self.assertTrue(c['permissions']);self.assertTrue(c['files'])
 def test_frozen_snapshot_and_license_are_verified(self):
  m=tool();d=m.load_catalog();proof=json.loads((R/'docs/connectors/PROVENANCE.json').read_bytes())
  self.assertEqual(proof['connector_count'],151)
  self.assertFalse(proof['upstream_code_executed']);self.assertFalse(proof['connector_code_vendored'])
  for path,digest in proof['distributed_files'].items():self.assertEqual(hashlib.sha256((R/path).read_bytes()).hexdigest(),digest)
  license=(R/'docs/connectors/UPSTREAM_LICENSE.txt').read_text();self.assertIn('muse-connectors contributors',license)
 def test_all_entries_have_browsable_source_fallback(self):
  body=(R/'docs/connectors/CATALOG.md').read_text();page=(R/'docs/connectors/index.html').read_text()
  for c in tool().load_catalog()['connectors']:
   self.assertIn(c['source_url'],body);self.assertIn('id="'+c['id']+'"',page)
  for token in ['connector-search','category-filter','specialist-filter','copy-prompt','aria-live','Content-Security-Policy']:
   self.assertIn(token,page)
  js=(R/'docs/connectors/app.js').read_text();self.assertNotIn('innerHTML',js);self.assertNotIn('eval(',js)
  self.assertNotIn('fetch(',js);self.assertNotIn('localStorage',js)
 def test_validate_refuses_malformed_and_false_claims(self):
  m=tool();base=m.load_catalog()
  variants=[]
  x=copy.deepcopy(base);x['connectors'][1]['id']=x['connectors'][0]['id'];variants.append(x)
  x=copy.deepcopy(base);x['connectors'][0]['source_url']='https://attacker.invalid/SKILL.md';variants.append(x)
  x=copy.deepcopy(base);x['connectors'][0]['files'].append('../private');variants.append(x)
  x=copy.deepcopy(base);x['connectors'][0]['specialists']=['nonexistent'];variants.append(x)
  x=copy.deepcopy(base);x['connectors'][0]['installed']=True;variants.append(x)
  x=copy.deepcopy(base);x['source']['commit']='main';variants.append(x)
  for i,x in enumerate(variants):
   with self.subTest(case=i),self.assertRaises(ValueError):m.validate_catalog(x)
 def test_sync_diff_reports_without_rewriting(self):
  m=tool();base=m.load_catalog();new=copy.deepcopy(base);row=copy.deepcopy(new['connectors'][0]);row['id']='new-service';row['name']='New service';new['connectors'].append(row)
  new['connectors'][1]['auth']='updated authentication';removed=new['connectors'].pop(2)['id']
  result=m.compare_catalogs(base,new)
  self.assertEqual(result['added'],['new-service']);self.assertEqual(result['removed'],[removed]);self.assertEqual(result['changed'],[base['connectors'][1]['id']]);self.assertFalse(result['applied'])
 def test_pack_is_create_only_and_manifested(self):
  m=tool()
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'catalog.zip';x=m.export_catalog(p)
   self.assertEqual(x['connectors'],151)
   with zipfile.ZipFile(p) as z:
    self.assertIsNone(z.testzip());manifest=json.loads(z.read('MANIFEST.json'))
    self.assertEqual(set(z.namelist()),set(manifest['files'])|{'MANIFEST.json'})
    for n,h in manifest['files'].items():self.assertEqual(hashlib.sha256(z.read(n)).hexdigest(),h)
   with self.assertRaises(FileExistsError):m.export_catalog(p)

class V1ProductTests(unittest.TestCase):
 def test_hero_leads_with_specialists_configs_connectors(self):
  s=(R/'README.md').read_text();hero=s.split('\n## ',1)[0]
  for value in ['Muse Specialist Toolkit','Your Muse. Your Specialists. Your Possibilities.','15','100+','150+']:self.assertIn(value,hero)
  self.assertNotIn('offline',hero.lower());self.assertNotIn('75 skills',hero.lower())
  self.assertLess(len(s.encode()),8000)
 def test_four_routes_and_current_release_metadata_agree(self):
  d=json.loads((R/'docs/discovery/agent-capabilities.json').read_bytes())
  self.assertEqual(d['project'],'Muse Specialist Toolkit');self.assertEqual(d['release'],'v1.0.0')
  self.assertEqual(d['custom_connector_count'],151);self.assertEqual(d['configuration_count'],115)
  for p in ['docs/v1/START_HERE.md','docs/v1/POST_RELEASE.md','docs/connectors/README.md','scripts/build_v1_release.py']:
   self.assertTrue((R/p).is_file(),p)
 def test_v1_documents_preserve_historical_assets_and_identity(self):
  s=(R/'docs/RELEASES.md').read_text()
  self.assertIn('v1.0.0',s);self.assertIn('v0.4.1-alpha',s)
  s=(R/'docs/v1/START_HERE.md').read_text()
  for value in ['Use with Muse','Run specialist tools','Open Personal Companion','Explore connectors','existing identity','30-day']:self.assertIn(value,s)

if __name__=='__main__':unittest.main(verbosity=2)

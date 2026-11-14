"""Product-level export, original-content preservation and usable kit checks."""
from pathlib import Path
from tempfile import TemporaryDirectory
import copy
import hashlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]
C=ROOT/'collections/muse-starters-v1'
EXTENSIONS=('data-engineer','reliability-engineer','automation-engineer','product-interface-designer')

def tool():
    spec=importlib.util.spec_from_file_location('r5_collection',ROOT/'tools/muse_collection.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()

class ProductTests(unittest.TestCase):
    def setUp(self):
        self.tool=tool()
        self.data=self.tool.load_collection(C)

    def test_combined_registry_contains_real_extensions_and_original_roles(self):
        self.assertTrue(hasattr(self.tool,'specialist_kit_files'),'Executable specialist exporter is absent')
        self.assertEqual(len(self.data.get('specialists',[])),15)
        roles={r['id']:r for r in self.data['specialists']}
        self.assertEqual(set(roles),set(self.tool.CORE_ROLES)|set(EXTENSIONS))
        for name in EXTENSIONS:
            role=roles[name]
            self.assertEqual(role['kind'],'executable-extension')
            self.assertTrue((ROOT/role['contract']).is_file())
            self.assertGreaterEqual(len(role['skills']),2)

    def test_original_skills_and_workflows_are_exactly_preserved(self):
        path=C/'R5_BASELINE.json';self.assertTrue(path.is_file())
        baseline=json.loads(path.read_text('utf-8'))
        skills={s['id']:s for s in self.data['skills']}
        workflows={w['id']:w for w in self.data['workflows']}
        for key,expected in baseline['skill_object_sha256'].items():
            self.assertEqual(digest(skills[key]),expected,key)
        for key,expected in baseline['workflow_object_sha256'].items():
            self.assertEqual(digest(workflows[key]),expected,key)
        self.assertEqual(sorted(p['id'] for p in self.data['starters']),baseline['starter_ids'])
        legacy=ROOT/'collections/muse-starters-v1/r5/baseline/legacy_catalog.json'
        self.assertEqual(hashlib.sha256(legacy.read_bytes()).hexdigest(),baseline['legacy_catalog_sha256'])
        self.assertEqual(json.loads((ROOT/'presets/catalog.json').read_bytes())['presets'][:11],json.loads(legacy.read_bytes())['presets'])

    def test_r5_skills_have_meaningful_depth_and_authored_case_closure(self):
        new=[s for s in self.data['skills'] if s.get('depth',{}).get('revision')=='R5']
        self.assertEqual(len(new),11)
        cases={c['id']:c for c in self.data['depth_cases']}
        for skill in new:
            with self.subTest(skill=skill['id']):
                self.assertEqual(skill['origin'],'ORIGINAL_FIRST_PARTY')
                self.assertEqual(skill['source_ids'],[])
                d=skill['depth'];self.assertGreaterEqual(len(d['decisions']),5)
                self.assertGreaterEqual(len(d['failure_modes']),3)
                self.assertGreaterEqual(len(d['domain_method']),150)
                self.assertGreaterEqual(len(d['additional_examples']),1)
                self.assertEqual(len(d['case_ids']),3)
                self.assertEqual(d['upstream_items'],[])
                for cid in d['case_ids']:
                    self.assertEqual(cases[cid]['skill_id'],skill['id'])
                    self.assertNotEqual(cases[cid]['reference_output'],cases[cid]['wrong_output'])
                    self.assertIsNone(cases[cid]['model_results'])

    def test_first_party_marker_cannot_relax_legacy_provenance(self):
        d=copy.deepcopy(self.data);d['skills'][0]['source_ids']=[]
        with self.assertRaises(ValueError):self.tool.validate(d)

    def test_selected_starters_reference_all_four_new_specialists_without_new_identities(self):
        bindings={p.get('specialist_role') for p in self.data['starters'] if p.get('specialist_role')}
        self.assertEqual(bindings,set(EXTENSIONS))
        for p in self.data['starters']:
            self.assertIn(p['base_role'],self.tool.CORE_ROLES)
            if p.get('specialist_role'):
                files=self.tool.package_files(self.data,p['id'])
                self.assertFalse(any(Path(f).name in ('IDENTITY.md','SOUL.md','MEMORY.md') for f in files))
                self.assertIn(p['specialist_role'],files['PROFILE.md'].decode())

    def test_unknown_specialist_reference_rejected(self):
        d=copy.deepcopy(self.data);d['starters'][0]['specialist_role']='unregistered-role'
        with self.assertRaises(ValueError):self.tool.validate(d)

    def test_r5_challenge_does_not_include_examples_or_oracle(self):
        new=[s for s in self.data['skills'] if s.get('depth',{}).get('revision')=='R5']
        self.assertEqual(len(new),11)
        for s in new:
            cid=s['depth']['case_ids'][0]
            arms=[self.tool.challenge_files(self.data,cid,a) for a in ('plain','candidate')]
            self.assertEqual(arms[0]['TASK.json'],arms[1]['TASK.json'])
            with self.assertRaises(ValueError):self.tool.challenge_files(self.data,cid,'upstream')
            candidate=b'\n'.join(arms[1].values()).decode()
            self.assertNotIn('reference_output',candidate)
            self.assertNotIn(s['depth']['worked_example']['result'],candidate)

    def test_each_specialist_kit_runs_from_clean_directory_without_repository_imports(self):
        self.assertTrue(hasattr(self.tool,'specialist_kit_files'))
        for role in EXTENSIONS:
            with self.subTest(role=role),TemporaryDirectory() as temp:
                files=self.tool.specialist_kit_files(self.data,role)
                first=self.tool.build_file_map_bytes(files)
                self.assertEqual(first,self.tool.build_file_map_bytes(files))
                with zipfile.ZipFile(io.BytesIO(first)) as z:z.extractall(temp)
                env={k:v for k,v in os.environ.items() if k not in ('PYTHONPATH','PYTHONHOME')}
                p=subprocess.run([sys.executable,'-B','run.py','--demo'],cwd=temp,env=env,
                    capture_output=True,text=True,timeout=20)
                self.assertEqual(p.returncode,0,p.stderr)
                report=json.loads(p.stdout)
                self.assertEqual(report['specialist'],role)
                self.assertGreaterEqual(len(report['results']),2)
                self.assertFalse(report['external_actions_performed'])
                self.assertTrue((Path(temp)/'SPECIALIST.json').is_file())
                manifest=json.loads(files['MANIFEST.json'])
                for name,expected in manifest['files'].items():
                    self.assertEqual(hashlib.sha256(files[name]).hexdigest(),expected)

    def test_kit_rejects_unknown_role_and_existing_output(self):
        self.assertTrue(hasattr(self.tool,'specialist_kit_files'))
        with self.assertRaises(ValueError):self.tool.specialist_kit_files(self.data,'invented')
        with TemporaryDirectory() as temp:
            destination=Path(temp)/'owned.zip';destination.write_bytes(b'keep')
            with self.assertRaises(ValueError):self.tool.write_new_pack(destination,b'replace')
            self.assertEqual(destination.read_bytes(),b'keep')

if __name__=='__main__':unittest.main()

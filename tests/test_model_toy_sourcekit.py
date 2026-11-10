"""Actual standalone CLI and deterministic artifact readback, not stdout-only demos."""
import hashlib
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

from muse_presets import model_toy_math as math
from test_model_toy_math import example


class SourcekitTests(unittest.TestCase):
    def setUp(self):
        try:self.k=importlib.import_module('muse_presets.model_toy_sourcekit')
        except ModuleNotFoundError:self.fail('No runnable Model Builder optimizer source kit is implemented')
        self.temp=tempfile.TemporaryDirectory(prefix='r60-kit-test-')
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve()
        self.zip=self.root/'model-builder-toy.zip'

    def export(self):
        result=self.k.export_sourcekit(self.zip)
        self.assertEqual(result['status'],'LOCAL_TOY_SOURCEKIT_EXPORTED')
        self.assertEqual(result['sha256'],math.digest(self.zip.read_bytes()))
        return result

    def extract(self):
        result=self.export()
        extracted=self.root/'fresh';extracted.mkdir()
        with zipfile.ZipFile(self.zip) as z:z.extractall(extracted)
        return result,extracted

    def invoke(self,script,args,cwd):
        env={k:v for k,v in os.environ.items() if k!='PYTHONPATH'}
        return subprocess.run([sys.executable,'-I','-B',str(script),*args],cwd=cwd,
                              env=env,capture_output=True,text=True,timeout=20)

    def test_complete_sourcekit_closed_tree_and_disabled_native_policy(self):
        r=self.export()
        v=self.k.verify_sourcekit(self.zip,r['sha256'])
        self.assertEqual(v['status'],'LOCAL_TOY_SOURCEKIT_VERIFIED')
        with zipfile.ZipFile(self.zip) as z:
            names=set(z.namelist())
            self.assertEqual(len(names),len(z.infolist()))
            for name in ('runtime/model_toy_math.py','runtime/model_toy_bundle.py',
                         'runtime/model_eval.py','runtime/model_toy_sourcekit.py',
                         'EXAMPLE_DATASET.json','SOURCEKIT_MANIFEST.json','LICENSE'):
                self.assertIn(name,names)
            manifest=json.loads(z.read('SOURCEKIT_MANIFEST.json'))
            self.assertEqual(set(manifest['files_sha256']),names-{'SOURCEKIT_MANIFEST.json'})
            self.assertFalse(manifest['native_installed'])
            self.assertFalse(manifest['independent_fleet_verified'])
            self.assertFalse(manifest['publicly_published'])
            self.assertIn(b'status: disabled',z.read('config/skills.yaml'))
            self.assertEqual(json.loads(z.read('EXAMPLE_DATASET.json')),example())

    def test_fresh_extraction_real_optimizer_recompute_and_rollback(self):
        r,e=self.extract()
        manifest=json.loads((e/'SOURCEKIT_MANIFEST.json').read_text())
        runtime=e/'runtime/model_toy_bundle.py'
        dest=self.root/'actual-run'
        run=self.invoke(runtime,['run','--dataset',str(e/'EXAMPLE_DATASET.json'),
            '--dataset-sha256',manifest['example_dataset_sha256'],'--to',str(dest),'--reviewed-data'],e)
        self.assertEqual(run.returncode,0,run.stdout+run.stderr)
        report=json.loads(run.stdout)
        self.assertEqual(report['optimizer_steps'],64)
        self.assertEqual(report['evaluation']['selected_checkpoint'],'candidate')
        verify=self.invoke(runtime,['verify','--bundle',str(dest),
            '--receipt-sha256',report['receipt_sha256']],e)
        self.assertEqual(verify.returncode,0,verify.stdout+verify.stderr)
        self.assertEqual(json.loads(verify.stdout)['status'],'LOCAL_TOY_BUNDLE_RECOMPUTED')
        restored=self.root/'restored-baseline.json'
        rollback=self.invoke(runtime,['restore-baseline','--bundle',str(dest),
            '--receipt-sha256',report['receipt_sha256'],'--to',str(restored)],e)
        self.assertEqual(rollback.returncode,0,rollback.stdout+rollback.stderr)
        self.assertEqual(restored.read_bytes(),(dest/'baseline.json').read_bytes())
        self.assertNotEqual(restored.read_bytes(),(dest/'candidate.json').read_bytes())

    def test_standalone_zip_verifier_works_without_original_repository(self):
        r,e=self.extract()
        check=self.invoke(e/'runtime/model_toy_sourcekit.py',
            ['verify','--archive',str(self.zip),'--sha256',r['sha256']],e)
        self.assertEqual(check.returncode,0,check.stdout+check.stderr)
        self.assertEqual(json.loads(check.stdout)['status'],'LOCAL_TOY_SOURCEKIT_VERIFIED')

    def test_cli_requires_inspected_data_and_missing_pin_never_runs(self):
        r,e=self.extract();dest=self.root/'unsafe'
        check=self.invoke(e/'runtime/model_toy_bundle.py',
            ['run','--dataset',str(e/'EXAMPLE_DATASET.json'),'--dataset-sha256','0'*64,
             '--to',str(dest)],e)
        self.assertEqual(check.returncode,2)
        self.assertEqual(json.loads(check.stdout)['status'],'REFUSED')
        self.assertFalse(dest.exists())

    def test_repeat_export_produces_identical_bytes(self):
        one=self.export();p=self.root/'second.zip'
        two=self.k.export_sourcekit(p)
        self.assertEqual(one['sha256'],two['sha256'])
        self.assertEqual(self.zip.read_bytes(),p.read_bytes())

    def test_existing_output_never_overwritten(self):
        self.zip.write_bytes(b'owner archive')
        with self.assertRaises(math.Refused):self.k.export_sourcekit(self.zip)
        self.assertEqual(self.zip.read_bytes(),b'owner archive')

    def test_wrong_sha_and_trailing_data_refused(self):
        r=self.export()
        with self.assertRaises(math.Refused):self.k.verify_sourcekit(self.zip,'0'*64)
        self.zip.write_bytes(self.zip.read_bytes()+b'UNLISTED PRIVATE BYTES')
        with self.assertRaises(math.Refused):self.k.verify_sourcekit(self.zip,math.digest(self.zip.read_bytes()))

    def test_invalid_zip_and_size_are_refused(self):
        for data in (b'not a ZIP',b'x'*(2*1024*1024+1)):
            self.zip.write_bytes(data)
            with self.subTest(size=len(data)),self.assertRaises(math.Refused):
                self.k.verify_sourcekit(self.zip,math.digest(data))

    def test_unsafe_path_duplicate_and_case_alias_members_refused(self):
        for names in (('../outside','ok'),('/abs','ok'),('X.py','x.py'),('same','same')):
            with zipfile.ZipFile(self.zip,'w') as z:
                if names[0] == names[1]:
                    with self.assertWarns(UserWarning):
                        for name in names:z.writestr(name,b'x')
                else:
                    for name in names:z.writestr(name,b'x')
            with self.subTest(names=names),self.assertRaises(math.Refused):
                self.k.verify_sourcekit(self.zip,math.digest(self.zip.read_bytes()))

    def test_forged_source_and_self_rehashed_manifest_refused(self):
        self.export()
        with zipfile.ZipFile(self.zip) as z:members={n:z.read(n) for n in z.namelist()}
        name='runtime/model_toy_math.py';members[name]+=b'\n# injected source\n'
        m=math.strict_json(members['SOURCEKIT_MANIFEST.json'])
        m['files_sha256'][name]=math.digest(members[name])
        members['SOURCEKIT_MANIFEST.json']=math.canonical_json(m)
        self.zip.write_bytes(self.k._archive(members))
        with self.assertRaisesRegex(math.Refused,'SOURCE'):
            self.k.verify_sourcekit(self.zip,math.digest(self.zip.read_bytes()))

    def test_forged_native_authority_refused(self):
        self.export()
        with zipfile.ZipFile(self.zip) as z:members={n:z.read(n) for n in z.namelist()}
        m=math.strict_json(members['SOURCEKIT_MANIFEST.json']);m['native_installed']=True
        members['SOURCEKIT_MANIFEST.json']=math.canonical_json(m)
        self.zip.write_bytes(self.k._archive(members))
        with self.assertRaises(math.Refused):self.k.verify_sourcekit(self.zip,math.digest(self.zip.read_bytes()))

    def test_unpacked_legacy_evaluator_keeps_its_original_refusal_contract(self):
        r,e=self.extract()
        raw=(e/'runtime/model_eval.py').read_bytes()
        blob=hashlib.sha1(f'blob {len(raw)}\0'.encode()+raw).hexdigest()
        self.assertEqual(blob,'d8143578cf942841184dc2a55233df8557b7eb61')

if __name__=='__main__':unittest.main()

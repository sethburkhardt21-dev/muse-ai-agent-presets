"""Real extracted Creative Studio kit: no repository import or paid provider."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile
from unittest.mock import patch
from muse_presets import creative_sourcekit as kit
from muse_presets import creative_production as cp
from muse_presets.public_export import select_public_files
from test_creative_production import brief

ROOT=Path(__file__).resolve().parents[1]

class CreativeSourcekitTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='creative-kit-test-')
        self.addCleanup(self.tmp.cleanup);self.base=Path(self.tmp.name)

    def build(self,name='studio.zip'):
        out=self.base/name
        report=kit.export_creative_sourcekit(ROOT,out)
        return out,report

    def extract(self):
        archive,_=self.build();root=self.base/'kit'
        with zipfile.ZipFile(archive) as z:z.extractall(root)
        return root

    def run_kit(self,root,*args,optimize=False):
        command=[sys.executable,'-I','-B']+(['-O'] if optimize else [])+[str(root/'run.py'),*args]
        return subprocess.run(command,cwd=self.base,env=dict(os.environ,PYTHONPATH='absent-repo',PYTHONDONTWRITEBYTECODE='1'),capture_output=True,text=True,timeout=100)

    def refused(self,root,*args,optimize=False):
        p=self.run_kit(root,*args,optimize=optimize)
        self.assertEqual(p.returncode,2,p.stdout+p.stderr)
        self.assertNotIn('Traceback',p.stderr)
        value=json.loads(p.stdout);self.assertEqual(value['status'],'REFUSED')
        self.assertFalse(value['native_installed']);self.assertFalse(value['media_rendered'])
        return value

    def test_exact_pinned_source_members(self):
        archive,r=self.build()
        with zipfile.ZipFile(archive) as z:
            for source,dest in kit.SOURCE_MAP.items():self.assertEqual(z.read(dest),(ROOT/source).read_bytes())
            m=json.loads(z.read('SOURCEKIT_MANIFEST.json'))
            self.assertEqual(set(m['files_sha256'])|{'SOURCEKIT_MANIFEST.json'},set(z.namelist()))
            self.assertFalse(m['media_renderer_bundled']);self.assertFalse(m['native_installed'])
        self.assertEqual(hashlib.sha256(archive.read_bytes()).hexdigest(),r['archive_sha256'])

    def test_canonical_bytes_reproduced(self):
        a,r=self.build();b,_=self.build('second.zip')
        self.assertEqual(a.read_bytes(),b.read_bytes())
        self.assertEqual(kit.verify_creative_sourcekit(ROOT,a,r['archive_sha256'])['status'],'CREATIVE_SOURCEKIT_VERIFIED')

    def test_create_only_package_preserves_existing_zip(self):
        out,_=self.build();raw=out.read_bytes()
        with self.assertRaises(ValueError):kit.export_creative_sourcekit(ROOT,out)
        self.assertEqual(raw,out.read_bytes())

    def test_invalid_external_digest_refused(self):
        out,_=self.build()
        for pin in ('0'*64,None,'','bad'):
            with self.subTest(pin=pin),self.assertRaises(ValueError):kit.verify_creative_sourcekit(ROOT,out,pin)

    def test_noncanonical_rehashed_zip_refused_before_parsing(self):
        out=self.base/'corrupt.zip';out.write_bytes(b'not a zip')
        original=zipfile.ZipFile
        def guard(*args,**kwargs):
            mode=args[1] if len(args)>1 else kwargs.get('mode','r')
            self.assertEqual(mode,'w','Untrusted archive was opened for reading')
            return original(*args,**kwargs)
        with patch.object(zipfile,'ZipFile',side_effect=guard),self.assertRaisesRegex(ValueError,'CANONICAL_ARCHIVE_CHANGED'):
            kit.verify_creative_sourcekit(ROOT,out,hashlib.sha256(out.read_bytes()).hexdigest())

    def test_source_drift_refused(self):
        source=self.base/'source'
        for n in kit.SOURCE_SHA:
            p=source/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/n).read_bytes())
        p=source/'src/muse_presets/creative_production.py';p.write_bytes(p.read_bytes()+b'\n# changed\n')
        with self.assertRaisesRegex(ValueError,'SOURCE_PIN_MISMATCH'):kit.export_creative_sourcekit(source,self.base/'bad.zip')

    def test_actual_demo_export_and_pinned_reopen(self):
        root=self.extract();out=self.base/'production'
        p=self.run_kit(root,'--operation','demo','--to',str(out))
        self.assertEqual(p.returncode,0,p.stdout+p.stderr);r=json.loads(p.stdout)
        self.assertEqual(r['status'],'CREATIVE_PROJECT_EXPORTED');self.assertEqual(r['shots'],3)
        self.assertEqual(len(list(out.iterdir())),5)
        q=self.run_kit(root,'--operation','verify','--project',str(out),'--sha256',r['brief_sha256'])
        self.assertEqual(q.returncode,0,q.stdout+q.stderr)
        self.assertEqual(json.loads(q.stdout)['status'],'CREATIVE_PROJECT_VERIFIED')

    def test_compile_external_brief_and_revision_compare(self):
        root=self.extract();before=self.base/'before.json';after=self.base/'after.json'
        a=brief();b=brief();b['scenes'][0]['shots'][1]['duration_frames']=96
        before.write_bytes(cp.canonical_bytes(a));after.write_bytes(cp.canonical_bytes(b))
        p=self.run_kit(root,'--operation','compile','--brief',str(after),'--to',str(self.base/'out'))
        self.assertEqual(p.returncode,0,p.stdout+p.stderr)
        self.assertEqual(json.loads(p.stdout)['total_frames'],192)
        q=self.run_kit(root,'--operation','diff','--before',str(before),'--after',str(after))
        self.assertEqual(q.returncode,0,q.stdout+q.stderr)
        self.assertEqual(json.loads(q.stdout)['shots']['changed'],['light'])

    def test_shipped_engine_selftests(self):
        p=self.run_kit(self.extract(),'--operation','self-test')
        self.assertEqual(p.returncode,0,p.stdout+p.stderr)
        result=json.loads(p.stdout)
        self.assertEqual(result['status'],'CREATIVE_SELF_TEST_PASSED')
        self.assertEqual(result['tests_run'],39);self.assertEqual(result['failures'],0);self.assertEqual(result['errors'],0)

    def test_existing_output_no_overwrite(self):
        root=self.extract();out=self.base/'existing';out.mkdir();sentinel=out/'owner.txt';sentinel.write_text('keep')
        self.refused(root,'--operation','demo','--to',str(out))
        self.assertEqual(sentinel.read_text(),'keep')

    def test_output_inside_immutable_kit_refused(self):
        root=self.extract();self.refused(root,'--operation','demo','--to',str(root/'output'))
        self.assertFalse((root/'output').exists())

    def test_bad_arguments_are_structured_refusals(self):
        root=self.extract()
        for args in (['--operation','compile'],['--operation','demo'],['--operation','verify'],['--operation','diff'],['--operation','demo','--to',str(self.base/'out'),'--brief','unrelated.json']):
            with self.subTest(args=args):self.refused(root,*args)

    def test_deep_duplicate_and_forged_manifests_refused(self):
        root=self.extract();p=root/'SOURCEKIT_MANIFEST.json';original=p.read_bytes()
        for data in (b'['*10000+b'0'+b']'*10000,b'{"schema":"forged",'+original.lstrip()[1:],cp.canonical_bytes(dict(json.loads(original),media_renderer_bundled=True))):
            p.write_bytes(data)
            self.refused(root,'--operation','self-test')
        p.write_bytes(original)

    def test_modified_module_and_rehashed_manifest_refused(self):
        root=self.extract();p=root/'muse_presets/creative_production.py';p.write_bytes(p.read_bytes()+b'\n# changed\n')
        m=root/'SOURCEKIT_MANIFEST.json';doc=json.loads(m.read_bytes());doc['files_sha256']['muse_presets/creative_production.py']=hashlib.sha256(p.read_bytes()).hexdigest();m.write_bytes(cp.canonical_bytes(doc))
        self.refused(root,'--operation','self-test')

    def test_import_shadow_and_unknown_directory_refused(self):
        root=self.extract();(root/'json.py').write_text('raise RuntimeError("untrusted")\n')
        self.refused(root,'--operation','self-test');(root/'json.py').unlink()
        (root/'extra').mkdir();self.refused(root,'--operation','self-test')

    def test_optimized_interpreter_refused(self):
        self.refused(self.extract(),'--operation','self-test',optimize=True)

    def test_unsafe_external_brief_refused(self):
        root=self.extract();p=self.base/'bad.json';p.write_bytes(b'['*10000+b'0'+b']'*10000)
        self.refused(root,'--operation','compile','--brief',str(p),'--to',str(self.base/'out'))
        self.assertFalse((self.base/'out').exists())

    def test_linked_kit_root_refused(self):
        root=self.extract();link=self.base/'linked-kit'
        try:link.symlink_to(root,target_is_directory=True)
        except (OSError,NotImplementedError):self.skipTest('Directory symlink privilege unavailable')
        self.refused(link,'--operation','self-test')

    def test_junction_kit_root_refused_on_windows(self):
        if os.name!='nt':self.skipTest('Windows junction only')
        root=self.extract();link=self.base/'junction-kit'
        p=subprocess.run(['cmd','/c','mklink','/J',str(link),str(root)],capture_output=True,timeout=15)
        self.assertEqual(p.returncode,0,p.stderr)
        try:self.refused(link,'--operation','self-test')
        finally:os.rmdir(link)

    def test_public_export_includes_all_new_source(self):
        files=select_public_files(ROOT)
        for name in ('src/muse_presets/creative_production.py','src/muse_presets/creative_sourcekit.py','src/muse_presets/creative_cli.py','tests/test_creative_production.py','tests/test_creative_sourcekit.py','examples/creative_brief.json','docs/kits/CREATIVE_SOURCEKIT.md'):
            self.assertIn(name,files)

if __name__=='__main__':unittest.main()

"""R61 opt-in extension staging and package/CLI admission tests."""
from __future__ import annotations
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from muse_presets import model_toy_bundle as bundle, model_toy_math as math
from muse_presets import model_toy_sourcekit as kit

class ExtensionInstallTests(unittest.TestCase):
    def setUp(self):
        spec=importlib.util.find_spec('muse_presets.model_toy_install')
        self.assertIsNotNone(spec,'R61 explicit opt-in extension stage/inspect CLI is not implemented')
        from muse_presets import model_toy_install
        self.api=model_toy_install
        self.temp=tempfile.TemporaryDirectory(prefix='r61-extension-')
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.dest=self.root/'extension'

    def stage(self):
        result=self.api.stage_extension(self.dest,include_toy_training=True)
        self.assertEqual(result['status'],'SOURCE_ONLY_TOY_EXTENSION_STAGED')
        self.assertFalse(result['native_installed'])
        self.assertFalse(result['external_effect_authorized'])
        self.assertFalse(result['training_started'])
        self.assertFalse((self.dest/'STAGING_INCOMPLETE').exists())
        self.assertEqual(result['stage_receipt_sha256'],math.digest(
            (self.dest/'INSTALL_RECEIPT.json').read_bytes()))
        return result

    def test_without_explicit_opt_in_no_directory_or_training(self):
        with self.assertRaisesRegex(math.Refused,'EXPLICIT_TOY_OPT_IN'):
            self.api.stage_extension(self.dest)
        self.assertFalse(self.dest.exists())

    def test_boolean_opt_in_is_not_a_string_or_integer(self):
        for value in (1,'true',None,[],{}):
            with self.subTest(value=value):
                with self.assertRaises(math.Refused):
                    self.api.stage_extension(self.dest,include_toy_training=value)
        self.assertFalse(self.dest.exists())

    def test_stage_matches_current_canonical_extension_source(self):
        result=self.stage()
        expected=kit._members()
        for name,raw in expected.items():self.assertEqual((self.dest/name).read_bytes(),raw,name)
        actual={p.relative_to(self.dest).as_posix() for p in self.dest.rglob('*') if p.is_file()}
        self.assertEqual(actual,set(expected)|{'INSTALL_RECEIPT.json'})
        inspected=self.api.inspect_extension(self.dest,result['stage_receipt_sha256'])
        self.assertEqual(inspected['status'],'LOCAL_TOY_EXTENSION_STAGE_MATCH')
        self.assertFalse(inspected['native_installed'])
        self.assertFalse(inspected['publisher_authenticated'])

    def test_repeat_stage_existing_destination_cannot_overwrite(self):
        result=self.stage()
        before={str(p.relative_to(self.dest)):p.read_bytes() for p in self.dest.rglob('*') if p.is_file()}
        with self.assertRaises(math.Refused):
            self.api.stage_extension(self.dest,include_toy_training=True)
        after={str(p.relative_to(self.dest)):p.read_bytes() for p in self.dest.rglob('*') if p.is_file()}
        self.assertEqual(before,after)

    def test_separate_stage_is_byte_identical(self):
        a=self.stage()
        d=self.root/'second'
        b=self.api.stage_extension(d,include_toy_training=True)
        self.assertEqual(a['stage_receipt_sha256'],b['stage_receipt_sha256'])
        self.assertEqual((self.dest/'INSTALL_RECEIPT.json').read_bytes(),(d/'INSTALL_RECEIPT.json').read_bytes())

    def test_wrong_receipt_pin_is_refused_without_modifying_files(self):
        self.stage()
        before=(self.dest/'INSTALL_RECEIPT.json').read_bytes()
        with self.assertRaisesRegex(math.Refused,'PIN'):
            self.api.inspect_extension(self.dest,'0'*64)
        self.assertEqual((self.dest/'INSTALL_RECEIPT.json').read_bytes(),before)

    def test_missing_pin_is_not_accepted(self):
        self.stage()
        for value in ('',None,True,15,'a'*63,'A'*64):
            with self.subTest(value=value):
                with self.assertRaises(math.Refused):self.api.inspect_extension(self.dest,value)

    def test_runtime_tampering_is_refused(self):
        result=self.stage()
        f=self.dest/'runtime/model_toy_math.py'
        f.write_bytes(f.read_bytes()+b'\n# unexpected drift\n')
        with self.assertRaisesRegex(math.Refused,'DRIFT'):
            self.api.inspect_extension(self.dest,result['stage_receipt_sha256'])

    def test_extra_file_is_refused(self):
        result=self.stage()
        (self.dest/'unexpected.txt').write_text('not part of reviewed source')
        with self.assertRaisesRegex(math.Refused,'FILE_SET'):
            self.api.inspect_extension(self.dest,result['stage_receipt_sha256'])

    def test_extra_empty_directory_is_refused(self):
        result=self.stage()
        (self.dest/'unreviewed-directory').mkdir()
        with self.assertRaisesRegex(math.Refused,'DIRECTORY_SET'):
            self.api.inspect_extension(self.dest,result['stage_receipt_sha256'])

    def test_duplicate_receipt_keys_are_refused(self):
        self.stage()
        p=self.dest/'INSTALL_RECEIPT.json';data=p.read_bytes()
        data=b'{"schema":"forged",'+data.lstrip()[1:];p.write_bytes(data)
        with self.assertRaises(math.Refused):self.api.inspect_extension(self.dest,math.digest(data))

    def test_self_rehashed_native_authority_claim_is_refused(self):
        self.stage()
        p=self.dest/'INSTALL_RECEIPT.json'
        data=json.loads(p.read_bytes());data['native_installed']=True
        raw=math.canonical_json(data);p.write_bytes(raw)
        with self.assertRaisesRegex(math.Refused,'RECEIPT'):
            self.api.inspect_extension(self.dest,math.digest(raw))

    def test_self_rehashed_file_pin_cannot_bless_changed_code(self):
        self.stage()
        p=self.dest/'runtime/model_toy_math.py';p.write_bytes(p.read_bytes()+b'\n# changed\n')
        rec=self.dest/'INSTALL_RECEIPT.json'
        data=json.loads(rec.read_bytes());data['files_sha256'][p.relative_to(self.dest).as_posix()]=math.digest(p.read_bytes())
        raw=math.canonical_json(data);rec.write_bytes(raw)
        with self.assertRaises(math.Refused):self.api.inspect_extension(self.dest,math.digest(raw))

    def test_partial_output_stays_incomplete_and_cannot_retry(self):
        original=bundle._write_new
        n=[0]
        def interrupted(p,data):
            n[0]+=1
            if n[0]==4:raise OSError('synthetic interruption')
            return original(p,data)
        with patch.object(bundle,'_write_new',side_effect=interrupted):
            with self.assertRaises((math.Refused,OSError)):
                self.api.stage_extension(self.dest,include_toy_training=True)
        self.assertTrue((self.dest/'STAGING_INCOMPLETE').is_file())
        before={str(p.relative_to(self.dest)):p.read_bytes() for p in self.dest.rglob('*') if p.is_file()}
        with self.assertRaises(math.Refused):self.api.stage_extension(self.dest,include_toy_training=True)
        self.assertEqual(before,{str(p.relative_to(self.dest)):p.read_bytes() for p in self.dest.rglob('*') if p.is_file()})

    def test_current_source_change_during_preflight_creates_no_output(self):
        actual=kit._members(); changed=dict(actual);changed['START_HERE.md']+=b'changed'
        with patch.object(kit,'_members',side_effect=[actual,changed]):
            with self.assertRaisesRegex(math.Refused,'SOURCE_CHANGED'):
                self.api.stage_extension(self.dest,include_toy_training=True)
        self.assertFalse(self.dest.exists())

    def test_symlinked_member_is_refused(self):
        result=self.stage()
        target=self.dest/'START_HERE.md';saved=target.read_bytes();target.unlink()
        external=self.root/'outside.md';external.write_bytes(saved)
        try:target.symlink_to(external)
        except (OSError,NotImplementedError):self.skipTest('OS symlink permission unavailable')
        with self.assertRaises(math.Refused):self.api.inspect_extension(self.dest,result['stage_receipt_sha256'])

    def test_hardlinked_member_is_refused(self):
        result=self.stage()
        file=self.dest/'START_HERE.md'
        try:os.link(file,self.root/'hardlink.md')
        except (OSError,NotImplementedError):self.skipTest('OS hardlinks unavailable')
        with self.assertRaises(math.Refused):self.api.inspect_extension(self.dest,result['stage_receipt_sha256'])

    def test_output_inside_existing_stage_is_refused_by_closed_tree(self):
        result=self.stage()
        sub=self.dest/'unapproved-output'
        self.api.stage_extension(sub,include_toy_training=True)
        with self.assertRaisesRegex(math.Refused,'FILE_SET|DIRECTORY_SET'):
            self.api.inspect_extension(self.dest,result['stage_receipt_sha256'])

    def test_unicode_space_path_and_disabled_registry(self):
        self.dest=self.root/'Model Builder é'
        self.stage()
        self.assertIn(b'status: disabled',(self.dest/'config/skills.yaml').read_bytes())
        binding=json.loads((self.dest/'config/host-binding.json').read_bytes())
        self.assertFalse(binding['training_service_authorized'])
        self.assertFalse(binding['scheduler_enabled'])

    def test_staged_kit_executes_real_training_verification_and_restore(self):
        self.stage()
        cli=self.dest/'runtime/model_toy_bundle.py'
        data=self.dest/'EXAMPLE_DATASET.json';pin=math.digest(data.read_bytes())
        run=self.root/'experiment'
        p=subprocess.run([sys.executable,'-I','-B',str(cli),'run','--dataset',str(data),
            '--dataset-sha256',pin,'--to',str(run),'--reviewed-data'],capture_output=True,text=True,timeout=30)
        self.assertEqual(p.returncode,0,p.stdout+p.stderr)
        info=json.loads(p.stdout);self.assertEqual(info['status'],'LOCAL_TOY_EXPERIMENT_RECORDED')
        verified=subprocess.run([sys.executable,'-I','-B',str(cli),'verify','--bundle',str(run),
            '--receipt-sha256',info['receipt_sha256']],capture_output=True,text=True,timeout=30)
        self.assertEqual(verified.returncode,0,verified.stdout+verified.stderr)
        output=self.root/'restored.json'
        restored=subprocess.run([sys.executable,'-I','-B',str(cli),'restore-baseline','--bundle',str(run),
            '--receipt-sha256',info['receipt_sha256'],'--to',str(output)],capture_output=True,text=True,timeout=30)
        self.assertEqual(restored.returncode,0,restored.stdout+restored.stderr)
        self.assertEqual(output.read_bytes(),(run/'baseline.json').read_bytes())

    def test_cli_stage_and_readback_and_no_opt_in_refusal(self):
        env=dict(os.environ,PYTHONPATH=str(Path(__file__).resolve().parents[1]/'src'),PYTHONDONTWRITEBYTECODE='1')
        cmd=[sys.executable,'-B','-m','muse_presets.model_toy_install']
        refused=subprocess.run([*cmd,'stage','--to',str(self.dest)],env=env,capture_output=True,text=True,timeout=30)
        self.assertEqual(refused.returncode,2)
        self.assertFalse(self.dest.exists())
        okay=subprocess.run([*cmd,'stage','--to',str(self.dest),'--include-toy-training'],env=env,capture_output=True,text=True,timeout=30)
        self.assertEqual(okay.returncode,0,okay.stdout+okay.stderr)
        data=json.loads(okay.stdout)
        read=subprocess.run([*cmd,'inspect','--root',str(self.dest),'--stage-sha256',data['stage_receipt_sha256']],env=env,capture_output=True,text=True,timeout=30)
        self.assertEqual(read.returncode,0,read.stdout+read.stderr)
        self.assertEqual(json.loads(read.stdout)['status'],'LOCAL_TOY_EXTENSION_STAGE_MATCH')

if __name__=='__main__':unittest.main()

"""Real create-only artifacts, verified recomputation and actual baseline restore."""
import copy
import importlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from test_model_toy_math import example
from muse_presets import model_toy_math as math


class BundleTests(unittest.TestCase):
    def setUp(self):
        try:self.b=importlib.import_module('muse_presets.model_toy_bundle')
        except ModuleNotFoundError:self.fail('T21 lacks persisted, independently recomputed toy checkpoints and rollback')
        self.temp=tempfile.TemporaryDirectory(prefix='r60-bundle-tests-')
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve()
        self.source=self.root/'dataset.json'
        self.raw=math.canonical_json(example())
        self.source.write_bytes(self.raw)
        self.pin=math.digest(self.raw)
        self.dest=self.root/'run'

    def run_model(self,**kw):
        return self.b.run_experiment(self.source,self.pin,self.dest,reviewed_data=True,**kw)

    def test_run_writes_pinned_actual_models_and_verified_recomputation(self):
        result=self.run_model()
        self.assertEqual(result['status'],'LOCAL_TOY_EXPERIMENT_RECORDED')
        self.assertEqual(len(list(self.dest.iterdir())),6)
        self.assertFalse((self.dest/'STAGING_INCOMPLETE').exists())
        receipt=self.b.verify_bundle(self.dest,result['receipt_sha256'])
        self.assertEqual(receipt['status'],'LOCAL_TOY_BUNDLE_RECOMPUTED')
        self.assertEqual(receipt['optimizer_steps'],64)
        self.assertFalse(receipt['promotion_authorized'])
        self.assertEqual(receipt['final_status'],'HELD_UNEVALUATED')

    def test_occupied_output_refused_and_bytes_unchanged(self):
        report=self.run_model()
        before={p.name:p.read_bytes() for p in self.dest.iterdir()}
        with self.assertRaises(math.Refused):self.run_model()
        self.assertEqual(before,{p.name:p.read_bytes() for p in self.dest.iterdir()})
        self.assertEqual(self.b.verify_bundle(self.dest,report['receipt_sha256'])['status'],'LOCAL_TOY_BUNDLE_RECOMPUTED')

    def test_changed_source_under_old_pin_refused_before_output(self):
        self.source.write_bytes(self.raw+b' ')
        with self.assertRaisesRegex(math.Refused,'PIN'):self.run_model()
        self.assertFalse(self.dest.exists())

    def test_unreviewed_input_refused_before_any_output(self):
        with self.assertRaisesRegex(math.Refused,'REVIEWED'):
            self.b.run_experiment(self.source,self.pin,self.dest)
        self.assertFalse(self.dest.exists())

    def test_true_baseline_restore_is_byte_exact_to_new_target(self):
        report=self.run_model()
        restored=self.root/'baseline-restored.json'
        result=self.b.restore_baseline(self.dest,report['receipt_sha256'],restored)
        self.assertEqual(result['status'],'BASELINE_RESTORED_TO_NEW_FILE')
        self.assertEqual(restored.read_bytes(),(self.dest/'baseline.json').read_bytes())
        self.assertNotEqual(restored.read_bytes(),(self.dest/'candidate.json').read_bytes())
        cp=math.strict_json(restored.read_bytes())
        self.assertEqual(math.predict(cp,['1']),'1')
        self.assertEqual(cp['optimizer_steps'],0)
        self.assertEqual(result['sha256'],math.digest(restored.read_bytes()))

    def test_rollback_cannot_overwrite_owner_file(self):
        report=self.run_model();p=self.root/'owner.json';p.write_bytes(b'owner bytes')
        with self.assertRaises(math.Refused):self.b.restore_baseline(self.dest,report['receipt_sha256'],p)
        self.assertEqual(p.read_bytes(),b'owner bytes')

    def test_wrong_receipt_pin_refused(self):
        self.run_model()
        with self.assertRaisesRegex(math.Refused,'PIN'):self.b.verify_bundle(self.dest,'0'*64)

    def test_modified_candidate_even_with_rehashed_manifest_refused_by_recomputation(self):
        self.run_model()
        candidate=math.strict_json((self.dest/'candidate.json').read_bytes())
        candidate['weights'][0]='99'
        (self.dest/'candidate.json').write_bytes(math.canonical_json(candidate))
        manifest=math.strict_json((self.dest/'MANIFEST.json').read_bytes())
        manifest['files_sha256']['candidate.json']=math.digest((self.dest/'candidate.json').read_bytes())
        (self.dest/'MANIFEST.json').write_bytes(math.canonical_json(manifest))
        new=math.digest((self.dest/'MANIFEST.json').read_bytes())
        with self.assertRaisesRegex(math.Refused,'RECOMPUTATION'):self.b.verify_bundle(self.dest,new)

    def test_forged_success_authority_refused(self):
        self.run_model()
        manifest=math.strict_json((self.dest/'MANIFEST.json').read_bytes())
        manifest['promotion_authorized']=True
        data=math.canonical_json(manifest);(self.dest/'MANIFEST.json').write_bytes(data)
        with self.assertRaisesRegex(math.Refused,'MANIFEST'):self.b.verify_bundle(self.dest,math.digest(data))

    def test_deleted_manifest_unknown_status_not_blind_retry(self):
        self.run_model();(self.dest/'MANIFEST.json').unlink()
        with self.assertRaises(math.Refused):self.b.verify_bundle(self.dest,'0'*64)
        with self.assertRaises(math.Refused):self.run_model()
        self.assertTrue((self.dest/'candidate.json').exists())

    def test_interrupted_write_preserves_hold_and_never_reexecutes_into_same_path(self):
        real=self.b._write_new
        def fail_candidate(path,data):
            if Path(path).name=='candidate.json':raise OSError('injected write failure')
            return real(path,data)
        with patch.object(self.b,'_write_new',side_effect=fail_candidate):
            with self.assertRaises(OSError):self.run_model()
        self.assertTrue((self.dest/'STAGING_INCOMPLETE').exists())
        before={p.name:p.read_bytes() for p in self.dest.iterdir()}
        with self.assertRaisesRegex(math.Refused,'INCOMPLETE'):self.b.verify_bundle(self.dest,'0'*64)
        with self.assertRaises(math.Refused):self.run_model()
        self.assertEqual(before,{p.name:p.read_bytes() for p in self.dest.iterdir()})

    def test_unlisted_output_and_nested_directory_refused(self):
        report=self.run_model()
        (self.dest/'unexpected.py').write_bytes(b'# not admitted')
        with self.assertRaisesRegex(math.Refused,'FILE_SET'):self.b.verify_bundle(self.dest,report['receipt_sha256'])
        (self.dest/'unexpected.py').unlink();(self.dest/'private').mkdir()
        with self.assertRaisesRegex(math.Refused,'FILE_SET'):self.b.verify_bundle(self.dest,report['receipt_sha256'])

    def test_relative_destination_and_missing_parent_refused(self):
        for dest in (Path('relative-output'),self.root/'missing'/'out'):
            with self.subTest(dest=str(dest)),self.assertRaises(math.Refused):
                self.b.run_experiment(self.source,self.pin,dest,reviewed_data=True)

    def test_symlinked_dataset_and_output_parent_refused(self):
        alias=self.root/'alias.json'
        try:alias.symlink_to(self.source)
        except (NotImplementedError,OSError):self.skipTest('symlink permission absent')
        with self.assertRaises(math.Refused):self.b.run_experiment(alias,self.pin,self.dest,reviewed_data=True)
        parent=self.root/'alias-dir';parent.symlink_to(self.root,target_is_directory=True)
        with self.assertRaises(math.Refused):self.b.run_experiment(self.source,self.pin,parent/'run',reviewed_data=True)

    def test_hardlinked_input_refused(self):
        alias=self.root/'hardlink.json'
        try:os.link(self.source,alias)
        except OSError:self.skipTest('hardlinks unavailable')
        with self.assertRaises(math.Refused):self.run_model()

    def test_symlinked_receipt_and_checkpoint_refused(self):
        report=self.run_model();original=(self.dest/'candidate.json').read_bytes()
        outside=self.root/'outside';outside.write_bytes(original)
        (self.dest/'candidate.json').unlink()
        try:(self.dest/'candidate.json').symlink_to(outside)
        except OSError:self.skipTest('symlink permission absent')
        with self.assertRaises(math.Refused):self.b.verify_bundle(self.dest,report['receipt_sha256'])

    def test_stored_config_and_dataset_tampering_refused(self):
        report=self.run_model();data=(self.dest/'dataset.json').read_bytes()
        (self.dest/'dataset.json').write_bytes(data+b' ')
        with self.assertRaises(math.Refused):self.b.verify_bundle(self.dest,report['receipt_sha256'])

    def test_identical_input_bundles_are_byte_identical_in_different_folders(self):
        one=self.run_model();second=self.root/'another'
        two=self.b.run_experiment(self.source,self.pin,second,reviewed_data=True)
        self.assertEqual(one['receipt_sha256'],two['receipt_sha256'])
        for p in self.dest.iterdir():self.assertEqual(p.read_bytes(),(second/p.name).read_bytes())

    def test_runtime_source_pin_change_refused(self):
        report=self.run_model()
        with patch.object(self.b,'runtime_pins',return_value={'math':'0'*64,'bundle':'1'*64}):
            with self.assertRaisesRegex(math.Refused,'RUNTIME'):self.b.verify_bundle(self.dest,report['receipt_sha256'])

    def test_final_data_never_written_when_input_violates_hold(self):
        d=example();d['rows'][-1]['target']='99';raw=math.canonical_json(d)
        self.source.write_bytes(raw)
        with self.assertRaisesRegex(math.Refused,'FINAL'):
            self.b.run_experiment(self.source,math.digest(raw),self.dest,reviewed_data=True)
        self.assertFalse(self.dest.exists())

if __name__=='__main__':unittest.main()

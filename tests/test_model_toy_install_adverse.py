"""Adverse filesystem/source-lifetime tests for the opt-in source-only stager."""
from __future__ import annotations
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from muse_presets import model_toy_bundle as bundle, model_toy_math as math
from muse_presets import model_toy_install as install, model_toy_sourcekit as kit

class InstallAdverseTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='r61-adverse-')
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.dest=self.root/'extension'

    def stage(self):return install.stage_extension(self.dest,include_toy_training=True)

    def test_changed_source_before_completion_stays_incomplete(self):
        actual=kit._members(); changed=dict(actual);changed['START_HERE.md']+=b'changed'
        with patch.object(kit,'_members',side_effect=[actual,actual,changed]):
            with self.assertRaisesRegex(math.Refused,'SOURCE_CHANGED'):
                self.stage()
        self.assertTrue((self.dest/install.MARKER).is_file())
        self.assertTrue((self.dest/install.RECEIPT).is_file())
        with self.assertRaises(math.Refused):self.stage()

    def test_changed_source_after_readback_restores_incomplete_marker(self):
        actual=kit._members(); changed=dict(actual);changed['START_HERE.md']+=b'changed'
        with patch.object(kit,'_members',side_effect=[actual,actual,actual,changed]):
            with self.assertRaisesRegex(math.Refused,'SOURCE_CHANGED'):
                self.stage()
        self.assertEqual((self.dest/install.MARKER).read_bytes(),install.MARKER_BYTES)

    def test_initial_marker_write_failure_preserves_owned_directory_and_hold(self):
        writer=bundle._write_new;n=[0]
        def fail_once(path,raw):
            n[0]+=1
            if n[0]==1:raise OSError('synthetic initial disk failure')
            return writer(path,raw)
        with patch.object(bundle,'_write_new',side_effect=fail_once):
            with self.assertRaises(OSError):self.stage()
        self.assertEqual((self.dest/install.MARKER).read_bytes(),install.MARKER_BYTES)
        self.assertFalse((self.dest/'runtime').exists())

    def test_changed_written_source_is_caught_before_completion(self):
        writer=bundle._write_new
        def corrupt(path,raw):
            return writer(path,raw+b'\n' if path.name=='model_toy_math.py' else raw)
        with patch.object(bundle,'_write_new',side_effect=corrupt):
            with self.assertRaisesRegex(math.Refused,'DRIFT'):
                self.stage()
        self.assertTrue((self.dest/install.MARKER).is_file())

    def test_changed_inspector_source_rejected_without_file_mutation(self):
        report=self.stage(); actual=kit._members(); changed=dict(actual)
        changed['START_HERE.md']+=b'changed'
        before={p.relative_to(self.dest).as_posix():p.read_bytes() for p in self.dest.rglob('*') if p.is_file()}
        with patch.object(kit,'_members',side_effect=[actual,changed]):
            with self.assertRaisesRegex(math.Refused,'SOURCE_CHANGED'):
                install.inspect_extension(self.dest,report['stage_receipt_sha256'])
        after={p.relative_to(self.dest).as_posix():p.read_bytes() for p in self.dest.rglob('*') if p.is_file()}
        self.assertEqual(before,after)

    def test_racing_receipt_after_member_read_is_refused(self):
        report=self.stage(); actual=kit._members();calls=[0]
        def racing():
            calls[0]+=1
            if calls[0]==2:(self.dest/install.RECEIPT).write_bytes(b'{}')
            return actual
        with patch.object(kit,'_members',side_effect=racing):
            with self.assertRaisesRegex(math.Refused,'RECEIPT_CHANGED'):
                install.inspect_extension(self.dest,report['stage_receipt_sha256'])

    def test_malformed_current_canonical_map_creates_no_destination(self):
        for value in (None,[],{}, {'../escape':b'x'},{'/absolute':b'x'},
                      {'runtime/a.py':b'x','runtime/A.py':b'x'},
                      {'INSTALL_RECEIPT.json':b'x'}, {'STAGING_INCOMPLETE':b'x'},
                      {'x':bytearray(b'x')},{'x':b'x'*(kit.MAX_FILE+1)}):
            with self.subTest(value=type(value).__name__):
                with patch.object(kit,'_members',return_value=value):
                    with self.assertRaises(math.Refused):self.stage()
                self.assertFalse(self.dest.exists())

    def test_runtime_fifo_refused_without_blocking(self):
        if not hasattr(os,'mkfifo'):self.skipTest('No FIFO on this OS')
        r=self.stage(); p=self.dest/'runtime/model_toy_math.py';p.unlink();os.mkfifo(p)
        with self.assertRaises(math.Refused):install.inspect_extension(self.dest,r['stage_receipt_sha256'])

    def test_incomplete_marker_alone_refuses_success(self):
        self.dest.mkdir();(self.dest/install.MARKER).write_bytes(install.MARKER_BYTES)
        with self.assertRaisesRegex(math.Refused,'INCOMPLETE_STAGE'):
            install.inspect_extension(self.dest,'a'*64)

    def test_existing_owner_file_is_not_a_stage_directory(self):
        self.dest.write_bytes(b'OWNER_DATA')
        with self.assertRaises(math.Refused):self.stage()
        self.assertEqual(self.dest.read_bytes(),b'OWNER_DATA')

    def test_missing_parent_refused_without_creation(self):
        target=self.root/'absent'/'child'
        with self.assertRaises(math.Refused):install.stage_extension(target,include_toy_training=True)
        self.assertFalse(target.parent.exists())

    def test_five_process_contenders_exactly_one_stage_and_no_overwrite(self):
        env=dict(os.environ,PYTHONPATH=str(Path(__file__).resolve().parents[1]/'src'),
                 PYTHONDONTWRITEBYTECODE='1')
        args=[sys.executable,'-B','-m','muse_presets.model_toy_install',
              'stage','--to',str(self.dest),'--include-toy-training']
        children=[subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                  env=env,text=True) for _ in range(5)]
        outputs=[]
        try:
            for child in children:
                out,err=child.communicate(timeout=30)
                outputs.append((child.returncode,json.loads(out),err))
        finally:
            for child in children:
                if child.poll() is None:
                    child.terminate();child.communicate(timeout=5)
        winners=[row for row in outputs if row[0]==0]
        self.assertEqual(len(winners),1,outputs)
        self.assertEqual(sum(row[0]==2 for row in outputs),4,outputs)
        for code,reply,err in outputs:
            self.assertEqual(err,'')
            self.assertEqual(reply['status'],'SOURCE_ONLY_TOY_EXTENSION_STAGED' if code==0 else 'REFUSED')
        pin=winners[0][1]['stage_receipt_sha256']
        self.assertEqual(install.inspect_extension(self.dest,pin)['status'],
                         'LOCAL_TOY_EXTENSION_STAGE_MATCH')

if __name__=='__main__':unittest.main()

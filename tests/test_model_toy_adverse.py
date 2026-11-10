"""Boundary/fault and independent-arithmetic tests; no network or user data."""
import copy
from decimal import Decimal, getcontext
from fractions import Fraction
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from muse_presets import model_toy_math as m, model_toy_bundle as b
from test_model_toy_math import example


class NumericalOracleTests(unittest.TestCase):
    def test_valid_extreme_dev_mse_is_not_mistaken_for_weight_limit(self):
        d=example()
        for row in d['rows']:
            if row['split']=='train':row['target']='1000'
            if row['split']=='dev':row['target']='-1000'
        result=m.fit_experiment(d)
        self.assertEqual(result['evaluation']['baseline_mse'],'4000000')
        self.assertEqual(result['evaluation']['candidate_mse'],'4000000')
        self.assertTrue(result['evaluation']['fallback_to_baseline'])

    def test_public_validator_does_not_round_illegal_features_into_range(self):
        d=example();d['rows'][0]['features']=['1.000000000001']
        old=getcontext().prec
        try:
            getcontext().prec=3
            with self.assertRaises(m.Refused):m.validate_dataset(d)
        finally:getcontext().prec=old

    def test_fraction_oracle_matches_five_independent_gradient_steps(self):
        d=example();train=[r for r in d['rows'] if r['split']=='train']
        data=[(Fraction(r['features'][0]),Fraction(r['target'])) for r in train]
        w=Fraction(0);bias=sum(y for x,y in data)/len(data);rate=Fraction(1,20)
        for _ in range(5):
            error=[(bias+w*x-y,x) for x,y in data]
            w-=rate*2*sum(e*x for e,x in error)/len(error)
            bias-=rate*2*sum(e for e,x in error)/len(error)
        trained=m.fit_experiment(d,steps=5)['candidate']
        dw=Decimal(w.numerator)/Decimal(w.denominator)
        db=Decimal(bias.numerator)/Decimal(bias.denominator)
        self.assertLess(abs(Decimal(trained['weights'][0])-dw),Decimal('1e-24'))
        self.assertLess(abs(Decimal(trained['bias'])-db),Decimal('1e-24'))

    def test_gradient_reduces_train_loss_for_40_seeded_datasets(self):
        rng=random.Random(67321)
        for trial in range(40):
            d=example()
            for row in d['rows']:
                if row['split']!='final':
                    x=rng.randint(-100,100)/100
                    row['features']=[f'{x:.2f}']
                    row['target']=str(rng.randint(-1000,1000))
            r=m.fit_experiment(d,steps=32)['evaluation']
            with self.subTest(trial=trial):
                self.assertLessEqual(Decimal(r['train_mse_after']),Decimal(r['train_mse_before'])+Decimal('1e-20'))
                self.assertEqual(r['final_status'],'HELD_UNEVALUATED')

    def test_maximum_rows_dimensions_and_steps_are_bounded_real_work(self):
        rows=[]
        for split,count in (('train',64),('dev',48),('final',16)):
            for i in range(count):
                rows.append({'id':f'{split}-{i}','family':f'{split}-group-{i}','split':split,
                    'features':None if split=='final' else ['0.5','-0.5','0.25','-0.25'],
                    'target':None if split=='final' else '1'})
        d={'schema':m.SCHEMA,'dataset_id':'max-fixture','data_kind':'synthetic','dimensions':4,'rows':rows}
        r=m.fit_experiment(d,steps=128,learning_rate='0.05')
        self.assertEqual(r['candidate']['optimizer_steps'],128)
        self.assertEqual(r['evaluation']['train_count'],64)
        self.assertEqual(r['evaluation']['dev_count'],48)
        self.assertEqual(r['evaluation']['final_count'],16)
        self.assertEqual(r['evaluation']['candidate_mse'],'0')

    def test_240_invalid_feature_variants_never_accepted(self):
        values=[None,True,False,0,1,0.5,[],{},'NaN','Infinity','-Infinity','1e0',
                ' 1','1 ','+1','00','01','1.000000000001','-1.000000000001','2',
                '0.'+'0'*30+'1','9'*100,'[','\x00']
        for index in range(240):
            d=example();d['rows'][index%5]['features']=[values[index%len(values)]]
            with self.subTest(index=index),self.assertRaises(m.Refused):m.fit_experiment(d)

    def test_baseline_mean_uses_train_not_development(self):
        d=example()
        for row in d['rows']:
            if row['split']=='dev':row['target']='1000'
        r=m.fit_experiment(d)
        self.assertEqual(r['baseline']['bias'],'1')

    def test_same_sample_order_permutation_has_same_parameters(self):
        d=example();one=m.fit_experiment(d)
        random.Random(11).shuffle(d['rows']);two=m.fit_experiment(d)
        self.assertEqual(one['candidate']['weights'],two['candidate']['weights'])
        self.assertEqual(one['candidate']['bias'],two['candidate']['bias'])
        self.assertEqual(one['evaluation']['candidate_mse'],two['evaluation']['candidate_mse'])

    def test_unsupported_training_kind_never_implies_production_model(self):
        d=example();d['data_kind']='pretrained-llm'
        with self.assertRaises(m.Refused):m.fit_experiment(d)


class ArtifactAdverseTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='r60-fault-')
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve()
        self.dataset=self.root/'dataset.json';self.raw=m.canonical_json(example())
        self.dataset.write_bytes(self.raw);self.pin=m.digest(self.raw);self.run=self.root/'run'

    def run_once(self):return b.run_experiment(self.dataset,self.pin,self.run,reviewed_data=True)

    def test_rollback_rechecks_baseline_bytes_after_bundle_verification(self):
        report=self.run_once();real=b.verify_bundle
        def verify_then_change(root,pin):
            result=real(root,pin)
            baseline=m.strict_json((root/'baseline.json').read_bytes());baseline['bias']='999'
            (root/'baseline.json').write_bytes(m.canonical_json(baseline))
            return result
        output=self.root/'rollback.json'
        with patch.object(b,'verify_bundle',side_effect=verify_then_change):
            with self.assertRaisesRegex(m.Refused,'BASELINE'):
                b.restore_baseline(self.run,report['receipt_sha256'],output)
        self.assertFalse(output.exists())

    def test_rollback_cannot_add_files_to_immutable_bundle(self):
        report=self.run_once()
        with self.assertRaises(m.Refused):b.restore_baseline(self.run,report['receipt_sha256'],self.run/'rollback.json')
        self.assertEqual(len(list(self.run.iterdir())),6)

    def test_rehashed_false_step_count_does_not_pass_recomputation(self):
        report=self.run_once()
        cp=m.strict_json((self.run/'candidate.json').read_bytes());cp['optimizer_steps']=2
        (self.run/'candidate.json').write_bytes(m.canonical_json(cp))
        man=m.strict_json((self.run/'MANIFEST.json').read_bytes())
        man['files_sha256']['candidate.json']=m.digest((self.run/'candidate.json').read_bytes())
        raw=m.canonical_json(man);(self.run/'MANIFEST.json').write_bytes(raw)
        with self.assertRaisesRegex(m.Refused,'RECOMPUTATION'):b.verify_bundle(self.run,m.digest(raw))

    def test_rehashed_fake_perfect_accuracy_does_not_pass(self):
        self.run_once()
        ev=m.strict_json((self.run/'evaluation.json').read_bytes());ev['candidate_mse']='0'
        (self.run/'evaluation.json').write_bytes(m.canonical_json(ev))
        man=m.strict_json((self.run/'MANIFEST.json').read_bytes())
        man['files_sha256']['evaluation.json']=m.digest((self.run/'evaluation.json').read_bytes())
        raw=m.canonical_json(man);(self.run/'MANIFEST.json').write_bytes(raw)
        with self.assertRaises(m.Refused):b.verify_bundle(self.run,m.digest(raw))

    def test_process_contention_on_same_output_has_one_winner(self):
        runtime=Path(b.__file__).resolve()
        args=[sys.executable,'-I','-B',str(runtime),'run','--dataset',str(self.dataset),
              '--dataset-sha256',self.pin,'--to',str(self.run),'--reviewed-data']
        children=[subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE) for _ in range(5)]
        result=[]
        try:
            for proc in children:
                out,err=proc.communicate(timeout=15);result.append((proc.returncode,json.loads(out),err))
        finally:
            for proc in children:
                if proc.poll() is None:proc.terminate();proc.communicate(timeout=5)
        winners=[r for r in result if r[0]==0]
        self.assertEqual(len(winners),1,result)
        self.assertTrue(all(r[0] in (0,2) for r in result),result)
        self.assertEqual(b.verify_bundle(self.run,winners[0][1]['receipt_sha256'])['status'],'LOCAL_TOY_BUNDLE_RECOMPUTED')

    def test_failure_before_manifest_keeps_marker_not_false_complete(self):
        writer=b._write_new
        def fail_manifest(path,data):
            if path.name=='MANIFEST.json':raise OSError('simulated disk failure')
            return writer(path,data)
        with patch.object(b,'_write_new',side_effect=fail_manifest):
            with self.assertRaises(OSError):self.run_once()
        self.assertTrue((self.run/'STAGING_INCOMPLETE').exists())
        self.assertFalse((self.run/'MANIFEST.json').exists())
        with self.assertRaisesRegex(m.Refused,'INCOMPLETE'):b.verify_bundle(self.run,'0'*64)

    def test_manifest_duplicate_key_refused(self):
        self.run_once()
        raw=(self.run/'MANIFEST.json').read_bytes()
        changed=b'{"schema":"forged",'+raw[1:]
        (self.run/'MANIFEST.json').write_bytes(changed)
        with self.assertRaisesRegex(m.Refused,'DUPLICATE'):b.verify_bundle(self.run,m.digest(changed))

    def test_oversized_regular_input_refused_without_outputs(self):
        self.dataset.write_bytes(b' '*(65536+1));pin=m.digest(self.dataset.read_bytes())
        with self.assertRaises(m.Refused):b.run_experiment(self.dataset,pin,self.run,reviewed_data=True)
        self.assertFalse(self.run.exists())

    @unittest.skipUnless(hasattr(os,'mkfifo'),'POSIX FIFO test only')
    def test_fifo_is_refused_without_blocking(self):
        fifo=self.root/'pipe';os.mkfifo(fifo)
        with self.assertRaises(m.Refused):b.run_experiment(fifo,'0'*64,self.run,reviewed_data=True)
        self.assertFalse(self.run.exists())

    def test_manifest_native_flag_wrong_type_zero_is_not_false_authority(self):
        self.run_once();man=m.strict_json((self.run/'MANIFEST.json').read_bytes())
        man['native_muse_invoked']=0;raw=m.canonical_json(man);(self.run/'MANIFEST.json').write_bytes(raw)
        with self.assertRaises(m.Refused):b.verify_bundle(self.run,m.digest(raw))

if __name__=='__main__':unittest.main()

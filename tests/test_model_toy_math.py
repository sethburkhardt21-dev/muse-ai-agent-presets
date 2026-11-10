"""Behavior-first tests: genuine bounded optimization, never supplied predictions."""
import copy
import importlib
import json
import unittest
from decimal import Decimal, getcontext, ROUND_UP


def example():
    rows=[]
    for i,x in enumerate(('-1','-0.5','0','0.5','1')):
        rows.append({'id':f'train-{i}', 'family':f'train-family-{i}', 'split':'train',
                     'features':[x], 'target':str(Decimal(x)*2+1)})
    for i,x in enumerate(('-0.75','0.25','0.75')):
        rows.append({'id':f'dev-{i}','family':f'dev-family-{i}','split':'dev',
                     'features':[x], 'target':str(Decimal(x)*2+1)})
    rows.append({'id':'final-0','family':'final-family','split':'final',
                 'features':None,'target':None})
    return {'schema':'r60/toy-linear-dataset-v1','dataset_id':'linear-fixture',
            'data_kind':'synthetic','dimensions':1,'rows':rows}


class ToyMathTests(unittest.TestCase):
    def setUp(self):
        try:
            self.m=importlib.import_module('muse_presets.model_toy_math')
        except ModuleNotFoundError:
            self.fail('T21 has no bounded toy optimizer: real parameter learning is missing')

    def refused(self,doc,code=None,**kw):
        with self.assertRaises(self.m.Refused) as err:
            self.m.fit_experiment(doc,**kw)
        if code:self.assertIn(code,str(err.exception))

    def test_real_learning_beats_mean_baseline_and_keeps_final_held(self):
        doc=example(); before=copy.deepcopy(doc)
        result=self.m.fit_experiment(doc,steps=64,learning_rate='0.05')
        b,c,e=result['baseline'],result['candidate'],result['evaluation']
        self.assertEqual(doc,before)
        self.assertEqual(c['optimizer_steps'],64)
        self.assertEqual(b['optimizer_steps'],0)
        self.assertGreater(Decimal(c['weights'][0]),Decimal('1.9'))
        self.assertLess(Decimal(e['candidate_mse']),Decimal(e['baseline_mse'])/100)
        self.assertEqual(e['selected_checkpoint'],'candidate')
        self.assertEqual(e['final_status'],'HELD_UNEVALUATED')
        self.assertFalse(e['promotion_authorized'])
        self.assertFalse(e['native_muse_invoked'])
        self.assertFalse(e['external_effect_authorized'])
        self.assertEqual(c['parent_sha256'],self.m.digest(self.m.canonical_json(b)))

    def test_train_only_weights_do_not_change_when_dev_labels_change(self):
        d=example(); x=self.m.fit_experiment(d)
        for r in d['rows']:
            if r['split']=='dev':r['target']='-50'
        y=self.m.fit_experiment(d)
        self.assertEqual(x['candidate']['weights'],y['candidate']['weights'])
        self.assertEqual(x['candidate']['bias'],y['candidate']['bias'])
        self.assertNotEqual(x['evaluation']['candidate_mse'],y['evaluation']['candidate_mse'])

    def test_worse_development_result_keeps_baseline(self):
        d=example()
        for r in d['rows']:
            if r['split']=='dev':r['target']='1'
        out=self.m.fit_experiment(d)['evaluation']
        self.assertEqual(out['baseline_mse'],'0')
        self.assertGreater(Decimal(out['candidate_mse']),0)
        self.assertTrue(out['fallback_to_baseline'])
        self.assertEqual(out['selected_checkpoint'],'baseline')

    def test_equal_development_result_keeps_baseline(self):
        d=example()
        for r in d['rows']:
            if r['split']!='final':r['target']='1'
        out=self.m.fit_experiment(d)
        self.assertEqual(out['candidate']['weights'],['0'])
        self.assertEqual(out['evaluation']['selected_checkpoint'],'baseline')

    def test_known_one_step_gradient_is_actual_arithmetic(self):
        result=self.m.fit_experiment(example(),steps=1,learning_rate='0.05')
        self.assertEqual(result['candidate']['weights'],['0.1'])
        self.assertEqual(result['candidate']['bias'],'1')

    def test_same_input_is_byte_deterministic(self):
        one=self.m.canonical_json(self.m.fit_experiment(example()))
        two=self.m.canonical_json(self.m.fit_experiment(example()))
        self.assertEqual(one,two)

    def test_decimal_global_context_does_not_change_results(self):
        before=self.m.fit_experiment(example())
        ctx=getcontext().copy()
        try:
            getcontext().prec=5;getcontext().rounding=ROUND_UP
            after=self.m.fit_experiment(example())
        finally:
            getcontext().prec=ctx.prec;getcontext().rounding=ctx.rounding
        self.assertEqual(before,after)

    def test_multidimensional_actual_prediction(self):
        d=example();d['dimensions']=2
        for r in d['rows']:
            if r['split']!='final':r['features'].append('0')
        out=self.m.fit_experiment(d)
        self.assertEqual(len(out['candidate']['weights']),2)
        self.assertEqual(out['candidate']['weights'][1],'0')
        pred=Decimal(self.m.predict(out['candidate'],['1','0']))
        self.assertLess(abs(pred-Decimal('3')),Decimal('0.1'))

    def test_final_target_exposure_is_refused(self):
        d=example();d['rows'][-1]['target']='3';self.refused(d,'FINAL')

    def test_final_feature_exposure_is_refused(self):
        d=example();d['rows'][-1]['features']=['1'];self.refused(d,'FINAL')

    def test_duplicate_sample_is_refused(self):
        d=example();d['rows'][5]['id']=d['rows'][0]['id'];self.refused(d,'ID')

    def test_family_cross_partition_is_refused(self):
        d=example();d['rows'][5]['family']=d['rows'][0]['family'];self.refused(d,'FAMILY')

    def test_missing_each_partition_is_refused(self):
        for split in ('train','dev','final'):
            d=example();d['rows']=[r for r in d['rows'] if r['split']!=split]
            with self.subTest(split=split):self.refused(d,'PARTITION')

    def test_extra_authority_and_prediction_fields_are_refused(self):
        for extra in ('trained','host_authenticated','promotion_authorized','candidate_predictions'):
            d=example();d[extra]=True
            with self.subTest(extra=extra):self.refused(d,'FIELDS')

    def test_row_extra_field_is_refused(self):
        d=example();d['rows'][0]['candidate']='precomputed';self.refused(d,'ROW_FIELDS')

    def test_invalid_dimension_bounds_and_types(self):
        for value in (0,5,True,'1',1.0,None):
            d=example();d['dimensions']=value
            with self.subTest(value=value):self.refused(d,'DIMENSION')

    def test_step_count_is_bounded_and_not_bool(self):
        for value in (0,129,-1,True,1.5,'64'):
            with self.subTest(value=value):self.refused(example(),'STEPS',steps=value)

    def test_learning_rate_is_bounded_decimal_string(self):
        for value in ('0','-0.1','1','NaN','Infinity','1e-3','0.0000000000001',0.05,True):
            with self.subTest(value=value):self.refused(example(),learning_rate=value)

    def test_invalid_numeric_fields_and_float_types(self):
        for value in ('NaN','inf','1e999','2','0.1234567890123','--1',True,0.1,None,{}):
            d=example();d['rows'][0]['features']=[value]
            with self.subTest(value=value):self.refused(d)

    def test_wrong_feature_dimension_refused(self):
        for vec in ([],['0','1'],None,'1'):
            d=example();d['rows'][0]['features']=vec
            with self.subTest(vec=vec):self.refused(d)

    def test_target_and_row_limits_refused(self):
        d=example();d['rows'][0]['target']='1001';self.refused(d)
        d=example();d['rows']*=20;self.refused(d,'ROWS')

    def test_invalid_source_id_and_non_synthetic_mode(self):
        for bad in ('../secret','a b','x'*65,''):
            d=example();d['dataset_id']=bad
            with self.subTest(bad=bad):self.refused(d)
        d=example();d['data_kind']='trusted-live-data';self.refused(d)

    def test_strict_json_refuses_duplicates_and_nonfinite(self):
        for raw in (b'{"x":1,"x":2}',b'{"x":NaN}',b'{"x":Infinity}',b'{"x":1.1}',b'[]',b'null',b''):
            with self.subTest(raw=raw),self.assertRaises(self.m.Refused):self.m.strict_json(raw)

    def test_strict_json_size_and_integer_budget(self):
        for raw in (b' '*65537,b'{"n":'+b'1'*5000+b'}',b'['*200+b']'*200):
            with self.subTest(size=len(raw)),self.assertRaises(self.m.Refused):self.m.strict_json(raw)

    def test_bad_checkpoint_schema_or_grant_refused(self):
        cp=self.m.fit_experiment(example())['candidate']
        for key,value in (('native_muse_invoked',True),('weights',['NaN']),('optimizer_steps',True),('parent_sha256','x')):
            bad=copy.deepcopy(cp);bad[key]=value
            with self.subTest(key=key),self.assertRaises(self.m.Refused):self.m.predict(bad,['0'])

    def test_no_final_inference_api(self):
        cp=self.m.fit_experiment(example())['candidate']
        with self.assertRaises(self.m.Refused):self.m.predict(cp,None)

if __name__=='__main__':unittest.main()

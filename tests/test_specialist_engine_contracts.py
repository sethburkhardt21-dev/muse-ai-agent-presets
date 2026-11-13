"""New roles must execute real offline examples, preserve inputs and refuse bad data."""
from __future__ import annotations
import copy
from decimal import localcontext, Inexact
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from examples import verify_role_packages as verify
from examples.specialist_engine_demo import FIXTURES
from muse_presets.specialist_engines import run_fixture
ROOT=Path(__file__).resolve().parents[1]

class SpecialistEngineContracts(unittest.TestCase):
    def test_new_role_skill_packets_pin_the_actual_engine_source(self):
        from muse_presets.role_skills import _build
        import hashlib
        original=(ROOT/'src/muse_presets/specialist_engines.py').read_bytes()
        for role in FIXTURES:
            with self.subTest(role=role):
                files,receipt,frozen=_build(role,None)
                links=json.loads(files['config/local-code-links.json'])
                self.assertTrue(links['source_code_linked'])
                self.assertIn({'path':'src/muse_presets/specialist_engines.py',
                               'sha256':hashlib.sha256(original).hexdigest(),
                               'disposition':'LOCAL_SOURCE_REFERENCE_NOT_REGISTERED'},links['source_files'])
                self.assertFalse(links['native_callable'])

    def test_reliability_independent_of_callers_decimal_precision(self):
        payload={'events':[True,True,False], 'target':'0.99'}
        with localcontext() as ctx:
            ctx.prec=6; one=run_fixture('infrastructure-reliability-engineer',payload)
        with localcontext() as ctx:
            ctx.prec=40; two=run_fixture('infrastructure-reliability-engineer',payload)
        self.assertEqual(one,two)

    def test_reliability_does_not_inherit_callers_inexact_trap(self):
        with localcontext() as ctx:
            ctx.traps[Inexact]=True
            out=run_fixture('infrastructure-reliability-engineer',{'events':[True,True,False],'target':'0.99'})
        self.assertEqual(out['failures'],1)

    def test_unhashable_role_refuses_as_value_error(self):
        with self.assertRaises(ValueError):run_fixture([], {})

    def test_extreme_target_refuses_instead_of_ambient_underflow(self):
        with self.assertRaises(ValueError):
            run_fixture('infrastructure-reliability-engineer',{'events':[True], 'target':'1e-999999'})

    def test_extra_fields_do_not_authorize_effects(self):
        for role,payload in FIXTURES.items():
            with self.subTest(role=role),self.assertRaises(ValueError):
                run_fixture(role,{**payload,'external_effect_authorized':True})

    def test_sources_never_modified(self):
        for role,payload in FIXTURES.items():
            with self.subTest(role=role):
                before=copy.deepcopy(payload);run_fixture(role,payload)
                self.assertEqual(payload,before)

    def test_data_identity_distinguishes_bool_integer_and_string(self):
        result=run_fixture('data-engineering-architect',{'key':'id','rows':[{'id':True},{'id':1},{'id':'1'}]})
        self.assertEqual(result['duplicate_count'],0)

    def test_data_missing_key_refuses(self):
        with self.assertRaisesRegex(ValueError,'MISSING_KEY'):
            run_fixture('data-engineering-architect',{'key':'id','rows':[{'value':1}]})

    def test_nonfinite_json_cells_refuse(self):
        for value in (float('nan'),float('inf'),float('-inf')):
            with self.subTest(value=value),self.assertRaises(ValueError):
                run_fixture('data-engineering-architect',{'key':'id','rows':[{'id':'a','value':value}]})

    def test_workflow_tie_breaking_is_stable_across_input_order(self):
        rows=[{'id':'z','deps':[]},{'id':'a','deps':[]},{'id':'last','deps':['z','a']}]
        one=run_fixture('automation-engineer',{'steps':rows})
        two=run_fixture('automation-engineer',{'steps':list(reversed(rows))})
        self.assertEqual(one,two);self.assertEqual(one['order'],['a','z','last'])

    def test_workflow_missing_dependency_refuses(self):
        with self.assertRaisesRegex(ValueError,'UNKNOWN_OR_SELF_DEPENDENCY'):
            run_fixture('automation-engineer',{'steps':[{'id':'a','deps':['missing']}]})

    def test_workflow_cycle_refuses(self):
        with self.assertRaisesRegex(ValueError,'DEPENDENCY_CYCLE'):
            run_fixture('automation-engineer',{'steps':[{'id':'a','deps':['b']},{'id':'b','deps':['a']}]})

    def test_ui_empty_label_is_finding_not_certification(self):
        x=run_fixture('product-interface-designer',FIXTURES['product-interface-designer'])
        self.assertEqual(x['missing_control_labels'],1);self.assertEqual(x['actual_browser_test'],'NOT_RUN')

    def test_ui_repeated_control_id_refuses(self):
        with self.assertRaisesRegex(ValueError,'DUPLICATE_CONTROL_ID'):
            run_fixture('product-interface-designer',{'screens':[{'id':'home','controls':[{'id':'x','label':'A'},{'id':'x','label':'B'}]}]})

    def test_payload_size_bound(self):
        with self.assertRaisesRegex(ValueError,'INPUT_SIZE_LIMIT'):
            run_fixture('data-engineering-architect',{'key':'id','rows':[{'id':'x','value':'x'*130000}]})

    def test_four_actual_clean_consumer_demos_are_classified(self):
        for role in FIXTURES:
            with self.subTest(role=role),tempfile.TemporaryDirectory() as td:
                out=verify._local_demo(ROOT,role,Path(td))
                self.assertEqual(out['local_demo_grade'],'LOCAL_OFFLINE_FIXTURE_DEMO_PASSED')
                self.assertTrue(out['local_engine_executed'])
                self.assertEqual(out['demo_exit_code'],0)
                self.assertFalse(out['independent_adjudicator_or_live_capture'])

    def test_forged_native_demo_refused(self):
        role='automation-engineer';fake=run_fixture(role,FIXTURES[role]);fake['native_registered']=True
        with patch.object(verify,'_process',return_value=json.dumps(fake)):
            with self.assertRaisesRegex(ValueError,'SPECIALIST_FIXTURE_EVIDENCE_INVALID'):
                verify._local_demo(ROOT,role,ROOT)

    def test_wrong_result_demo_refused(self):
        role='data-engineering-architect';fake=run_fixture(role,FIXTURES[role]);fake['duplicate_count']=0
        with patch.object(verify,'_process',return_value=json.dumps(fake)):
            with self.assertRaisesRegex(ValueError,'SPECIALIST_FIXTURE_EVIDENCE_INVALID'):
                verify._local_demo(ROOT,role,ROOT)

if __name__=='__main__':unittest.main()

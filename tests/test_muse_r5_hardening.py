"""Independent edge oracles and exported-product failure boundaries for R5."""
from pathlib import Path
from tempfile import TemporaryDirectory
import copy
import importlib.util
import io
import json
import os
import subprocess
import sys
import unittest
import zipfile
from muse_presets.specialist_extensions import evaluate

ROOT=Path(__file__).resolve().parents[1]
C=ROOT/'collections/muse-starters-v1'

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result

class BoundaryTests(unittest.TestCase):
    def test_conflicting_batch_preserves_original_row_order(self):
        state=[{'key':k,'version':1,'value':1,'deleted':False} for k in ('B','A')]
        events=[{'key':'A','version':2,'value':v,'deleted':False} for v in (2,3)]
        r=evaluate('incremental-pipeline',{'state':state,'events':events})
        self.assertEqual(r['state'],state)
        self.assertEqual(r['applied_keys'],[])

    def test_exactly_consumed_error_budget_is_exhausted(self):
        r=evaluate('service-objectives',{'good_events':9,'total_events':10,'target':'0.9','window_minutes':60})
        self.assertEqual(r['remaining_bad_events'],'0');self.assertEqual(r['status'],'exhausted')

    def test_selector_strategy_requires_a_string(self):
        candidate={'id':'a','strategy':[],'matches':1,'visible':True,'stable':True,'target_id':'save'}
        with self.assertRaises(ValueError):evaluate('selector-resilience',{'target_id':'save','candidates':[candidate]})

    def test_cyclic_or_nonfinite_json_refused_without_recursion_crash(self):
        cyclic={};cyclic['self']=cyclic
        for value in (cyclic,{'x':float('inf')},{'x':set([1])}):
            with self.subTest(value=type(value)),self.assertRaises(ValueError):
                evaluate('schema-evolution',value)

    def test_capacity_ceil_uses_decimal_boundary(self):
        base={'per_instance_rps':'250','target_utilization':'0.6','instances':1,'reserve_instances':0}
        self.assertEqual(evaluate('capacity-planning',{**base,'demand_rps':'150'})['required_instances'],1)
        self.assertEqual(evaluate('capacity-planning',{**base,'demand_rps':'150.000000001'})['required_instances'],2)

    def test_unknown_query_plan_rows_are_retained(self):
        r=evaluate('query-plan-review',{'details':['future engine format']})
        self.assertEqual(r['unclassified'],['future engine format']);self.assertFalse(r['performance_proven'])

    def test_different_record_types_at_one_version_are_conflicting(self):
        first={'key':'a','version':1,'value':1,'deleted':False}
        second={**first,'value':True}
        r=evaluate('incremental-pipeline',{'state':[],'events':[first,second]})
        self.assertEqual(r['status'],'conflict');self.assertEqual(r['state'],[])

    def test_future_incident_observation_and_naive_timezone_refused(self):
        for at in ('2026-01-01T13:00:00Z','2026-01-01T12:00:00'):
            with self.subTest(at=at),self.assertRaises(ValueError):
                evaluate('incident-triage',{'events':[{'id':'start','at':at,'kind':'start'}],
                    'as_of':'2026-01-01T12:00:00Z'})

class ProductHardeningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.collection=module('r5_hardening_collection',ROOT/'tools/muse_collection.py')
        cls.data=cls.collection.load_collection(C)
        cls.checker=module('r5_hardening_checker',C/'depth/check_outputs.py')

    def test_all_33_new_cases_pass_and_wrong_examples_fail(self):
        cases=[c for c in self.data['depth_cases'] if '-r5-' in c['id']]
        self.assertEqual(len(cases),33)
        for case in cases:
            with self.subTest(case=case['id']):
                self.assertTrue(self.checker.check_case(case,case['reference_output'])['passed'])
                self.assertFalse(self.checker.check_case(case,case['wrong_output'])['passed'])
                changed=copy.deepcopy(case);changed['reference_output']={'forged':'not used'}
                self.assertTrue(self.checker.check_case(changed,case['reference_output'])['passed'])

    def test_calculated_quantity_mutations_fail_not_only_scope_flags(self):
        fields={'schema-evolution':('added',['invented']),
          'incremental-pipeline':('state',[]),'query-plan-review':('table_scans',[]),
          'service-objectives':('burn_rate','999'),'capacity-planning':('required_instances',999),
          'incident-triage':('time_to_resolve_seconds',999),'automation-contract':('blocked_steps',[]),
          'selector-resilience':('selected','wrong'),'effect-reconciliation':('observation','success'),
          'design-token-audit':('pairs',[]),'interaction-state-coverage':('missing_required',[])}
        for skill,(key,bad) in fields.items():
            case=next(c for c in self.data['depth_cases'] if c['id']==skill+'-r5-standard')
            value=copy.deepcopy(case['reference_output']);self.assertNotEqual(value[key],bad)
            value[key]=bad
            with self.subTest(skill=skill):self.assertFalse(self.checker.check_case(case,value)['passed'])

    def test_original_r5_skill_has_no_invented_upstream_comparison_arm(self):
        with self.assertRaises(ValueError):
            self.collection.challenge_files(self.data,'schema-evolution-r5-standard','upstream')

    def test_role_registry_cannot_substitute_another_specialists_tools(self):
        data=copy.deepcopy(self.data)
        next(r for r in data['specialists'] if r['id']=='data-engineer')['skills']=['service-objectives','capacity-planning']
        with self.assertRaises(ValueError):self.collection.validate(data)

    def test_five_workflow_demos_execute_real_bound_tools_and_preserve_unexecuted_handoffs(self):
        self.assertTrue(hasattr(self.collection,'workflow_demo'))
        workflows=[w for w in self.data['workflows'] if 'tool_bindings' in w]
        self.assertEqual(len(workflows),5)
        for workflow in workflows:
            result=self.collection.workflow_demo(self.data,workflow['id'])
            self.assertEqual([r['skill_id'] for r in result['results']],
                             [b['skill_id'] for b in workflow['tool_bindings']])
            self.assertGreaterEqual(len(result['results']),2)
            self.assertFalse(result['full_workflow_executed'])
            self.assertFalse(result['external_actions_performed'])
            self.assertTrue(result['unexecuted_skills'])
            text=self.collection.render_workflow(workflow,{s['id']:s for s in self.data['skills']})
            self.assertIn('muse_presets.specialist_extensions.evaluate',text)

    def unpack(self,temp):
        files=self.collection.specialist_kit_files(self.data,'data-engineer')
        with zipfile.ZipFile(io.BytesIO(self.collection.build_file_map_bytes(files))) as z:z.extractall(temp)

    def run_kit(self,temp,*args):
        env={k:v for k,v in os.environ.items() if k not in ('PYTHONPATH','PYTHONHOME')}
        return subprocess.run([sys.executable,'-B','run.py',*args],cwd=temp,env=env,capture_output=True,text=True,timeout=15)

    def test_modified_tool_bytes_refused_before_import(self):
        with TemporaryDirectory() as temp:
            self.unpack(temp)
            target=Path(temp)/'specialist_extensions/data.py'
            target.write_text(target.read_text('utf-8')+'\nraise RuntimeError("UNREVIEWED_MODULE_EXECUTED")\n',encoding='utf-8')
            p=self.run_kit(temp,'--demo')
            self.assertEqual(p.returncode,2);self.assertIn('KIT_MEMBER_CHANGED',p.stderr)
            self.assertNotIn('UNREVIEWED_MODULE_EXECUTED',p.stderr)

    def test_custom_input_duplicate_keys_and_wrong_role_tool_refused(self):
        with TemporaryDirectory() as temp:
            self.unpack(temp);path=Path(temp)/'input.json'
            path.write_text('{"current": [], "current": [], "proposed": [], "row_count": 0}',encoding='utf-8')
            p=self.run_kit(temp,'--tool','schema-evolution','--input','input.json')
            self.assertEqual(p.returncode,2);self.assertIn('DUPLICATE_JSON_KEY',p.stderr)
            path.write_text('{}',encoding='utf-8')
            p=self.run_kit(temp,'--tool','service-objectives','--input','input.json')
            self.assertEqual(p.returncode,2);self.assertIn('TOOL_OUTSIDE_SPECIALIST_SCOPE',p.stderr)

if __name__=='__main__':unittest.main()

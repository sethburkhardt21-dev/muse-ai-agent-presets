"""Observable R5 tool outcomes; no model or production-provider claims."""
from __future__ import annotations
import copy
import importlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class SpecialistToolTests(unittest.TestCase):
    def run_tool(self, skill, inputs):
        self.assertTrue((ROOT/'src/muse_presets/specialist_extensions/__init__.py').is_file(),
                        'Four executable specialist extensions have not been implemented')
        return importlib.import_module('muse_presets.specialist_extensions').evaluate(skill, inputs)

    def test_schema_additive_nullable_column_is_compatible(self):
        col={'name':'id','type':'integer','nullable':False}
        result=self.run_tool('schema-evolution',{'current':[col],
            'proposed':[col,{'name':'note','type':'text','nullable':True}],'row_count':100})
        self.assertEqual(result['status'],'compatible')
        self.assertEqual(result['added'],['note'])
        self.assertEqual(result['backfill_required'],[])
        self.assertFalse(result['database_modified'])

    def test_schema_nonnullable_addition_and_removed_columns_require_migration(self):
        result=self.run_tool('schema-evolution',{'current':[{'name':'old','type':'text','nullable':True}],
            'proposed':[{'name':'new','type':'integer','nullable':False}],'row_count':4})
        self.assertEqual(result['status'],'migration_required')
        self.assertEqual(result['backfill_required'],['new'])
        self.assertEqual(result['removed'],['old'])

    def test_schema_empty_table_needs_no_backfill(self):
        r=self.run_tool('schema-evolution',{'current':[],
            'proposed':[{'name':'id','type':'integer','nullable':False}],'row_count':0})
        self.assertEqual(r['backfill_required'],[])
        self.assertEqual(r['status'],'compatible')

    def test_incremental_late_event_cannot_resurrect_deleted_row(self):
        tomb={'key':'A','version':3,'value':None,'deleted':True}
        event={'key':'A','version':2,'value':10,'deleted':False}
        data={'state':[tomb],'events':[event,tomb]}; before=copy.deepcopy(data)
        r=self.run_tool('incremental-pipeline',data)
        self.assertEqual(r['state'],[tomb]); self.assertEqual(data,before)
        self.assertEqual(r['stale_events'],1); self.assertEqual(r['duplicate_events'],1)
        self.assertEqual(r['status'],'applied')

    def test_incremental_conflict_is_atomic(self):
        old={'key':'A','version':1,'value':10,'deleted':False}
        new={'key':'A','version':2,'value':20,'deleted':False}
        conflict={**new,'value':21}
        r=self.run_tool('incremental-pipeline',{'state':[old],'events':[new,conflict]})
        self.assertEqual(r['status'],'conflict'); self.assertEqual(r['state'],[old])
        self.assertEqual(r['conflicting_keys'],['A'])

    def test_incremental_event_order_is_irrelevant(self):
        events=[{'key':'A','version':v,'value':v*2,'deleted':False} for v in [3,1,2]]
        first=self.run_tool('incremental-pipeline',{'state':[],'events':events})
        second=self.run_tool('incremental-pipeline',{'state':[],'events':events[::-1]})
        self.assertEqual(first,second); self.assertEqual(first['state'][0]['version'],3)

    def test_sqlite_plan_distinguishes_search_index_scan_and_table_scan(self):
        r=self.run_tool('query-plan-review',{'details':['SCAN users',
            'SEARCH orders USING INDEX order_id (id=?)','SCAN tags USING COVERING INDEX tag_name',
            'USE TEMP B-TREE FOR ORDER BY']})
        self.assertEqual(r['table_scans'],['SCAN users'])
        self.assertEqual(len(r['index_scans']),1); self.assertEqual(len(r['searches']),1)
        self.assertEqual(len(r['temporary_sorts']),1); self.assertFalse(r['performance_proven'])

    def test_slo_budget_and_burn_rate_are_calculated_from_event_counts(self):
        r=self.run_tool('service-objectives',{'good_events':998,'total_events':1000,
            'target':'0.999','window_minutes':60})
        self.assertEqual(r['allowed_bad_events'],'1')
        self.assertEqual(r['remaining_bad_events'],'-1'); self.assertEqual(r['burn_rate'],'2')
        self.assertEqual(r['status'],'exhausted')

    def test_slo_zero_traffic_is_unknown_not_perfect(self):
        r=self.run_tool('service-objectives',{'good_events':0,'total_events':0,
            'target':'0.99','window_minutes':60})
        self.assertIsNone(r['sli']); self.assertIsNone(r['burn_rate'])
        self.assertEqual(r['status'],'no_traffic')

    def test_capacity_includes_reserve_and_never_claims_scaling(self):
        r=self.run_tool('capacity-planning',{'demand_rps':'900','per_instance_rps':'250',
            'target_utilization':'0.6','instances':4,'reserve_instances':1})
        self.assertEqual(r['required_instances'],7); self.assertEqual(r['additional_instances'],3)
        self.assertFalse(r['scale_actions_performed'])

    def test_incident_orders_actual_offsets_and_reports_single_incident_durations(self):
        events=[{'id':'resolved','at':'2026-01-01T12:20:00Z','kind':'resolved'},
                {'id':'start','at':'2026-01-01T07:00:00-05:00','kind':'start'},
                {'id':'mitigated','at':'2026-01-01T12:05:00Z','kind':'mitigation'}]
        r=self.run_tool('incident-triage',{'events':events,'as_of':'2026-01-01T12:30:00Z'})
        self.assertEqual(r['event_order'],['start','mitigated','resolved'])
        self.assertEqual(r['time_to_mitigate_seconds'],300)
        self.assertEqual(r['time_to_resolve_seconds'],1200)
        self.assertEqual(r['status'],'resolved')

    def test_incident_unresolved_is_not_marked_resolved(self):
        r=self.run_tool('incident-triage',{'events':[{'id':'s','at':'2026-01-01T12:00:00Z','kind':'start'}],
            'as_of':'2026-01-01T12:10:00Z'})
        self.assertIsNone(r['time_to_resolve_seconds']); self.assertEqual(r['status'],'open')

    def plan(self):
        return {'allowed_targets':['demo'], 'steps':[
            {'id':'read','depends_on':[],'kind':'read','target':'demo','approval':False,'idempotency_key':None},
            {'id':'send','depends_on':['read'],'kind':'send','target':'demo','approval':False,'idempotency_key':'once'}]}

    def test_automation_contract_reports_missing_approval_without_dispatch(self):
        r=self.run_tool('automation-contract',self.plan())
        self.assertEqual(r['order'],['read','send'])
        self.assertEqual(r['blocked_steps'],[{'id':'send','reasons':['approval_missing']}])
        self.assertFalse(r['execution_authorized']); self.assertFalse(r['external_actions_performed'])

    def test_automation_declared_approval_still_does_not_grant_authority(self):
        p=self.plan();p['steps'][1]['approval']=True
        r=self.run_tool('automation-contract',p)
        self.assertEqual(r['review'],'ready_for_host_review'); self.assertFalse(r['execution_authorized'])

    def test_automation_cycle_refused(self):
        p=self.plan();p['steps'][0]['depends_on']=['send']
        with self.assertRaises(ValueError):self.run_tool('automation-contract',p)

    def test_selector_ambiguity_and_wrong_target_do_not_select(self):
        r=self.run_tool('selector-resilience',{'target_id':'submit','candidates':[
            {'id':'a','strategy':'role','matches':2,'visible':True,'stable':True,'target_id':'submit'},
            {'id':'b','strategy':'testid','matches':1,'visible':True,'stable':True,'target_id':'delete'}]})
        self.assertIsNone(r['selected']); self.assertFalse(r['browser_action_performed'])

    def test_selector_unique_visible_bound_target_selected(self):
        c={'id':'a','strategy':'role','matches':1,'visible':True,'stable':True,'target_id':'submit'}
        r=self.run_tool('selector-resilience',{'target_id':'submit','candidates':[c]})
        self.assertEqual(r['selected'],'a'); self.assertEqual(r['status'],'candidate_identified')

    def effect(self):
        return {'operation':{'id':'op','request_sha256':'a'*64,'target':'demo'},'evidence':[]}

    def test_effect_missing_terminal_evidence_never_authorizes_retry(self):
        x=self.effect();x['evidence']=[{**x['operation'],'operation_id':'op','state':'unknown','receipt_id':None}]
        del x['evidence'][0]['id']
        r=self.run_tool('effect-reconciliation',x)
        self.assertEqual(r['observation'],'unknown'); self.assertFalse(r['retry_authorized'])
        self.assertTrue(r['requires_provider_readback'])

    def test_effect_contradictory_reports_preserved_as_conflict(self):
        x=self.effect();base={'operation_id':'op','request_sha256':'a'*64,'target':'demo','receipt_id':'receipt'}
        x['evidence']=[{**base,'state':'success'},{**base,'state':'failure'}]
        r=self.run_tool('effect-reconciliation',x)
        self.assertEqual(r['observation'],'conflict'); self.assertFalse(r['retry_authorized'])

    def test_effect_wrong_request_is_not_reused(self):
        x=self.effect();x['evidence']=[{'operation_id':'op','request_sha256':'b'*64,'target':'demo',
            'state':'success','receipt_id':'r'}]
        self.assertEqual(self.run_tool('effect-reconciliation',x)['observation'],'conflict')

    def test_contrast_uses_actual_token_values_without_certifying_accessibility(self):
        r=self.run_tool('design-token-audit',{'tokens':{'ink':'#000000','paper':'#ffffff'},
            'pairs':[{'id':'text','foreground':'ink','background':'paper','minimum_ratio':'4.5'}]})
        self.assertEqual(r['pairs'][0]['ratio'],21.0);self.assertTrue(r['pairs'][0]['passed'])
        self.assertFalse(r['conformance_certified'])

    def test_contrast_insufficient_pair_reports_failure(self):
        r=self.run_tool('design-token-audit',{'tokens':{'ink':'#aaaaaa','paper':'#ffffff'},
            'pairs':[{'id':'text','foreground':'ink','background':'paper','minimum_ratio':'4.5'}]})
        self.assertEqual(r['status'],'fail'); self.assertFalse(r['pairs'][0]['passed'])

    def test_interaction_graph_reports_missing_unreachable_and_dead_end_states(self):
        r=self.run_tool('interaction-state-coverage',{'states':['idle','loading','success','error'],
            'initial':'idle','terminal_states':['success'],'required_states':['idle','loading','success','error','empty'],
            'transitions':[{'from':'idle','event':'submit','to':'loading'},
                {'from':'loading','event':'ok','to':'success'}]})
        self.assertEqual(r['missing_required'],['empty']);self.assertEqual(r['unreachable'],['error'])
        self.assertEqual(r['status'],'incomplete');self.assertFalse(r['browser_tested'])

    def test_interaction_nondeterministic_same_event_refused(self):
        p={'states':['a','b'],'initial':'a','terminal_states':['b'],'required_states':['a','b'],
           'transitions':[{'from':'a','event':'go','to':'b'},{'from':'a','event':'go','to':'a'}]}
        with self.assertRaises(ValueError):self.run_tool('interaction-state-coverage',p)

    def test_invalid_scalar_and_unknown_fields_refused(self):
        good={'good_events':9,'total_events':10,'target':'0.9','window_minutes':60}
        for delta in ({'good_events':True},{'target':'NaN'},{'target':'1'},
                      {'total_events':8},{'window_minutes':0},{'unreviewed':True}):
            with self.subTest(delta=delta),self.assertRaises(ValueError):
                self.run_tool('service-objectives',{**good,**delta})

    def test_unknown_tool_refused(self):
        with self.assertRaises(ValueError):self.run_tool('run-shell',{'command':'not executable'})

class R5CatalogAcceptance(unittest.TestCase):
    def test_exact_inventory(self):
        c=ROOT/'collections/muse-starters-v1'
        skills=json.loads((c/'skills.json').read_text('utf-8'))
        workflows=json.loads((c/'workflows.json').read_text('utf-8'))
        starters=json.loads((c/'starters.json').read_text('utf-8'))
        self.assertEqual((len(skills),len(workflows),len(starters)),(75,25,100))
        self.assertTrue((c/'specialists.json').is_file(),'Unified specialist registry is absent')
        roles=json.loads((c/'specialists.json').read_text('utf-8'))
        self.assertEqual(len(roles),15);self.assertEqual(len({r['id'] for r in roles}),15)

if __name__=='__main__':unittest.main()

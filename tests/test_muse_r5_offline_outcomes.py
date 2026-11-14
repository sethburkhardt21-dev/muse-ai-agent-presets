"""Independent observable regression cases for all eleven registered tools."""
from __future__ import annotations
import copy
import sqlite3
import unittest
from muse_presets.specialist_extensions import evaluate


class OfflineOutcomeTests(unittest.TestCase):
    def test_schema_change_reports_risk_and_preserves_input(self):
        case = {'current':[{'name':'id','type':'integer','nullable':False}],
                'proposed':[{'name':'id','type':'integer','nullable':False},
                            {'name':'tenant','type':'text','nullable':False}], 'row_count':17}
        saved=copy.deepcopy(case)
        result=evaluate('schema-evolution',case)
        self.assertEqual(result['status'],'migration_required')
        self.assertEqual(result['backfill_required'],['tenant'])
        self.assertFalse(result['database_modified'])
        self.assertEqual(case,saved)

    def test_incremental_late_event_cannot_resurrect_deleted_record(self):
        tomb={'key':'row','version':8,'value':None,'deleted':True}
        old={'key':'row','version':7,'value':{'title':'old'},'deleted':False}
        result=evaluate('incremental-pipeline',{'state':[tomb],'events':[old,tomb]})
        self.assertEqual(result['state'],[tomb])
        self.assertEqual((result['duplicate_events'],result['stale_events']),(1,1))
        self.assertFalse(result['external_writes'])

    def test_query_classifier_handles_actual_in_memory_sqlite_plan(self):
        with sqlite3.connect(':memory:') as db:
            db.execute('CREATE TABLE item (id INTEGER PRIMARY KEY, name TEXT)')
            db.execute('CREATE INDEX item_name ON item(name)')
            details=[r[3] for r in db.execute('EXPLAIN QUERY PLAN SELECT id FROM item WHERE name=?',('demo',))]
        result=evaluate('query-plan-review',{'details':details})
        self.assertEqual(result['searches'],details)
        self.assertFalse(result['query_executed'])
        self.assertFalse(result['performance_proven'])

    def test_slo_reports_exhausted_budget_from_exact_event_counts(self):
        result=evaluate('service-objectives',{'good_events':998,'total_events':1000,
            'target':'0.999','window_minutes':60})
        self.assertEqual(result['status'],'exhausted')
        self.assertEqual((result['allowed_bad_events'],result['remaining_bad_events'],result['burn_rate']),('1','-1','2'))
        self.assertFalse(result['monitoring_configured'])

    def test_capacity_example_is_seven_instances_not_a_scaling_action(self):
        result=evaluate('capacity-planning',{'demand_rps':'900','per_instance_rps':'250',
            'target_utilization':'0.6','instances':4,'reserve_instances':1})
        self.assertEqual((result['required_instances'],result['additional_instances']),(7,3))
        self.assertEqual(result['available_rps_after_reserve'],'450')
        self.assertFalse(result['scale_actions_performed'])

    def test_incident_orders_offsets_and_reports_one_incident_duration(self):
        case={'events':[{'id':'end','at':'2026-01-01T12:20:00Z','kind':'resolved'},
              {'id':'start','at':'2026-01-01T07:00:00-05:00','kind':'start'},
              {'id':'mitigate','at':'2026-01-01T12:05:00Z','kind':'mitigation'}],
              'as_of':'2026-01-01T12:30:00Z'}
        result=evaluate('incident-triage',case)
        self.assertEqual(result['event_order'],['start','mitigate','end'])
        self.assertEqual((result['time_to_mitigate_seconds'],result['time_to_resolve_seconds']),(300,1200))
        self.assertFalse(result['remediation_performed'])

    def test_automation_blocking_propagates_without_dispatch(self):
        case={'allowed_targets':['sandbox'], 'steps':[
            {'id':'read','depends_on':[],'kind':'read','target':'sandbox','approval':False,'idempotency_key':None},
            {'id':'send','depends_on':['read'],'kind':'send','target':'sandbox','approval':False,'idempotency_key':'op1'},
            {'id':'after','depends_on':['send'],'kind':'read','target':'sandbox','approval':False,'idempotency_key':None}]}
        result=evaluate('automation-contract',case)
        self.assertEqual(result['order'],['read','send','after'])
        self.assertEqual(result['blocked_steps'],[{'id':'send','reasons':['approval_missing']},
                                                 {'id':'after','reasons':['dependency_blocked']}])
        self.assertFalse(result['execution_authorized'])
        self.assertFalse(result['external_actions_performed'])

    def test_selector_requires_unique_visible_target(self):
        def row(name,count,target='submit'):
            return {'id':name,'strategy':'role','matches':count,'visible':True,'stable':True,'target_id':target}
        result=evaluate('selector-resilience',{'target_id':'submit','candidates':[
            row('ambiguous',2),row('wrong',1,'delete'),row('correct',1)]})
        self.assertEqual(result['selected'],'correct')
        self.assertEqual(len(result['rejected']),2)
        self.assertFalse(result['browser_action_performed'])

    def test_reconciliation_consistent_success_is_not_retry_permission(self):
        result=evaluate('effect-reconciliation',{'operation':{'id':'once','request_sha256':'b'*64,'target':'sandbox'},
            'evidence':[{'operation_id':'once','request_sha256':'b'*64,'target':'sandbox','state':'success','receipt_id':'receipt'}]})
        self.assertEqual(result['observation'],'success')
        self.assertFalse(result['retry_authorized'])
        self.assertTrue(result['requires_provider_readback'])
        self.assertFalse(result['provider_evidence_authenticated'])

    def test_contrast_observable_output_preserves_limited_scope(self):
        result=evaluate('design-token-audit',{'tokens':{'ink':'#000000','paper':'#ffffff'},
            'pairs':[{'id':'text','foreground':'ink','background':'paper','minimum_ratio':'4.5'}]})
        self.assertEqual(result['pairs'][0]['ratio'],21.0)
        self.assertTrue(result['pairs'][0]['passed'])
        self.assertFalse(result['conformance_certified'])
        self.assertFalse(result['rendered_ui_inspected'])

    def test_interaction_coverage_does_not_claim_browser_testing(self):
        result=evaluate('interaction-state-coverage',{'states':['idle','loading','done','error'],
            'initial':'idle','terminal_states':['done'],'required_states':['idle','loading','done','error','empty'],
            'transitions':[{'from':'idle','event':'submit','to':'loading'},
                           {'from':'loading','event':'complete','to':'done'}]})
        self.assertEqual(result['missing_required'],['empty'])
        self.assertEqual(result['unreachable'],['error'])
        self.assertEqual(result['status'],'incomplete')
        self.assertFalse(result['browser_tested'])

    def test_unknown_tool_and_non_json_inputs_refused(self):
        with self.assertRaises(ValueError):evaluate('run-shell',{'command':'not admitted'})
        with self.assertRaises(ValueError):evaluate('service-objectives',{'target':float('nan')})


if __name__=='__main__':unittest.main()

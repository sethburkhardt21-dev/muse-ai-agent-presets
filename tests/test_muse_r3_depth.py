"""R3 behavior and source contracts; these do not certify model performance."""
from pathlib import Path
import copy, hashlib, importlib.util, json, unittest
ROOT=Path(__file__).resolve().parents[1]
C=ROOT/'collections/muse-starters-v1'
SELECTED='weekly-reset inbox-triage meeting-to-actions decision-budget lecture-map retrieval-practice misconception-clinic exam-plan question-to-evidence literature-triage competing-explanations interview-synthesis minimal-repair api-contract accessible-ui release-readiness creative-brief storyboard edit-and-export prose-revision project-prioritization metrics-review dataset-intake spreadsheet-reconcile data-quality-review resume-tailor itinerary-plan care-coordination'.split()
def load_module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
class R3DepthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tool=load_module('r3_collection',ROOT/'tools/muse_collection.py')
        cls.data=cls.tool.load_collection(C)
        cls.skills={s['id']:s for s in cls.data['skills']}
        cls.cases={x['id']:x for x in cls.data.get('depth_cases',[])}
        cls.checks=load_module('r3_output_checks',C/'depth/check_outputs.py')
    def test_counts_and_scope(self):
        self.assertEqual(len(SELECTED),28)
        self.assertEqual(len(self.skills),75)
        self.assertEqual(len(self.data['starters']),100)
        self.assertEqual(len(self.data['workflows']),25)
        self.assertEqual(sum(bool(s.get('depth')) for s in self.skills.values()),75)
    def test_r3_status_is_not_model_superiority(self):
        counts=json.loads((C/'COUNTS.json').read_text(encoding='utf-8'))
        self.assertEqual(counts['depth_expanded_skills'],75)
        self.assertEqual(counts['foundation_skills_awaiting_depth'],0)
        self.assertEqual(counts['paired_muse_comparisons_executed'],0)
    def test_registry_and_documents_agree(self):
        status={x['skill_id']:x for x in json.loads((C/'DEPTH_STATUS.json').read_text(encoding='utf-8'))}
        for sid in SELECTED:
            with self.subTest(sid=sid):
                self.assertNotEqual(status[sid]['state'],'FOUNDATION_SOURCE_ONLY')
                self.assertEqual(status[sid]['paired_muse_runs'],0)
                d=self.skills[sid]['depth']
                self.assertEqual((C/'skills'/sid/'DEPTH.md').read_text(encoding='utf-8'),self.tool.render_depth(self.skills[sid]))
                self.assertEqual(len(d['case_ids']),3)
    def test_non_json_outputs_and_false_authority_do_not_pass(self):
        for sid in SELECTED:
            cid=sid+'-r3-standard';self.assertIn(cid,self.cases)
            c=self.cases[cid]
            for o in (None,[],{'result':float('nan')},{}, {'passed':True,'authenticated':True}):
                with self.subTest(sid=sid,value=repr(o)):
                    self.assertFalse(self.checks.check_case(c,o)['passed'])
    def test_comparison_task_inputs_are_identical_and_examples_absent(self):
        for sid in SELECTED:
            self.assertIn('depth',self.skills[sid])
            depth=self.skills[sid]['depth']
            for cid in depth['case_ids']:
                with self.subTest(cid=cid):
                    packets=[self.tool.challenge_files(self.data,cid,arm) for arm in ('plain','upstream','candidate')]
                    self.assertEqual(packets[0]['TASK.json'],packets[1]['TASK.json'])
                    self.assertEqual(packets[1]['TASK.json'],packets[2]['TASK.json'])
                    text=b'\n'.join(packets[2].values()).decode()
                    for ex in [depth['worked_example'],*depth.get('additional_examples',[])]:
                        self.assertNotIn(ex['result'],text)
                    self.assertNotIn('reference_output',text)
                    self.assertNotIn('wrong_output',text)
    def test_all_r3_examples_validate_and_negative_controls_fail(self):
        for sid in SELECTED:
            for suffix in ('standard','edge','recovery'):
                cid=sid+'-r3-'+suffix
                with self.subTest(case=cid):
                    self.assertIn(cid,self.cases)
                    c=self.cases[cid]
                    self.assertTrue(self.checks.check_case(c,c['reference_output'])['passed'],self.checks.check_case(c,c['reference_output']))
                    self.assertFalse(self.checks.check_case(c,c['wrong_output'])['passed'])
                    self.assertIsNone(c['model_results'])
    def test_original_r2_assets_are_preserved(self):
        manifest=C/'R3_BASELINE_ASSETS.json'
        self.assertTrue(manifest.exists())
        # Exact historical bytes remain pinned. Seven intentionally expanded files
        # have immutable baseline copies; separate R5 projection tests enforce that
        # current data preserves every original field except the admitted additions.
        migrated={'evaluation_cases.json','starters.json','workflows.json'} | {
            'starters/'+sid+'/STARTER.md' for sid in
            ('data-cleaner','operations-analyst','customer-support-designer','frontend-partner')}
        prefix='collections/muse-starters-v1/'
        for p,h in json.loads(manifest.read_text(encoding='utf-8'))['files'].items():
            relative=p[len(prefix):] if p.startswith(prefix) else None
            source=C/'r5'/'baseline'/relative if relative in migrated else ROOT/p
            with self.subTest(path=p):self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),h)

def _skill_test(sid):
    def test(self):
        s=self.skills[sid];self.assertIn('depth',s,'R3 capability has not been authored')
        d=s['depth'];self.assertGreaterEqual(len(d['decisions']),5)
        self.assertGreaterEqual(len(d['failure_modes']),3)
        self.assertGreaterEqual(len(d.get('additional_examples',[])),1)
        self.assertTrue(d.get('domain_method'))
        self.assertTrue(d.get('output_contract'))
        self.assertTrue(d.get('upstream_items'))
        self.assertEqual(d.get('comparison_result'),'NOT_RUN')
        for cid in d['case_ids']:self.assertEqual(self.cases[cid]['skill_id'],sid)
    return test
for sid in SELECTED:setattr(R3DepthTests,'test_depth_'+sid.replace('-','_'),_skill_test(sid))
if __name__=='__main__':unittest.main()


class R3AdverseTests(unittest.TestCase):
    setUpClass = classmethod(R3DepthTests.setUpClass.__func__)
    """Input mutation and invariance checks, not model benchmark outcomes."""
    def case(self, sid, suffix='standard'):
        return copy.deepcopy(self.cases[sid+'-r3-'+suffix])
    def passed(self,c,o):return self.checks.check_case(c,o)['passed']
    def test_gold_answer_poison_does_not_change_domain_decision(self):
        for sid in SELECTED:
            c=self.case(sid);answer=copy.deepcopy(c['reference_output'])
            c['reference_output']={'fabricated':'winner'};c['wrong_output']={'fabricated':'loser'}
            with self.subTest(skill=sid):self.assertTrue(self.passed(c,answer))
    def test_weekly_capacity_change_invalidates_old_allocation(self):
        c=self.case('weekly-reset');old=c['reference_output'];c['inputs']['available_minutes']=300
        self.assertFalse(self.passed(c,old))
        expected=dict(usable_minutes=180,selected=['A'],deferred=['B','C'],blocked=[],completed=[],allocated_minutes=180,remaining_minutes=0)
        self.assertTrue(self.passed(c,expected))
    def test_weekly_unmet_dependency_is_blocked_not_scheduled(self):
        c=self.case('weekly-reset');c['inputs']['tasks'][0]['dependencies']=['B'];c['inputs']['tasks'][1]['state']='blocked'
        expected=dict(usable_minutes=480,selected=['C'],deferred=[],blocked=['A','B'],completed=[],allocated_minutes=120,remaining_minutes=360)
        self.assertFalse(self.passed(c,c['reference_output']))
        self.assertTrue(self.passed(c,expected))
    def test_weekly_unknown_dependency_is_invalid(self):
        c=self.case('weekly-reset');c['inputs']['tasks'][0]['dependencies']=['missing']
        self.assertFalse(self.passed(c,c['reference_output']))
    def test_boolean_is_not_integer_capacity(self):
        c=self.case('weekly-reset');c['inputs']['available_minutes']=True
        self.assertFalse(self.passed(c,c['reference_output']))
    def test_inbox_event_order_not_input_order(self):
        c=self.case('inbox-triage','edge');c['inputs']['events'].reverse()
        self.assertTrue(self.passed(c,c['reference_output']))
    def test_unknown_send_is_not_overridden_by_new_draft(self):
        c=self.case('inbox-triage','recovery');o=copy.deepcopy(c['reference_output'])
        c['inputs']['events'].append(dict(id='m4',thread_id='T1',kind='draft',at='2026-11-12T12:00:00-05:00',deadline=None,text='Unsent draft.'))
        o['threads'][0]['evidence_ids'].append('m4')
        self.assertTrue(self.passed(c,o));o['threads'][0]['status']='waiting';self.assertFalse(self.passed(c,o))
    def test_duplicate_mail_event_id_refuses_ambiguous_evidence(self):
        c=self.case('inbox-triage');c['inputs']['events'].append(copy.deepcopy(c['inputs']['events'][0]))
        self.assertFalse(self.passed(c,c['reference_output']))
    def test_deposit_affects_cash_not_total_cost(self):
        c=self.case('decision-budget');c['inputs']['options'][1]['deposit_cents']=3000
        o=copy.deepcopy(c['reference_output']);o['options'][1]['cash_today_cents']=33000;o['options'][1]['feasible']=False;o['cheapest_feasible_ids']=['A']
        self.assertTrue(self.passed(c,o));o['options'][1]['cost_cents']+=3000;self.assertFalse(self.passed(c,o))
    def test_nonrefundable_prepay_is_not_prorated_to_short_horizon(self):
        c=self.case('decision-budget');c['inputs']['horizon_months']=1
        o=copy.deepcopy(c['reference_output']);o['options'][0]['cost_cents']=7000;o['cheapest_feasible_ids']=['A']
        self.assertTrue(self.passed(c,o));o['options'][1]['cost_cents']=2500;self.assertFalse(self.passed(c,o))
    def test_oracle_cannot_cite_missing_transcript(self):
        c=self.case('meeting-to-actions');c['semantic_oracle']['actions'][0]['source_lines']=['absent']
        self.assertFalse(self.passed(c,c['reference_output']))
    def test_oracle_cannot_cite_unread_slide(self):
        c=self.case('lecture-map');c['semantic_oracle']['concepts'][0]['source_slides']=['s3']
        self.assertFalse(self.passed(c,c['reference_output']))
    def test_same_attempt_replay_does_not_double_grade(self):
        c=self.case('retrieval-practice');c['inputs']['attempts'].append(copy.deepcopy(c['inputs']['attempts'][0]))
        self.assertTrue(self.passed(c,c['reference_output']))
    def test_conflicting_attempt_replay_refused(self):
        c=self.case('retrieval-practice');q=copy.deepcopy(c['inputs']['attempts'][0]);q['assisted']=True;c['inputs']['attempts'].append(q)
        self.assertFalse(self.passed(c,c['reference_output']))
    def test_assisted_evidence_does_not_certify_transfer(self):
        c=self.case('misconception-clinic');o=copy.deepcopy(c['reference_output']);o['transfer_status']='observed'
        self.assertFalse(self.passed(c,o))
    def test_source_access_withdrawal_changes_claim_verdict(self):
        c=self.case('question-to-evidence');c['inputs']['sources'][0]['accessed']=False
        o=dict(claims=[dict(id='c1',status='unresolved',supporting_source_ids=[])],excluded_source_ids=['s1','s2'])
        self.assertTrue(self.passed(c,o));self.assertFalse(self.passed(c,c['reference_output']))
    def test_conflicting_doi_record_is_not_counted_as_replication(self):
        c=self.case('literature-triage');c['inputs']['records'][1]['study_id']='other'
        self.assertFalse(self.passed(c,c['reference_output']))
    def test_only_observed_prediction_contradictions_eliminate(self):
        c=self.case('competing-explanations');c['inputs']['observations']['small-input']='slow'
        o=dict(chosen_test_id='small-input',eliminated_hypotheses=['H2'])
        self.assertTrue(self.passed(c,o));o['eliminated_hypotheses'].append('H1');self.assertFalse(self.passed(c,o))
    def test_more_quotes_do_not_create_more_participants(self):
        c=self.case('interview-synthesis');q=dict(id='q5',participant='P1',theme='navigation',supports=True,text='Still difficult.');c['inputs']['quotes'].append(q)
        o=copy.deepcopy(c['reference_output']);o['quoted_evidence'].append(dict(id='q5',text='Still difficult.'))
        self.assertTrue(self.passed(c,o));o['support_fraction']=1;self.assertFalse(self.passed(c,o))
    def test_patch_receipts_for_old_candidate_are_not_accepted(self):
        c=self.case('minimal-repair');c['inputs']['checks'][0]['candidate']='different'
        o=dict(status='test-failure',patch_admissible=False,verified_checks=[],deployed=False)
        self.assertTrue(self.passed(c,o));self.assertFalse(self.passed(c,c['reference_output']))
    def test_idempotency_scope_does_not_leak_another_principals_result(self):
        c=self.case('api-contract');c['inputs']['request']['principal']='other-owner'
        self.assertTrue(self.passed(c,dict(outcome='new-request',resource_id=None,new_effects=0)))
        self.assertFalse(self.passed(c,c['reference_output']))
    def test_unknown_idempotent_operation_is_not_replayed_as_complete(self):
        c=self.case('api-contract');c['inputs']['record']['state']='unknown'
        self.assertTrue(self.passed(c,dict(outcome='reconcile',resource_id=None,new_effects=0)))
        self.assertFalse(self.passed(c,c['reference_output']))
    def test_changed_idempotency_payload_requires_conflict(self):
        c=self.case('api-contract');c['inputs']['request']['payload']='changed'
        self.assertTrue(self.passed(c,dict(outcome='conflict',resource_id=None,new_effects=0)))
    def test_accessibility_empty_scope_cannot_pass(self):
        c=self.case('accessible-ui');c['inputs'].update(checks=[],full_scope=True)
        self.assertTrue(self.passed(c,dict(checks=[],overall='incomplete',conformance='undetermined')))
    def test_release_candidate_change_invalidates_all_old_receipts(self):
        c=self.case('release-readiness');c['inputs']['candidate']='H3'
        o=dict(gates=[dict(id='unit',status='stale'),dict(id='package',status='stale')],verdict='HOLD',publication_status='not-performed')
        self.assertTrue(self.passed(c,o))
    def test_brief_does_not_manufacture_approval(self):
        c=self.case('creative-brief');o=copy.deepcopy(c['reference_output']);o['acceptance']='approved'
        self.assertFalse(self.passed(c,o))
    def test_storyboard_overlap_changes_runtime(self):
        c=self.case('storyboard');c['inputs']['overlap_frames']=[12,12]
        o=dict(total_frames=264,duration_seconds=11,target_met=False,continuity_breaks=[],rendered=False)
        self.assertTrue(self.passed(c,o));self.assertFalse(self.passed(c,c['reference_output']))
    def test_media_audio_presence_is_not_delivery_confirmation(self):
        c=self.case('edit-and-export');c['inputs']['observed']['audio']=True
        o=dict(completion='rendered-complete',missing_requirements=[],delivery_status='not-performed')
        self.assertTrue(self.passed(c,o));o['delivery_status']='confirmed';self.assertFalse(self.passed(c,o))
    def test_prose_edit_preserves_uncertainty_and_command(self):
        c=self.case('prose-revision');o=copy.deepcopy(c['reference_output']);o['revised_text']=o['revised_text'].replace('may','will')
        self.assertFalse(self.passed(c,o));o=copy.deepcopy(c['reference_output']);o['revised_text']=o['revised_text'].replace('--safe','--force')
        self.assertFalse(self.passed(c,o))
    def test_project_cycle_does_not_block_independent_work(self):
        c=self.case('project-prioritization');c['inputs']['tasks'][2]['deps']=['B']
        o=dict(selected=['C'],blocked=['A','B'],deferred=[],completed=[],resource_used={'dev':4})
        self.assertTrue(self.passed(c,o))
    def test_metric_denominator_changes_answer(self):
        c=self.case('metrics-review');c['inputs']['current_exposure']=900
        o=copy.deepcopy(c['reference_output']);o.update(current_rate=0.1,rate_relative_change=0.0)
        self.assertTrue(self.passed(c,o));self.assertFalse(self.passed(c,c['reference_output']))
    def test_metric_zero_denominator_is_unknown_not_zero(self):
        c=self.case('metrics-review');c['inputs']['current_exposure']=0
        o=copy.deepcopy(c['reference_output']);o.update(current_rate=None,rate_relative_change=None)
        self.assertTrue(self.passed(c,o));o['current_rate']=0;self.assertFalse(self.passed(c,o))
    def test_dataset_post_outcome_feature_blocks_admission(self):
        c=self.case('dataset-intake');c['inputs']['features'][0]['known_before']=False
        o=copy.deepcopy(c['reference_output']);o['post_outcome_features']=['x']
        self.assertTrue(self.passed(c,o));self.assertFalse(self.passed(c,c['reference_output']))
    def test_sheet_totals_never_merge_currencies(self):
        c=self.case('spreadsheet-reconcile');c['inputs']={'source':[dict(id='a',currency='USD',amount='1.00'),dict(id='b',currency='EUR',amount='1.00')],'workbook':[dict(id='a',currency='USD',amount='1.00'),dict(id='b',currency='EUR',amount='1.00')]}
        o=dict(source_totals={'USD':100,'EUR':100},workbook_totals={'USD':100,'EUR':100},duplicate_ids=[],missing_ids=[],extra_ids=[],conflicting_ids=[],workbook_modified=False)
        self.assertTrue(self.passed(c,o));o['source_totals']={'USD':200};self.assertFalse(self.passed(c,o))
    def test_conflicting_source_version_holds_original_state(self):
        c=self.case('data-quality-review');c['inputs']['events'].append(dict(key='A',version=2,payload=99))
        o=dict(status='held-conflict',state=[dict(key='A',version=2,payload=20)])
        self.assertTrue(self.passed(c,o));self.assertFalse(self.passed(c,c['reference_output']))
    def test_resume_personal_project_is_not_employment(self):
        c=self.case('resume-tailor');o=copy.deepcopy(c['reference_output']);o['bullets'][0]['scope']='employment'
        self.assertFalse(self.passed(c,o))
    def test_trip_equivalent_utc_offsets_preserve_connection(self):
        c=self.case('itinerary-plan');c['inputs']['arrival']='2026-11-12T19:00:00+00:00';c['inputs']['departure']='2026-11-12T20:00:00+00:00'
        self.assertTrue(self.passed(c,c['reference_output']))
    def test_care_version_change_does_not_implicitly_accept_assignment(self):
        c=self.case('care-coordination');c['inputs']['active_plan']['version']='P3'
        o=copy.deepcopy(c['reference_output']);o['plan_version']='P3'
        self.assertTrue(self.passed(c,o));o['assignments'][1]['state']='accepted';self.assertFalse(self.passed(c,o))
    def test_original_r2_case_projection_hash_is_exact(self):
        manifest=json.loads((C/'R3_BASELINE_ASSETS.json').read_text(encoding='utf-8'))
        originals=[self.cases[cid] for cid in manifest['original_case_ids']]
        actual=hashlib.sha256(json.dumps(originals,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
        self.assertEqual(actual,manifest['original_cases_sha256'])

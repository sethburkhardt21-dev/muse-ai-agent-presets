"""Acceptance and negative tests for the additive Muse collection exporter."""
import copy
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('muse_collection', ROOT/'tools'/'muse_collection.py')
if SPEC is None or SPEC.loader is None:
    raise RuntimeError('module loader missing')
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)
COLLECTION = ROOT/'collections'/'muse-starters-v1'

class CollectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = mod.load_collection(COLLECTION)

    def test_100_distinct_starters(self):
        self.assertEqual(len(self.data['starters']), 100)
        self.assertEqual(len({x['id'] for x in self.data['starters']}), 100)
        self.assertEqual(len({x['first_task'] for x in self.data['starters']}), 100)

    def test_75_distinct_skills(self):
        self.assertEqual(len(self.data['skills']), 75)
        self.assertEqual(len({x['id'] for x in self.data['skills']}), 75)
        self.assertEqual(len({tuple(x['steps']) for x in self.data['skills']}), 75)

    def test_25_workflows(self):
        self.assertEqual(len(self.data['workflows']),25)

    def test_11_core_roles_preserved(self):
        self.assertEqual(set(mod.CORE_ROLES), {x['base_role'] for x in self.data['starters']})

    def test_all_profiles_build(self):
        for p in self.data['starters']:
            with self.subTest(starter=p['id']):
                content = mod.build_bytes(self.data, p['id'])
                with zipfile.ZipFile(io.BytesIO(content)) as z:
                    self.assertIn('START_HERE.md', z.namelist())
                    self.assertIn('PROFILE.md', z.namelist())
                    self.assertIn('MANIFEST.json',z.namelist())
                    self.assertNotIn('MEMORY.md',z.namelist())
                    self.assertLess(len(content),1_000_000)

    def test_selected_skills_only(self):
        p=self.data['starters'][0]
        names=mod.package_files(self.data,p['id'])
        self.assertLess(sum(k.endswith('/SKILL.md') for k in names), len(self.data['skills']))
        self.assertIn(p['title'],names['PROFILE.md'].decode())

    def test_deterministic_build(self):
        self.assertEqual(mod.build_bytes(self.data,'daily-planner'),mod.build_bytes(self.data,'daily-planner'))

    def test_manifest_file_hashes(self):
        import hashlib
        with zipfile.ZipFile(io.BytesIO(mod.build_bytes(self.data,'daily-planner'))) as z:
            m=json.loads(z.read('MANIFEST.json'))
            for n,h in m['files'].items():
                self.assertEqual(hashlib.sha256(z.read(n)).hexdigest(),h)
            self.assertEqual(set(z.namelist()),set(m['files'])|{'MANIFEST.json'})
            self.assertEqual(m['evaluation'],'SOURCE_CHECKED_NOT_BEHAVIORALLY_EVALUATED')

    def test_unknown_starter_rejected(self):
        with self.assertRaises(mod.CollectionError):mod.build_bytes(self.data,'not-an-agent')

    def test_existing_output_never_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'pack.zip';p.write_bytes(b'user-content')
            with self.assertRaises(mod.CollectionError):mod.write_new_pack(p,b'new')
            self.assertEqual(p.read_bytes(),b'user-content')

    def test_output_round_trip(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'pack.zip';b=mod.build_bytes(self.data,'daily-planner')
            mod.write_new_pack(p,b)
            self.assertEqual(p.read_bytes(),b)

    def test_parent_traversal_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(mod.CollectionError):mod.write_new_pack(Path(d)/'x'/'..'/'p.zip',b'a')

    def test_missing_parent_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(mod.CollectionError):mod.write_new_pack(Path(d)/'missing'/'p.zip',b'a')

    def test_symlink_output_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'p.zip';target=Path(d)/'target';target.write_bytes(b'a')
            try:p.symlink_to(target)
            except (OSError,NotImplementedError):self.skipTest('symlink creation unavailable')
            with self.assertRaises(mod.CollectionError):mod.write_new_pack(p,b'b')
            self.assertEqual(target.read_bytes(),b'a')

    def test_symlink_parent_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            target=Path(d)/'real';target.mkdir();link=Path(d)/'alias'
            try:link.symlink_to(target,target_is_directory=True)
            except (OSError,NotImplementedError):self.skipTest('symlink creation unavailable')
            with self.assertRaises(mod.CollectionError):mod.write_new_pack(link/'pack.zip',b'a')

    def test_duplicate_json_keys_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x.json';p.write_text('{"id":1,"id":2}')
            with self.assertRaises(mod.CollectionError):mod.read_json(p)

    def test_oversized_json_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x.json';p.write_bytes(b' '*(mod.MAX_JSON_BYTES+1))
            with self.assertRaises(mod.CollectionError):mod.read_json(p)

    def test_symlink_json_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            target=Path(d)/'real.json';target.write_text('{}');p=Path(d)/'x.json'
            try:p.symlink_to(target)
            except (OSError,NotImplementedError):self.skipTest('symlink creation unavailable')
            with self.assertRaises(mod.CollectionError):mod.read_json(p)

    def test_duplicate_starter_rejected(self):
        d=copy.deepcopy(self.data);d['starters'].append(copy.deepcopy(d['starters'][0]))
        with self.assertRaises(mod.CollectionError):mod.validate(d)

    def test_duplicate_skill_rejected(self):
        d=copy.deepcopy(self.data);d['skills'].append(copy.deepcopy(d['skills'][0]))
        with self.assertRaises(mod.CollectionError):mod.validate(d)

    def test_missing_skill_rejected(self):
        d=copy.deepcopy(self.data);d['starters'][0]['skills'].append('not-real')
        with self.assertRaises(mod.CollectionError):mod.validate(d)

    def test_missing_workflow_rejected(self):
        d=copy.deepcopy(self.data);d['starters'][0]['workflows'].append('not-real')
        with self.assertRaises(mod.CollectionError):mod.validate(d)

    def test_path_like_id_rejected(self):
        d=copy.deepcopy(self.data);d['starters'][0]['id']='../../other'
        with self.assertRaises(mod.CollectionError):mod.validate(d)

    def test_unknown_source_rejected(self):
        d=copy.deepcopy(self.data);d['skills'][0]['source_ids']=['fake-source']
        with self.assertRaises(mod.CollectionError):mod.validate(d)

    def test_unpinned_source_rejected(self):
        d=copy.deepcopy(self.data);d['sources'][0]['revision']='main'
        with self.assertRaises(mod.CollectionError):mod.validate(d)

    def test_unlicensed_copy_rejected(self):
        d=copy.deepcopy(self.data);d['sources'][0]['reuse']='copy';d['sources'][0]['license']='UNKNOWN'
        with self.assertRaises(mod.CollectionError):mod.validate(d)

    def test_empty_workflow_steps_rejected(self):
        d=copy.deepcopy(self.data);d['skills'][0]['steps']=[]
        with self.assertRaises(mod.CollectionError):mod.validate(d)

    def test_identical_skill_bodies_rejected(self):
        d=copy.deepcopy(self.data);d['skills'][1]['steps']=d['skills'][0]['steps'][:]
        with self.assertRaises(mod.CollectionError):mod.validate(d)

    def test_inflated_evaluation_rejected(self):
        d=copy.deepcopy(self.data);d['skills'][0]['evaluation']='PROVEN_BETTER_THAN_COMPETITORS'
        with self.assertRaises(mod.CollectionError):mod.validate(d)

    def test_unknown_core_role_rejected(self):
        d=copy.deepcopy(self.data);d['starters'][0]['base_role']='new-runtime'
        with self.assertRaises(mod.CollectionError):mod.validate(d)

    def test_hidden_automatic_actions_rejected(self):
        d=copy.deepcopy(self.data);d['starters'][0]['automatic_external_actions']=True
        with self.assertRaises(mod.CollectionError):mod.validate(d)

    def test_held_sources_not_copied(self):
        for s in self.data['sources']:
            if s['license'] in ['UNKNOWN','NOASSERTION']:
                self.assertEqual(s['reuse'],'reference-only')

    def test_every_skill_has_evaluation_cases(self):
        by={x['skill_id'] for x in self.data['evaluation_cases']}
        self.assertEqual(by,{x['id'] for x in self.data['skills']})
        for x in self.data['evaluation_cases']:
            self.assertEqual(x['results'],{'baseline':None,'upstream':None,'candidate':None})

    def test_no_personal_runtime_data_in_exports(self):
        names=mod.package_files(self.data,'daily-planner')
        for n in names:
            self.assertFalse(n.endswith(('.db','.sqlite','.env','.exe','.sh','.ps1')))
            self.assertFalse(n.startswith(('/', '../')))

    def test_cli_list_and_show(self):
        import subprocess,sys
        a=subprocess.run([sys.executable,str(ROOT/'tools/muse_collection.py'),'list'],capture_output=True,text=True)
        self.assertEqual(a.returncode,0,a.stderr)
        self.assertIn('daily-planner',a.stdout)
        b=subprocess.run([sys.executable,str(ROOT/'tools/muse_collection.py'),'show','daily-planner'],capture_output=True,text=True)
        self.assertEqual(b.returncode,0,b.stderr)
        self.assertIn('First task',b.stdout)

    def test_cli_validate(self):
        import subprocess,sys
        a=subprocess.run([sys.executable,str(ROOT/'tools/muse_collection.py'),'check'],capture_output=True,text=True)
        self.assertEqual(a.returncode,0,a.stderr)
        self.assertEqual(json.loads(a.stdout)['starters'],100)

    def test_cli_bad_id_no_traceback(self):
        import subprocess,sys
        a=subprocess.run([sys.executable,str(ROOT/'tools/muse_collection.py'),'show','../bad'],capture_output=True,text=True)
        self.assertEqual(a.returncode,2)
        self.assertNotIn('Traceback',a.stderr)

    def test_nonobject_evaluation_rejected_cleanly(self):
        d=copy.deepcopy(self.data);d['evaluation_cases'][0]=[]
        with self.assertRaises(mod.CollectionError):mod.validate(d)

    def test_deep_json_rejected_cleanly(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'deep.json';p.write_text('['*2000+'0'+']'*2000)
            with self.assertRaises(mod.CollectionError):mod.read_json(p)

    def test_nontext_license_notice_rejected(self):
        d=copy.deepcopy(self.data);d['sources'][0].update(reuse='adaptation',notice_text=True)
        with self.assertRaises(mod.CollectionError):mod.validate(d)

    def test_source_license_required(self):
        d=copy.deepcopy(self.data);del d['sources'][0]['license']
        with self.assertRaises(mod.CollectionError):mod.validate(d)

    def test_fifo_rejected_without_hanging(self):
        import subprocess,sys
        if not hasattr(os,'mkfifo'):self.skipTest('named pipes unavailable')
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'pipe';os.mkfifo(p)
            code="import importlib.util;from pathlib import Path;s=importlib.util.spec_from_file_location('m',%r);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);m.read_json(Path(%r))" % (str(ROOT/'tools/muse_collection.py'),str(p))
            result=subprocess.run([sys.executable,'-I','-S','-B','-c',code],capture_output=True,text=True,timeout=3)
            self.assertNotEqual(result.returncode,0)
            self.assertIn('regular file',result.stderr)

    def test_profile_preserves_user_current_task(self):
        p=mod.package_files(self.data,'daily-planner')['START_HERE.md'].decode()
        self.assertIn('my current task',p)
        self.assertIn('example',p)

    def test_workflows_are_optional_recipes(self):
        p=mod.package_files(self.data,'daily-planner')['PROFILE.md'].decode()
        self.assertIn('Optional workflow recipes',p)

    def test_rendered_files_match_catalog(self):
        ss={s['id']:s for s in self.data['sources']}
        for s in self.data['skills']:
            self.assertEqual((COLLECTION/'skills'/s['id']/'SKILL.md').read_text(encoding='utf-8'),mod.render_skill(s,ss))
        for p in self.data['starters']:
            self.assertEqual((COLLECTION/'starters'/p['id']/'STARTER.md').read_text(encoding='utf-8'),mod.render_profile(p))

    def test_project_license_in_export(self):
        files=mod.package_files(self.data,'daily-planner')
        self.assertIn('LICENSE',files)
        self.assertIn('Muse AI Agent Presets contributors',files['LICENSE'].decode())


class DepthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = mod.load_collection(COLLECTION)
        cls.expected={'daily-briefing','source-flashcards','claim-audit','bug-reproduction',
                      'code-review','continuity-review','model-comparison','resume-without-replay'}

    def test_eight_existing_skills_have_substantive_depth(self):
        deep={s['id']:s for s in self.data['skills'] if s.get('depth')}
        self.assertTrue(self.expected <= set(deep))
        self.assertEqual(len(deep),75)
        for s in deep.values():
            self.assertGreaterEqual(len(s['depth']['decisions']),3)
            self.assertGreaterEqual(len(s['depth']['failure_modes']),3)
            self.assertTrue(s['depth']['worked_example']['result'])
            self.assertEqual(len(s['depth']['case_ids']),3)

    def test_concrete_cases_replace_placeholder_only_evaluation(self):
        cases=self.data.get('depth_cases',[])
        self.assertEqual(len(cases),225)
        original=[c for c in cases if c['skill_id'] in self.expected]
        self.assertEqual(len(original),24)
        self.assertEqual({c['skill_id'] for c in original},self.expected)
        for c in cases:
            self.assertIsInstance(c['inputs'],dict)
            self.assertTrue(c['inputs'])
            self.assertGreater(len(c['request']),50)
            self.assertTrue(c['review_rubric'])
            self.assertEqual(c['model_results'],None)
            self.assertEqual(c['status'],'PUBLIC_REGRESSION_CASE_NOT_MODEL_RESULT')

    def test_selected_pack_contains_only_relevant_depth_assets(self):
        files=mod.package_files(self.data,'daily-planner')
        self.assertIn('skills/daily-briefing/DEPTH.md',files)
        self.assertIn('practice/check_outputs.py',files)
        self.assertNotIn('skills/bug-reproduction/DEPTH.md',files)
        self.assertIn('## Go deeper',files['skills/daily-briefing/SKILL.md'].decode())

    def test_depth_reference_closure_is_enforced(self):
        d=copy.deepcopy(self.data)
        target=next(s for s in d['skills'] if s['id']=='daily-briefing')
        target.setdefault('depth',{})['case_ids']=['missing-case']
        with self.assertRaises(mod.CollectionError):mod.validate(d)

    def test_depth_cases_cannot_claim_model_execution(self):
        d=copy.deepcopy(self.data)
        self.assertTrue(d.get('depth_cases'))
        d['depth_cases'][0]['model_results']={'candidate':'winner'}
        with self.assertRaises(mod.CollectionError):mod.validate(d)

    def test_paired_task_packets_do_not_include_reference_answers(self):
        self.assertTrue(hasattr(mod,'challenge_files'))
        packet=mod.challenge_files(self.data,'daily-briefing-standard','candidate')
        self.assertIn('TASK.json',packet)
        self.assertNotIn('reference_output',json.loads(packet['TASK.json']))
        self.assertNotIn('AUTHORED_ANSWER.json',packet)
        self.assertNotIn('reference_output',b'\n'.join(packet.values()).decode())

    def test_plain_baseline_packet_has_no_candidate_instructions(self):
        self.assertTrue(hasattr(mod,'challenge_files'))
        packet=mod.challenge_files(self.data,'daily-briefing-standard','plain')
        self.assertEqual(set(packet),{'TASK.json','RUN_PROTOCOL.md'})

    def test_competitor_packet_has_no_candidate_instructions(self):
        self.assertTrue(hasattr(mod,'challenge_files'))
        packet=mod.challenge_files(self.data,'daily-briefing-standard','upstream')
        self.assertIn('UPSTREAM_REFERENCE.json',packet)
        self.assertFalse(any(p.startswith('skills/') for p in packet))

class OutputCheckTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec=importlib.util.spec_from_file_location('depth_checks', COLLECTION/'depth'/'check_outputs.py')
        cls.check=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.check)
        cls.cases=json.loads((COLLECTION/'depth_cases.json').read_text())

    def test_all_authored_demonstrations_meet_mechanical_contract(self):
        for case in self.cases:
            with self.subTest(case=case['id']):
                result=self.check.check_case(case,case['reference_output'])
                self.assertTrue(result['passed'],result)
                self.assertTrue(result['human_review_required'])
                self.assertEqual(result['evidence_grade'],'SUPPLIED_OUTPUT_MECHANICALLY_CHECKED')

    def test_every_seeded_wrong_output_is_rejected(self):
        for case in self.cases:
            with self.subTest(case=case['id']):
                self.assertFalse(self.check.check_case(case,case['wrong_output'])['passed'])

    def test_malformed_output_is_not_a_pass(self):
        for case in self.cases:
            for output in (None,[],{},True,{'outcome':float('nan')}):
                with self.subTest(case=case['id'],output=output):
                    self.assertFalse(self.check.check_case(case,output)['passed'])

    def test_unknown_case_kind_is_rejected(self):
        c=copy.deepcopy(self.cases[0]);c['skill_id']='unknown-skill'
        self.assertFalse(self.check.check_case(c,c['reference_output'])['passed'])

    def test_identical_conditions_are_required_for_paired_comparison(self):
        runs=self.check.example_run_metadata()
        self.assertTrue(self.check.check_comparability(runs)['comparable'])
        runs[1]['environment']['model']='different-model'
        self.assertFalse(self.check.check_comparability(runs)['comparable'])

    def test_missing_arm_is_not_comparable(self):
        self.assertFalse(self.check.check_comparability(self.check.example_run_metadata()[:2])['comparable'])

    def test_shared_session_is_not_an_independent_comparison(self):
        runs=self.check.example_run_metadata();runs[1]['session_id']=runs[0]['session_id']
        self.assertFalse(self.check.check_comparability(runs)['comparable'])

    def test_case_coverage_must_match(self):
        runs=self.check.example_run_metadata();runs[1]['case_ids']=[]
        self.assertFalse(self.check.check_comparability(runs)['comparable'])

    def test_no_generated_superiority_from_metadata(self):
        result=self.check.check_comparability(self.check.example_run_metadata())
        self.assertNotIn('winner',result)
        self.assertEqual(result['measurement'],'METADATA_CONSISTENCY_ONLY')

    def test_fake_authentication_metadata_does_not_attest_provider(self):
        runs=self.check.example_run_metadata()
        for r in runs:r['provider_authenticated']=True
        self.assertFalse(self.check.check_comparability(runs)['provider_identity_verified'])

class DepthBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=mod.load_collection(COLLECTION)
        spec=importlib.util.spec_from_file_location('dc_boundary',COLLECTION/'depth'/'check_outputs.py')
        cls.check=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.check)

    def test_candidate_challenge_excludes_its_worked_answer(self):
        for skill in self.data['skills']:
            if not skill.get('depth'):continue
            packet=mod.challenge_files(self.data,skill['depth']['case_ids'][0],'candidate')
            content=b'\n'.join(packet.values()).decode()
            self.assertNotIn(skill['depth']['worked_example']['result'],content)
            self.assertNotIn('Worked example (authored, synthetic)',content)

    def test_all_three_arms_receive_byte_identical_task_data(self):
        for case in self.data['depth_cases']:
            skill=next(s for s in self.data['skills'] if s['id']==case['skill_id'])
            arms=('plain','candidate') if skill.get('origin')=='ORIGINAL_FIRST_PARTY' else ('plain','upstream','candidate')
            if len(arms)==2:
                with self.assertRaises(mod.CollectionError):mod.challenge_files(self.data,case['id'],'upstream')
            packets=[mod.challenge_files(self.data,case['id'],a) for a in arms]
            self.assertEqual(len({p['TASK.json'] for p in packets}),1)
            for p in packets:
                data=json.loads(p['TASK.json'])
                self.assertEqual(set(data),{'id','skill_id','request','inputs'})
                self.assertNotIn('oracle',data)
                if case['skill_id']=='source-flashcards':
                    self.assertFalse(any('answer' in x for x in data['inputs']['targets']))

    def test_naive_schedule_time_rejected(self):
        case=next(c for c in self.data['depth_cases'] if c['id']=='daily-briefing-standard')
        result=copy.deepcopy(case['reference_output']);result['schedule'][0]['start']='2026-11-16T09:00:00'
        self.assertFalse(self.check.check_case(case,result)['passed'])

    def test_missing_task_is_not_a_feasible_plan(self):
        case=next(c for c in self.data['depth_cases'] if c['id']=='daily-briefing-standard')
        result=copy.deepcopy(case['reference_output']);result['schedule'].pop()
        self.assertFalse(self.check.check_case(case,result)['passed'])

    def test_wrong_claim_quote_rejected(self):
        case=next(c for c in self.data['depth_cases'] if c['skill_id']=='claim-audit')
        result=copy.deepcopy(case['reference_output']);result['findings'][0]['evidence'][0]['quote']='made-up observation'
        self.assertFalse(self.check.check_case(case,result)['passed'])

    def test_check_output_json_duplicate_keys_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'a.json';p.write_text('{"x":1,"x":2}')
            with self.assertRaises(self.check.ContractError):self.check.read_json(p)

    def test_check_output_json_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'a.json';p.write_text('{}');link=Path(d)/'b.json'
            try:link.symlink_to(p)
            except (OSError,NotImplementedError):self.skipTest('symlink unsupported')
            with self.assertRaises(self.check.ContractError):self.check.read_json(link)

    @unittest.skipUnless(hasattr(os,'mkfifo'),'POSIX named pipes only')
    def test_check_output_named_pipe_refused_before_open(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'fifo';os.mkfifo(p)
            with self.assertRaises(self.check.ContractError):self.check.read_json(p)

    def test_nonfinite_metric_refused(self):
        case=next(c for c in self.data['depth_cases'] if c['skill_id']=='model-comparison')
        for x in (True,float('nan'),float('inf')):
            result=copy.deepcopy(case['reference_output']);result['delta']=x
            self.assertFalse(self.check.check_case(case,result)['passed'])

    def test_unknown_model_not_comparable(self):
        runs=self.check.example_run_metadata()
        for r in runs:r['environment']['model']='unknown'
        self.assertFalse(self.check.check_comparability(runs)['comparable'])

    def test_incomplete_budget_metadata_not_comparable(self):
        runs=self.check.example_run_metadata()
        for r in runs:r['environment'].pop('max_output_tokens')
        self.assertFalse(self.check.check_comparability(runs)['comparable'])


class DepthContractHardeningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec=importlib.util.spec_from_file_location('depth_contract_hardening',COLLECTION/'depth'/'check_outputs.py')
        cls.check=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.check)

    def test_matching_invalid_numeric_budgets_do_not_establish_comparability(self):
        for field,values in {'time_budget_seconds':[None,0,-1,True,float('nan')],
                             'max_output_tokens':[None,0,-1,True,2.5],
                             'temperature':[None,-1,True,float('inf')]}.items():
            for value in values:
                with self.subTest(field=field,value=value):
                    runs=self.check.example_run_metadata()
                    for r in runs:r['environment'][field]=value
                    self.assertFalse(self.check.check_comparability(runs)['comparable'])

    def test_invalid_tool_inventory_is_not_comparable(self):
        for value in ('all',None,[{}],['browser','browser']):
            runs=self.check.example_run_metadata()
            for r in runs:r['environment']['tools']=value
            self.assertFalse(self.check.check_comparability(runs)['comparable'])

    def test_invalid_context_hash_is_not_comparable(self):
        for value in ('unknown','a'*63,None):
            runs=self.check.example_run_metadata()
            for r in runs:r['environment']['supplied_context_sha256']=value
            self.assertFalse(self.check.check_comparability(runs)['comparable'])

    def test_model_identity_whitespace_does_not_hide_unknown(self):
        runs=self.check.example_run_metadata()
        for r in runs:r['environment']['model']=' unknown '
        self.assertFalse(self.check.check_comparability(runs)['comparable'])

    def test_missing_or_invalid_platform_is_not_comparable(self):
        for value in (None,'','unknown'):
            runs=self.check.example_run_metadata()
            for r in runs:r['environment']['platform']=value
            self.assertFalse(self.check.check_comparability(runs)['comparable'])

    def test_comparison_case_order_must_match(self):
        runs=self.check.example_run_metadata()
        for r in runs:r['case_ids']=['case-a','case-b']
        runs[1]['case_ids'].reverse()
        self.assertFalse(self.check.check_comparability(runs)['comparable'])

    def test_unsafe_archive_member_names_are_rejected(self):
        for name in ('../escape','/absolute','C:/drive','a/../b','a\\b','a//b',
                     'a/./b','a/CON.txt','trail./file','file:stream','a/','nul','a\x00b'):
            with self.subTest(name=name):
                with self.assertRaises(mod.CollectionError):mod.build_file_map_bytes({name:b'x'})

    def test_cross_platform_archive_collisions_rejected(self):
        with self.assertRaises(mod.CollectionError):
            mod.build_file_map_bytes({'A.md':b'x','a.md':b'y'})

    def test_archive_file_directory_collision_rejected(self):
        with self.assertRaises(mod.CollectionError):
            mod.build_file_map_bytes({'one':b'x','one/two':b'y'})

    def test_archive_values_are_bytes(self):
        with self.assertRaises(mod.CollectionError):mod.build_file_map_bytes({'a.md':'not bytes'})

    def test_empty_archive_refused(self):
        with self.assertRaises(mod.CollectionError):mod.build_file_map_bytes({})

    def test_owned_bug_example_fails_before_and_passes_after(self):
        def original(items):return sum(items[:-1])
        def repaired(items):return sum(items)
        cases=[([],0),([4],4),([5,7],12),([-3,8],5),([0,0],0)]
        failures=[items for items,want in cases if original(items)!=want]
        self.assertEqual(failures,[[4],[5,7],[-3,8]])
        self.assertTrue(all(repaired(items)==want for items,want in cases))

class ManagedMuseComparisonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec=importlib.util.spec_from_file_location('managed_muse_checks',COLLECTION/'depth'/'check_outputs.py')
        cls.check=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.check)

    def test_managed_opaque_model_allows_limited_host_matched_comparison(self):
        runs=self.check.example_run_metadata()
        for r in runs:
            r['environment']['model']=None
            r['environment']['model_visibility']='managed-opaque'
            r['environment']['visible_model_setting']='provider default; no model selector'
        result=self.check.check_comparability(runs)
        self.assertTrue(result['comparable'],result)
        self.assertEqual(result['comparison_scope'],'HOST_MATCHED_MODEL_OPAQUE')
        self.assertFalse(result['underlying_model_parity_verified'])

    def test_opaque_model_requires_observed_setting_not_invented_model(self):
        runs=self.check.example_run_metadata()
        for r in runs:
            r['environment']['model']=None
            r['environment']['model_visibility']='managed-opaque'
        self.assertFalse(self.check.check_comparability(runs)['comparable'])

    def test_opaque_and_declared_arms_cannot_be_mixed(self):
        runs=self.check.example_run_metadata()
        runs[1]['environment'].update(model=None,model_visibility='managed-opaque',
            visible_model_setting='provider default; no model selector')
        self.assertFalse(self.check.check_comparability(runs)['comparable'])

class ObservableContextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec=importlib.util.spec_from_file_location('observable_context',COLLECTION/'depth'/'check_outputs.py')
        cls.check=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.check)

    def test_hash_names_supplied_context_not_hidden_provider_memory(self):
        runs=self.check.example_run_metadata()
        self.assertIn('supplied_context_sha256',runs[0]['environment'])
        self.assertNotIn('memory_context_sha256',runs[0]['environment'])

    def test_memory_mode_is_an_observation_not_a_hidden_state_attestation(self):
        runs=self.check.example_run_metadata()
        self.assertIn('memory_mode_observed',runs[0]['environment'])
        for r in runs:r['environment']['memory_mode_observed']=None
        self.assertFalse(self.check.check_comparability(runs)['comparable'])

class ParticipantScopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=mod.load_collection(COLLECTION)
        spec=importlib.util.spec_from_file_location('participant_scope',COLLECTION/'depth'/'check_outputs.py')
        cls.check=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.check)

    def test_participant_does_not_receive_unavailable_practice_instructions(self):
        for case in self.data['depth_cases']:
            packet=mod.challenge_files(self.data,case['id'],'candidate')
            depth=packet['skills/'+case['skill_id']+'/DEPTH.md'].decode()
            self.assertNotIn('Practice case IDs:',depth)
            self.assertNotIn('practice/check_outputs.py',depth)

    def test_explicitly_opaque_sampling_setting_has_limited_comparison(self):
        runs=self.check.example_run_metadata()
        for r in runs:
            r['environment']['temperature']=None
            r['environment']['temperature_visibility']='managed-opaque'
        result=self.check.check_comparability(runs)
        self.assertTrue(result['comparable'],result)
        self.assertEqual(result['comparison_scope'],'HOST_MATCHED_SETTINGS_PARTLY_OPAQUE')

    def test_opaque_sampling_setting_must_not_invent_temperature(self):
        runs=self.check.example_run_metadata()
        for r in runs:r['environment']['temperature_visibility']='managed-opaque'
        self.assertFalse(self.check.check_comparability(runs)['comparable'])

if __name__=='__main__':unittest.main()

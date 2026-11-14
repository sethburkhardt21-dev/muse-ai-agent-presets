#!/usr/bin/env python3
"""Optional, offline mechanical checks for supplied C100 practice outputs.

This program does not call a model, execute candidate code, inspect a live
account, or authenticate provider evidence. Human semantic/visual review is
always required. Expected examples are authored fixtures, not observed runs.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timedelta
import json
import math
import os
from pathlib import Path
import stat
import sys
from typing import Any

MAX_BYTES = 2_000_000

class ContractError(ValueError):
    """An input or output does not meet a closed-world fixture contract."""

def require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)

def text(value: Any, name: str) -> str:
    require(isinstance(value,str) and bool(value.strip()) and len(value)<=30000,
            name+' must be nonempty bounded text')
    return value

def number(value: Any, name: str) -> float:
    require(type(value) in (int,float) and math.isfinite(value),name+' must be finite numeric data')
    return value

def records(value: Any, name: str, key: str) -> dict[str,dict[str,Any]]:
    require(isinstance(value,list) and len(value)<=1000,name+' must be a bounded list')
    result={}
    for row in value:
        require(isinstance(row,dict),name+' contains a non-object')
        ident=text(row.get(key),name+'.'+key)
        require(ident not in result,'duplicate '+name+' identity: '+ident)
        result[ident]=row
    return result

def ids(value: Any, name: str) -> list[str]:
    require(isinstance(value,list) and len(value)<=1000,name+' must be a bounded list')
    for v in value:text(v,name)
    require(len(value)==len(set(value)),name+' has duplicate identities')
    return value

def instant(value: Any) -> datetime:
    result=datetime.fromisoformat(text(value,'timestamp').replace('Z','+00:00'))
    require(result.tzinfo is not None and result.utcoffset() is not None,'timestamp needs an explicit offset')
    return result

def _daily(c: dict[str,Any], o: dict[str,Any]) -> None:
    i=c['inputs']; tasks=records(i['tasks'],'tasks','id')
    start,end=instant(i['window']['start']),instant(i['window']['end'])
    require(start<end,'empty work window')
    priorities=ids(o['priority_ids'],'priority_ids')
    expected=sorted(tasks,key=lambda x:tasks[x]['priority'])[:3]
    require(priorities==expected,'priority order differs from the supplied order')
    occupied=[]
    for e in i['events']:
        a,b=instant(e['start']),instant(e['end'])+timedelta(minutes=number(e['buffer_after_minutes'],'buffer'))
        require(a<b,'invalid fixed interval')
        occupied.append((max(start,a),min(end,b)))
    schedule=records(o['schedule'],'schedule','task_id');deferred=records(o['deferred'],'deferred','task_id')
    require(not (schedule.keys() & deferred.keys()),'task both scheduled and deferred')
    require(schedule.keys() | deferred.keys()==tasks.keys(),'tasks missing or invented')
    for tid,row in deferred.items():
        text(row.get('reason'),'deferral reason')
        # These fixtures explicitly require the first two deadlines to be met.
        require(tasks[tid]['priority']>2,'high-priority required task was deferred')
    for tid,row in schedule.items():
        a,b=instant(row['start']),instant(row['end'])
        require(start<=a<b<=end,'task outside the work window')
        require((b-a).total_seconds()==60*number(tasks[tid]['minutes'],'task duration'),'silently shortened or extended task')
        if tasks[tid]['deadline'] is not None:require(b<=instant(tasks[tid]['deadline']),'task misses deadline')
        for x,y in occupied:require(not (x<y and a<y and x<b),'overlapping task, event or buffer')
        occupied.append((a,b))
    # Merge fixed intervals so an overlap does not double-count occupied time.
    intervals=sorted((a,b) for a,b in occupied if a<b); merged=[]
    for a,b in intervals:
        if merged and a<=merged[-1][1]:merged[-1]=(merged[-1][0],max(merged[-1][1],b))
        else:merged.append((a,b))
    free=(end-start).total_seconds()/60-sum((b-a).total_seconds()/60 for a,b in merged)
    require(free>=i['minimum_free_minutes'],'requested free buffer is missing')
    require(o['external_actions_performed'] is False,'draft represented as an external action')
    text(o.get('brief'),'brief')

def _flashcards(c: dict[str,Any], o: dict[str,Any]) -> None:
    i=c['inputs'];targets=records(i['targets'],'targets','id');cards=records(o['cards'],'cards','id')
    require(cards.keys()==targets.keys(),'cards missing, duplicated, disputed or invented')
    require(set(ids(o['held_ids'],'held_ids'))==set(i['hold_ids']),'disputed cards must remain held')
    sources={(s['source_id'],s['locator']):s['text'] for s in i['sources']}
    for key,t in targets.items():
        row=cards[key]
        require(row['source_id']==t['source_id'] and row['locator']==t['locator'],'wrong source location')
        require(text(row['quote'],'quote') in sources[(row['source_id'],row['locator'])],'quote not present at locator')
        answer=text(row['answer'],'answer').strip().rstrip('.')
        # Exact-answer exercises are intentional; paraphrase quality is a human check.
        require(answer.casefold()==c['oracle']['answers'][key].casefold(),'value, units or condition differ from closed-answer target')
        q=text(row['question'],'question')
        require(answer.casefold() not in q.casefold(),'question leaks its answer')
    text(o.get('notes'),'notes')

def _claims(c: dict[str,Any], o: dict[str,Any]) -> None:
    i=c['inputs'];claims=records(i['claims'],'claims','id');findings=records(o['findings'],'findings','claim_id')
    require(findings.keys()==claims.keys(),'missing or invented claim')
    source=records(i['records'],'evidence records','id')
    for key,row in findings.items():
        expected=c['oracle'][key]
        require(row['verdict']==expected['verdict'],'incorrect claim scope or verdict')
        ev=records(row['evidence'],'claim evidence','record_id')
        require(set(expected['record_ids'])<=ev.keys()<=source.keys(),'missing or invented evidence')
        for rid,e in ev.items():
            require(e['locator']==source[rid]['locator'],'wrong evidence locator')
            require(text(e['quote'],'evidence quote') in source[rid]['text'],'unsupported quote')
        text(row.get('reason'),'reason')
    text(o.get('summary'),'summary')

def _bug(c: dict[str,Any], o: dict[str,Any]) -> None:
    i=c['inputs'];run=i['run']
    if 'ModuleNotFoundError:' in run['log']:outcome,action='setup-blocked','repair_test_setup'
    elif i['observed']==i['expected'] and run['exit_code']==0:outcome,action='not-reproduced','narrow_report'
    elif 'AssertionError:' in run['log'] and run['exit_code']!=0:outcome,action='reproduced','repair_with_regression'
    else:raise ContractError('fixture has no classifiable observation')
    require(o['outcome']==outcome and o['next_action']==action,'setup, reproduction and repair stages conflated')
    for a,b in [('revision','source_revision'),('input','input'),('expected','expected'),('actual','observed'),('control_result','control_observed')]:
        require(o[a]==i[b],'altered reproduction '+a)
    require(o['test_executed_by_respondent'] is False,'invented respondent execution')
    text(o.get('explanation'),'explanation')

def _review(c: dict[str,Any], o: dict[str,Any]) -> None:
    i=c['inputs'];findings=records(o['findings'],'findings','id')
    require(set(c['oracle']['required_finding_ids'])==findings.keys(),'missed defect or false-positive finding')
    for key,f in findings.items():
        require(f['path']==i['path'] and type(f['line']) is int and f['line']==2,'wrong source location')
        require(f['severity']=='blocker','contract failure incorrectly classified')
        for field in ('impact','suggestion'):text(f.get(field),field)
        if key=='dropped-final-item':require(f['example_input']==[5,7] and f['expected']==12,'wrong failing example')
        if key=='empty-input-crash':require(f['example_input']==[] and f['expected']==0,'wrong boundary example')
    require(o['reviewer_independence']=='NOT_ESTABLISHED','invented reviewer independence')
    text(o.get('summary'),'summary')

def _continuity(c: dict[str,Any], o: dict[str,Any]) -> None:
    i=c['inputs'];expected=[]
    for obs in i['observations']:
        for attr,value in i['invariants'].items():
            if attr in obs and obs[attr]!=value:expected.append((obs['frame'],obs['shot'],attr,value,obs[attr]))
    require(isinstance(o['findings'],list),'findings must be a list')
    found=[(f['frame'],f['shot'],f['attribute'],f['expected'],f['observed']) for f in o['findings']]
    require(len(found)==len(set(found)) and set(found)==set(expected),'missed continuity break or unapproved false positive')
    require(o['direct_visual_inspection'] is False,'invented direct image inspection')
    require(o['review_scope']==i['available_evidence'],'incorrect review scope')
    require(set(ids(o['repair_shots'],'repair_shots'))=={x[1] for x in expected},'repair exceeds or misses affected shots')
    require(ids(o['unreviewed_frames'],'unreviewed_frames')==(['ALL'] if not i['observations'] else []),'missing observation coverage not reported')
    text(o.get('summary'),'summary')

def _models(c: dict[str,Any], o: dict[str,Any]) -> None:
    i=c['inputs'];n=len(i['labels']);require(n>0,'empty planned case set')
    scores={role:sum(i[role].get(k)==v for k,v in i['labels'].items())/n for role in ('baseline','candidate')}
    delta=scores['candidate']-scores['baseline']
    eligible=i['environment_baseline']==i['environment_candidate']
    decision='candidate-within-this-protocol' if eligible and delta>=i['minimum_delta'] else 'no-decision'
    for key,value in [('baseline_accuracy',scores['baseline']),('candidate_accuracy',scores['candidate']),('delta',delta)]:
        require(abs(number(o[key],key)-value)<1e-9,'incorrect metric or denominator: '+key)
    require(type(o['case_count']) is int and o['case_count']==n,'case count does not match plan')
    require(o['decision']==decision,'decision contradicts frozen conditions or threshold')
    require(o['general_superiority'] is False,'public fixture result promoted to general superiority')
    text(o.get('reason'),'reason')

def _resume(c: dict[str,Any], o: dict[str,Any]) -> None:
    i=c['inputs'];steps=records(i['steps'],'steps','id');actions=records(o['actions'],'actions','step_id')
    require(steps.keys()==actions.keys(),'missing, duplicated or invented step')
    expected={'completed':'read_existing','unknown':'reconcile_original','not-started':'execute_once_after_precheck','denied':'do_not_bypass'}
    for key,s in steps.items():
        a=actions[key]
        require(a['action']==expected[s['state']],'unsafe replay, refusal bypass or lost completed work')
        require(a['operation_id']==s['operation_id'],'original operation identity changed')
    require(set(ids(o['independent_work'],'independent_work'))==set(i['independent_step_ids']),'independent work unnecessarily blocked or invented')
    require(o['new_external_actions_performed'] is False,'invented execution')
    text(o.get('summary'),'summary')

# R3 domain checks. All calculations use supplied fixture inputs, never an
# authored reference_output. Two extraction tasks additionally use a private
# adjudication oracle; that checks traceability, not general language quality.
from collections import Counter
from decimal import Decimal, InvalidOperation
import re


def _r3_int(value: Any, name: str, minimum: int = 0) -> int:
    require(type(value) is int and value >= minimum, name+' must be an integer at least '+str(minimum))
    return value


def _r3_bool(value: Any, name: str) -> bool:
    require(type(value) is bool, name+' must be boolean')
    return value


def _r3_list(value: Any, name: str) -> list[Any]:
    require(isinstance(value,list) and len(value)<=1000,name+' must be a bounded list')
    return value


def _r3_equal(actual: Any, expected: Any, path: str='output') -> None:
    """Typed comparison of independently calculated facts, not prose quality."""
    if type(expected) is float:
        require(type(actual) in (int,float) and math.isfinite(actual) and
                math.isclose(actual,expected,rel_tol=1e-9,abs_tol=1e-9),path+' differs from calculated value')
    elif isinstance(expected,dict):
        require(isinstance(actual,dict) and set(actual)==set(expected),path+' has missing or undeclared fields')
        for key,value in expected.items():_r3_equal(actual[key],value,path+'.'+key)
    elif isinstance(expected,list):
        require(isinstance(actual,list) and len(actual)==len(expected),path+' has missing or duplicate entries')
        # Ordering is material for a selected execution sequence and an exact
        # supplied instruction list; other record/set outputs may be reordered.
        if path.rsplit('.',1)[-1] not in ('selected','instructions'):
            key=lambda x:json.dumps(x,sort_keys=True,ensure_ascii=False,allow_nan=False)
            actual=sorted(actual,key=key);expected=sorted(expected,key=key)
        for n,(a,b) in enumerate(zip(actual,expected)):_r3_equal(a,b,path+f'[{n}]')
    else:
        require(type(actual) is type(expected) and actual==expected,path+' differs from supported fact')


def _r3_weekly(c: dict[str,Any]) -> dict[str,Any]:
    i=c['inputs'];usable=_r3_int(i['available_minutes'],'available')-_r3_int(i['reserve_minutes'],'reserve')
    require(usable>=0,'reserve exceeds availability')
    rows=records(i['tasks'],'tasks','id');selected=[];deferred=[];blocked=[];used=0
    completed=[tid for tid,t in rows.items() if t['state']=='done']
    for t in rows.values():
        require(set(ids(t['dependencies'],'task dependencies'))<=rows.keys(),'unknown task dependency')
    for tid,t in sorted(rows.items(),key=lambda x:(_r3_int(x[1]['priority'],'priority'),x[0])):
        minutes=_r3_int(t['minutes'],'task minutes',1);state=t['state']
        require(state in ('ready','blocked','done'),'invalid task state')
        if state=='done':continue
        elif state=='blocked' or not set(t['dependencies'])<=set(completed+selected):blocked.append(tid)
        elif used+minutes<=usable:selected.append(tid);used+=minutes
        else:deferred.append(tid)
    return dict(usable_minutes=usable,selected=selected,deferred=deferred,blocked=blocked,
                completed=completed,allocated_minutes=used,remaining_minutes=usable-used)


def _r3_inbox(c: dict[str,Any]) -> dict[str,Any]:
    events=records(c['inputs']['events'],'events','id');threads={}
    for eid,e in sorted(events.items(),key=lambda x:(instant(x[1]['at']),x[0])):
        tid=text(e['thread_id'],'thread id');kind=e['kind']
        require(kind in ('received','sent','draft','cancelled','send_unknown','suspicious'),'unknown mail event')
        r=threads.setdefault(tid,dict(thread_id=tid,status='reply',evidence_ids=[],deadline=None))
        r['evidence_ids'].append(eid)
        if kind=='received':r['status']='reply';r['deadline']=e['deadline']
        elif kind=='sent':r['status']='waiting';r['deadline']=None
        elif kind=='cancelled':r['status']='closed';r['deadline']=None
        elif kind=='send_unknown':r['status']='reconcile'
        elif kind=='suspicious':r['status']='verify'
    return dict(threads=list(threads.values()),external_actions=[])


def _r3_meeting(c: dict[str,Any]) -> dict[str,Any]:
    lines=records(c['inputs']['transcript'],'transcript','id');a=c['semantic_oracle']
    decisions=ids(a['decision_lines'],'decision lines');unresolved=ids(a['unresolved_lines'],'unresolved lines')
    require(set(decisions+unresolved)<=lines.keys(),'oracle references missing transcript lines')
    actions=records(a['actions'],'actions','id')
    for row in actions.values():
        require(set(ids(row['source_lines'],'action sources'))<=lines.keys(),'action source missing')
        text(row['owner'],'owner');require(row['due'] is None or isinstance(row['due'],str),'invalid due date')
    return dict(decision_lines=decisions,actions=list(actions.values()),unresolved_lines=unresolved,external_actions=[])


def _r3_budget(c: dict[str,Any]) -> dict[str,Any]:
    i=c['inputs'];h=_r3_int(i['horizon_months'],'horizon',1);cap=_r3_int(i['cash_cap_cents'],'cash cap')
    rows=records(i['options'],'options','id');out=[]
    for oid,r in rows.items():
        setup=_r3_int(r['setup_cents'],'setup');monthly=_r3_int(r['monthly_cents'],'monthly')
        prepay=_r3_int(r['prepay_months'],'prepay months');block=_r3_int(r['prepay_cents'],'prepay cents')
        deposit=_r3_int(r['deposit_cents'],'deposit')
        require(not(prepay and monthly),'ambiguous mixed billing fixture')
        require(prepay>0 or block==0,'prepay amount without billing interval')
        cost=setup+(((h+prepay-1)//prepay)*block if prepay else h*monthly)
        cash=setup+(block if prepay else monthly)+deposit
        out.append(dict(id=oid,cost_cents=cost,cash_today_cents=cash,feasible=cash<=cap))
    feasible=[r for r in out if r['feasible']]
    minimum=min((r['cost_cents'] for r in feasible),default=None)
    return dict(options=out,cheapest_feasible_ids=[r['id'] for r in feasible if r['cost_cents']==minimum])


def _r3_lecture(c: dict[str,Any]) -> dict[str,Any]:
    slides=records(c['inputs']['slides'],'slides','id');a=c['semantic_oracle']
    unread=[sid for sid,s in slides.items() if not _r3_bool(s['readable'],'slide readability')]
    concepts=records(a['concepts'],'concepts','id')
    for row in concepts.values():
        refs=ids(row['source_slides'],'concept sources')
        require(bool(refs) and set(refs)<=slides.keys() and not(set(refs)&set(unread)),'concept cites unread source')
    edges=_r3_list(a['prerequisite_edges'],'edges')
    for edge in edges:require(isinstance(edge,list) and len(edge)==2 and set(edge)<=concepts.keys(),'invalid prerequisite edge')
    return dict(concepts=list(concepts.values()),prerequisite_edges=edges,unreadable_slides=unread,full_source_reviewed=not unread)


def _r3_retrieval(c: dict[str,Any]) -> dict[str,Any]:
    i=c['inputs'];rubric=records(i['rubric'],'rubric','item_id');seen={};out=[];independent=0;assisted=0
    for r in _r3_list(i['attempts'],'attempts'):
        aid=text(r['attempt_id'],'attempt');require(r['item_id'] in rubric,'unknown rubric item')
        if aid in seen:
            require(seen[aid]==r,'conflicting replay cannot be scored');continue
        seen[aid]=r;helped=_r3_bool(r['assisted'],'assisted')
        score=len(set(ids(r['concepts'],'answer concepts'))&set(ids(rubric[r['item_id']]['concepts'],'rubric concepts')))
        out.append(dict(attempt_id=aid,score=score,independent=not helped))
        if helped:assisted+=score
        else:independent+=score
    return dict(attempts=out,independent_points=independent,assisted_points=assisted,mastery_claim=False)


def _r3_misconception(c: dict[str,Any]) -> dict[str,Any]:
    i=c['inputs'];flags=[_r3_bool(i[k],k) for k in ('concept_rule_wrong','transcription_error','condition_missing')]
    require(sum(flags)<=1,'ambiguous diagnosis requires a different fixture')
    diagnosis=['conceptual-rule','transcription','missing-condition'][flags.index(True)] if any(flags) else 'insufficient-evidence'
    probes=ids(i['available_probes'],'probes');new=[p for p in probes if p!=i['original_item']]
    require(bool(new),'no distinct transfer probe')
    return dict(diagnosis=diagnosis,original_reasoning_preserved=True,
                transfer_status='observed' if _r3_bool(i['independent_transfer_observed'],'transfer observation') else 'untested',next_probe_id=new[0])


def _r3_exam(c: dict[str,Any]) -> dict[str,Any]:
    i=c['inputs'];available=_r3_int(i['available_minutes'],'available');reserve=_r3_int(i['reserve_minutes'],'reserve')
    require(available>=reserve,'reserve exceeds availability');capacity=available-reserve
    topics=records(i['topics'],'topics','id');completed=[k for k,v in topics.items() if v['state']=='done'];selected=[];deferred=[];used=0
    for tid,t in sorted(topics.items(),key=lambda x:(_r3_int(x[1]['priority'],'priority'),x[0])):
        m=_r3_int(t['minutes'],'topic minutes',1)
        if tid in completed:continue
        deps=set(ids(t['dependencies'],'prerequisites'))
        if t['state']=='ready' and deps<=set(completed+selected) and used+m<=capacity:selected.append(tid);used+=m
        else:deferred.append(tid)
    return dict(study_capacity=capacity,selected=selected,completed=completed,deferred=deferred,
                study_minutes=used,total_minutes=used+reserve,readiness_certified=False)


def _r3_question(c: dict[str,Any]) -> dict[str,Any]:
    i=c['inputs'];sources=records(i['sources'],'sources','id');claims=records(i['claims'],'claims','id');out=[]
    excluded=[sid for sid,s in sources.items() if not _r3_bool(s['accessed'],'accessed') or not _r3_bool(s['active'],'active')]
    for cid,claim in claims.items():
        require(claim['kind'] in ('descriptive','causal'),'unknown question type');supports=[]
        for sid in ids(claim['source_ids'],'claim sources'):
            require(sid in sources,'unknown source');s=sources[sid]
            if sid not in excluded and (claim['kind']=='descriptive' or s['design']=='controlled'):supports.append(sid)
        out.append(dict(id=cid,status='supported' if supports else 'unresolved',supporting_source_ids=supports))
    return dict(claims=out,excluded_source_ids=excluded)


def _r3_literature(c: dict[str,Any]) -> dict[str,Any]:
    rows=records(c['inputs']['records'],'records','id');doi_seen={};families=set();awaiting=[];excluded=[];duplicates=[]
    for rid,r in rows.items():
        doi=text(r['doi'],'doi')
        if doi in doi_seen:
            prior=doi_seen[doi]
            require(prior['study_id']==r['study_id'] and prior['eligible']==r['eligible'] and prior['full_text']==r['full_text'],'conflicting duplicate report')
            duplicates.append(rid);continue
        doi_seen[doi]=r
        if not _r3_bool(r['full_text'],'full text') or r['eligible'] is None:awaiting.append(rid)
        elif _r3_bool(r['eligible'],'eligible'):families.add(text(r['study_id'],'study family'))
        else:excluded.append(rid)
    return dict(unique_report_count=len(doi_seen),included_study_ids=sorted(families),awaiting_record_ids=awaiting,
                excluded_record_ids=excluded,duplicate_record_ids=duplicates)


def _r3_hypotheses(c: dict[str,Any]) -> dict[str,Any]:
    i=c['inputs'];hs=ids(i['hypotheses'],'hypotheses');tests=records(i['tests'],'tests','id');choices=[];eliminated=set()
    require(isinstance(i['observations'],dict),'observations must be an object')
    require(set(i['observations'])<=tests.keys(),'unknown observed test')
    for tid,t in tests.items():
        require(set(t['predictions'])==set(hs),'incomplete prediction matrix')
        vals=[text(v,'prediction') for v in t['predictions'].values()]
        if len(set(vals))>1:choices.append((_r3_int(t['cost'],'cost'),tid))
        observed=i['observations'].get(tid)
        if observed is not None:
            text(observed,'observed result');eliminated.update(h for h in hs if t['predictions'][h]!=observed)
    return dict(chosen_test_id=min(choices)[1] if choices else None,eliminated_hypotheses=sorted(eliminated))


def _r3_interviews(c: dict[str,Any]) -> dict[str,Any]:
    i=c['inputs'];ps=records(i['participants'],'participants','id');qs=records(i['quotes'],'quotes','id')
    asked={p for p,r in ps.items() if _r3_bool(r['asked'],'asked')};support=set();dissent=set();evidence=[]
    for qid,q in qs.items():
        require(q['participant'] in ps,'unknown participant')
        if q['theme']!=i['theme']:continue
        require(q['participant'] in asked,'quote from participant marked unasked')
        (support if _r3_bool(q['supports'],'supports') else dissent).add(q['participant'])
        evidence.append(dict(id=qid,text=text(q['text'],'quote')))
    return dict(supporters=sorted(support),dissenters=sorted(dissent),not_asked=sorted(set(ps)-asked),denominator=len(asked),
                support_fraction=len(support)/len(asked) if asked else None,quoted_evidence=evidence,population_claim=False)


def _r3_repair(c: dict[str,Any]) -> dict[str,Any]:
    i=c['inputs'];verified=[];checks=records(i['checks'],'checks','id')
    if i['current']!=i['base']:status='source-drift'
    elif not _r3_bool(i['reproduced'],'reproduced'):status='unreproduced'
    elif not set(ids(i['changed_files'],'changed files'))<=set(ids(i['allowed_files'],'allowed files')):status='scope-violation'
    elif not checks or any(not _r3_bool(r['passed'],'passed') or r['candidate']!=i['candidate'] for r in checks.values()):status='test-failure'
    else:status='locally-verified';verified=list(checks)
    return dict(status=status,patch_admissible=status=='locally-verified',verified_checks=verified,deployed=False)


def _r3_api(c: dict[str,Any]) -> dict[str,Any]:
    i=c['inputs']
    if i['mode']=='compatibility':
        breaking=(_r3_bool(i['optional_response_field_added'],'field added') and
                  _r3_bool(i['strict_unknown_field_decoder'],'strict decoder') and not _r3_bool(i['consumer_updated'],'consumer updated'))
        return dict(compatible=not breaking,reason_code='strict-client-break' if breaking else 'compatible-under-supplied-contract')
    require(i['mode']=='idempotency','unknown API fixture mode');r=i['record'];q=i['request']
    same=all(r[k]==q[k] for k in ('principal','operation','key'))
    if not same:outcome='new-request';resource=None
    elif r['payload']!=q['payload']:outcome='conflict';resource=None
    elif r['state']=='unknown':outcome='reconcile';resource=None
    elif r['state']=='completed':outcome='replay';resource=r['resource_id']
    else:raise ContractError('unsupported idempotency state')
    return dict(outcome=outcome,resource_id=resource,new_effects=0)


def _r3_access(c: dict[str,Any]) -> dict[str,Any]:
    i=c['inputs'];rows=records(i['checks'],'checks','id');out=[]
    for cid,r in rows.items():
        require(r['observed'] in ('pass','fail','not-tested','not-applicable'),'invalid observed check')
        out.append(dict(id=cid,status=r['observed']))
    statuses={x['status'] for x in out}
    overall='barrier-found' if 'fail' in statuses else 'incomplete' if 'not-tested' in statuses or not rows else 'scoped-pass'
    complete=_r3_bool(i['full_scope'],'full scope') and overall=='scoped-pass'
    return dict(checks=out,overall=overall,conformance='scope-conforms' if complete else 'undetermined')


def _r3_release(c: dict[str,Any]) -> dict[str,Any]:
    i=c['inputs'];rows=records(i['obligations'],'obligations','id');gates=[];ready=bool(rows)
    for gid,g in rows.items():
        required=_r3_bool(g['required'],'required');applicable=_r3_bool(g['applicable'],'applicable');r=g['receipt']
        if not applicable:s='not-applicable'
        elif r is None:s='not-run'
        elif r['candidate']!=i['candidate']:s='stale'
        else:s=r['status'];require(s in ('pass','fail','not-run'),'invalid gate outcome')
        gates.append(dict(id=gid,status=s))
        if required and applicable and s!='pass':ready=False
    require(i['publication_status'] in ('not-performed','unknown','confirmed'),'invalid publication state')
    return dict(gates=gates,verdict='GO' if ready else 'HOLD',publication_status=i['publication_status'])


def _r3_brief(c: dict[str,Any]) -> dict[str,Any]:
    i=c['inputs'];proposals=records(i['proposed_choices'],'proposals','id');conflicts=records(i['conflicts'],'conflicts','id')
    require(isinstance(i['confirmed_constraints'],dict),'invalid confirmed constraints')
    protected=ids(i['protected_text'],'protected text')
    acceptance='blocked-conflict' if conflicts else 'approved' if _r3_bool(i['user_approved'],'user approved') else 'proposed'
    return dict(confirmed_constraints=i['confirmed_constraints'],proposed_choice_ids=list(proposals),protected_text=protected,
                conflict_ids=list(conflicts),acceptance=acceptance,deliverable='brief')


def _r3_story(c: dict[str,Any]) -> dict[str,Any]:
    i=c['inputs'];shots=records(i['shots'],'shots','id');overlaps=_r3_list(i['overlap_frames'],'overlaps')
    require(len(overlaps)==max(0,len(shots)-1),'transition count differs from shot boundaries')
    frame_counts=[_r3_int(s['frames'],'shot frames',1) for s in shots.values()]
    for index,v in enumerate(overlaps):
        v=_r3_int(v,'overlap');require(v<=min(frame_counts[index:index+2]),'overlap exceeds adjacent shot')
    total=sum(frame_counts)-sum(overlaps);require(total>=0,'negative timeline')
    fps=_r3_int(i['fps'],'fps',1);breaks=[];previous=None
    for sid,s in shots.items():
        if previous is not None and s['in_state']!=previous and not _r3_bool(s['allowed_transition'],'allowed transition'):breaks.append(sid)
        previous=s['out_state']
    return dict(total_frames=total,duration_seconds=total/fps,target_met=total==_r3_int(i['target_frames'],'target',1),continuity_breaks=breaks,rendered=False)


def _r3_media(c: dict[str,Any]) -> dict[str,Any]:
    i=c['inputs'];r=i['required'];v=i['observed'];missing=[]
    exists=_r3_bool(v['exists'],'file exists')
    if not exists:missing=['render']
    else:
        if (v['width'],v['height'])!=(r['width'],r['height']):missing.append('dimensions')
        if v['fps']!=r['fps']:missing.append('fps')
        duration=number(v['duration'],'duration')
        if not number(r['min_duration'],'minimum')<=duration<=number(r['max_duration'],'maximum'):missing.append('duration')
        if _r3_bool(r['audio'],'required audio') and not _r3_bool(v['audio'],'observed audio'):missing.append('audio')
        if _r3_bool(r['captions'],'required captions') and not _r3_bool(v['captions'],'observed captions'):missing.append('captions')
        if not _r3_bool(v['visual_checked'],'visual check'):missing.append('visual-inspection')
    return dict(completion='blocked' if not exists else 'rendered-partial' if missing else 'rendered-complete',
                missing_requirements=missing,delivery_status=text(i['delivery_status'],'delivery status'))


def _r3_prose(c: dict[str,Any],o: dict[str,Any]) -> None:
    i=c['inputs'];source=text(i['text'],'source');revised=text(o['revised_text'],'revision')
    require(set(o)=={'revised_text','mode','protected_spans_preserved'},'undeclared prose output fields')
    require(i['mode'] in ('edit','audit') and o['mode']==i['mode'],'wrong edit mode')
    if i['mode']=='audit':require(revised==source,'audit changed source')
    for span in ids(i['protected'],'protected spans'):require(span in revised,'protected literal changed')
    for phrase in ids(i['required_phrases'],'required qualifiers'):require(phrase in revised,'required qualifier missing')
    numeric=lambda s:Counter(re.findall(r'(?<![A-Za-z0-9_])\d+(?:\.\d+)?%?',s))
    require(not (numeric(revised)-numeric(source)),'revision added an unsupported numeric claim')
    require(o['protected_spans_preserved'] is True,'preservation status mismatch')


def _r3_project(c: dict[str,Any]) -> dict[str,Any]:
    i=c['inputs'];rows=records(i['tasks'],'tasks','id');cap=i['capacity'];require(isinstance(cap,dict) and bool(cap),'missing resource capacity')
    for k,v in cap.items():text(k,'resource');_r3_int(v,'capacity')
    complete=[k for k,r in rows.items() if _r3_bool(r['done'],'done')];selected=[];blocked=[];used={k:0 for k in cap}
    def closure(tid: str, visiting: set[str], order: list[str]) -> None:
        if tid in complete or tid in selected or tid in order:return
        require(tid in rows,'missing dependency '+tid)
        if tid in visiting:raise ContractError('dependency cycle')
        visiting.add(tid)
        for dependency in ids(rows[tid]['deps'],'dependencies'):closure(dependency,visiting,order)
        visiting.remove(tid);order.append(tid)
    for tid,r in sorted(rows.items(),key=lambda x:(_r3_int(x[1]['priority'],'priority'),x[0])):
        if tid in complete or tid in selected:continue
        bundle=[]
        try:closure(tid,set(),bundle)
        except ContractError:blocked.append(tid);continue
        cost={k:0 for k in cap}
        for item in bundle:
            effort=rows[item]['effort'];require(isinstance(effort,dict) and set(effort)<=set(cap),'unknown required resource')
            for resource,n in effort.items():cost[resource]+=_r3_int(n,'effort')
        if all(used[k]+cost[k]<=cap[k] for k in cap):
            selected.extend(bundle)
            for k in cap:used[k]+=cost[k]
    deferred=[k for k in rows if k not in set(complete+selected+blocked)]
    return dict(selected=selected,blocked=blocked,deferred=deferred,completed=complete,resource_used=used)


def _r3_metrics(c: dict[str,Any]) -> dict[str,Any]:
    i=c['inputs'];same=i['prior_definition']==i['current_definition']
    a=number(i['prior_count'],'prior count');b=number(i['current_count'],'current count')
    x=number(i['prior_exposure'],'prior exposure');y=number(i['current_exposure'],'current exposure')
    require(min(a,b,x,y)>=0,'negative count or exposure')
    prior=a/x if x else None;current=b/y if y else None
    return dict(comparable=same,count_delta=b-a if same else None,
                count_relative_change=(b-a)/a if same and a else None,
                prior_rate=prior if same else None,current_rate=current if same else None,
                rate_relative_change=(current-prior)/prior if same and prior not in (None,0) and current is not None else None,causal_claim=False)


def _r3_dataset(c: dict[str,Any]) -> dict[str,Any]:
    i=c['inputs'];seen={};duplicates=set();conflicts=set();groups={}
    for r in _r3_list(i['rows'],'rows'):
        rid=text(r['id'],'record id');entity=text(r['entity'],'entity');partition=text(r['partition'],'partition')
        if rid in seen:
            (duplicates if r==seen[rid] else conflicts).add(rid)
        else:seen[rid]=r
        groups.setdefault(entity,set()).add(partition)
    features=records(i['features'],'features','id');late=[k for k,v in features.items() if not _r3_bool(v['known_before'],'feature availability')]
    overlap=sorted(k for k,v in groups.items() if len(v)>1)
    require(i['rights'] in ('clear','unknown','denied'),'invalid rights status')
    return dict(duplicate_record_ids=sorted(duplicates),conflicting_record_ids=sorted(conflicts),overlapping_entities=overlap,
                post_outcome_features=late,rights_status=i['rights'],admitted=i['rights']=='clear' and not(conflicts or overlap or late))


def _r3_cents(value: Any) -> int:
    require(isinstance(value,str) and len(value)<=50,'money must be bounded decimal text')
    try:d=Decimal(value)
    except InvalidOperation as exc:raise ContractError('invalid monetary value') from exc
    require(d.is_finite(),'nonfinite money');cents=d*100
    require(cents==cents.to_integral_value() and abs(cents)<=10**15,'money must fit exact minor units')
    return int(cents)


def _r3_sheet(c: dict[str,Any]) -> dict[str,Any]:
    i=c['inputs'];source=records(i['source'],'source','id');work=_r3_list(i['workbook'],'workbook');st={};wt={};counts=Counter();conflicts=set()
    for r in source.values():
        cur=text(r['currency'],'currency');st[cur]=st.get(cur,0)+_r3_cents(r['amount'])
    for r in work:
        rid=text(r['id'],'transaction id');cur=text(r['currency'],'currency');amount=_r3_cents(r['amount'])
        wt[cur]=wt.get(cur,0)+amount;counts[rid]+=1
        if rid in source and (cur!=source[rid]['currency'] or amount!=_r3_cents(source[rid]['amount'])):conflicts.add(rid)
    return dict(source_totals=st,workbook_totals=wt,duplicate_ids=sorted(k for k,v in counts.items() if v>1),
                missing_ids=sorted(set(source)-set(counts)),extra_ids=sorted(set(counts)-set(source)),conflicting_ids=sorted(conflicts),workbook_modified=False)


def _r3_quality(c: dict[str,Any]) -> dict[str,Any]:
    i=c['inputs']
    if i['mode']=='refresh':
        start=datetime.fromisoformat(text(i['start'],'start')).date();end=datetime.fromisoformat(text(i['end'],'end')).date();require(start<end,'empty refresh window')
        initial=records(i['initial'],'initial dates','date');replacement=records(i['replacement'],'replacement dates','date')
        parse=lambda x:datetime.fromisoformat(x).date()
        require(all(start<=parse(k)<end for k in replacement),'replacement outside authorized window')
        result=[v for k,v in initial.items() if not start<=parse(k)<end]+list(replacement.values())
        return dict(status='accepted',state=sorted(result,key=lambda r:r['date']))
    require(i['mode']=='upsert','invalid quality mode');initial=records(i['initial'],'initial','key');seen={};state=dict(initial);conflict=False
    for r in [*initial.values(),*_r3_list(i['events'],'events')]:
        key=text(r['key'],'key');v=_r3_int(r['version'],'business version');pair=(key,v)
        if pair in seen and seen[pair]!=r['payload']:conflict=True
        seen[pair]=r['payload']
        if key not in state or v>state[key]['version']:state[key]=r
    return dict(status='held-conflict' if conflict else 'accepted',state=list(initial.values()) if conflict else list(state.values()))


def _r3_resume(c: dict[str,Any],o: dict[str,Any]) -> None:
    i=c['inputs'];evidence=records(i['evidence'],'evidence','id');bullets=records(o['bullets'],'bullets','evidence_id')
    require(set(o)=={'bullets','supported_requirement_ids','gap_requirement_ids'},'undeclared resume output fields')
    require(set(bullets)==set(evidence),'evidence missing or fabricated')
    supported=set()
    for eid,e in evidence.items():
        b=bullets[eid];require(set(b)=={'evidence_id','scope','maturity','text'},'invalid bullet contract')
        require(b['scope']==e['scope'] and b['maturity']==e['maturity'],'contribution or maturity inflated')
        prose=text(b['text'],'bullet');original=text(e['fact'],'fact')
        require(set(re.findall(r'\d+',prose))<=set(re.findall(r'\d+',original)),'invented resume metric')
        # Closed fixture facts do not authorize deployment, employment or credentials.
        for term in ('deployed','production users','certified architect','sole owner'):
            require(term not in prose.lower() or term in original.lower(),'unsupported resume claim')
        supported.update(ids(e['supported_requirements'],'supported requirements'))
    requirements=set(ids(i['requirements'],'requirements'));supported &= requirements
    _r3_equal(o['supported_requirement_ids'],sorted(supported),'supported_requirement_ids')
    _r3_equal(o['gap_requirement_ids'],sorted(requirements-supported),'gap_requirement_ids')


def _r3_travel(c: dict[str,Any]) -> dict[str,Any]:
    i=c['inputs'];gap=(instant(i['departure'])-instant(i['arrival'])).total_seconds()/60;buffer=_r3_int(i['buffer_minutes'],'buffer')
    return dict(connection_minutes=gap,required_buffer_minutes=buffer,feasible=gap>=buffer,shortfall_minutes=max(0.0,buffer-gap),booking_status=text(i['booking_status'],'booking status'))


def _r3_care(c: dict[str,Any]) -> dict[str,Any]:
    i=c['inputs'];plan=i['active_plan'];tasks=records(i['tasks'],'tasks','id');questions=records(i['clinical_questions'],'clinical questions','id')
    records(plan['instructions'],'plan instructions','id')
    return dict(plan_version=text(plan['version'],'plan version'),instructions=plan['instructions'],
                assignments=[dict(task_id=k,owner=text(v['owner'],'owner'),state='accepted' if _r3_bool(v['accepted'],'accepted') else 'pending') for k,v in tasks.items()],
                clinical_question_ids=list(questions),delivery_status=text(i['delivery_status'],'delivery status'),treatment_changed=False)


_R3_CALCULATORS={
    'weekly-reset':_r3_weekly,'inbox-triage':_r3_inbox,'meeting-to-actions':_r3_meeting,
    'decision-budget':_r3_budget,'lecture-map':_r3_lecture,'retrieval-practice':_r3_retrieval,
    'misconception-clinic':_r3_misconception,'exam-plan':_r3_exam,'question-to-evidence':_r3_question,
    'literature-triage':_r3_literature,'competing-explanations':_r3_hypotheses,'interview-synthesis':_r3_interviews,
    'minimal-repair':_r3_repair,'api-contract':_r3_api,'accessible-ui':_r3_access,'release-readiness':_r3_release,
    'creative-brief':_r3_brief,'storyboard':_r3_story,'edit-and-export':_r3_media,
    'project-prioritization':_r3_project,'metrics-review':_r3_metrics,'dataset-intake':_r3_dataset,
    'spreadsheet-reconcile':_r3_sheet,'data-quality-review':_r3_quality,'itinerary-plan':_r3_travel,'care-coordination':_r3_care,
}


def _r3_check(c: dict[str,Any],o: dict[str,Any]) -> None:
    sid=c['skill_id']
    if sid=='prose-revision':_r3_prose(c,o)
    elif sid=='resume-tailor':_r3_resume(c,o)
    else:_r3_equal(o,_R3_CALCULATORS[sid](c))


CHECKS={'daily-briefing':_daily,'source-flashcards':_flashcards,'claim-audit':_claims,
        'bug-reproduction':_bug,'code-review':_review,'continuity-review':_continuity,
        'model-comparison':_models,'resume-without-replay':_resume}

CHECKS.update({key:_r3_check for key in (*_R3_CALCULATORS,'prose-revision','resume-tailor')})

# R4 registration: source-pinned first-party checker, never donor code.
def _register_r4_checks():
    import importlib.util as _r4_import
    import hashlib as _r4_hash
    _here=Path(__file__).parent
    _candidates=(_here/'r4_checks.py',_here.parent/'r4'/'r4_checks.py')
    for _candidate in _candidates:
        if not _candidate.exists():continue
        if _candidate.is_symlink() or not _candidate.is_file():raise ValueError('R4 checker path refused')
        _raw=_candidate.read_bytes()
        if len(_raw)>250000 or _r4_hash.sha256(_raw).hexdigest()!='e51ccbc89059f15cf6ae192c23a6a90c15fd8329e7a07521873abbc5d0c93ba7':raise ValueError('R4 checker source mismatch')
        _spec=_r4_import.spec_from_file_location('muse_r4_checks',_candidate)
        if _spec is None or _spec.loader is None:raise ValueError('R4 checker loader unavailable')
        _module=_r4_import.module_from_spec(_spec);_spec.loader.exec_module(_module)
        CHECKS.update(_module.R4_CHECKS)
        return
_register_r4_checks()

# R5 optional registration, retaining all original R2/R3/R4 checker behavior.
def _register_r5_checks():
    import importlib.util as _import
    import hashlib as _hash
    here=Path(__file__).parent
    for candidate in (here/'r5_checks.py',here.parent/'r5'/'r5_checks.py'):
        if not candidate.exists():continue
        if candidate.is_symlink() or not candidate.is_file():raise ValueError('R5 checker path refused')
        raw=candidate.read_bytes()
        if len(raw)>250000 or _hash.sha256(raw).hexdigest()!='82e4226576964f59f11f7fea4f2b90af63d7678dfd9ddb98699211b1e1c19847':
            raise ValueError('R5 checker source mismatch')
        spec=_import.spec_from_file_location('muse_r5_checks',candidate)
        if spec is None or spec.loader is None:raise ValueError('R5 checker loader unavailable')
        module=_import.module_from_spec(spec);spec.loader.exec_module(module)
        CHECKS.update(module.R5_CHECKS)
        return
_register_r5_checks()

def check_case(case: Any, output: Any) -> dict[str,Any]:
    failures=[]
    try:
        require(isinstance(case,dict) and isinstance(output,dict),'case and output must be objects')
        # Reject non-JSON and non-finite caller values before any domain checks.
        encoded=json.dumps(output,allow_nan=False)
        require(len(encoded.encode())<=MAX_BYTES,'output exceeds size budget')
        require(case.get('skill_id') in CHECKS,'unsupported case skill')
        CHECKS[case['skill_id']](case,output)
    except (ContractError,KeyError,TypeError,ValueError,OverflowError,RecursionError) as e:
        failures.append(str(e) or type(e).__name__)
    return {'passed':not failures,'failures':failures,'human_review_required':True,
            'evidence_grade':'SUPPLIED_OUTPUT_MECHANICALLY_CHECKED','model_called':False,
            'provider_identity_verified':False}

def example_run_metadata() -> list[dict[str,Any]]:
    """Synthetic records for tests/documentation, never supplied as real runs."""
    return [{'arm':arm,'session_id':'synthetic-'+arm,'case_ids':['demo-case'],
             'case_set_sha256':'a'*64,'protocol_sha256':'b'*64,'status':'completed',
             'synthetic':True,'environment':{'platform':'Muse','model':'fixture-model',
             'tools':[],'time_budget_seconds':60,'max_output_tokens':2000,
             'temperature':0,'supplied_context_sha256':'c'*64,'memory_mode_observed':'synthetic fresh context'}}
            for arm in ('plain','upstream','candidate')]

def _sha256(value: Any, name: str) -> str:
    value=text(value,name)
    require(len(value)==64 and all(c in '0123456789abcdef' for c in value),'invalid '+name)
    return value

def _environment(value: Any) -> dict[str,Any]:
    fields={'platform','model','tools','time_budget_seconds','max_output_tokens','temperature','supplied_context_sha256','memory_mode_observed'}
    require(isinstance(value,dict) and fields<=value.keys(),'incomplete environment')
    platform=text(value['platform'],'platform').strip()
    require(platform.lower() not in ('unknown','unspecified'),'unknown platform comparability')
    visibility=value.get('model_visibility','declared')
    require(visibility in ('declared','managed-opaque'),'invalid model visibility')
    if visibility=='managed-opaque':
        require(value['model'] is None,'opaque model must not invent a model identity')
        text(value.get('visible_model_setting'),'observed visible model setting')
    else:
        identity=text(value['model'],'model').strip()
        require(identity.lower() not in ('unknown','unspecified'),'unknown model comparability')
    ids(value['tools'],'tool inventory')
    require(number(value['time_budget_seconds'],'time budget')>0,'time budget must be positive')
    require(type(value['max_output_tokens']) is int and value['max_output_tokens']>0,'token budget must be a positive integer')
    temperature_visibility=value.get('temperature_visibility','declared')
    require(temperature_visibility in ('declared','managed-opaque'),'invalid temperature visibility')
    if temperature_visibility=='managed-opaque':
        require(value['temperature'] is None,'opaque sampling setting must not invent a temperature')
    else:
        require(number(value['temperature'],'temperature')>=0,'temperature must be nonnegative')
    _sha256(value['supplied_context_sha256'],'supplied context hash')
    text(value['memory_mode_observed'],'observed memory mode')
    return value

def check_comparability(runs: Any) -> dict[str,Any]:
    problems=[];scope='NOT_COMPARABLE'
    try:
        rows=records(runs,'runs','arm')
        require(set(rows)=={'plain','upstream','candidate'},'all three comparison arms required')
        reference=rows['plain'];session_ids=[]
        require(bool(ids(reference['case_ids'],'case_ids')),'empty case set')
        reference_env=_environment(reference['environment'])
        for row in rows.values():
            require(row['status']=='completed','partial run cannot be ranked')
            for field in ('case_set_sha256','protocol_sha256'):
                require(_sha256(row.get(field),field)==reference[field],'different '+field)
            require(ids(row['case_ids'],'case_ids')==reference['case_ids'],'different case coverage or order')
            require(_environment(row['environment'])==reference_env,'different model, tools, memory or budget')
            session_ids.append(text(row.get('session_id'),'session_id'))
        require(len(session_ids)==len(set(session_ids)),'shared session contaminates arms')
        scope='HOST_MATCHED_MODEL_OPAQUE' if reference_env.get('model_visibility')=='managed-opaque' else 'DECLARED_MODEL_AND_HOST_MATCHED'
        if reference_env.get('temperature_visibility')=='managed-opaque':scope='HOST_MATCHED_SETTINGS_PARTLY_OPAQUE'
    except (ContractError,KeyError,TypeError,ValueError,OverflowError) as e:problems.append(str(e))
    return {'comparable':not problems,'issues':problems,'measurement':'METADATA_CONSISTENCY_ONLY',
            'comparison_scope':scope,'underlying_model_parity_verified':False,
            'provider_identity_verified':False,'behavioral_superiority_established':False,
            'human_review_required':True}

def _unique_pairs(items: list[tuple[str,Any]]) -> dict[str,Any]:
    result={}
    for k,v in items:
        require(k not in result,'duplicate JSON key: '+k);result[k]=v
    return result

def read_json(path: Path) -> Any:
    if '..' in path.parts:raise ContractError('parent traversal refused')
    p=path.absolute()
    for part in [*reversed(p.parents),p]:
        st=part.lstat()
        if stat.S_ISLNK(st.st_mode):
            trusted=(sys.platform=='darwin' and str(part) in ('/var','/tmp','/etc') and st.st_uid==0 and str(part.resolve())=='/private'+str(part))
            require(trusted,'symlink path refused')
        require(not (getattr(st,'st_file_attributes',0)&0x400 and not stat.S_ISLNK(st.st_mode)),'reparse path refused')
    require(stat.S_ISREG(p.lstat().st_mode),'not a regular JSON file')
    flags=os.O_RDONLY|getattr(os,'O_NONBLOCK',0)|getattr(os,'O_NOFOLLOW',0)
    with os.fdopen(os.open(p,flags),'rb') as f:
        require(stat.S_ISREG(os.fstat(f.fileno()).st_mode),'not a regular JSON file')
        b=f.read(MAX_BYTES+1)
    require(len(b)<=MAX_BYTES,'JSON size limit exceeded')
    result=json.loads(b.decode('utf-8'),object_pairs_hook=_unique_pairs,
                      parse_constant=lambda x: (_ for _ in ()).throw(ContractError('non-finite JSON value')))
    stack=[(result,0)]
    while stack:
        value,level=stack.pop();require(level<=64,'JSON nesting too deep')
        if isinstance(value,dict):stack.extend((v,level+1) for v in value.values())
        elif isinstance(value,list):stack.extend((v,level+1) for v in value)
        elif type(value) is float:require(math.isfinite(value),'non-finite numeric value')
    return result

def main(argv: list[str]|None=None) -> int:
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest='command',required=True)
    check=sub.add_parser('check');check.add_argument('--case',type=Path,required=True);check.add_argument('--output',type=Path,required=True)
    compare=sub.add_parser('compare-metadata');compare.add_argument('--runs',type=Path,required=True)
    args=p.parse_args(argv)
    try:
        result=check_case(read_json(args.case),read_json(args.output)) if args.command=='check' else check_comparability(read_json(args.runs))
        print(json.dumps(result,sort_keys=True))
        return 0 if result.get('passed',result.get('comparable',False)) else 2
    except (OSError,UnicodeError,json.JSONDecodeError,ContractError,RecursionError) as e:
        print(json.dumps({'passed':False,'error':str(e),'model_called':False}),file=sys.stderr);return 2

if __name__=='__main__':raise SystemExit(main())

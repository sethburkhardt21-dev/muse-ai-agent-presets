"""Input-derived checks for supplied R4 exercises; no model or provider execution.
The calculated fields below are narrow, closed-world facts. A passing record is
not a useful-prose judgment, clinical guidance, an installation, or a benchmark.
"""
from __future__ import annotations
import argparse
import json
import math
import hashlib
from pathlib import Path
from collections import Counter
from typing import Any

class Invalid(ValueError): pass

def need(ok: bool, message: str) -> None:
    if not ok: raise Invalid(message)

def integer(v: Any, name: str, minimum: int = 0) -> int:
    need(type(v) is int and minimum <= v <= 10**12, 'invalid integer: '+name)
    return v

def ids(rows: Any) -> list[str]:
    need(isinstance(rows,list) and len(rows)<=10000,'expected bounded list')
    need(all(isinstance(x,str) and x and len(x)<=500 for x in rows),'invalid IDs')
    need(len(rows)==len(set(rows)),'duplicate IDs')
    return rows

def indexed(rows: Any) -> dict[str,dict]:
    need(isinstance(rows,list) and len(rows)<=10000,'expected bounded records')
    need(all(isinstance(x,dict) for x in rows),'invalid record')
    keys=ids([x.get('id') for x in rows]);return dict(zip(keys,rows))

def boolean(v: Any) -> bool:
    need(type(v) is bool,'expected boolean');return v

def exact(actual: Any, expected: Any) -> bool:
    if type(expected) is float:
        return type(actual) in (int,float) and math.isfinite(actual) and math.isclose(actual,expected,rel_tol=1e-9,abs_tol=1e-9)
    if type(actual) is not type(expected): return False
    if isinstance(expected,dict):return set(actual)==set(expected) and all(exact(actual[k],expected[k]) for k in expected)
    if isinstance(expected,list):return len(actual)==len(expected) and all(exact(a,b) for a,b in zip(actual,expected))
    return actual==expected

def safe_json(value: Any) -> None:
    stack=[(value,0)];count=0
    while stack:
        v,d=stack.pop();count+=1
        need(d<=32 and count<=100000,'input complexity limit')
        if isinstance(v,dict):
            need(all(isinstance(k,str) for k in v),'non-string JSON key');stack.extend((z,d+1) for z in v.values())
        elif isinstance(v,list):stack.extend((z,d+1) for z in v)
        elif type(v) is float:need(math.isfinite(v),'nonfinite number')
        elif type(v) not in (int,str,bool,type(None)):raise Invalid('not JSON data')
    need(len(json.dumps(value,allow_nan=False).encode())<=1_000_000,'input byte limit')

def calculate(sid: str, x: dict) -> dict:
    """Calculate only the declared structured properties of one exercise."""
    if sid=='scope-and-route':
        rows=indexed(x['tasks']);done=set(ids(x['completed']));tools=set(ids(x['available_tools']));ready=[];held=[]
        need(done<=set(rows),'unknown completed task')
        for k,r in rows.items():
            deps=set(ids(r['dependencies']));need(deps<=set(rows),'unknown dependency')
            if k in done:continue
            if not deps<=done or (r['tool'] and r['tool'] not in tools) or (boolean(r['external']) and not boolean(r['authorized'])):held.append(k)
            else:ready.append(k)
        return dict(ready=sorted(ready),held=sorted(held),completed=sorted(done))
    if sid=='source-and-custody':
        rows=indexed(x['artifacts']);valid=[];quarantine=[]
        for k,r in rows.items():
            for f in ('expected_sha256','observed_sha256'):need(isinstance(r[f],str) and len(r[f])==64 and set(r[f])<=set('0123456789abcdef'),'bad hash')
            (valid if r['expected_sha256']==r['observed_sha256'] and boolean(r['reuse_authorized']) else quarantine).append(k)
        return dict(verified_bytes=sorted(valid),quarantined=sorted(quarantine),origin_authenticated=False)
    if sid=='bounded-review':
        req=set(ids(x['required']));checks=indexed(x['checks']);need(bool(req),'empty review scope');need(set(checks)<=req,'unknown requirement')
        fail=sorted(k for k,r in checks.items() if r['state']=='fail');unknown=sorted(req-{k for k,r in checks.items() if r['state'] in ('pass','fail')})
        need(all(r['state'] in ('pass','fail','unknown') for r in checks.values()),'bad check state')
        return dict(failed=fail,unobserved=unknown,verdict='changes-needed' if fail else ('insufficient-evidence' if unknown else 'accepted-for-stated-scope'))
    if sid=='household-project':
        rows=indexed(x['tasks']);done=set(ids(x['completed']));need(done<=set(rows),'unknown completed task');nexts=[];gated=[];blocked=[]
        for k,r in rows.items():
            deps=set(ids(r['dependencies']));need(deps<=set(rows) and k not in deps,'invalid dependency')
            if k in done:continue
            if boolean(r['professional_required']) and not boolean(r['professional_confirmed']):gated.append(k)
            elif not deps<=done:blocked.append(k)
            else:nexts.append(k)
        costs=indexed(x['materials']);total=sum(integer(r['cost_cents'],'material cost') for r in costs.values())
        return dict(next_safe_tasks=sorted(nexts),professional_gate=sorted(gated),dependency_hold=sorted(blocked),material_total_cents=total)
    if sid=='teach-back':
        concepts=set(ids(x['required_concepts']));observed=set(ids(x['demonstrated']));contradicted=set(ids(x['contradicted']));need((observed|contradicted)<=concepts,'unknown concept')
        return dict(demonstrated=sorted(observed-contradicted),needs_repair=sorted((concepts-observed)|contradicted),transfer='observed' if boolean(x['unseen_transfer_correct']) and not boolean(x['assisted']) else 'not-established')
    if sid=='change-brief':
        before=indexed(x['before']);after=indexed(x['after']);shared=set(before)&set(after)
        return dict(added=sorted(set(after)-set(before)),removed=sorted(set(before)-set(after)),modified=sorted(k for k in shared if before[k]['value']!=after[k]['value']),unchanged=sorted(k for k in shared if before[k]['value']==after[k]['value']),observation_version=x['after_version'])
    if sid=='visual-reference':
        refs=indexed(x['references']);rules=indexed(x['rules']);usable=[];unverified=[]
        for k,r in rules.items():
            origins=set(ids(r['reference_ids']));need(origins and origins<=set(refs),'unknown visual source')
            (usable if all(boolean(refs[o]['observed']) for o in origins) else unverified).append(k)
        return dict(observation_supported_rules=sorted(usable),unverified_rules=sorted(unverified),redistribution_approved=all(boolean(r['redistribution_authorized']) for r in refs.values()) and bool(refs))
    if sid=='customer-discovery':
        rows=indexed(x['observations']);people=set();behavior=set();paid=set()
        for r in rows.values():
            need(r['kind'] in ('opinion','observed-workaround','paid'), 'bad evidence class');need(isinstance(r['participant'],str) and bool(r['participant'].strip()),'invalid participant identity');people.add(r['participant'])
            if r['kind'] in ('observed-workaround','paid'):behavior.add(r['participant'])
            if r['kind']=='paid':paid.add(r['participant'])
        return dict(participants=len(people),behavior_participants=len(behavior),paying_participants=len(paid),market_demand_proven=False)
    if sid=='offer-design':
        p=integer(x['price_cents'],'price');unit=integer(x['variable_cents'],'variable');fixed=integer(x['fixed_cents'],'fixed');n=integer(x['customers'],'customers');cap=integer(x['capacity'],'capacity')
        return dict(contribution_per_customer_cents=p-unit,scenario_margin_cents=(p-unit)*n-fixed,within_capacity=n<=cap,ready_for_pilot=n<=cap and p>unit and boolean(x['scope_defined']) and boolean(x['claims_supported']))
    if sid=='content-system':
        sources=indexed(x['sources']);items=indexed(x['items']);ready=[];held=[]
        for k,r in items.items():
            refs=set(ids(r['source_ids']));need(refs<=set(sources),'unknown content source')
            (ready if refs and all(boolean(sources[a]['current']) and boolean(sources[a]['reuse_authorized']) for a in refs) else held).append(k)
        return dict(draft_ready=sorted(ready),source_hold=sorted(held),published=False)
    if sid=='service-playbook':
        rows=indexed(x['steps']);completed={k for k,r in rows.items() if r['state']=='completed'};ready=[];reconcile=[];held=[]
        for k,r in rows.items():
            need(r['state'] in ('planned','completed','unknown','denied'),'bad service state');deps=set(ids(r['dependencies']));need(deps<=set(rows),'unknown service dependency')
            if k in completed:continue
            if r['state']=='unknown':reconcile.append(k)
            elif r['state']=='denied' or not boolean(r['owner_accepted']) or not deps<=completed:held.append(k)
            else:ready.append(k)
        return dict(completed=sorted(completed),ready=sorted(ready),reconcile_original=sorted(reconcile),held=sorted(held))
    if sid=='analysis-notebook':
        rows=indexed(x['rows']);values=[r['value'] for r in rows.values() if r['value'] is not None]
        need(all(type(v) in (int,float) and math.isfinite(v) for v in values),'invalid observation')
        return dict(input_rows=len(rows),observed_rows=len(values),missing_rows=len(rows)-len(values),sum=sum(values),mean=sum(values)/len(values) if values else None,imputation_performed=False)
    if sid=='chart-story':
        purpose=x['purpose'];need(purpose in ('trend','relationship','category'),'unknown chart purpose')
        chosen={'trend':'line','relationship':'scatter','category':'bar'}[purpose];base=x['axis_min'];need(type(base) in (int,float) and math.isfinite(base),'bad axis minimum')
        return dict(chart=chosen,baseline_correction_needed=chosen=='bar' and base!=0,missing_units=not bool(x['units']),observed_points=integer(x['observed_points'],'points'),causal_claim_supported=False)
    if sid=='portfolio-story':
        rows=indexed(x['claims']);allowed=[];unsupported=[]
        for k,r in rows.items():
            need(r['stage_claimed'] in ('built','tested','deployed'),'bad claim stage');stages=set(ids(r['observed_stages']));need(stages<={'built','tested','deployed'},'bad observation stage')
            (allowed if r['stage_claimed'] in stages and boolean(r['attribution_correct']) else unsupported).append(k)
        return dict(supported_claims=sorted(allowed),unsupported_claims=sorted(unsupported),employment_equivalence_asserted=False)
    if sid=='role-fit':
        rows=indexed(x['requirements']);hard=[];gaps=[];transfer=[];met=[]
        for k,r in rows.items():
            need(r['evidence'] in ('direct','transferable','none'),'bad fit evidence')
            if r['evidence']=='direct':met.append(k)
            else:
                (transfer if r['evidence']=='transferable' else gaps).append(k)
                if boolean(r['nonnegotiable']):hard.append(k)
        return dict(direct=sorted(met),transferable=sorted(transfer),missing=sorted(gaps),eligibility_to_clarify=sorted(hard),hiring_prediction=None)
    if sid=='interview-rehearsal':
        req=set(ids(x['rubric']));observed=set(ids(x['observed']));need(observed<=req,'unknown rubric item')
        return dict(covered=sorted(observed),missing=sorted(req-observed),overrun_seconds=max(0,integer(x['duration_seconds'],'duration')-integer(x['budget_seconds'],'budget')),unaided_demonstration=not boolean(x['coached']))
    if sid=='difficult-message':
        facts=set(ids(x['verified_fact_ids']));claims=indexed(x['assertions']);unsupported=[];unlabeled=[]
        for k,r in claims.items():
            if r['kind']=='fact' and r['source_id'] not in facts:unsupported.append(k)
            elif r['kind']=='interpretation' and not boolean(r['labeled']):unlabeled.append(k)
            need(r['kind'] in ('fact','interpretation'),'bad assertion kind')
        return dict(unsupported_facts=sorted(unsupported),unlabeled_interpretations=sorted(unlabeled),clear_request=boolean(x['specific_ask']),sent=False)
    if sid=='negotiation-prep':
        rows=indexed(x['offers']);floor=integer(x['minimum_net_cents'],'floor');limit=integer(x['maximum_hours'],'hours');acceptable=[];net={}
        for k,r in rows.items():
            value=integer(r['guaranteed_cents'],'guaranteed')-integer(r['cost_cents'],'cost');net[k]=value
            if value>=floor and integer(r['hours'],'hours')<=limit:acceptable.append(k)
        return dict(net_guaranteed_cents=net,within_stated_limits=sorted(acceptable),agreement_reached=False)
    if sid=='meal-plan':
        recipes=indexed(x['recipes']);allergens=set(ids(x['avoid_allergens']));usable=[];excluded=[]
        for k,r in recipes.items():
            (usable if boolean(r['ingredient_labels_known']) and not allergens.intersection(ids(r['allergens'])) else excluded).append(k)
        need(integer(x['portions'],'portions')>0 and integer(x['yield_per_batch'],'yield')>0,'positive portions/yield needed')
        batches=(x['portions']+x['yield_per_batch']-1)//x['yield_per_batch'];shopping=max(0,batches*integer(x['units_per_batch'],'units')-integer(x['pantry_units'],'pantry'))
        return dict(eligible_from_supplied_labels=sorted(usable),excluded=sorted(excluded),batches=batches,units_to_buy=shopping,medical_safety_certified=False)
    if sid=='garden-observe':
        rows=indexed(x['observations']);plants={};seen_sequences=set()
        for k,r in rows.items():
            seq=integer(r['sequence'],'observation sequence');p=r['plant_id'];need(isinstance(p,str) and p,'invalid plant ID')
            need((p,seq) not in seen_sequences,'ambiguous observation sequence');seen_sequences.add((p,seq))
            if p not in plants or seq>plants[p]['sequence']:plants[p]=dict(id=k,sequence=seq)
        return dict(latest_observation_ids=sorted(r['id'] for r in plants.values()),missing_measurements=sorted(k for k in plants if x['measurements'].get(k) is None),treatment_applied=False,diagnosis_confirmed=False)
    if sid=='hobby-practice':
        sections=indexed(x['sections']);total=sum(integer(r['minutes'],'practice minutes') for r in sections.values());budget=integer(x['budget_minutes'],'budget');pain=boolean(x['stop_signal'])
        return dict(total_minutes=total,within_budget=total<=budget,action='stop-and-reassess' if pain else ('shorten-session' if total>budget else 'practice'),skill_mastery_proven=False)
    if sid=='event-plan':
        guests=indexed(x['guests']);accepted=[k for k,r in guests.items() if boolean(r['confirmed'])];pending=sorted(set(guests)-set(accepted));total=integer(x['fixed_cents'],'fixed')+len(accepted)*integer(x['per_guest_cents'],'per guest')+integer(x['reserve_cents'],'reserve')
        return dict(confirmed_people=len(accepted),pending_guest_ids=pending,within_capacity=len(accepted)+integer(x['staff_count'],'staff')<=integer(x['capacity'],'capacity'),cost_for_confirmed_cents=total,booked=False)
    if sid=='purchase-compare':
        rows=indexed(x['options']);req=set(ids(x['required_features']));eligible={};cash={};incomplete=[];rejected=[]
        for k,r in rows.items():
            if not req<=set(ids(r['features'])):rejected.append(k);continue
            costs=r['costs_cents'];need(isinstance(costs,list) and bool(costs),'missing purchase cost breakdown')
            deposit=integer(r.get('refundable_deposit_cents',0),'refundable deposit')
            if any(v is None for v in costs):incomplete.append(k);continue
            eligible[k]=sum(integer(v,'purchase cost') for v in costs);cash[k]=eligible[k]+deposit
        best=min(eligible.values()) if eligible else None
        return dict(complete_totals_cents=eligible,cash_due_cents=cash,lowest_complete_cost_ids=sorted(k for k,v in eligible.items() if v==best),unknown_total_ids=sorted(incomplete),fit_rejected_ids=sorted(rejected),purchased=False)
    if sid=='appointment-prep':
        observations=indexed(x['observations']);undated=sorted(k for k,r in observations.items() if r.get('when') is None);meds={}
        for r in x['medication_records']:meds.setdefault(r['name'],set()).add(r['instruction'])
        return dict(undated_observation_ids=undated,medication_conflicts=sorted(k for k,v in meds.items() if len(v)>1),questions=list(ids(x['questions'])),urgent_contact_priority=boolean(x['urgent_flag']),diagnosis_made=False)
    if sid=='accessibility-routine':
        rows=indexed(x['steps']);needs=set(ids(x['required_access']));compatible=[];blocked=[];total=0
        for k,r in rows.items():
            if needs<=set(ids(r['supported_access'])):compatible.append(k);total+=integer(r['effort_units'],'effort')
            else:blocked.append(k)
        return dict(compatible_steps=sorted(compatible),adaptation_needed=sorted(blocked),effort_total=total,within_user_budget=total<=integer(x['effort_budget'],'effort budget'),needs_inferred=False)
    if sid=='reflection-journal':
        rows=indexed(x['entries']);facts=[];feelings=[];interpretations=[]
        for k,r in rows.items():
            need(r['kind'] in ('event','feeling','interpretation'),'bad reflection kind');{'event':facts,'feeling':feelings,'interpretation':interpretations}[r['kind']].append(k)
        need(x['mode'] in ('listen','reflect','plan'),'unknown reflection mode')
        return dict(events=sorted(facts),feelings=sorted(feelings),interpretations=sorted(interpretations),offer_action_plan=x['mode']=='plan',prioritize_human_support=boolean(x['urgent_flag']),diagnosis_made=False)
    if sid=='habit-experiment':
        rows=indexed(x['opportunities']);known=[r for r in rows.values() if r['completed'] is not None];need(all(r['completed'] is None or type(r['completed']) is bool for r in rows.values()),'bad habit observation');success=sum(r['completed'] is True for r in known)
        return dict(opportunities=len(rows),observed=len(known),missing=len(rows)-len(known),successes=success,observed_rate=success/len(known) if known else None,causal_effect_established=False)
    if sid=='family-archive':
        rows=indexed(x['items']);groups={};share=[];held=[]
        for k,r in rows.items():
            h=r['sha256'];need(isinstance(h,str) and len(h)==64 and set(h)<=set('0123456789abcdef'),'bad archive hash');groups.setdefault(h,[]).append(k)
            people=set(ids(r['people']));consent=set(ids(r['public_consent_people']))
            (share if boolean(r['item_public_permission']) and people<=consent else held).append(k)
        return dict(byte_duplicate_groups=sorted(sorted(v) for v in groups.values() if len(v)>1),public_share_eligible=sorted(share),private_or_unresolved=sorted(held),originals_deleted=False)
    raise Invalid('unknown R4 skill')

def check_case(case: Any, output: Any) -> dict[str,Any]:
    try:
        safe_json(case);safe_json(output)
        need(isinstance(case,dict) and isinstance(output,dict),'case and output must be objects')
        x=case['inputs'];need(isinstance(x,dict),'inputs must be an object')
        need(isinstance(x['revision'],str) and x['revision'],'missing input revision')
        need(output.get('input_revision')==x['revision'],'input revision mismatch')
        need(output.get('external_actions_performed') is False,'exercise must not claim real external effects')
        expected=calculate(case['skill_id'],x)
        observed={k:output.get(k) for k in expected}
        need(set(output)==set(expected)|{'input_revision','external_actions_performed'},'unknown or missing result fields')
        need(exact(observed,expected),'structured outcome differs from supplied input')
        return dict(passed=True,issues=[],scope='SUPPLIED_EXERCISE_ONLY',model_called=False)
    except (Invalid,KeyError,TypeError,ValueError,OverflowError,RecursionError) as exc:
        return dict(passed=False,issues=[str(exc)],scope='SUPPLIED_EXERCISE_ONLY',model_called=False)

def r4_dispatch(case: dict, output: dict) -> None:
    result=check_case(case,output)
    if not result['passed']:raise ValueError('; '.join(result['issues']))

SKILL_IDS='scope-and-route source-and-custody bounded-review household-project teach-back change-brief visual-reference customer-discovery offer-design content-system service-playbook analysis-notebook chart-story portfolio-story role-fit interview-rehearsal difficult-message negotiation-prep meal-plan garden-observe hobby-practice event-plan purchase-compare appointment-prep accessibility-routine reflection-journal habit-experiment family-archive'.split()
R4_CHECKS={sid:r4_dispatch for sid in SKILL_IDS}

def trusted_root_alias(path: str, target: str, owner: int, platform: str) -> bool:
    return platform=='darwin' and path in ('/var','/tmp','/etc') and owner==0 and target=='/private'+path

def _read(path: Path) -> Any:
    import stat,os,sys
    p=path.absolute()
    need('..' not in path.parts,'parent traversal refused')
    for q in [*reversed(p.parents),p]:
        s=q.lstat()
        if stat.S_ISLNK(s.st_mode):
            need(trusted_root_alias(str(q),str(q.resolve()),s.st_uid,sys.platform),'linked path refused')
        elif getattr(s,'st_file_attributes',0)&0x400:raise Invalid('reparse path refused')
    need(stat.S_ISREG(p.stat().st_mode),'not a regular file')
    flags=os.O_RDONLY|getattr(os,'O_NONBLOCK',0)|getattr(os,'O_NOFOLLOW',0)
    with os.fdopen(os.open(p,flags),'rb') as f:
        need(stat.S_ISREG(os.fstat(f.fileno()).st_mode),'not a regular file');raw=f.read(1_000_001)
    need(len(raw)<=1_000_000,'input byte limit')
    def pairs(values):
        d={}
        for k,v in values:need(k not in d,'duplicate JSON key');d[k]=v
        return d
    result=json.loads(raw.decode('utf-8'),object_pairs_hook=pairs,parse_constant=lambda _:(_ for _ in ()).throw(Invalid('nonfinite JSON')))
    safe_json(result);return result

def main(argv=None) -> int:
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--case',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args(argv)
    try:r=check_case(_read(a.case),_read(a.output))
    except (OSError,UnicodeError,ValueError,RecursionError) as e:r=dict(passed=False,issues=[str(e)],model_called=False)
    print(json.dumps(r,sort_keys=True));return 0 if r['passed'] else 2
if __name__=='__main__':raise SystemExit(main())

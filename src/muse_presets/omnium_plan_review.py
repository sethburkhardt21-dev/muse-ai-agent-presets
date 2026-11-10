"""Read-only consumer of the original Omnium omnium.mission_plan PLAN result.

This is deliberately NOT a mission compiler, dispatch service, planner,
worker scheduler, issuer, lease owner or alternative plan_checker. The real
Omnium route/checker must still independently authenticate any original
receipt, source custody and registered adapter state before a host may
consider any work. This module only demonstrates the *absence* of runnable
worker authority in one pinned plan artifact.

The fixed source pins and four planning functions are from the existing
Omnium mission_adapter/card_schema/adapter_registry reviewed on 2026-11-09.
A future Omnium registry change must be source-reviewed and reissued.
"""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from .native_canary import _no_duplicate_json, _reject_constant
from .native_skill_binding import _regular_bytes

SCHEMA="r67/omnium-plan-consumer-v1"
ROUTE="omnium.mission_plan"
OMNIUM_SCHEMA_SHA256="d2dc10d8b83a21c5ea68b224ff4cf0cd1b1d8015576fbf471bf14071a7c3c6fb"
OMNIUM_REGISTRY_SHA256="32c7cdff51c3f91db6dfde0b92e839f03162af3085595eb22f30678417aaa95c"
OMNIUM_COMPILER_SHA256="6397a8468407d41e0235470557616e3132abd64618b0f01790689e547027b999"
ADMITTED_PLANNING_FUNCTIONS=frozenset({
    "omnium.ledger_verify",
    "omnium.mission_plan",
    "omnium.foundry_review",
    "omnium.library_retrieve",
})
PLAN_KEYS=frozenset({
    "plan","plan_version","route","card_set_sha256","schema_sha256",
    "registry_sha256","compiler_sha256","ledger_sha256","census_sha256",
    "files_in_census","cards","adapter_requirements","evidence_obligations",
    "executes","effects","plan_sha256",
})
CARD_KEYS=frozenset({
    "card_id","title","card_sha256","muse_flow","missing_adapter_functions",
    "steps","acceptance_checks",
})
STEP_KEYS=frozenset({
    "step_id","action","adapter_function","adapter_status",
    "depends_on","produces","evidence_obligations",
})
HEX64=re.compile(r"^[0-9a-f]{64}$")
IDENT=re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
FN=re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")
MAX_PLAN_BYTES=96*1024
MAX_CARDS=16
MAX_STEPS=64


def _require(condition:bool, reason:str)->None:
    if not condition:
        raise ValueError(reason)


def _hex(value:Any)->bool:
    return type(value) is str and HEX64.fullmatch(value) is not None


def _identifier(value:Any)->bool:
    return type(value) is str and IDENT.fullmatch(value) is not None


def _function(value:Any)->bool:
    return type(value) is str and FN.fullmatch(value) is not None


def _text(value:Any)->bool:
    return (type(value) is str and 1<=len(value)<=1024 and value.strip()==value
            and all(ord(c)>=32 or c=="\t" for c in value))


def _canonical(payload:object)->bytes:
    try:
        raw=json.dumps(payload,sort_keys=True,separators=(",",":"),
                       ensure_ascii=False,allow_nan=False).encode("utf-8")
    except (TypeError,ValueError,UnicodeError,RecursionError,OverflowError) as exc:
        raise ValueError("OMNIUM_PLAN_NOT_SERIALIZABLE") from exc
    _require(len(raw)<=MAX_PLAN_BYTES,"OMNIUM_PLAN_TOO_LARGE")
    return raw


def _digest(payload:object)->str:
    return hashlib.sha256(_canonical(payload)).hexdigest()


def load_omnium_plan_file(path:Path)->dict:
    """Use existing strict local regular-file reader (no symlink or JSON NaN)."""
    try:
        name=Path(path)
        _require(name.suffix.lower()==".json","EXPECTED_PLAN_JSON_FILE")
        raw=_regular_bytes(name,MAX_PLAN_BYTES)
        result=json.loads(raw.decode("utf-8"),
                          object_pairs_hook=_no_duplicate_json,
                          parse_constant=_reject_constant)
        _require(type(result) is dict,"OMNIUM_PLAN_NOT_OBJECT")
        return result
    except (OSError,TypeError,ValueError,UnicodeError) as exc:
        raise ValueError("UNSAFE_OMNIUM_PLAN_FILE") from exc


def _obligation_step(card_id:str, step:dict)->list[dict]:
    base=[{"obligation":"step-completion-record",
           "card_id":card_id,"step_id":step["step_id"]}]
    return base+[
        {"obligation":"artifact-produced","card_id":card_id,
         "step_id":step["step_id"],"artifact":artifact}
        for artifact in step["produces"]
    ]


def review_omnium_plan_only(
    plan:object,
    expected_plan_sha256:object,
    *,
    expected_schema_sha256:object,
    expected_registry_sha256:object
)->dict:
    """Inspect a pin-bound plan for *planning* and missing-worker holds.

    The supplied plan, pins and declared Omnium origin are not authenticated.
    The original Omnium plan_checker and host evidence remain authoritative.
    This function never imports Omnium, runs a plan or executes its steps.
    """
    _require(type(plan) is dict and set(plan)==PLAN_KEYS,
             "OMNIUM_PLAN_TOP_FIELDS_REFUSED")
    _require(_hex(expected_plan_sha256)
             and expected_schema_sha256==OMNIUM_SCHEMA_SHA256
             and expected_registry_sha256==OMNIUM_REGISTRY_SHA256,
             "EXPECTED_PLAN_AND_SOURCE_PINS_REQUIRED")
    _require(plan["plan"]=="atlas-omnium/mission-plan"
             and type(plan["plan_version"]) is int
             and plan["plan_version"]==1
             and plan["route"]==ROUTE
             and plan["executes"] is False
             and plan["effects"]=="none",
             "OMNIUM_PLAN_EXECUTION_OR_ROUTE_REFUSED")
    for name in ("card_set_sha256","schema_sha256","registry_sha256",
                 "compiler_sha256","ledger_sha256","census_sha256","plan_sha256"):
        _require(_hex(plan[name]),"OMNIUM_PLAN_BAD_DIGEST_"+name)
    _require(plan["schema_sha256"]==expected_schema_sha256
             and plan["registry_sha256"]==expected_registry_sha256
             and plan["compiler_sha256"]==OMNIUM_COMPILER_SHA256,
             "OMNIUM_SOURCE_VERSION_NOT_ADMITTED")
    _require(type(plan["files_in_census"]) is int
             and 0<=plan["files_in_census"]<=1_000_000,
             "OMNIUM_CENSUS_COUNT_BAD")
    _require(plan["plan_sha256"]==expected_plan_sha256
             and _digest({k:v for k,v in plan.items()
                          if k!="plan_sha256"})==expected_plan_sha256,
             "OMNIUM_PLAN_SHA_MISMATCH")
    cards=plan["cards"]
    _require(type(cards) is list and 1<=len(cards)<=MAX_CARDS,
             "OMNIUM_PLAN_CARDS_INVALID")
    needs={}
    missing=set()
    admitted=set()
    referenced={}
    card_ids=set()
    total_steps=0
    obligations=[]
    for card in cards:
        _require(type(card) is dict and set(card)==CARD_KEYS,
                 "OMNIUM_COMPILED_CARD_FIELDS_REFUSED")
        cid=card["card_id"]
        _require(_identifier(cid) and cid not in card_ids
                 and _hex(card["card_sha256"])
                 and _text(card["title"]) and _text(card["muse_flow"]),
                 "OMNIUM_COMPILED_CARD_INVALID")
        card_ids.add(cid)
        missing_list=card["missing_adapter_functions"]
        _require(type(missing_list) is list and len(missing_list)<=MAX_STEPS,
                 "OMNIUM_MISSING_DECLARATIONS_BAD")
        declared=set()
        for item in missing_list:
            _require(type(item) is dict and set(item)=={"name","reason"}
                     and _function(item["name"]) and _text(item["reason"])
                     and item["name"] not in ADMITTED_PLANNING_FUNCTIONS
                     and item["name"] not in declared,
                     "OMNIUM_MISSING_ADAPTER_DECLARATION_BAD")
            declared.add(item["name"])
            missing.add(item["name"])
            needs.setdefault(item["name"],{"function":item["name"],
                   "status":"MISSING_ADAPTER","used_by":[]})
        steps=card["steps"]
        _require(type(steps) is list and steps
                 and total_steps+len(steps)<=MAX_STEPS,
                 "OMNIUM_STEPS_BUDGET_REFUSED")
        seen_step_ids=set()
        for step in steps:
            _require(type(step) is dict and set(step)==STEP_KEYS,
                     "OMNIUM_STEP_FIELDS_REFUSED")
            sid=step["step_id"]
            fn=step["adapter_function"]
            status=step["adapter_status"]
            _require(_identifier(sid) and sid not in seen_step_ids
                     and _text(step["action"]) and _function(fn),
                     "OMNIUM_STEP_ID_OR_FUNCTION_INVALID")
            deps=step["depends_on"]
            _require(type(deps) is list and len(deps)<=MAX_STEPS
                     and len(deps)==len(set(map(str,deps)))
                     and all(_identifier(d) and d in seen_step_ids for d in deps)
                     and deps==sorted(deps),
                     "OMNIUM_STEP_DEPENDENCY_INVALID")
            produced=step["produces"]
            _require(type(produced) is list and len(produced)<=MAX_STEPS
                     and all(_text(x) for x in produced),
                     "OMNIUM_STEP_PRODUCED_ARTIFACTS_INVALID")
            want="ADMITTED_ROUTE" if fn in ADMITTED_PLANNING_FUNCTIONS else "MISSING_ADAPTER"
            _require(status==want and (want=="ADMITTED_ROUTE" or fn in declared),
                     "OMNIUM_ADAPTER_STATUS_MISMATCH_OR_UNDECLARED")
            _require(step["evidence_obligations"]==_obligation_step(cid,step),
                     "OMNIUM_STEP_EVIDENCE_OBLIGATIONS_BAD")
            seen_step_ids.add(sid)
            total_steps+=1
            slot=needs.setdefault(fn,{"function":fn,"status":want,"used_by":[]})
            _require(slot["status"]==want,
                     "OMNIUM_ADAPTER_STATUS_CONFLICT")
            slot["used_by"].append(f"{cid}/{sid}")
            referenced[fn]=want
            if want=="ADMITTED_ROUTE":
                admitted.add(fn)
        checks=card["acceptance_checks"]
        _require(type(checks) is list and 1<=len(checks)<=MAX_STEPS,
                 "OMNIUM_ACCEPTANCE_CHECKS_MISSING")
        for chk in checks:
            _require(type(chk) is dict
                     and {"check_id","description","verifier"}<=set(chk)
                     and set(chk)<={"check_id","description","verifier","evidence"}
                     and _identifier(chk["check_id"])
                     and _text(chk["description"]) and _text(chk["verifier"]),
                     "OMNIUM_ACCEPTANCE_CHECK_BAD")
            obligations.append({"obligation":"acceptance-check",
                 "card_id":cid,"check_id":chk["check_id"],
                 "verifier":chk["verifier"],"description":chk["description"]})
    for entry in needs.values():
        entry["used_by"]=sorted(entry["used_by"])
    supplied=plan["adapter_requirements"]
    _require(type(supplied) is list
             and supplied==[needs[k] for k in sorted(needs)]
             and plan["evidence_obligations"]==obligations,
             "OMNIUM_REQUIREMENTS_OR_ACCEPTANCE_DRIFT")
    return {
        "schema":SCHEMA,
        "route":ROUTE,
        "status":("PLAN_ONLY_MISSING_WORKER_ADAPTER_HELD" if missing
                  else "PLAN_ONLY_REGISTERED_ROUTES_NO_WORKER"),
        "plan_sha256":expected_plan_sha256,
        "card_count":len(card_ids),
        "step_count":total_steps,
        "admitted_planning_functions":sorted(admitted),
        "missing_adapter_functions":sorted(missing),
        "worker_dispatch_status":"NOT_INVOKED",
        "route_registry_snapshot":"SOURCE_PINNED_PLANNING_ONLY",
        "external_plan_sha_authenticated":False,
        "original_omnium_checker_reopened":False,
        "independent_host_attested":False,
        "provider_authenticated":False,
        "native_worker_invoked":False,
        "worker_result_verified":False,
        "recipient_readback_verified":False,
        "external_effect_authorized":False,
    }

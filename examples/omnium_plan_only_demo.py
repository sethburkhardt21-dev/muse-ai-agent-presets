"""Fictional input modeled on actual Omnium plan output; no Omnium route run.

This tests the T15 neutral read-only consumer seam, NOT compiler accuracy,
worker dispatch, host attestation or a signed original mission-plan receipt.
All custody digests except pinned schema/registry/compiler are synthetic.
"""
from __future__ import annotations

import copy
import hashlib
import json

from muse_presets.omnium_plan_review import (
    OMNIUM_SCHEMA_SHA256,OMNIUM_REGISTRY_SHA256,
    OMNIUM_COMPILER_SHA256,review_omnium_plan_only,
)


def recalc(plan:dict)->dict:
    """Recompute only the *local fixture* plan hash, not an issuer signature."""
    result=copy.deepcopy(plan)
    core={k:v for k,v in result.items() if k!="plan_sha256"}
    payload=json.dumps(core,sort_keys=True,separators=(",",":"),
                       ensure_ascii=False,allow_nan=False).encode("utf-8")
    result["plan_sha256"]=hashlib.sha256(payload).hexdigest()
    return result


def synthetic_plan()->dict:
    """One registered plan/review route and one intentionally absent worker."""
    cid="card-one"
    step_a={
        "step_id":"source-review",
        "action":"Review a fictional source diff without running a worker",
        "adapter_function":"omnium.foundry_review",
        "adapter_status":"ADMITTED_ROUTE",
        "depends_on":[],
        "produces":["source-report"],
        "evidence_obligations":[
            {"obligation":"step-completion-record","card_id":cid,
             "step_id":"source-review"},
            {"obligation":"artifact-produced","card_id":cid,
             "step_id":"source-review","artifact":"source-report"},
        ],
    }
    step_b={
        "step_id":"worker-proposal",
        "action":"Propose a worker action but never dispatch it",
        "adapter_function":"omnium.worker.execute",
        "adapter_status":"MISSING_ADAPTER",
        "depends_on":["source-review"],
        "produces":["worker-report"],
        "evidence_obligations":[
            {"obligation":"step-completion-record","card_id":cid,
             "step_id":"worker-proposal"},
            {"obligation":"artifact-produced","card_id":cid,
             "step_id":"worker-proposal","artifact":"worker-report"},
        ],
    }
    check={"check_id":"verify-source",
           "description":"Independent source review and no worker-dispatch claim",
           "verifier":"adversarial-verifier"}
    plan={
        "plan":"atlas-omnium/mission-plan",
        "plan_version":1,
        "route":"omnium.mission_plan",
        "card_set_sha256":"a"*64,
        "schema_sha256":OMNIUM_SCHEMA_SHA256,
        "registry_sha256":OMNIUM_REGISTRY_SHA256,
        "compiler_sha256":OMNIUM_COMPILER_SHA256,
        "ledger_sha256":"b"*64,
        "census_sha256":"c"*64,
        "files_in_census":15,
        "cards":[{
            "card_id":cid,
            "title":"Review a synthetic plan",
            "card_sha256":"d"*64,
            "muse_flow":"offline-proof-only",
            "missing_adapter_functions":[
                {"name":"omnium.worker.execute",
                 "reason":"No registered execution/worker route in Omnium registry"}
            ],
            "steps":[step_a,step_b],
            "acceptance_checks":[check],
        }],
        "adapter_requirements":[
            {"function":"omnium.foundry_review","status":"ADMITTED_ROUTE",
             "used_by":["card-one/source-review"]},
            {"function":"omnium.worker.execute","status":"MISSING_ADAPTER",
             "used_by":["card-one/worker-proposal"]},
        ],
        "evidence_obligations":[{
            "obligation":"acceptance-check","card_id":cid,
            "check_id":check["check_id"],"verifier":check["verifier"],
            "description":check["description"],
        }],
        "executes":False,
        "effects":"none",
    }
    return recalc(plan)


def demonstrate()->dict:
    plan=synthetic_plan()
    result=review_omnium_plan_only(
        plan,plan["plan_sha256"],
        expected_schema_sha256=OMNIUM_SCHEMA_SHA256,
        expected_registry_sha256=OMNIUM_REGISTRY_SHA256)
    if (result["status"]!="PLAN_ONLY_MISSING_WORKER_ADAPTER_HELD"
        or result["worker_dispatch_status"]!="NOT_INVOKED"
        or result["external_effect_authorized"] is not False):
        raise RuntimeError("OMNIUM_WORKER_SEAM_FALSE_AUTHORITY")
    return {
        **result,
        "synthetic_fixture":True,
        "omnium_mission_plan_invoked":False,
        "recipient_readback_verified":False,
        "original_source_cards_authenticated":False,
        "source_repo":"Atlas-Omnium (untrusted source label)",
        "source_registry_grade":"FOUR_PLANNING_REVIEW_RETRIEVAL_ROUTES_ONLY",
    }


if __name__=="__main__":
    print(json.dumps(demonstrate(),sort_keys=True,indent=2,ensure_ascii=False))

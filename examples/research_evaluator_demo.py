"""Two-source research trace with disjoint synthetic development/heldout cohorts.

No web, model, external effect, owner account, native Muse or scientific verdict.
"""
from __future__ import annotations

import copy
import hashlib
import json

from muse_presets.research_evaluator import evaluate_research_case


def _source(sid:str,family:str,partition:str,text:str)->dict:
    return {
        "source_id":sid,"family_id":family,"partition":partition,
        "text":text,"sha256":hashlib.sha256(text.encode("utf-8")).hexdigest(),
    }


def demonstrate()->dict:
    development=(
        "Development experiment: candidate correct on 8 of 10 synthetic cases.\n"
        "Dataset selection may account for the observed difference."
    )
    heldout=(
        "Held-out experiment: candidate correct on 2 of 4 synthetic cases; "
        "baseline correct on 3 of 4.\nNo generalization proven."
    )
    quote_a="candidate correct on 8 of 10 synthetic cases"
    quote_b="candidate correct on 2 of 4 synthetic cases"
    case={
        "schema":"r52/research-evidence-v1",
        "question":"Does an observed development improvement generalize across source families?",
        "hypothesis":"The candidate performs better on an independent held-out cohort.",
        "alternative":"The development advantage may result from dataset selection.",
        "falsifier":"An independent held-out set shows no candidate advantage.",
        "decision_rule":{"minimum_source_families":2,"heldout_required":True},
        "examiner":{
            "reviewer_id":"synthetic-reviewer-one",
            "candidate_author_id":"synthetic-author-two",
            "rubric_frozen_before_results":True,
            "heldout_seen_by_candidate":False,
        },
        "sources":[
            _source("dev-cohort","family-development","development",development),
            _source("holdout-cohort","family-heldout","heldout",heldout),
        ],
        "excerpts":[
            {"source_id":"dev-cohort","quote":quote_a,
             "offset":development.index(quote_a),"stance":"supports"},
            {"source_id":"holdout-cohort","quote":quote_b,
             "offset":heldout.index(quote_b),"stance":"contradicts"},
        ]
    }
    report=evaluate_research_case(case)
    tampered=copy.deepcopy(case)
    tampered["sources"][1]["text"]+="\nUnadmitted changed source."
    refused=False
    try:
        evaluate_research_case(tampered)
    except ValueError as exc:
        refused=str(exc)=="SOURCE_SHA256_MISMATCH"
    if not refused:
        raise RuntimeError("SOURCE_DRIFT_NOT_REFUSED")
    if (report["status"]!="LOCAL_SOURCE_TRACE_VERIFIED"
        or report["source_count"]!=2
        or report["evidence_partitions"]!={"development":1,"heldout":1}
        or report["scientific_hypothesis_proven"] is not False
        or len(report["citations"])!=2):
        raise RuntimeError("UNEXPECTED_RESEARCH_TRACE")
    return {
        "schema":"muse-presets/offline-demonstration-v1",
        "sandbox_only":True,
        "native_muse_installed":False,
        "external_effect_authorized":False,
        "scientific_verdict":"NOT_INDEPENDENTLY_VERIFIED",
        "research_evaluator":{**report,"tampered_source_refused":refused},
    }


if __name__=="__main__":
    print(json.dumps(demonstrate(),indent=2,sort_keys=True,ensure_ascii=False))

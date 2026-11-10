"""R53 actual offline numeric held-out evaluation on synthetic binary outcomes.

No scholarship retrieval, model execution, independent timestamps or causal proof.
"""
from __future__ import annotations

import copy
import hashlib
import json

from muse_presets.numeric_evaluation import evaluate_numeric_case,prediction_digest


def _source(identifier:str,family:str,part:str,text:str)->dict:
    return {
        "source_id":identifier,"family_id":family,"partition":part,
        "text":text,"sha256":hashlib.sha256(text.encode("utf-8")).hexdigest(),
    }


def demonstrate()->dict:
    dev="Synthetic development cohort: candidate metrics appeared better than baseline."
    held="Synthetic heldout cohort: baseline outperformed candidate."
    qa="candidate metrics appeared better"
    qb="baseline outperformed candidate"
    evidence={
        "schema":"r52/research-evidence-v1",
        "question":"Does candidate improvement generalize across heldout families?",
        "hypothesis":"Candidate prediction score is better than baseline on heldout records.",
        "alternative":"Candidate improvement may be restricted to development selection.",
        "falsifier":"Candidate heldout Brier score exceeds baseline heldout Brier.",
        "decision_rule":{"minimum_source_families":2,"heldout_required":True},
        "examiner":{
            "reviewer_id":"synthetic-independent-reviewer",
            "candidate_author_id":"synthetic-candidate-author",
            "rubric_frozen_before_results":True,
            "heldout_seen_by_candidate":False,
        },
        "sources":[
            _source("development-cohort","source-family-dev","development",dev),
            _source("heldout-cohort","source-family-held","heldout",held),
        ],
        "excerpts":[
            {"source_id":"development-cohort","quote":qa,
             "offset":dev.index(qa),"stance":"supports"},
            {"source_id":"heldout-cohort","quote":qb,
             "offset":held.index(qb),"stance":"contradicts"},
        ],
    }
    rows=[]
    labels=[1,0,1,0]
    for family,source,cp,bp in (
        ("development","development-cohort",[0.8,0.2,0.7,0.3],[0.6,0.4,0.6,0.4]),
        ("heldout","heldout-cohort",[0.2,0.8,0.4,0.6],[0.7,0.3,0.6,0.4]),
    ):
        for i,(label,p,b) in enumerate(zip(labels,cp,bp),1):
            rows.append({
                "sample_id":family+"-sample-"+str(i),
                "source_id":source,
                "partition":family,
                "feature_text":"synthetic-"+family+"-feature-"+str(i),
                "truth":label,
                "candidate_probability":p,
                "baseline_probability":b,
            })
    case={
        "schema":"r53/numeric-heldout-evaluation-v1",
        "evidence_case":evidence,
        "plan":{
            "metric":"accuracy_brier_calibration",
            "threshold":0.5,
            "confidence":0.95,
            "frozen_before_labels":True,
            "heldout_unseen_by_candidate":True,
        },
        "samples":rows,
        "prediction_sha256":prediction_digest(rows),
    }
    score=evaluate_numeric_case(case)
    altered=copy.deepcopy(case)
    altered["samples"][0]["candidate_probability"]=0.1
    refused=False
    try:
        evaluate_numeric_case(altered)
    except ValueError as exc:
        refused=str(exc)=="PREDICTION_COMMITMENT_MISMATCH"
    if not refused or score["partitions"]["heldout"]["paired_accuracy_delta"]>=0:
        raise RuntimeError("HELDOUT_COMMITMENT_OR_BASELINE_CROSSCHECK_FAILED")
    if score["scientific_hypothesis_proven"] or score["independent_commitment_time_verified"]:
        raise RuntimeError("FALSE_INDEPENDENT_EVALUATION_CLAIM")
    return {
        "schema":"muse-presets/offline-demonstration-v1",
        "sandbox_only":True,
        "native_muse_installed":False,
        "external_effect_authorized":False,
        "scientific_verdict":"NOT_INDEPENDENTLY_VERIFIED",
        "numeric_evaluation":score,
        "tampered_prediction_refused":refused,
    }


if __name__=="__main__":
    print(json.dumps(demonstrate(),indent=2,sort_keys=True,ensure_ascii=False))

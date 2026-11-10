"""R53 numeric held-out evaluator for local, caller-provided binary predictions.

Reuses the exact-source R52 research trace to guard source families and
partitions. Computes descriptive accuracy/Brier/ECE and Wilson intervals.
Does not authenticate prediction timing, outcome labels, publisher identity,
causality, scientific truth, or any external provider.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

from .native_canary import _no_duplicate_json, _reject_constant
from .native_skill_binding import _regular_bytes
from .research_evaluator import (
    _canonical, _sha, _slug, _strict_string,
    evaluate_research_case,
)

SCHEMA="r53/numeric-heldout-evaluation-v1"
INPUT_KEYS=frozenset({"schema","evidence_case","plan","samples","prediction_sha256"})
PLAN_KEYS=frozenset({
    "metric","threshold","confidence","frozen_before_labels",
    "heldout_unseen_by_candidate",
})
SAMPLE_KEYS=frozenset({
    "sample_id","source_id","partition","feature_text","truth",
    "candidate_probability","baseline_probability",
})
COMMIT_KEYS=(
    "sample_id","source_id","partition","feature_text",
    "candidate_probability","baseline_probability",
)
MAX_NUMERIC_CASE_BYTES=65536
MAX_SAMPLES=128
MIN_PER_PARTITION=4
Z_95=1.959963984540054


def _refuse(message:str)->None:
    raise ValueError(message)


def _prediction_rows(rows:Any)->list[dict]:
    """Sorted caller-supplied predictions; deliberately exclude answer labels."""
    if type(rows) is not list or not 1<=len(rows)<=MAX_SAMPLES:
        _refuse("SAMPLE_COUNT_INVALID")
    result=[]
    for row in rows:
        if type(row) is not dict or set(row)!=SAMPLE_KEYS:
            _refuse("SAMPLE_FIELDS_INVALID")
        result.append({name:row[name] for name in COMMIT_KEYS})
    try:
        return sorted(result,key=lambda r:r["sample_id"])
    except (KeyError,TypeError) as exc:
        raise ValueError("INVALID_SAMPLE_IDENTIFIERS") from exc


def prediction_digest(samples:Any)->str:
    """Deterministic commitment to given predictions, *not* a trusted time seal."""
    try:
        return _sha(_canonical(_prediction_rows(samples)))
    except (ValueError,TypeError,OverflowError) as exc:
        raise ValueError("INVALID_PREDICTION_RECORD") from exc


def _probability(value:Any,field:str)->float:
    if type(value) not in (int,float) or not math.isfinite(value) or not 0.0<=value<=1.0:
        _refuse("INVALID_PROBABILITY_"+field.upper())
    return float(value)


def _wilson_95(successes:int,n:int)->list[float]:
    """Wilson score interval for one binomial accuracy rate; descriptive only."""
    if n<1 or not 0<=successes<=n:
        raise ValueError("UNEXPECTED_WILSON_INPUT")
    p=successes/n
    z2=Z_95*Z_95
    denominator=1+z2/n
    center=(p+z2/(2*n))/denominator
    half=Z_95/denominator*math.sqrt(p*(1-p)/n+z2/(4*n*n))
    return [round(max(0.0,center-half),6),round(min(1.0,center+half),6)]


def _calibration_error(rows:list[tuple[int,float]],nbins:int=4)->float:
    """Descriptive equal-width ECE. Too small for claims of real calibration."""
    n=len(rows)
    total=0.0
    for bin_index in range(nbins):
        member=[(truth,p) for truth,p in rows if min(nbins-1,int(p*nbins))==bin_index]
        if not member:
            continue
        avg_probability=math.fsum(p for _,p in member)/len(member)
        observed_frequency=math.fsum(float(y) for y,_ in member)/len(member)
        total+=len(member)/n*abs(avg_probability-observed_frequency)
    return round(total,6)


def _score(rows:list[dict],threshold:float)->dict:
    n=len(rows)
    candidates=[(r["truth"],r["candidate_probability"]) for r in rows]
    baselines=[(r["truth"],r["baseline_probability"]) for r in rows]
    def model_metrics(items:list[tuple[int,float]])->dict:
        correct=sum((float(p)>=threshold)==bool(y) for y,p in items)
        accuracy=correct/n
        brier=math.fsum((p-y)**2 for y,p in items)/n
        return {
            "accuracy":round(accuracy,6),
            "correct":correct,
            "total":n,
            "brier":round(brier,6),
            "wilson95_accuracy":_wilson_95(correct,n),
            "ece_4bins":_calibration_error(items),
        }
    candidate=model_metrics(candidates)
    baseline=model_metrics(baselines)
    outcomes={"candidate_only_correct":0,"baseline_only_correct":0,
              "both_correct":0,"both_incorrect":0}
    for row in rows:
        truth=bool(row["truth"])
        cand=row["candidate_probability"]>=threshold
        base=row["baseline_probability"]>=threshold
        if cand==truth and base==truth:
            outcomes["both_correct"]+=1
        elif cand==truth:
            outcomes["candidate_only_correct"]+=1
        elif base==truth:
            outcomes["baseline_only_correct"]+=1
        else:
            outcomes["both_incorrect"]+=1
    return {
        "n":n,
        "source_families":len(set(r["family_id"] for r in rows)),
        "candidate":candidate,
        "baseline":baseline,
        "paired_outcomes":outcomes,
        "paired_accuracy_delta":round(candidate["accuracy"]-baseline["accuracy"],6),
        "paired_brier_advantage":round(baseline["brier"]-candidate["brier"],6),
        "difference_interval":"NOT_ESTIMATED_NO_CAUSAL_CONCLUSION",
    }


def evaluate_numeric_case(case:Any)->dict:
    """Validate source families and compute actual held-out binary scores."""
    if type(case) is not dict or set(case)!=INPUT_KEYS or case.get("schema")!=SCHEMA:
        _refuse("NUMERIC_CASE_SCHEMA_REFUSED")
    try:
        # Serialization for the size limit permits NaN only temporarily:
        # the typed probability checks below reject it with the correct
        # INVALID_PROBABILITY classification before any scoring or hashing.
        serialized=json.dumps(case,sort_keys=True,separators=(",",":"),
                              ensure_ascii=False,allow_nan=True).encode("utf-8")
        if len(serialized)>MAX_NUMERIC_CASE_BYTES:
            _refuse("NUMERIC_CASE_TOO_LARGE")
    except (TypeError,ValueError,OverflowError) as exc:
        raise ValueError("INVALID_NUMERIC_CASE_ENCODING") from exc

    evidence=case["evidence_case"]
    trace=evaluate_research_case(evidence)
    plan=case["plan"]
    if type(plan) is not dict or set(plan)!=PLAN_KEYS:
        _refuse("INVALID_NUMERIC_PLAN")
    if (plan.get("frozen_before_labels") is not True
        or plan.get("heldout_unseen_by_candidate") is not True):
        _refuse("UNSEALED_EVALUATION_PLAN")
    if plan["metric"]!="accuracy_brier_calibration":
        _refuse("UNSUPPORTED_EVALUATION_METRIC")
    threshold=plan["threshold"]
    if (type(threshold) not in (int,float) or not math.isfinite(threshold)
        or not 0.0<threshold<1.0):
        _refuse("INVALID_EVALUATION_THRESHOLD")
    if type(plan["confidence"]) not in (int,float) or plan["confidence"]!=0.95:
        _refuse("UNSUPPORTED_CONFIDENCE_LEVEL")
    source_table={row["source_id"]:row for row in evidence["sources"]}
    if len(source_table)!=trace["source_count"]:
        _refuse("UNEXPECTED_EVIDENCE_SOURCE_SET")
    rows=case["samples"]
    if type(rows) is not list or not 1<=len(rows)<=MAX_SAMPLES:
        _refuse("SAMPLE_COUNT_INVALID")
    seen_ids=set()
    seen_contents=set()
    groups={"development":[],"heldout":[]}
    for item in rows:
        if type(item) is not dict or set(item)!=SAMPLE_KEYS:
            _refuse("SAMPLE_FIELDS_INVALID")
        sid=_slug(item["sample_id"],"sample_id")
        source_id=_slug(item["source_id"],"source_id")
        if sid in seen_ids:
            _refuse("DUPLICATE_SAMPLE_ID")
        seen_ids.add(sid)
        if source_id not in source_table:
            _refuse("UNKNOWN_EVIDENCE_SOURCE")
        if type(item["partition"]) is not str or item["partition"] not in ("development","heldout"):
            _refuse("INVALID_SAMPLE_PARTITION")
        source=source_table[source_id]
        if item["partition"]!=source["partition"]:
            _refuse("SAMPLE_CONTENT_PARTITION_LEAK")
        features=_strict_string(item["feature_text"],256,"feature_text")
        digest=_sha(features.encode("utf-8"))
        if digest in seen_contents:
            _refuse("DUPLICATE_SAMPLE_CONTENT")
        seen_contents.add(digest)
        actual=item["truth"]
        if type(actual) is not int or actual not in (0,1):
            _refuse("INVALID_TRUTH_LABEL")
        candidate=_probability(item["candidate_probability"],"candidate")
        baseline=_probability(item["baseline_probability"],"baseline")
        groups[item["partition"]].append({
            "sample_id":sid,
            "family_id":source["family_id"],
            "truth":actual,
            "candidate_probability":candidate,
            "baseline_probability":baseline,
        })
    if len(groups["heldout"])<MIN_PER_PARTITION:
        _refuse("INSUFFICIENT_HELDOUT_SAMPLES")
    if len(groups["development"])<MIN_PER_PARTITION:
        _refuse("INSUFFICIENT_DEVELOPMENT_SAMPLES")
    families=set()
    for group in groups.values():
        families.update(r["family_id"] for r in group)
    if len(families)<evidence["decision_rule"]["minimum_source_families"]:
        _refuse("INSUFFICIENT_SCORED_SOURCE_FAMILIES")
    claimed_digest=case["prediction_sha256"]
    if type(claimed_digest) is not str or len(claimed_digest)!=64:
        _refuse("INVALID_PREDICTION_COMMITMENT")
    try:
        observed_digest=prediction_digest(rows)
    except ValueError as exc:
        raise ValueError("INVALID_PREDICTION_COMMITMENT") from exc
    if observed_digest!=claimed_digest:
        _refuse("PREDICTION_COMMITMENT_MISMATCH")
    normalized={**case,"samples":sorted(rows,key=lambda r:r["sample_id"])}
    report={
        "schema":"r53/numeric-heldout-report-v1",
        "status":"LOCAL_NUMERIC_HELDOUT_EVALUATED",
        "input_sha256":_sha(_canonical(normalized)),
        "evidence_trace_input_sha256":trace["input_sha256"],
        "prediction_sha256":claimed_digest,
        "prediction_data_matches_caller_commitment":True,
        "rubric_claimed_frozen":True,
        "threshold":float(threshold),
        "interval_method":"WILSON_SCORE_95_BINOMIAL_ACCURACY_DESCRIPTIVE",
        "calibration_metric":"ECE_EQUAL_WIDTH_4_BINS_EXPLORATORY",
        "partitions":{
            name:_score(sorted(items,key=lambda r:r["sample_id"]),float(threshold))
            for name,items in groups.items()
        },
        "evaluated_source_families":len(families),
        "source_evidence_trace_status":trace["status"],
        "independent_commitment_time_verified":False,
        "independent_outcome_authenticity_verified":False,
        "scientific_hypothesis_proven":False,
        "causal_effect_established":False,
        "native_muse_installed":False,
        "provider_data_retrieved":False,
        "external_effect_authorized":False,
        "warnings":[
            "All labels, source family IDs and pre-result commitments are caller-supplied, not independently verified.",
            "Wilson accuracy intervals and 4-bin ECE describe supplied records; neither proves calibration or a paired improvement.",
            "A matching prediction hash is not evidence of a trusted prior timestamp, controlled blinding or publication identity.",
        ],
    }
    return report


def load_numeric_file(path:Path)->dict:
    """Bounded, symlink-refusing UTF-8 JSON intake for a single evaluation."""
    try:
        raw=_regular_bytes(Path(path),MAX_NUMERIC_CASE_BYTES)
        item=json.loads(raw.decode("utf-8"),
                        object_pairs_hook=_no_duplicate_json,
                        parse_constant=_reject_constant)
    except (OSError,ValueError,TypeError,UnicodeError) as exc:
        raise ValueError("UNSAFE_NUMERIC_CASE_FILE") from exc
    if type(item) is not dict:
        _refuse("NUMERIC_CASE_MUST_BE_OBJECT")
    return item

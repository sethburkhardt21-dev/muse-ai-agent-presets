"""Offline Research Evaluator: exact evidence trace with held-out source-family checks.

This validates only user-supplied source bytes and excerpt positions. Stance,
family identity, authorship, precommitment and source authenticity remain
caller assertions. It never fetches papers, evaluates scientific truth, grants
independent reviewer authority, or starts any external provider.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from .finder import MAX_FILE_BYTES
from .native_skill_binding import _regular_bytes
from .native_canary import _no_duplicate_json, _reject_constant

SCHEMA="r52/research-evidence-v1"
SOURCE_KEYS=frozenset({"source_id","family_id","partition","text","sha256"})
EXCERPT_KEYS=frozenset({"source_id","quote","offset","stance"})
INPUT_KEYS=frozenset({
    "schema","question","hypothesis","alternative","falsifier",
    "decision_rule","examiner","sources","excerpts",
})
EXAMINER_KEYS=frozenset({
    "reviewer_id","candidate_author_id","rubric_frozen_before_results",
    "heldout_seen_by_candidate",
})
DECISION_KEYS=frozenset({"minimum_source_families","heldout_required"})
SLUG=re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
SHA=re.compile(r"^[0-9a-f]{64}$")
PARTITIONS=frozenset({"development","heldout"})
STANCES=frozenset({"supports","contradicts","neutral"})
MAX_SOURCES=16
MAX_EXCERPTS=32
MAX_CASE_BYTES=32768


def _refuse(reason:str)->None:
    raise ValueError(reason)


def _strict_string(value:Any,max_length:int,field:str)->str:
    if type(value) is not str or not value.strip() or len(value)>max_length:
        _refuse("INVALID_"+field.upper())
    if "\x00" in value or any(ord(c)<32 and c not in "\r\n\t" for c in value):
        _refuse("INVALID_"+field.upper())
    return value


def _slug(value:Any,field:str)->str:
    if type(value) is not str or SLUG.fullmatch(value) is None or len(value)>80:
        _refuse("INVALID_"+field.upper())
    return value


def _sha(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()


def _canonical(value:dict)->bytes:
    return json.dumps(value,sort_keys=True,separators=(",",":"),
                      ensure_ascii=False,allow_nan=False).encode("utf-8")


def evaluate_research_case(case:Any)->dict:
    """Produce reproducible exact citation locations, not a semantic verdict."""
    if type(case) is not dict or set(case)!=INPUT_KEYS or case.get("schema")!=SCHEMA:
        _refuse("RESEARCH_CASE_SCHEMA_REFUSED")

    question=_strict_string(case["question"],512,"question")
    hypothesis=_strict_string(case["hypothesis"],512,"hypothesis")
    alternative=_strict_string(case["alternative"],512,"alternative")
    falsifier=_strict_string(case["falsifier"],512,"falsifier")

    rule=case["decision_rule"]
    if type(rule) is not dict or set(rule)!=DECISION_KEYS:
        _refuse("DECISION_RULE_FIELDS")
    minimum=rule.get("minimum_source_families")
    if type(minimum) is not int or not 2<=minimum<=MAX_SOURCES:
        _refuse("MINIMUM_SOURCE_FAMILIES_INVALID")
    if rule.get("heldout_required") is not True:
        _refuse("HELDOUT_EVALUATION_REQUIRED")

    examiner=case["examiner"]
    if type(examiner) is not dict or set(examiner)!=EXAMINER_KEYS:
        _refuse("EXAMINER_FIELDS")
    reviewer=_slug(examiner["reviewer_id"],"reviewer_id")
    candidate=_slug(examiner["candidate_author_id"],"candidate_author_id")
    if reviewer==candidate:
        _refuse("REVIEWER_AUTHOR_CONFLICT")
    if examiner["rubric_frozen_before_results"] is not True:
        _refuse("RUBRIC_NOT_PRECOMMITTED")
    if examiner["heldout_seen_by_candidate"] is not False:
        _refuse("HELDOUT_LEAK_OR_UNVERIFIED_FLAG")

    sources=case["sources"]
    if type(sources) is not list or not 2<=len(sources)<=MAX_SOURCES:
        _refuse("SOURCE_COUNT_INVALID")
    lookup={}
    families={}
    digests=set()
    counts={"development":0,"heldout":0}
    for record in sources:
        if type(record) is not dict or set(record)!=SOURCE_KEYS:
            _refuse("SOURCE_RECORD_FIELDS")
        sid=_slug(record["source_id"],"source_id")
        family=_slug(record["family_id"],"family_id")
        partition=record["partition"]
        if type(partition) is not str or partition not in PARTITIONS:
            _refuse("INVALID_PARTITION")
        if sid in lookup:
            _refuse("DUPLICATE_SOURCE_ID")
        if family in families and families[family]!=partition:
            _refuse("CROSS_PARTITION_SOURCE_FAMILY_LEAK")
        text=_strict_string(record["text"],MAX_FILE_BYTES,"source_text")
        raw=text.encode("utf-8")
        if len(raw)>MAX_FILE_BYTES:
            _refuse("SOURCE_TOO_LARGE")
        supplied=record["sha256"]
        if type(supplied) is not str or SHA.fullmatch(supplied) is None:
            _refuse("INVALID_SOURCE_DIGEST")
        if _sha(raw)!=supplied:
            _refuse("SOURCE_SHA256_MISMATCH")
        if supplied in digests:
            _refuse("DUPLICATE_SOURCE_BYTES")
        digests.add(supplied)
        families[family]=partition
        lookup[sid]={"text":text,"digest":supplied,
                     "family":family,"partition":partition}
        counts[partition]+=1
    if not all(counts.values()):
        _refuse("HELDOUT_OR_DEVELOPMENT_SOURCES_MISSING")
    if len(families)<minimum:
        _refuse("NOT_ENOUGH_INDEPENDENT_SOURCE_FAMILIES")

    excerpts=case["excerpts"]
    if type(excerpts) is not list or not 2<=len(excerpts)<=MAX_EXCERPTS:
        _refuse("EXCERPT_COUNT_INVALID")
    seen=set()
    citation_rows=[]
    labels={"supports":0,"contradicts":0,"neutral":0}
    evidence_partition={"development":0,"heldout":0}
    used_families=set()
    for row in excerpts:
        if type(row) is not dict or set(row)!=EXCERPT_KEYS:
            _refuse("EXCERPT_FIELDS")
        sid=_slug(row["source_id"],"excerpt_source")
        if sid not in lookup:
            _refuse("EXCERPT_UNKNOWN_SOURCE")
        quote=_strict_string(row["quote"],256,"quote")
        offset=row["offset"]
        if type(offset) is not int or offset<0:
            _refuse("INVALID_EXCERPT_OFFSET")
        stance=row["stance"]
        if type(stance) is not str or stance not in STANCES:
            _refuse("INVALID_STANCE")
        original=lookup[sid]
        if original["text"][offset:offset+len(quote)]!=quote:
            _refuse("QUOTE_POSITION_MISMATCH")
        identity=(sid,offset,quote)
        if identity in seen:
            _refuse("DUPLICATE_EXCERPT")
        seen.add(identity)
        used_families.add(original["family"])
        evidence_partition[original["partition"]]+=1
        labels[stance]+=1
        citation_rows.append({
            "source_id":sid,
            "family_id":original["family"],
            "partition":original["partition"],
            "source_sha256":original["digest"],
            "quote":quote,
            "quote_sha256":_sha(quote.encode("utf-8")),
            "offset":offset,
            "line":original["text"].count("\n",0,offset)+1,
            "caller_supplied_stance":stance,
            "stance_semantically_verified":False,
        })
    if not all(evidence_partition.values()):
        _refuse("HELDOUT_EVIDENCE_REQUIRED")
    if len(used_families)<minimum:
        _refuse("NOT_ENOUGH_EVIDENCED_SOURCE_FAMILIES")

    citations=sorted(citation_rows,key=lambda x:(x["source_id"],x["offset"],x["quote_sha256"]))
    return {
        "schema":"r52/research-trace-report-v1",
        "status":"LOCAL_SOURCE_TRACE_VERIFIED",
        "input_sha256":_sha(_canonical(case)),
        "question":question,
        "hypothesis":hypothesis,
        "alternative":alternative,
        "falsifier":falsifier,
        "source_count":len(lookup),
        "source_families":len(families),
        "partitions":counts,
        "evidence_partitions":evidence_partition,
        "caller_stance_counts":labels,
        "citations":citations,
        "conclusion_grade":"EXCERPT_MATCH_ONLY_SEMANTICS_NOT_VERIFIED",
        "precommit_grade":"CALLER_ASSERTED_NOT_INDEPENDENTLY_ATTESTED",
        "independent_examiner_verified":False,
        "scientific_hypothesis_proven":False,
        "native_installed":False,
        "external_effect_authorized":False,
        "provider_data_retrieved":False,
        "heldout_independence_authenticated":False,
        "warnings":[
            "Source bytes and positions verified locally, not original publisher identity.",
            "Source family, reviewer separation, label stance and precommit timing are caller claims.",
            "No causal, scientific or external validation verdict follows from matching excerpts.",
        ],
    }


def load_case_file(path:Path)->dict:
    """Read one bounded UTF-8 case; reject symlinks, JSON keys and NaN."""
    try:
        raw=_regular_bytes(Path(path),MAX_CASE_BYTES)
        parsed=json.loads(raw.decode("utf-8"),
                          object_pairs_hook=_no_duplicate_json,
                          parse_constant=_reject_constant)
    except (OSError,TypeError,ValueError,UnicodeError) as exc:
        raise ValueError("UNSAFE_RESEARCH_CASE_FILE") from exc
    if type(parsed) is not dict:
        _refuse("RESEARCH_CASE_MUST_BE_OBJECT")
    return parsed

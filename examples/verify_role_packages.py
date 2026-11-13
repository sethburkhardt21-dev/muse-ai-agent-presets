"""R47 GitHub clean-clone role package verifier.

Exercises fifteen pristine local source packages and only supported offline
examples. No native Muse/Hatch account, plugin, network, desktop, model or
remote machine is accessed. Unavailable engines are labelled, never faked.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile

from muse_presets.catalog import load_registry
from muse_presets.playbooks import load_playbook
from muse_presets.standalone_pack import (
    plan_standalone_pack, stage_standalone_pack,
    inspect_standalone_pack, export_clean_standalone_pack)
from muse_presets.portable_connectors import (
    plan_connector, run_offline_fixture, reconcile_fixture)

SCHEMA="r47/github-role-acceptance-v1"
TEMPLATE_ROLES=frozenset({
    "creative-studio","adversarial-verifier","personal-companion",
})
SLICE_ROLES=frozenset({
    "claims-adjudicator","reverse-engineering-researcher","research-evaluator",
})
SCRIPT_DEMOS={
    "research-evaluator":("research_evaluator_demo.py","muse-presets/offline-demonstration-v1"),
    "garden-companion":("garden_calendar_demo.py","LOCAL_SQLITE_DEMO_PASSED"),
    "learning-coach":("learning_session_demo.py","LOCAL_NONCLINICAL_STUDY_DEMO_PASSED"),
    "claims-adjudicator":("priority_slices.py","muse-presets/offline-demonstration-v1"),
    "reverse-engineering-researcher":("priority_slices.py","muse-presets/offline-demonstration-v1"),
}
ROLE_RUNNERS={
    "coordinator":("coordinator-dropin","coordinator_workgraph","LOCAL_COORDINATOR_DEMO_PASSED"),
    "model-builder":("model-builder-dropin","model_development_metrics","LOCAL_MODEL_BUILDER_DEMO_PASSED"),
}


def _process(args:list[str],cwd:Path,*,timeout:int=60)->str:
    env={**os.environ,"PYTHONPATH":str(cwd/"src"),"PYTHONDONTWRITEBYTECODE":"1"}
    proc=subprocess.run(args,cwd=cwd,env=env,capture_output=True,text=True,
                        encoding="utf-8",errors="replace",timeout=timeout)
    if proc.returncode!=0:
        raise ValueError("LOCAL_DEMO_FAILED:"+Path(args[2] if len(args)>2 else args[-1]).name)
    return proc.stdout


def _local_demo(root:Path,role:str,base:Path)->dict:
    # These new source-tree engines perform bounded analysis, not native activation.
    fixture_expectations = {
        "data-engineering-architect": ("duplicate_count", 1),
        "infrastructure-reliability-engineer": ("failures", 1),
        "automation-engineer": ("order", ["build", "test"]),
        "product-interface-designer": ("missing_control_labels", 1),
    }
    if role in fixture_expectations:
        output=_process([sys.executable,"-B","examples/specialist_engine_demo.py",
                         "--role",role],root,timeout=30)
        data=json.loads(output)
        field,expected=fixture_expectations[role]
        if (type(data) is not dict or data.get("role")!=role
                or data.get("grade")!="OFFLINE_FIXTURE_ONLY"
                or data.get(field)!=expected
                or data.get("native_registered") is not False
                or data.get("external_effect_authorized") is not False
                or data.get("production_effect_verified") is not False
                or (role=="product-interface-designer"
                    and data.get("actual_browser_test")!="NOT_RUN")):
            raise ValueError("SPECIALIST_FIXTURE_EVIDENCE_INVALID")
        return {"local_demo_grade":"LOCAL_OFFLINE_FIXTURE_DEMO_PASSED",
                "local_engine_executed":True,"demo_exit_code":0,
                "fixture_result_checked":True,
                "independent_adjudicator_or_live_capture":False}
    if role in TEMPLATE_ROLES:
        return {"local_demo_grade":"SOURCE_TEMPLATE_ONLY",
                "local_engine_executed":False,"demo_exit_code":None,
                "independent_adjudicator_or_live_capture":False}
    if role in ROLE_RUNNERS:
        cmd,runner,expected=ROLE_RUNNERS[role]
        staged=base/"engine-probe"
        result=_process([sys.executable,"-B","-m","muse_presets.cli",cmd,
                         "--to",str(staged)],root,timeout=40)
        stage_report=json.loads(result)
        if stage_report.get("native_installed") is not False:
            raise ValueError("ROLE_RUNNER_NATIVE_STATUS_FORGED")
        runner_path=staged/"custom-skills"/runner/"run.py"
        if not runner_path.is_file() or runner_path.is_symlink():
            raise ValueError("ROLE_RUNNER_MISSING")
        output=_process([sys.executable,"-I","-B",str(runner_path),
                         "--operation","demo"],root,timeout=35)
        data=json.loads(output)
        if (data.get("status")!=expected or data.get("native_tool_invoked") is not False
            or data.get("external_effect_authorized") is not False):
            raise ValueError("ROLE_ENGINE_EVIDENCE_INVALID")
        toy_flags={}
        if role=="model-builder":
            toy_output=_process([sys.executable,"-I","-B",str(runner_path),
                                 "--operation","toy-demo","--allow-local-training"],root,timeout=45)
            toy=json.loads(toy_output)
            if (toy.get("status")!="LOCAL_TOY_MODEL_DEMO_PASSED"
                or toy.get("trained_this_call") is not True
                or toy.get("checkpoint_reloaded") is not True
                or toy.get("baseline_recovered") is not True
                or toy.get("candidate_correct")!=4 or toy.get("baseline_correct")!=2
                or toy.get("promotion_authorized") is not False
                or toy.get("native_tool_invoked") is not False
                or toy.get("external_effect_authorized") is not False):
                raise ValueError("TOY_TRAINING_CHECKPOINT_DEMO_INCOMPLETE")
            toy_flags={"toy_training_executed":True,"checkpoint_inference_executed":True,
                       "baseline_recovery_tested":True,
                       "toy_model_family":"binary-integer-perceptron",
                       "training_authority":"LOCAL_EXPLICIT_OPT_IN_ONLY"}
            linear=json.loads(_process([sys.executable,"-I","-B",str(runner_path),
                "--operation","linear-demo","--allow-local-training"],root,timeout=45))
            if (linear.get("status")!="LOCAL_LINEAR_MODEL_DEMO_PASSED"
                or linear.get("optimizer_steps")!=64
                or linear.get("bundle_recomputed") is not True
                or linear.get("baseline_restored_byte_exact") is not True
                or linear.get("final_status")!="HELD_UNEVALUATED"
                or linear.get("promotion_authorized") is not False
                or linear.get("native_tool_invoked") is not False
                or linear.get("external_effect_authorized") is not False):
                raise ValueError("LINEAR_TRAINING_RECOMPUTATION_OR_ROLLBACK_NOT_PROVEN")
            toy_flags.update({"linear_training_executed":True,
                "linear_bundle_recomputed":True,"linear_baseline_restored":True,
                "linear_optimizer_steps":64})
        return {"local_demo_grade":"LOCAL_ENGINE_DEMO_PASSED",
                "local_engine_executed":True,"demo_exit_code":0,
                "independent_adjudicator_or_live_capture":False,**toy_flags}
    if role=="software-engineer":
        output=_process([sys.executable,"-B",
                         "examples/software_engineer_claim_gate_demo.py"],root,timeout=70)
        if ("Atomic first claim, no-replay, UNKNOWN recovery: PASS" not in output
            or "NOT INVOKED" not in output):
            raise ValueError("ENGINE_CLAIM_GATE_DEMO_INCOMPLETE")
        workflow_output=_process([sys.executable,"-B",
                         "examples/software_engineer_workflow_demo.py"],root,timeout=90)
        workflow=json.loads(workflow_output)
        trace=workflow.get("workflow",{})
        if (workflow.get("status")!="LOCAL_ENGINEERING_WORKFLOW_GREEN"
            or trace.get("red_exit")!=1 or trace.get("green_exit")!=0
            or trace.get("green_tests")!=4
            or trace.get("baseline_commit")==trace.get("patched_commit")
            or workflow.get("independent_review_status")!="PENDING_EXTERNAL_REVIEWS"
            or workflow.get("native_muse_invoked") is not False
            or workflow.get("external_effect_authorized") is not False):
            raise ValueError("ENGINEERING_WORKFLOW_DEMO_INCOMPLETE")
        return {"local_demo_grade":"LOCAL_ENGINE_DEMO_PASSED",
                "local_engine_executed":True,"demo_exit_code":0,
                "workflow_red_green_proven":True,
                "workflow_independent_review_complete":False,
                "independent_adjudicator_or_live_capture":False}
    if role in SCRIPT_DEMOS:
        file,expected=SCRIPT_DEMOS[role]
        output=_process([sys.executable,"-B","examples/"+file],root,timeout=55)
        report=json.loads(output)
        numeric_flags={}
        if role in SLICE_ROLES:
            if report.get("schema")!=expected or not report.get("sandbox_only"):
                raise ValueError("LOCAL_SLICE_DEMO_INVALID")
            if role=="research-evaluator":
                trace=report.get("research_evaluator")
                if (type(trace) is not dict
                    or trace.get("status")!="LOCAL_SOURCE_TRACE_VERIFIED"
                    or trace.get("tampered_source_refused") is not True
                    or trace.get("source_count")!=2
                    or trace.get("evidence_partitions")!={"development":1,"heldout":1}
                    or len(trace.get("citations",[]))!=2
                    or trace.get("scientific_hypothesis_proven") is not False
                    or trace.get("independent_examiner_verified") is not False
                    or report.get("native_muse_installed") is not False):
                    raise ValueError("RESEARCH_EVALUATOR_LOCAL_EVIDENCE_INVALID")
                numeric_output=_process(
                    [sys.executable,"-B","examples/numeric_evaluation_demo.py"],
                    root,timeout=55)
                numeric_report=json.loads(numeric_output)
                numeric_trace=numeric_report.get("numeric_evaluation")
                if (numeric_report.get("schema")!="muse-presets/offline-demonstration-v1"
                    or numeric_report.get("sandbox_only") is not True
                    or numeric_report.get("tampered_prediction_refused") is not True
                    or type(numeric_trace) is not dict
                    or numeric_trace.get("status")!="LOCAL_NUMERIC_HELDOUT_EVALUATED"
                    or numeric_trace.get("scientific_hypothesis_proven") is not False
                    or numeric_trace.get("independent_commitment_time_verified") is not False
                    or numeric_trace.get("independent_outcome_authenticity_verified") is not False
                    or numeric_trace.get("partitions",{}).get("heldout",{}).get("paired_accuracy_delta",1)>=0
                    or numeric_report.get("external_effect_authorized") is not False
                    or numeric_report.get("native_muse_installed") is not False):
                    raise ValueError("RESEARCH_NUMERIC_HELDOUT_DEMO_INVALID")
                numeric_flags={
                    "numeric_heldout_scored":True,
                    "numeric_scientific_verdict_verified":False,
                }
            if role=="claims-adjudicator" and (
                report["claims_adjudicator"].get("disposition")!="OVERCLAIM"
                or report["claims_adjudicator"].get("independent_verified") is not False):
                raise ValueError("CLAIMS_SCOPE_DEMO_INVALID")
            if role=="reverse-engineering-researcher" and (
                "reverse_engineering_researcher" not in report
                or report.get("native_muse_installed") is not False):
                raise ValueError("REVERSE_SCOPE_DEMO_INVALID")
        elif report.get("status")!=expected:
            raise ValueError("LOCAL_SOURCE_ENGINE_DEMO_INVALID")
        grade="LOCAL_SLICE_DEMO_PASSED" if role in SLICE_ROLES else "LOCAL_ENGINE_DEMO_PASSED"
        return {"local_demo_grade":grade,"local_engine_executed":True,
                "demo_exit_code":0,
                "independent_adjudicator_or_live_capture":False,
                **numeric_flags}
    raise ValueError("UNCLASSIFIED_ROLE_CAPABILITY")


def verify_one(root:Path,role:str)->dict:
    root=Path(root).resolve(strict=True)
    catalog=load_registry()["presets"]
    if type(role) is not str or role not in catalog:
        raise ValueError("INVALID_ROLE")
    if not (root/"presets"/role/"INSTALL.md").is_file():
        raise ValueError("MISSING_ROLE_INSTALL_GUIDE")
    with tempfile.TemporaryDirectory(prefix="r47-github-role-") as scratch:
        base=Path(scratch)
        source=base/"role-pack"
        export=base/"source.zip"
        planned=plan_standalone_pack(role)
        created=stage_standalone_pack(
            source,role,expected_profile_source_sha256=planned["profile_source_sha256"])
        inspected=inspect_standalone_pack(source)
        if (created.get("status")!="LOCAL_STANDALONE_STAGED"
            or inspected.get("status")!="LOCAL_STANDALONE_MATCH"
            or inspected.get("native_installed") is not False):
            raise ValueError("ROLE_PACKAGE_SOURCE_INSPECTION_FAILED")
        receipt=json.loads((source/"INSTALL_RECEIPT.json").read_text(encoding="utf-8"))
        if (receipt["role"]!=role or receipt["profile_source_sha256"]!=planned["profile_source_sha256"]
            or receipt["native_installed"] or receipt["external_effect_authorized"]):
            raise ValueError("ROLE_SOURCE_RECEIPT_INCONSISTENT")
        exported=export_clean_standalone_pack(source,export)
        if exported["status"]!="LOCAL_EXPORT_CREATED":
            raise ValueError("ROLE_EXPORT_REJECTED")
        with zipfile.ZipFile(export) as z:
            names=z.namelist()
            if (z.testzip() is not None or len(names)!=len(set(names))
                or "INSTALL_RECEIPT.json" not in names
                or any(n.startswith("/") or ".." in Path(n).parts for n in names)):
                raise ValueError("ROLE_ARCHIVE_INVALID")
            if json.loads(z.read("INSTALL_RECEIPT.json"))!=receipt:
                raise ValueError("ROLE_ARCHIVE_RECEIPT_MISMATCH")
        source_zip_sha=hashlib.sha256(export.read_bytes()).hexdigest()
        if source_zip_sha!=exported["sha256"]:
            raise ValueError("ROLE_ARCHIVE_SHA_MISMATCH")
        declared=load_playbook(role)["optional_tool_categories"]
        if not declared:
            raise ValueError("ROLE_ALLOWLIST_EMPTY")
        request_id="r47."+role.replace("-","_")
        proposal=plan_connector(role,declared[0],request_id=request_id)
        observation="Synthetic source-only contract for "+role
        rows=[{"id":"sample-1","observation":observation,
               "sha256":hashlib.sha256(observation.encode("utf-8")).hexdigest()}]
        found=run_offline_fixture(proposal,rows)
        if reconcile_fixture(proposal,rows,found)["status"]!="CONSISTENT_OFFLINE_FIXTURE_ONLY":
            raise ValueError("ROLE_FIXTURE_RECONCILIATION_FAILED")
        demo=_local_demo(root,role,base)
        return {
            "role":role,
            "source_inspection":inspected["status"],
            "source_export":exported["status"],
            "source_sha256":planned["profile_source_sha256"],
            "role_zip_sha256":source_zip_sha,
            "role_zip_file_count":len(names),
            "subchats":inspected["subchat_count"],
            "disabled_skills":inspected["skill_count"],
            "connector_grade":"CONSISTENT_OFFLINE_FIXTURE_ONLY",
            "provider_connected":False,"native_installed":False,
            "external_effects_authorized":False,
            **demo,
        }


def verify_all(root:Path,roles:list[str])->dict:
    if type(roles) is not list or not roles or len(set(roles))!=len(roles):
        raise ValueError("INVALID_ROLE_LIST")
    report={role:verify_one(root,role) for role in roles}
    shared={}
    if set(roles)==set(load_registry()["presets"]):
        out=_process([sys.executable,"-B","examples/evidence_ledger_demo.py"],
                     Path(root).resolve(strict=True),timeout=45)
        if ("Locally verified receipt chain" not in out
            or "NOT VERIFIED" not in out):
            raise ValueError("SHARED_EVIDENCE_FINDER_UNVERIFIED")
        shared={"evidence-finder":{
            "local_demo_grade":"LOCAL_ENGINE_DEMO_PASSED",
            "demo_exit_code":0,
            "native_invocation_verified":False,
        }}
    return {
        "schema":SCHEMA,
        "status":"CLEAN_CLONE_ROLE_MATRIX_SOURCE_ONLY",
        "role_count":len(report),"roles":report,
        "subchats":sum(row["subchats"] for row in report.values()),
        "disabled_skills":sum(row["disabled_skills"] for row in report.values()),
        "shared_services":shared,
        "native_installed":False,"public_git_pushed":False,
        "provider_connected":False,"external_effects_authorized":False,
        "source_only":True,
    }


def main(argv:list[str]|None=None)->int:
    parser=argparse.ArgumentParser(description="GitHub source-only fifteen role qualification")
    options=parser.add_mutually_exclusive_group(required=True)
    options.add_argument("--all",action="store_true")
    options.add_argument("--role",choices=load_registry()["presets"])
    args=parser.parse_args(argv)
    root=Path(__file__).resolve().parents[1]
    roles=load_registry()["presets"] if args.all else [args.role]
    print(json.dumps(verify_all(root,roles),indent=2,sort_keys=True))
    return 0


if __name__=="__main__":
    try:
        raise SystemExit(main())
    except (OSError,ValueError,TypeError,KeyError,subprocess.TimeoutExpired) as exc:
        print(json.dumps({"status":"REFUSED","reason":str(exc),
                          "native_installed":False,"public_git_pushed":False}))
        raise SystemExit(2)

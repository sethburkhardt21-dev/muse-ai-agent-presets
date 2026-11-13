"""Executable zero-to-one GitHub source quickstart for all fifteen generic roles.

--all and --role without --to are disposable offline smoke tests. --to is
create-only and delegates entirely to the existing T07 standalone stager.
No Muse host, account, shell, browser, model or network connector is used.
"""
from __future__ import annotations

import argparse
from contextlib import nullcontext
import hashlib
import json
from pathlib import Path
import tempfile

from muse_presets.catalog import load_registry
from muse_presets.playbooks import load_playbook
from muse_presets.standalone_pack import (
    plan_standalone_pack, stage_standalone_pack, inspect_standalone_pack)
from muse_presets.portable_connectors import (
    plan_connector, run_offline_fixture, reconcile_fixture)

SCHEMA="r45/github-quickstart-v1"


def _run_role(role: str, destination: Path) -> dict:
    """Use only the already-tested source APIs, never fabricate a new installer."""
    plan=plan_standalone_pack(role)
    staged=stage_standalone_pack(
        destination,role,
        expected_profile_source_sha256=plan["profile_source_sha256"])
    checked=inspect_standalone_pack(destination)
    if (staged["status"]!="LOCAL_STANDALONE_STAGED"
        or checked["status"]!="LOCAL_STANDALONE_MATCH"
        or checked["native_installed"]
        or checked["profile_source_sha256"]!=plan["profile_source_sha256"]):
        raise ValueError("QUICKSTART_SOURCE_INSPECTION_FAILED")
    tools=load_playbook(role)["optional_tool_categories"]
    if not tools:
        raise ValueError("ROLE_TOOL_DECLARATION_MISSING")
    request_id="r45."+role.replace("-","_")
    proposal=plan_connector(role,tools[0],request_id=request_id)
    sample="Synthetic local observation for "+role
    rows=[{"id":"sample-1","sha256":hashlib.sha256(sample.encode("utf-8")).hexdigest(),
           "observation":sample}]
    report=run_offline_fixture(proposal,rows)
    reconciliation=reconcile_fixture(proposal,rows,report)
    if reconciliation["status"]!="CONSISTENT_OFFLINE_FIXTURE_ONLY":
        raise ValueError("QUICKSTART_FIXTURE_REVIEW_FAILED")
    return {
        "source_inspection":checked["status"],
        "profile_source_sha256":plan["profile_source_sha256"],
        "subchats":checked["subchat_count"],
        "disabled_skills":checked["skill_count"],
        "offline_example":reconciliation["status"],
        "role_capability_sample":tools[0],
        "real_model_invocation":False,
        "native_installed":False,
        "external_effects_authorized":False,
        "role_engine_verification":"SEPARATE_ROLE_SPECIFIC_DEMO_IF_AVAILABLE",
    }


def main(argv=None)->int:
    parser=argparse.ArgumentParser(
        description="Portable GitHub source quickstart; no native host required")
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--role",choices=load_registry()["presets"])
    group.add_argument("--all",action="store_true",help="smoke all fifteen in disposable temp paths")
    parser.add_argument("--to",type=Path,help="create-only output for one role; never overwrite")
    args=parser.parse_args(argv)
    if args.all and args.to is not None:
        parser.error("--to requires --role; --all is a disposable smoke test")
    roles=load_registry()["presets"] if args.all else [args.role]
    if args.to is None:
        with tempfile.TemporaryDirectory(prefix="muse-github-quickstart-") as tmp:
            root=Path(tmp)
            result={role:_run_role(role,root/role) for role in roles}
    else:
        result={args.role:_run_role(args.role,args.to)}
    report={
        "schema":SCHEMA,
        "mode":"CREATE_ONLY_SOURCE_PACKAGE" if args.to is not None else
               "DISPOSABLE_SOURCE_CHECK",
        "role_count":len(roles),"roles":result,
        "total_subchat_scopes":sum(r["subchats"] for r in result.values()),
        "total_disabled_skills":sum(r["disabled_skills"] for r in result.values()),
        "native_installed":False,"real_model_invocation":False,
        "provider_access":"NONE","external_effect_authorized":False,
        "can_publish":False,
        "source_release_grade":"OFFLINE_SOURCE_SMOKE_ONLY",
    }
    print(json.dumps(report,sort_keys=True,indent=2))
    return 0


if __name__=="__main__":
    try:
        raise SystemExit(main())
    except (OSError,ValueError,TypeError,KeyError) as exc:
        print(json.dumps({"status":"REFUSED","reason":str(exc),
                          "native_installed":False,"external_effect_authorized":False}))
        raise SystemExit(2)

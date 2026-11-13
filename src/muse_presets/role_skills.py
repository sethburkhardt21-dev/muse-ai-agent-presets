"""T06 role-method skill proposals: source-checked, disabled, never a native grant.

Uses the existing T04/T05 source contracts and the R32 custom-skill descriptor
shape; no executable runner, scheduler, host registry write or owner identity.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from typing import Any

from .catalog import DISPLAY, ROOT, SLUG
from .native_canary import _no_duplicate_json, _reject_constant
from .native_skill_binding import _regular_bytes, _unsafe_source_path, NAME, _registry
from .subchat_scopes import _source as _role_source, plan_subchat_scopes
from .system_profile import plan_system_profile

SOURCE_ROOT=ROOT
SCHEMA="r42/role-skills-v1"
MANIFEST="ROLE_SKILL_RECEIPT.json"
MAX_FILE_BYTES=131072
SHARED_SKILLS=("evidence_audit","safe_resume","research_verification",
               "consent_and_effects","quality_handoff")

LOCAL_MODULES={
    "coordinator": ("coordinator_dropin.py", "coordinator_review.py"),
    "software-engineer": ("engineer_dropin.py", "engineering_pack.py",
                           "provenance_vault.py", "iron_ledger_consumer.py"),
    "model-builder": ("model_builder_dropin.py", "model_eval.py"),
    "data-engineering-architect": ("specialist_engines.py",),
    "infrastructure-reliability-engineer": ("specialist_engines.py",),
    "automation-engineer": ("specialist_engines.py",),
    "product-interface-designer": ("specialist_engines.py",),
}
_HEX=re.compile(r"^[0-9a-f]{64}$")


def _json(value:Any)->bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False)+"\n").encode("utf-8")


def _parse(data:bytes)->Any:
    return json.loads(data.decode("utf-8"),object_pairs_hook=_no_duplicate_json,
                      parse_constant=_reject_constant)


def _sha(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()


def _source(role:str)->tuple[dict,dict,dict[str,bytes]]:
    preset,book,frozen=_role_source(role)
    for sid in SHARED_SKILLS:
        rel="skills/shared/"+sid.replace("_","-")+"/SKILL.md"
        frozen[rel]=_regular_bytes(SOURCE_ROOT/rel,MAX_FILE_BYTES)
    for filename in LOCAL_MODULES.get(role,()):
        rel="src/muse_presets/"+filename
        frozen[rel]=_regular_bytes(SOURCE_ROOT/rel,MAX_FILE_BYTES)
    return preset,book,frozen


def skill_id(role:str,method:str)->str:
    _,book,_=_source(role)
    if not isinstance(method,str) or method not in [row["id"] for row in book["methods"]]:
        raise ValueError("UNKNOWN_METHOD")
    name=role.replace("-","_")+"_"+method.replace("-","_")
    if NAME.fullmatch(name) is None:
        raise ValueError("INVALID_ROLE_SKILL_ID")
    return name


def _build(role:str,display_name:str|None)->tuple[dict[str,bytes],dict,dict[str,bytes]]:
    preset,book,frozen=_source(role)
    name=role.replace("-"," ").title() if display_name is None else display_name
    if not isinstance(name,str) or DISPLAY.fullmatch(name) is None:
        raise ValueError("INVALID_ROLE_SKILL_DISPLAY_NAME")
    profile=plan_system_profile(role,display_name=name)
    scoped=plan_subchat_scopes(role,display_name=name)
    methods=[row["id"] for row in book["methods"]]
    if (scoped["methods"]!=methods
        or scoped["profile_source_sha256"]!=profile["source_sha256"]):
        raise ValueError("PROFILE_SUBCHAT_SOURCE_MISMATCH")
    files={}
    mapping={}
    names=[]
    for method in book["methods"]:
        mid=method["id"]
        sid=skill_id(role,mid)
        names.append(sid)
        scope=f"custom-skills/{sid}/"
        description=method["trigger"]
        if ("\n" in description or "\r" in description or "\x00" in description
                or len(description)>400):
            raise ValueError("INVALID_SKILL_TRIGGER")
        yaml=(f"name: {sid}\n"
              f"title: {name} - {mid.replace('-', ' ').title()}\n"
              f"description: {description}\n"
              "include_in_prompt: false\n")
        steps="\n".join(f"{i}. {v}" for i,v in enumerate(method["steps"],1))
        evidence="\n".join(f"- {v}" for v in method["evidence"])
        doc=(f"---\nname: {sid}\ndescription: {description}\n---\n\n"
             f"# {name}: {mid}\n\n"
             f"Role: {role}. This skill is not installed. It is a source-only, "
             "owner-unbound procedure; no host identity, tool call or consent is implied.\n\n"
             f"## Trigger\n\n{description}\n\n"
             f"## Steps\n\n{steps}\n\n"
             f"## Evidence to return\n\n{evidence}\n\n"
             f"## Stop condition\n\n{method['stop_rule']}\n\n"
             f"## Handoff\n\nPropose {method['handoff_to']} for separate owner-approved "
             "delivery only. Do not send automatically.\n\n"
             "## Runtime\n\nNo executable is included. Host registration, "
             "model-selected invocation, recipient readback and permissions "
             "must be proven independently. Disabled by default.\n")
        files[scope+"SKILL.md"]=doc.encode("utf-8")
        files[scope+"skill.yaml"]=yaml.encode("utf-8")
        mapping[mid]=[{
            "skill":sid,"enabled":False,"native_registered":False,
            "provider_skill_id":None,"owner_id":None,
            "method_context":f"subchats/{mid}/CONTEXT.md",
        }]
    if len(names)!=3 or len(set(names))!=3:
        raise ValueError("INVALID_SKILL_METHOD_SET")
    for sid in SHARED_SKILLS:
        original="skills/shared/"+sid.replace("_","-")+"/SKILL.md"
        source=frozen[original].decode("utf-8")
        expected="name: "+sid.replace("_","-")
        if not source.startswith("---\n"+expected+"\n"):
            raise ValueError("INVALID_SHARED_SKILL_SOURCE")
        body=source.replace(expected,"name: "+sid,1)
        files[f"custom-skills/{sid}/SKILL.md"]=body.encode("utf-8")
        desc=next(line[len("description: "):] for line in source.splitlines()
                  if line.startswith("description: "))
        if "\n" in desc or len(desc)>400:
            raise ValueError("INVALID_SHARED_SKILL_DESCRIPTION")
        files[f"custom-skills/{sid}/skill.yaml"]=(f"name: {sid}\n"
             f"title: Shared - {sid.replace(chr(95),chr(32)).title()}\n"
             f"description: {desc}\ninclude_in_prompt: false\n").encode("utf-8")
    registry="version: 1\nentries:\n"+"".join(
        f"  {sid}:\n    status: disabled\n" for sid in sorted([*names,*SHARED_SKILLS]))
    files["config/skills.yaml"]=registry.encode("utf-8")
    files["config/subchat-skills.json"]=_json({
        "schema":SCHEMA,"role":role,"mapping":mapping,
        "profile_source_sha256":profile["source_sha256"],
        "native_loaded":False,"recipient_verified":False,
        "external_effect_authorized":False,
    })
    links=[]
    for filename in LOCAL_MODULES.get(role,()):
        relative="src/muse_presets/"+filename
        links.append({"path":relative,"sha256":_sha(frozen[relative]),
                      "disposition":"LOCAL_SOURCE_REFERENCE_NOT_REGISTERED"})
    files["config/local-code-links.json"]=_json({
        "schema":"r42/local-source-code-links-v1","role":role,
        "source_code_linked":bool(links),"source_files":links,
        "bundled_executables":False,"native_callable":False,
    })
    files["config/host-binding.json"]=_json({
        "schema":SCHEMA,"role":role,
        "host_kind":"RECEIVING_OWNER_DISCOVERS_PERSONAL_HATCH",
        "owner_id":None,"agent_id":None,"session_id":None,
        "native_registered":False,"native_loaded":False,
        "model_selected_skill":False,"recipient_readback":False,
        "external_effect_authorized":False,
        "apply":"NOT_IMPLEMENTED_SOURCE_PROPOSAL_ONLY",
        "registry_policy":"DISABLED_UNTIL_SUPPORTED_PROVIDER_OWNER_GRANT",
    })
    for path,data in files.items():
        if len(data)==0 or len(data)>MAX_FILE_BYTES or b"\x00" in data:
            raise ValueError("INVALID_SKILL_SOURCE_CONTENT")
    source_pins={p:_sha(data) for p,data in frozen.items()}
    receipt={
        "schema":SCHEMA,"role":role,"display_name":name,
        "source_pins":source_pins,
        "profile_source_sha256":profile["source_sha256"],
        "method_ids":methods,"skill_ids":names,
        "shared_skill_ids":list(SHARED_SKILLS),
        "files":{p:_sha(data) for p,data in files.items()},
        "grade":"LOCAL_SKILL_DESCRIPTOR_ONLY",
        "provider_issued_skill_ids":False,
        "native_registered":False,"native_loaded":False,
        "model_selected_invocation":False,
        "recipient_readback":False,
        "external_effect_authorized":False,"can_apply":False,
    }
    return files,receipt,frozen


def plan_role_skills(role:str,*,display_name:str|None=None)->dict:
    files,receipt,_=_build(role,display_name)
    return {"status":"SOURCE_PLAN_ONLY","role":role,
            "profile_source_sha256":receipt["profile_source_sha256"],
            "skill_ids":receipt["skill_ids"],
            "shared_skill_ids":receipt["shared_skill_ids"],"file_count":len(files),
            "native_registered":False,"can_apply":False}


def _new_dest(dest:Path)->None:
    if _unsafe_source_path(dest):
        raise ValueError("UNSAFE_SKILL_DESTINATION")
    if dest.exists() or dest.is_symlink():
        raise FileExistsError("SKILL_DESTINATION_EXISTS")
    if not dest.parent.is_dir():
        raise FileNotFoundError("SKILL_PARENT_REQUIRED")


def _write_new(path:Path,data:bytes)->None:
    with path.open("xb") as stream:
        stream.write(data)


def stage_role_skills(destination:Path,role:str,*,display_name:str|None=None,
                      expected_profile_source_sha256:str|None=None)->dict:
    """Create-only, fail-closed source staging; no host registration."""
    dest=Path(destination)
    _new_dest(dest)
    files,receipt,frozen=_build(role,display_name)
    if expected_profile_source_sha256 is not None and (
            type(expected_profile_source_sha256) is not str
            or not _HEX.fullmatch(expected_profile_source_sha256)
            or expected_profile_source_sha256!=receipt["profile_source_sha256"]):
        raise ValueError("SKILL_SOURCE_PIN_MISMATCH")
    dest.mkdir(exist_ok=False)
    _write_new(dest/"STAGING_INCOMPLETE",b"LOCAL_STAGING_INCOMPLETE_NO_AUTO_RETRY\n")
    (dest/"custom-skills").mkdir()
    (dest/"config").mkdir()
    for relative in sorted(files):
        path=dest/relative
        path.parent.mkdir(parents=True,exist_ok=True)
        _write_new(path,files[relative])
    if _source(role)[2]!=frozen or _build(role,display_name)[1]!=receipt:
        raise ValueError("SKILL_SOURCE_CHANGED_DURING_STAGE")
    _write_new(dest/MANIFEST,_json(receipt))
    (dest/"STAGING_INCOMPLETE").unlink()
    return {"status":"LOCAL_ROLE_SKILLS_STAGED","role":role,
            "skill_count":len(receipt["skill_ids"])+len(receipt["shared_skill_ids"]),
            "native_registered":False,"external_effect_authorized":False,
            "source_sha256":receipt["profile_source_sha256"]}


def _closed_tree(dest:Path,expected:set[str],names:list[str])->bool:
    dirs={"custom-skills","config"}|{"custom-skills/"+name for name in names}
    actual_dirs,actual_files=set(),set()
    try:
        entries=list(dest.rglob("*"))
    except OSError:
        return False
    if len(entries)>65:
        return False
    for entry in entries:
        if _unsafe_source_path(entry):
            return False
        relative=entry.relative_to(dest).as_posix()
        if entry.is_dir():actual_dirs.add(relative)
        elif entry.is_file():actual_files.add(relative)
        else:return False
    return dirs==actual_dirs and actual_files==expected|{MANIFEST}


def inspect_role_skills(destination:Path)->dict:
    dest=Path(destination)
    failure={"status":"REVIEW_REQUIRED","native_registered":False,
             "external_effect_authorized":False,"can_apply":False}
    try:
        if _unsafe_source_path(dest) or not dest.is_dir():
            return failure
        marker=dest/"STAGING_INCOMPLETE"
        if marker.exists() or marker.is_symlink():
            return {**failure,"status":"INCOMPLETE_STAGE"}
        raw=_regular_bytes(dest/MANIFEST,MAX_FILE_BYTES)
        claim=_parse(raw)
        if not isinstance(claim,dict) or claim.get("schema")!=SCHEMA:
            return failure
        files,expected,_=_build(claim.get("role"),claim.get("display_name"))
        # A role/method switch is a policy tamper, not merely source drift.
        if claim.get("method_ids")!=expected["method_ids"]:
            return failure
        if claim.get("source_pins")!=expected["source_pins"] or (
                claim.get("profile_source_sha256")!=expected["profile_source_sha256"]):
            return {**failure,"status":"SOURCE_DRIFT"}
        if raw!=_json(expected) or not _closed_tree(dest,set(files),expected["skill_ids"]+expected["shared_skill_ids"]):
            return failure
        for relative,data in files.items():
            if _regular_bytes(dest/relative,MAX_FILE_BYTES)!=data:
                return failure
        registered,registry_sha=_registry(dest/"config/skills.yaml")
        if registered!={name:"disabled" for name in expected["skill_ids"]+expected["shared_skill_ids"]}:
            return failure
        return {**failure,"status":"LOCAL_ROLE_SKILLS_MATCH",
                "role":expected["role"],"skill_ids":expected["skill_ids"],
                "shared_skill_ids":expected["shared_skill_ids"],
                "registry_sha256":registry_sha,
                "profile_source_sha256":expected["profile_source_sha256"]}
    except (OSError,ValueError,TypeError,KeyError):
        return failure


def preview_role_skills(candidate:Path,target:Path)->dict:
    """Never write or merge host data. Show exact per-file collision policy."""
    candidate,target=Path(candidate),Path(target)
    if inspect_role_skills(candidate)["status"]!="LOCAL_ROLE_SKILLS_MATCH":
        raise ValueError("UNTRUSTED_SKILL_CANDIDATE")
    if _unsafe_source_path(target) or (target.exists() and not target.is_dir()):
        raise ValueError("UNSAFE_SKILL_TARGET")
    changes=[]
    for path in sorted(candidate.rglob("*"),key=lambda p:p.relative_to(candidate).as_posix()):
        if not path.is_file() or path.name==MANIFEST:continue
        rel=path.relative_to(candidate).as_posix()
        dest=target/rel
        if _unsafe_source_path(dest):
            raise ValueError("UNSAFE_SKILL_TARGET_MEMBER")
        if dest.exists():
            current=_regular_bytes(dest,MAX_FILE_BYTES)
            action="UNCHANGED" if current==_regular_bytes(path,MAX_FILE_BYTES) else "REVIEW_CONFLICT"
        else:action="CREATE"
        changes.append({"path":rel,"action":action})
    return {"status":"PREVIEW_ONLY","files":changes,"can_apply":False,
            "native_registered":False,"external_effect_authorized":False,
            "unlisted_owner_files":"UNTOUCHED"}

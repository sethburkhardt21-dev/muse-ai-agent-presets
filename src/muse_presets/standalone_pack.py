"""T07 standalone generic role package lifecycle; source only, never native install.

Composes canonical T04 system profiles, T05 scoped subchats and T06 disabled
role skills. No owner credentials, provider session, registry writes or live
host effects. Uninstall/rollback and upgrade are review-only proposals.
"""
from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path
from typing import Any

from .native_canary import _no_duplicate_json, _reject_constant
from .native_skill_binding import _regular_bytes, _unsafe_source_path
from . import system_profile, subchat_scopes, role_skills

SCHEMA="r43/standalone-source-package-v1"
MANIFEST="INSTALL_RECEIPT.json"
COMPONENTS={
    "system-profile": (system_profile,system_profile.MANIFEST,
                       "LOCAL_SYSTEM_PROFILE_MATCH"),
    "subchat-scopes": (subchat_scopes,subchat_scopes.MANIFEST,
                       "LOCAL_SUBCHATS_MATCH"),
    "role-skills": (role_skills,role_skills.MANIFEST,
                    "LOCAL_ROLE_SKILLS_MATCH"),
}
MAX_FILE_BYTES=131072
MAX_ARCHIVE_BYTES=16*1024*1024


def _sha(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()


def _json(value:Any)->bytes:
    return (json.dumps(value,indent=2,sort_keys=True,ensure_ascii=False)+"\n").encode("utf-8")


def _parse(raw:bytes)->Any:
    return json.loads(raw.decode("utf-8"),object_pairs_hook=_no_duplicate_json,
                      parse_constant=_reject_constant)


def _current_plan(role:str,display_name:str|None=None)->dict:
    p=system_profile.plan_system_profile(role,display_name=display_name)
    r=subchat_scopes.plan_subchat_scopes(role,display_name=display_name)
    s=role_skills.plan_role_skills(role,display_name=display_name)
    if (p["source_sha256"]!=r["profile_source_sha256"]
            or p["source_sha256"]!=s["profile_source_sha256"]
            or len(r["methods"])!=3 or len(s["skill_ids"])!=3
            or len(s["shared_skill_ids"])!=5
            or len(set(s["shared_skill_ids"]))!=5):
        raise ValueError("COMPONENT_SOURCE_OR_ROLE_MISMATCH")
    return {
        "role":role,
        "display_name":role.replace("-"," ").title() if display_name is None else display_name,
        "profile_source_sha256":p["source_sha256"],
        "method_ids":r["methods"],"skill_ids":s["skill_ids"],
        "shared_skill_ids":s["shared_skill_ids"],
    }


def _expected_receipt(role:str,display_name:str|None)->dict:
    plan=_current_plan(role,display_name)
    records={}
    for part,(module,manifest,_) in COMPONENTS.items():
        # This is the actual canonical source-backed component manifest, not
        # a hash supplied by the locally editable package.
        record=module._build(role,display_name)[1]
        records[part]={
            "manifest":manifest,
            "receipt_sha256":_sha(module._json(record)),
            "profile_source_sha256":record["profile_source_sha256"] if
                part!="system-profile" else record["source_sha256"],
        }
        if records[part]["profile_source_sha256"]!=plan["profile_source_sha256"]:
            raise ValueError("STANDALONE_SOURCE_PIN_DISAGREEMENT")
    return {
        "schema":SCHEMA,"role":role,"display_name":plan["display_name"],
        "profile_source_sha256":plan["profile_source_sha256"],
        "method_ids":plan["method_ids"],"skill_ids":plan["skill_ids"],
        "shared_skill_ids":plan["shared_skill_ids"],
        "components":records,
        "grade":"LOCAL_SOURCE_ONLY",
        "native_installed":False,"provider_owner_id":None,
        "registered_skills":False,"model_invocation_verified":False,
        "recipient_readback_verified":False,"external_effect_authorized":False,
        "can_apply":False,"can_delete":False,
    }


def plan_standalone_pack(role:str,*,display_name:str|None=None)->dict:
    record=_expected_receipt(role,display_name)
    return {"status":"SOURCE_PLAN_ONLY","role":role,
            "profile_source_sha256":record["profile_source_sha256"],
            "components":sorted(COMPONENTS),"native_installed":False,
            "can_apply":False,"can_delete":False}


def _require_new(path:Path)->None:
    if _unsafe_source_path(path):
        raise ValueError("UNSAFE_STANDALONE_DESTINATION")
    if path.exists() or path.is_symlink():
        raise FileExistsError("STANDALONE_DESTINATION_OCCUPIED")
    if not path.parent.is_dir():
        raise FileNotFoundError("STANDALONE_PARENT_REQUIRED")


def _write_new(path:Path,data:bytes)->None:
    with path.open("xb") as file:
        file.write(data)


def stage_standalone_pack(destination:Path,role:str,*,display_name:str|None=None,
                          expected_profile_source_sha256:str|None=None)->dict:
    """Create-only. Incomplete failures remain as fenced owned draft directories."""
    dest=Path(destination)
    _require_new(dest)
    admitted=_current_plan(role,display_name)
    before=_expected_receipt(role,display_name)
    if expected_profile_source_sha256 is not None and (
            type(expected_profile_source_sha256) is not str
            or expected_profile_source_sha256!=admitted["profile_source_sha256"]):
        raise ValueError("STANDALONE_SOURCE_PIN_MISMATCH")
    dest.mkdir(exist_ok=False)
    marker=dest/"STAGING_INCOMPLETE"
    _write_new(marker,b"INCOMPLETE_STANDALONE_SOURCE_STAGE_NO_AUTO_RETRY\n")
    system_profile.stage_system_profile(
        dest/"system-profile",role,display_name=display_name,
        expected_source_sha256=admitted["profile_source_sha256"])
    subchat_scopes.stage_subchat_scopes(
        dest/"subchat-scopes",role,display_name=display_name,
        expected_profile_source_sha256=admitted["profile_source_sha256"])
    role_skills.stage_role_skills(
        dest/"role-skills",role,display_name=display_name,
        expected_profile_source_sha256=admitted["profile_source_sha256"])
    try:
        later_plan=_current_plan(role,display_name)
        later_receipt=_expected_receipt(role,display_name)
    except (ValueError, OSError) as exc:
        raise ValueError("STANDALONE_SOURCE_CHANGED_DURING_STAGE") from exc
    if later_plan!=admitted or later_receipt!=before:
        raise ValueError("STANDALONE_SOURCE_CHANGED_DURING_STAGE")
    for part,(module,manifest,matched) in COMPONENTS.items():
        if module.__dict__["inspect_"+{
            "system-profile":"system_profile","subchat-scopes":"subchat_scopes",
            "role-skills":"role_skills"
        }[part]](dest/part)["status"]!=matched:
            raise ValueError("STANDALONE_COMPONENT_NOT_PRISTINE")
        observed=_sha(_regular_bytes(dest/part/manifest,MAX_FILE_BYTES))
        if observed!=before["components"][part]["receipt_sha256"]:
            raise ValueError("STANDALONE_COMPONENT_MANIFEST_MISMATCH")
    _write_new(dest/MANIFEST,_json(before))
    marker.unlink()
    return {"status":"LOCAL_STANDALONE_STAGED","role":role,
            "component_count":3,"method_count":3,"skill_count":8,
            "profile_source_sha256":admitted["profile_source_sha256"],
            "native_installed":False,"external_effect_authorized":False}


def inspect_standalone_pack(destination:Path)->dict:
    """Strict source-based inspection, never treat mutable receipt as authority."""
    dest=Path(destination)
    base={"status":"REVIEW_REQUIRED","native_installed":False,
          "can_apply":False,"can_delete":False,"external_effect_authorized":False}
    try:
        if _unsafe_source_path(dest) or not dest.is_dir():
            return base
        marker=dest/"STAGING_INCOMPLETE"
        if marker.exists() or marker.is_symlink():
            return {**base,"status":"INCOMPLETE_STAGE"}
        if {p.name for p in dest.iterdir()} != set(COMPONENTS)|{MANIFEST}:
            return base
        raw=_regular_bytes(dest/MANIFEST,MAX_FILE_BYTES)
        claimed=_parse(raw)
        if not isinstance(claimed,dict) or claimed.get("schema")!=SCHEMA:
            return base
        role=claimed.get("role")
        name=claimed.get("display_name")
        expected=_expected_receipt(role,name)
        if (claimed.get("method_ids")!=expected["method_ids"]
                or claimed.get("skill_ids")!=expected["skill_ids"]
                or claimed.get("shared_skill_ids")!=expected["shared_skill_ids"]
                or set(claimed.get("components",{}))!=set(COMPONENTS)):
            return base
        statuses={}
        for part,(module,manifest,matched) in COMPONENTS.items():
            if _unsafe_source_path(dest/part) or not (dest/part).is_dir():
                return base
            func={"system-profile":system_profile.inspect_system_profile,
                  "subchat-scopes":subchat_scopes.inspect_subchat_scopes,
                  "role-skills":role_skills.inspect_role_skills}[part]
            result=func(dest/part)
            statuses[part]=result["status"]
            if result["status"] not in (matched,"OWNER_CUSTOMIZED","SOURCE_DRIFT"):
                return base
            if result["status"]=="OWNER_CUSTOMIZED" and part=="role-skills":
                return base
            if _sha(_regular_bytes(dest/part/manifest,MAX_FILE_BYTES))!=expected["components"][part]["receipt_sha256"]:
                return base
        if "SOURCE_DRIFT" in statuses.values():
            return {**base,"status":"SOURCE_DRIFT"}
        if raw!=_json(expected):
            return base
        customized=any(s=="OWNER_CUSTOMIZED" for s in statuses.values())
        return {**base,"status":"OWNER_CUSTOMIZED" if customized else "LOCAL_STANDALONE_MATCH",
                "role":role,"profile_source_sha256":expected["profile_source_sha256"],
                "subchat_count":len(expected["method_ids"]),
                "skill_count":len(expected["skill_ids"])+len(expected["shared_skill_ids"]),
                "owner_customizations_present":customized,
                "components":statuses}
    except (OSError,ValueError,TypeError,KeyError,AttributeError):
        return base


def _owner_edit(relative:str)->bool:
    parts=relative.split("/")
    if len(parts)==3 and parts[:2]==["system-profile","profile"]:
        return parts[2] in system_profile.OWNER_FILES
    return (len(parts)==4 and parts[:2]==["subchat-scopes","subchats"]
            and parts[3] in subchat_scopes.OWNER_FILES)


def preview_standalone_upgrade(candidate:Path,target:Path)->dict:
    """Read-only change classification; never modify receiving-owner state."""
    candidate,target=Path(candidate),Path(target)
    if inspect_standalone_pack(candidate)["status"]!="LOCAL_STANDALONE_MATCH":
        raise ValueError("UNTRUSTED_STANDALONE_CANDIDATE")
    if _unsafe_source_path(target) or (target.exists() and not target.is_dir()):
        raise ValueError("UNSAFE_UPGRADE_TARGET")
    rows=[]
    for path in sorted(candidate.rglob("*"),key=lambda p:p.relative_to(candidate).as_posix()):
        if not path.is_file():
            continue
        relative=path.relative_to(candidate).as_posix()
        new_dest=target/relative
        if _unsafe_source_path(new_dest):
            raise ValueError("UNSAFE_UPGRADE_TARGET_MEMBER")
        if new_dest.exists():
            current=_regular_bytes(new_dest,MAX_FILE_BYTES)
            incoming=_regular_bytes(path,MAX_FILE_BYTES)
            action="UNCHANGED" if current==incoming else (
                "PRESERVE_OWNER_EDIT" if _owner_edit(relative) else "REVIEW_CONFLICT")
        else:
            action="CREATE"
        rows.append({"path":relative,"action":action})
    return {"status":"UPGRADE_PREVIEW_ONLY","files":rows,
            "can_apply":False,"native_installed":False,"external_effect_authorized":False,
            "unknown_owner_files":"UNTOUCHED"}


def export_clean_standalone_pack(source:Path,destination:Path)->dict:
    """Export pristine original source only, no customized owner memory."""
    source,destination=Path(source),Path(destination)
    if inspect_standalone_pack(source)["status"]!="LOCAL_STANDALONE_MATCH":
        raise ValueError("UNTRUSTED_OR_CUSTOMIZED_EXPORT")
    _require_new(destination)
    files=sorted((p for p in source.rglob("*") if p.is_file()),
                 key=lambda p:p.relative_to(source).as_posix())
    if len(files)>128 or sum(p.stat().st_size for p in files)>MAX_ARCHIVE_BYTES:
        raise ValueError("STANDALONE_EXPORT_TOO_LARGE")
    with zipfile.ZipFile(destination,mode="x") as z:
        for f in files:
            relative=f.relative_to(source).as_posix()
            if relative.startswith("/") or ".." in Path(relative).parts:
                raise ValueError("UNSAFE_STANDALONE_EXPORT_PATH")
            info=zipfile.ZipInfo(relative,date_time=(2026,11,8,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED
            info.create_system=3
            info.external_attr=0o100644<<16
            z.writestr(info,_regular_bytes(f,MAX_FILE_BYTES))
    with zipfile.ZipFile(destination,"r") as z:
        names=z.namelist()
        if len(names)!=len(set(names)) or z.testzip() is not None:
            raise ValueError("INVALID_STANDALONE_EXPORT")
    return {"status":"LOCAL_EXPORT_CREATED","sha256":_sha(destination.read_bytes()),
            "bytes":destination.stat().st_size,"file_count":len(files),
            "native_installed":False,"external_effect_authorized":False,
            "owner_state_exported":False}


def plan_uninstall_standalone(destination:Path)->dict:
    """Purely advisory removal plan; original host owner grant is unavailable."""
    destination=Path(destination)
    result=inspect_standalone_pack(destination)
    if result["status"] not in ("LOCAL_STANDALONE_MATCH","OWNER_CUSTOMIZED"):
        raise ValueError("UNTRUSTED_UNINSTALL_SOURCE")
    return {"status":"UNINSTALL_PREVIEW_ONLY","role":result["role"],
            "grade":"LOCAL_SOURCE_ONLY","can_delete":False,
            "requires_owner_confirmation":True,
            "owner_customizations_present":result["owner_customizations_present"],
            "requires_private_owner_export":result["owner_customizations_present"],
            "external_effect_authorized":False,
            "next":"SAVE_OWNER_DATA_AND_USE_AUTHENTICATED_SUPPORTED_HOST_UNINSTALL"}

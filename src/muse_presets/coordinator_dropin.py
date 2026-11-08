"""Source-only portable Coordinator role pack with offline graph/evidence review.

Never installs into Muse, starts an agent, creates a scheduler, assumes Omnium
placement authority, or changes an owner's existing system files.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from .catalog import DOCUMENTS, load_registry, render_preset
from .lifecycle import inspect_render
from .native_canary import _admitted_destination, _no_duplicate_json, _reject_constant, _serialized
from .native_skill_binding import _unsafe_source_path

SCHEMA = "r33/coordinator-dropin-v1"
SKILLS = {
    "coordinator_workgraph": {
        "description": "Offline bounded dependency graph verification without dispatch",
        "method": "review",
    },
    "coordinator_evidence": {
        "description": "Offline actor and reviewer assertion correlation; never native proof",
        "method": "evidence",
    },
}
ROOMS = {
    "intake": {
        "purpose": "Clarify observable request scope, work inputs, dependencies and budget before any delegation",
        "actions": "Check exact source and owner-approved scope; derive a candidate graph for separate user review only",
        "stop": "Stop when real owner permission or original target is unknown; do not mint host grants",
        "next": "dependency-review",
    },
    "dependency-review": {
        "purpose": "Review an externally supplied task graph for cycles, missing prerequisites and review separation",
        "actions": "Call the bounded local workgraph review with a supplied synthetic or approved graph; do not schedule",
        "stop": "External effects, invalid source or budget overrun stay held; no fallback dispatcher",
        "next": "acceptance-review",
    },
    "acceptance-review": {
        "purpose": "Correlate completion assertions and identify missing real provider and recipient evidence",
        "actions": "Check exact source pins, actor and distinct reviewer claims, preserve UNKNOWN as HOLD",
        "stop": "A self-authored PASS cannot imply independent verification, original recipient delivery or deployment",
        "next": "intake",
    },
}
EXTRA_FILES = {
    "CONNECTORS.md": "# Optional connectors\n\nNo provider account is connected by this package. Discover schemas and verify owner grants in the actual receiving host before any effect.\n",
    "BROWSER.md": "# Browser constraints\n\nNever navigate or act from the offline reviewer. Browser and CUA drivers require separate explicit task and host grants.\n",
    "VOICE.md": "# Voice constraints\n\nNo voice identity or personal audio assets are bundled. Voice is optional and disabled.\n",
}
BINDING = {
    "schema": "r33/coordinator-host-binding-v1",
    "owner_user_id": None,
    "native_session_id": None,
    "native_agent_id": None,
    "registered": False,
    "installed": False,
    "native_authenticated": False,
    "recipient_readback_verified": False,
    "external_effect_authorized": False,
}
HOOKS = {
    "schema": "r33/coordinator-hooks-v1",
    "enabled": False,
    "installed": False,
    "managed_schedule": False,
    "event_handlers": [],
}
README = """# Coordinator — independent neutral native-format source pack

This package has a REAL local source-only graph/assertion reviewer.
It is not a scheduler, mission compiler, Omnium executor, signed grant,
host session or agent communication service.

Two custom skills exist as **disabled metadata** and have a runnable offline
script. Submit bounded synthetic JSON through stdin with --operation review
or --operation evidence; --operation demo exercises a complete toy graph.
No model/host, browser, remote computer, user file or recipient is invoked.

Each of the three subchat folders has distinct role, context, tools and memory
instructions, but every native chat ID is null and not installed.
The owner profile remains an inert draft and no existing Muse files are changed.
Use scripts/doctor.py for self-check continuity, and source-repository
coordinator-dropin-inspect for source-pinned inspection.

Provider-level discovery, native call, recipient readback and wrong-owner
refusal must be proven on a separate receiving owner account. Nothing here
counts as WIRED, USED, USEFUL or public release.
"""

RUNNER = r'''#!/usr/bin/env python3
"""Offline Coordinator reviewer: never creates missions, schedules or grants."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys


def refuse(reason):
    print(json.dumps({
        "status":"REVIEW_REQUIRED","reason":reason,"native_tool_invoked":False,
        "provider_authenticated":False,"external_effect_authorized":False,
        "recipient_readback_verified":False,
    },sort_keys=True))
    return 2


def unique_pairs(pairs):
    out={}
    for key,value in pairs:
        if key in out:
            raise ValueError("DUPLICATE_JSON_KEY")
        out[key]=value
    return out


def demo_graph():
    return {
        "schema":"r33/coordinator-workgraph-v1","workspace":"fictional-example",
        "budget_units":4,
        "tasks":[
            {"id":"diagnose-1","role":"software-engineer",
             "reviewer":"adversarial-verifier","requires":[],
             "estimated_units":2,"effect_class":"none",
             "source_sha256":"a"*64,"acceptance":["Exact local reproduction recorded"]},
            {"id":"review-2","role":"claims-adjudicator",
             "reviewer":"research-evaluator","requires":["diagnose-1"],
             "estimated_units":2,"effect_class":"external",
             "source_sha256":"b"*64,"acceptance":["Recipient receipt must be externally checked"]},
        ]}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--operation",required=True,
                        choices=("demo","review","evidence"))
    args=parser.parse_args(argv)
    root=Path(__file__).resolve().parents[2]
    engine=root/"runtime"/"coordinator_review.py"
    catalog=root/"runtime"/"coordinator_roles.json"
    if (not engine.is_file() or engine.is_symlink()
        or not catalog.is_file() or catalog.is_symlink()):
        return refuse("MISSING_OR_UNTRUSTED_RUNTIME")
    sys.path.insert(0,str(root/"runtime"))
    try:
        from coordinator_review import review_workgraph, review_assertions
        if args.operation=="demo":
            report=review_workgraph(demo_graph())
            if (report["status"]!="LOCAL_PLAN_REVIEW_ONLY" or
                report["execution_order"]!=["diagnose-1","review-2"] or
                report["held_effect_tasks"]!=["review-2"]):
                return refuse("DEMO_REVIEW_REFUSED")
            print(json.dumps({
                "status":"LOCAL_COORDINATOR_DEMO_PASSED",
                "execution_order":report["execution_order"],
                "workgraph_sha256":report["workgraph_sha256"],
                "held_effect_tasks":report["held_effect_tasks"],
                "native_tool_invoked":False,
                "external_effect_authorized":False,
                "recipient_readback_verified":False,
            },sort_keys=True))
            return 0
        raw=sys.stdin.buffer.read(65537)
        if len(raw)>65536 or not raw:
            return refuse("INPUT_SIZE_INVALID")
        data=json.loads(raw,object_pairs_hook=unique_pairs,
                        parse_constant=lambda value: (_ for _ in ()).throw(
                            ValueError("NONSTANDARD_CONSTANT")))
        if args.operation=="review":
            report=review_workgraph(data)
        else:
            if type(data) is not dict or set(data)!={"graph","assertions"}:
                return refuse("ASSERTION_WRAPPER_INVALID")
            report=review_assertions(data["graph"],data["assertions"])
        report={**report,"native_tool_invoked":False,
                "external_effect_authorized":False}
        print(json.dumps(report,sort_keys=True))
        return 0 if report["status"] in ("LOCAL_PLAN_REVIEW_ONLY",
                                        "UNATTESTED_ASSERTIONS_ONLY") else 2
    except (OSError,ValueError,TypeError,KeyError,ImportError,json.JSONDecodeError):
        return refuse("UNTRUSTED_INPUT_OR_RUNTIME")


if __name__=="__main__":
    raise SystemExit(main())
'''

DOCTOR = r'''#!/usr/bin/env python3
"""Self-hash inventory only. NOT a publisher signature or Muse authentication."""
import hashlib
import json
import os
from pathlib import Path


def reject():
    print(json.dumps({"status":"REVIEW_REQUIRED","native_authenticated":False,
                      "external_effect_authorized":False},sort_keys=True))
    return 2


def unique(pairs):
    out={}
    for key,value in pairs:
        if key in out:
            raise ValueError("DUPLICATE_KEY")
        out[key]=value
    return out


def main():
    root=Path(__file__).resolve().parents[1]
    if (root/"STAGING_INCOMPLETE").exists():
        return reject()
    receipt=root/"receipts"/"COORDINATOR_RECEIPT.json"
    try:
        if receipt.is_symlink() or not receipt.is_file() or receipt.stat().st_size>30000:
            return reject()
        record=json.loads(receipt.read_bytes(),object_pairs_hook=unique,
                          parse_constant=lambda _: (_ for _ in ()).throw(
                              ValueError("NONSTANDARD_CONSTANT")))
        required={"schema","role_id","files_sha256","directories",
                  "native_installed","native_authenticated",
                  "external_effect_authorized","evidence_grade"}
        if (type(record) is not dict or set(record)!=required or
            record["schema"]!="r33/coordinator-dropin-v1" or
            record["role_id"]!="coordinator" or
            any(record[key] is not False for key in
                ("native_installed","native_authenticated","external_effect_authorized")) or
            record["evidence_grade"]!="LOCAL_SOURCE_ONLY"):
            return reject()
        expected=record["files_sha256"]
        if type(expected) is not dict or len(expected)>150:
            return reject()
        seen=set()
        dirs={"."}
        for parent,subdirs,files in os.walk(root,followlinks=False):
            folder=Path(parent)
            for name in subdirs:
                path=folder/name
                if path.is_symlink() or (
                    hasattr(path,"is_junction") and path.is_junction()
                ):
                    return reject()
                dirs.add(path.relative_to(root).as_posix())
            for name in files:
                path=folder/name
                if path.is_symlink() or not path.is_file():
                    return reject()
                seen.add(path.relative_to(root).as_posix())
        if (seen != set(expected)|{"receipts/COORDINATOR_RECEIPT.json"} or
            dirs != set(record["directories"])):
            return reject()
        for name,pin in expected.items():
            if (type(name) is not str or type(pin) is not str or
                len(pin)!=64 or any(c not in "0123456789abcdef" for c in pin) or
                Path(name).is_absolute() or ".." in Path(name).parts):
                return reject()
            file=root/name
            if (file.is_symlink() or not file.is_file() or
                file.stat().st_size>3_000_000 or
                hashlib.sha256(file.read_bytes()).hexdigest()!=pin):
                return reject()
    except (OSError,ValueError,KeyError,TypeError):
        return reject()
    print(json.dumps({"status":"LOCAL_SELF_HASH_MATCH",
                      "native_authenticated":False,
                      "external_effect_authorized":False,
                      "publisher_authenticated":False},sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
'''


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _source_runtime() -> dict[str, bytes]:
    path=Path(__file__).with_name("coordinator_review.py")
    if path.is_symlink() or not path.is_file() or path.stat().st_size>250000:
        raise ValueError("SOURCE_NOT_ADMITTED")
    raw=path.read_bytes()
    names=load_registry()["presets"]
    if (type(names) is not list or len(names)!=11 or len(set(names))!=11 or
        "coordinator" not in names):
        raise ValueError("CATALOG_INVALID")
    roles=_serialized({"schema":"r33/generic-role-catalog-v1","roles":sorted(names)})
    return {"runtime/coordinator_review.py":raw,
            "runtime/coordinator_roles.json":roles}


def _sidecars(profile: Path) -> dict[str, bytes]:
    content={"README.md":README.encode("utf-8"),"scripts/doctor.py":DOCTOR.encode("utf-8")}
    for name in (*DOCUMENTS,"ROLE_PLAYBOOK.md","FAMILY_LINK.json"):
        file=profile/name
        if file.is_symlink() or not file.is_file():
            raise ValueError("PROFILE_MISSING")
        content[f"system-files/{name}"]=file.read_bytes()
    for name,body in EXTRA_FILES.items():
        content[f"system-files/{name}"]=body.encode("utf-8")
    for name,config in SKILLS.items():
        prefix=f"custom-skills/{name}/"
        content[prefix+"skill.yaml"]=(
            f"name: {name}\ntitle: Coordinator {config['method'].title()}\n"
            f"description: {config['description']}\ninclude_in_prompt: false\n"
        ).encode("utf-8")
        content[prefix+"SKILL.md"]=(
            f"---\nname: {name}\ndescription: {config['description']}\n---\n\n"
            f"# Coordinator {config['method'].title()}\n\n"
            f"Call run.py --operation {config['method']} only on bounded synthetic "
            "or explicitly approved data. The offline runner cannot grant owner "
            "authority, dispatch work, create schedules or deliver a result. "
            "The receiving host must independently register this skill. "
            "Keep the package-local skills.yaml entry disabled.\n"
        ).encode("utf-8")
        content[prefix+"run.py"]=RUNNER.encode("utf-8")
    content["config/skills.yaml"]=("version: 1\nentries:\n"+"".join(
        f"  {name}:\n    status: disabled\n" for name in sorted(SKILLS)
    )).encode("utf-8")
    content["config/host-binding.json"]=_serialized(BINDING)
    content["hooks/HOOKS.json"]=_serialized(HOOKS)
    manifest={"schema":"r33/coordinator-subchats-v1","subchats":{}}
    for name,config in ROOMS.items():
        prefix=f"subchats/{name}/"
        content[prefix+"ROLE.md"]=(
            f"# {name.replace('-',' ').title()}\n\n{config['purpose']}\n\n"
            "This is an unbound role folder, NOT a real Muse subchat ID.\n"
        ).encode("utf-8")
        content[prefix+"CONTEXT.md"]=(
            f"# Bounded context\n\n{config['actions']}\n\n"
            "No parent transcript or original personal identity is inherited.\n"
        ).encode("utf-8")
        content[prefix+"MEMORY.md"]=(
            "# Memory custody\n\nNo personal history. Preserve only approved "
            "task-local, source-pinned facts in receiving owner-controlled state.\n"
        ).encode("utf-8")
        content[prefix+"TOOLS.md"]=(
            f"# Tools and refusals\n\n{config['stop']}\n\n"
            "Native tool discovery, permission, actor and recipient IDs are unverified.\n"
        ).encode("utf-8")
        row={"schema":"r33/coordinator-subchat-v1","role":name,
             "handoff_to":config["next"],"native_chat_id":None,
             "native_loaded":False,"enabled":False,"owner_user_id":None}
        content[prefix+"SUBCHAT.json"]=_serialized(row)
        manifest["subchats"][name]={"path":f"subchats/{name}","enabled":False,
                                     "native_chat_id":None}
    content["config/subchats.json"]=_serialized(manifest)
    return content


def _tree(root: Path) -> tuple[set[str], set[str]]:
    files=set()
    dirs={"."}
    for parent,subdirs,filenames in os.walk(root,followlinks=False):
        folder=Path(parent)
        for name in subdirs:
            file=folder/name
            if file.is_symlink() or (hasattr(file,"is_junction") and file.is_junction()):
                raise ValueError("SYMLINKED_DIRECTORY")
            dirs.add(file.relative_to(root).as_posix())
        for name in filenames:
            file=folder/name
            if file.is_symlink() or not file.is_file():
                raise ValueError("UNTRUSTED_FILE")
            files.add(file.relative_to(root).as_posix())
    return files,dirs


def _receipt(root: Path, extras: dict[str, bytes]) -> dict:
    files={}
    for file in (root/"profile").iterdir():
        if file.is_symlink() or not file.is_file():
            raise ValueError("PROFILE_UNTRUSTED")
        files[file.relative_to(root).as_posix()]=_sha(file.read_bytes())
    for name,data in extras.items():
        files[name]=_sha(data)
    dirs={"."}
    for rel in [*files,"receipts/COORDINATOR_RECEIPT.json"]:
        parent=Path(rel).parent
        while str(parent) not in (".",""):
            dirs.add(parent.as_posix())
            parent=parent.parent
    return {
        "schema":SCHEMA,"role_id":"coordinator",
        "files_sha256":dict(sorted(files.items())),
        "directories":sorted(dirs),
        "native_installed":False,
        "native_authenticated":False,
        "external_effect_authorized":False,
        "evidence_grade":"LOCAL_SOURCE_ONLY",
    }


def stage_coordinator_dropin(destination: Path) -> dict:
    """Create a standalone source-only role bundle; no live owner state."""
    target=Path(destination)
    _admitted_destination(target)
    source=_source_runtime()  # snapshot source bytes before writing destination
    target.mkdir(exist_ok=False)
    marker=target/"STAGING_INCOMPLETE"
    marker.write_text("Local source stage incomplete; do not install.\n",encoding="utf-8")
    render_preset("coordinator",target/"profile",display_name="Coordinator")
    extras={**source,**_sidecars(target/"profile")}
    for relative,body in sorted(extras.items()):
        file=target/relative
        file.parent.mkdir(exist_ok=True,parents=True)
        with file.open("xb") as handle:
            handle.write(body)
    if source!=_source_runtime():
        raise ValueError("SOURCE_CHANGED_DURING_STAGE")
    receipt=_receipt(target,extras)
    out=target/"receipts"/"COORDINATOR_RECEIPT.json"
    out.parent.mkdir(exist_ok=False)
    with out.open("xb") as handle:
        handle.write(_serialized(receipt))
    marker.unlink()
    if inspect_coordinator_dropin(target)["status"]!="LOCAL_COORDINATOR_MATCH":
        raise ValueError("LOCAL_PACK_READBACK_REFUSED")
    return {
        "status":"SOURCE_ONLY_COORDINATOR_STAGED",
        "role_id":"coordinator",
        "subchat_count":len(ROOMS),
        "custom_skill_count":len(SKILLS),
        "native_installed":False,
        "external_effect_authorized":False,
    }


def inspect_coordinator_dropin(destination: Path) -> dict:
    """Require unchanged current source, all expected neutral files and no extras."""
    refuse={"status":"REVIEW_REQUIRED","native_installed":False,
            "external_effect_authorized":False}
    root=Path(destination)
    if _unsafe_source_path(root) or not root.is_dir():
        return refuse
    if (root/"STAGING_INCOMPLETE").exists() or (root/"STAGING_INCOMPLETE").is_symlink():
        return {**refuse,"status":"INCOMPLETE_STAGE"}
    try:
        profile=root/"profile"
        if inspect_render(profile)["status"]!="LOCAL_MATCH":
            return refuse
        extras={**_source_runtime(),**_sidecars(profile)}
        expected=_receipt(root,extras)
        path=root/"receipts"/"COORDINATOR_RECEIPT.json"
        if path.is_symlink() or not path.is_file() or path.stat().st_size>30000:
            return refuse
        receipt=json.loads(path.read_bytes(),object_pairs_hook=_no_duplicate_json,
                           parse_constant=_reject_constant)
        if type(receipt) is not dict or receipt!=expected:
            return refuse
        files,dirs=_tree(root)
        if (files!=set(expected["files_sha256"])|{"receipts/COORDINATOR_RECEIPT.json"} or
            dirs!=set(expected["directories"])):
            return refuse
        if any((root/name).read_bytes()!=body for name,body in extras.items()):
            return refuse
        if any(_sha((root/name).read_bytes())!=digest for name,digest in
               expected["files_sha256"].items()):
            return refuse
        if path.read_bytes()!=_serialized(expected):
            return refuse
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError):
        return refuse
    return {"status":"LOCAL_COORDINATOR_MATCH","role_id":"coordinator",
            "native_installed":False,"external_effect_authorized":False}

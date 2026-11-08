"""Create-only portable Model Builder pack with bounded offline evaluation.

This is neither a model trainer nor a Muse host installation. All native
skills, subchats, hooks and rights remain unbound or disabled.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from .catalog import DOCUMENTS, render_preset
from .lifecycle import inspect_render
from .native_canary import _admitted_destination, _serialized, _no_duplicate_json, _reject_constant
from .native_skill_binding import _unsafe_source_path
from .coordinator_dropin import _tree, DOCTOR as GENERIC_SELF_HASH_DOCTOR

SCHEMA = "r33/model-builder-dropin-v1"
SKILLS = {
    "model_development_metrics": {
        "description":"Bounded development-set scoring with explicit protected final split",
        "method":"evaluate",
    },
    "model_checkpoint_verifier": {
        "description":"Actual synthetic checkpoint-byte digest verification; not trained weights",
        "method":"checkpoint",
    },
}
ROOMS = {
    "data-custody": {
        "purpose":"Admit versioned data/model source only after documented rights and family-split checks",
        "actions":"Check source families across train, dev and protected final, protect final labels from local development code",
        "stop":"No independently verified rights, held-out boundary or host grant means no training",
        "next":"development-evaluation",
    },
    "development-evaluation": {
        "purpose":"Measure bounded candidate versus baseline development predictions using actual provided rows",
        "actions":"Compute exact integer correct counts, deterministic accuracy and comparative delta for development only",
        "stop":"Caller predictions and apparent gain cannot count as real inference, training or final examination",
        "next":"artifact-verification",
    },
    "artifact-verification": {
        "purpose":"Verify bounded synthetic checkpoint bytes and retain source lineage without declaring optimizer steps",
        "actions":"Rehash actual supplied bytes, correlate input source digests and require separate external training provenance",
        "stop":"No authenticated weights, optimizer record, examiner and owner grant means SOURCE_ONLY/HOLD",
        "next":"data-custody",
    },
}
EXTRA = {
    "CONNECTORS.md":"# Optional connectors\n\nNo hosted model registry, inference endpoint, machine or paid account is configured. Discover native grants at receiving host before use.\n",
    "BROWSER.md":"# Browser\n\nNo browser integration is installed. Remote model downloads and dataset retrieval require separately authorized tools and rights.\n",
    "VOICE.md":"# Voice\n\nNo voice identity, recordings or speech models included. Voice is off.\n",
}
BINDING = {
    "schema":"r33/model-builder-host-binding-v1",
    "owner_user_id":None,
    "native_agent_id":None,
    "provider_session_id":None,
    "native_authenticated":False,
    "registered":False,
    "installed":False,
    "training_authorized":False,
    "model_selected_invocation_verified":False,
    "recipient_readback_verified":False,
    "external_effect_authorized":False,
}
HOOKS = {"schema":"r33/model-builder-hooks-v1","enabled":False,
         "installed":False,"scheduler_enabled":False,"event_handlers":[]}
README = """# Model Builder — neutral source-only development verifier

The two callable local skills are development-metric scoring and bounded
synthetic checkpoint SHA-256 verification. No optimizer, training step,
actual model weights, GPU, model download, paid API, data rights clearance,
blind final evaluation or native Muse invocation occurs here.

The checked-in runtime accepts strictly bounded caller-provided rows and
synthetic bytes. It verifies disjoint source families, holds protected-final
labels, measures development accuracy, and refuses forged training and
promotion claims. The checkpoint is intentionally synthetic, NOT an actual
trained adapter. The original host's registration, model-selected calls,
reviewer authority, recipient readback and wrong-owner denial are NOT_RUN.

Two skill descriptors exist with local scripts; config/skills.yaml is disabled.
The three subchat folders contain only unbound draft role/context/memory
contracts. No existing host, owner identity, model cache or state is changed.
Run scripts/doctor.py for local self-hash, not publisher authentication.
"""

RUNNER = r'''#!/usr/bin/env python3
"""No training/GPU/provider calls. Real local scoring and SHA-256 only."""
from __future__ import annotations
import argparse
import base64
import binascii
import hashlib
import json
from pathlib import Path
import sys


def refuse(reason):
    print(json.dumps({"status":"REVIEW_REQUIRED","reason":reason,
                      "trained":False,"native_tool_invoked":False,
                      "external_effect_authorized":False,
                      "promotion_authorized":False},sort_keys=True))
    return 2


def unique_pairs(pairs):
    out={}
    for k,v in pairs:
        if k in out:
            raise ValueError("DUPLICATE_JSON_KEY")
        out[k]=v
    return out


def demo():
    data={
        "schema":"r33/model-builder-development-v1",
        "model_source_sha256":"a"*64,"dataset_source_sha256":"b"*64,
        "rights_status":"UNVERIFIED",
        "rows":[
            {"sample_id":"train-1","family_id":"family-a","split":"train","label":1,"baseline":None,"candidate":None},
            {"sample_id":"dev-1","family_id":"family-b","split":"dev","label":1,"baseline":0,"candidate":1},
            {"sample_id":"dev-2","family_id":"family-c","split":"dev","label":0,"baseline":0,"candidate":0},
            {"sample_id":"final-1","family_id":"family-d","split":"final","label":None,"baseline":None,"candidate":None},
        ],
    }
    blob=b"synthetic-candidate-weights"
    manifest={
        "schema":"r33/model-builder-checkpoint-v1",
        "artifact_kind":"synthetic-checkpoint-bytes",
        "artifact_sha256":hashlib.sha256(blob).hexdigest(),
        "parent_model_sha256":"a"*64,
        "dataset_source_sha256":"b"*64,
        "optimizer_steps":0,"weights_trained":False,"rights_status":"UNVERIFIED",
    }
    return data,manifest,blob


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--operation",required=True,
                        choices=("demo","evaluate","checkpoint"))
    args=parser.parse_args(argv)
    root=Path(__file__).resolve().parents[2]
    engine=root/"runtime"/"model_eval.py"
    if engine.is_symlink() or not engine.is_file() or engine.stat().st_size>65536:
        return refuse("SOURCE_RUNTIME_MISSING")
    receipt=root/"receipts"/"MODEL_BUILDER_RECEIPT.json"
    if receipt.is_symlink() or not receipt.is_file() or receipt.stat().st_size>30000:
        return refuse("SOURCE_RECEIPT_MISSING")
    try:
        source=json.loads(receipt.read_bytes(),object_pairs_hook=unique_pairs)
        if (source.get("schema")!="r33/model-builder-dropin-v1" or
            source.get("native_installed") is not False or
            source.get("native_authenticated") is not False or
            source.get("external_effect_authorized") is not False or
            source.get("files_sha256",{}).get("runtime/model_eval.py")!=
                hashlib.sha256(engine.read_bytes()).hexdigest()):
            return refuse("SOURCE_RUNTIME_DRIFT_OR_FORGED_GRANT")
        sys.path.insert(0,str(root/"runtime"))
        from model_eval import evaluate_development,verify_checkpoint_bytes
        if args.operation=="demo":
            data,manifest,blob=demo()
            metric=evaluate_development(data)
            artifact=verify_checkpoint_bytes(manifest,blob)
            if (metric.get("status")!="LOCAL_DEV_METRICS_ONLY" or
                metric["dev_n"]!=2 or metric["candidate_correct"]!=2 or
                artifact.get("status")!="LOCAL_CHECKPOINT_DIGEST_MATCH"):
                return refuse("LOCAL_DEMO_REFUSED")
            print(json.dumps({
                "status":"LOCAL_MODEL_BUILDER_DEMO_PASSED",
                "dev_n":metric["dev_n"],"candidate_correct":metric["candidate_correct"],
                "checkpoint_status":artifact["status"],
                "model_trained":False,"native_tool_invoked":False,
                "external_effect_authorized":False,"final_status":"HELD_UNEVALUATED",
            },sort_keys=True))
            return 0
        raw=sys.stdin.buffer.read(16385)
        if len(raw)>16384 or not raw:
            return refuse("INPUT_SIZE_REFUSED")
        data=json.loads(raw,object_pairs_hook=unique_pairs,
                        parse_constant=lambda _: (_ for _ in ()).throw(ValueError("NONSTANDARD_NUMBER")))
        if args.operation=="evaluate":
            result=evaluate_development(data)
        else:
            if type(data) is not dict or set(data)!={"manifest","bytes_base64"}:
                return refuse("CHECKPOINT_INPUT_SCHEMA")
            encoded=data["bytes_base64"]
            if type(encoded) is not str or not 1<=len(encoded)<=6000:
                return refuse("CHECKPOINT_INPUT_SIZE")
            blob=base64.b64decode(encoded,validate=True)
            result=verify_checkpoint_bytes(data["manifest"],blob)
        result={**result,"native_tool_invoked":False,"external_effect_authorized":False}
        print(json.dumps(result,sort_keys=True))
        return 0 if result["status"] in (
            "LOCAL_DEV_METRICS_ONLY","LOCAL_CHECKPOINT_DIGEST_MATCH") else 2
    except (OSError,ValueError,TypeError,KeyError,ImportError,json.JSONDecodeError,binascii.Error):
        return refuse("UNTRUSTED_INPUT_OR_RUNTIME")


if __name__=="__main__":
    raise SystemExit(main())
'''

def _doctor() -> str:
    # Shared reviewed fail-closed self-hash reader is copied as raw source.
    # The installed packet needs no coordinator module or runtime import.
    changes=[
        ('COORDINATOR_RECEIPT.json','MODEL_BUILDER_RECEIPT.json'),
        ('r33/coordinator-dropin-v1',SCHEMA),
        ('record["role_id"]!="coordinator"','record["role_id"]!="model-builder"'),
    ]
    text=GENERIC_SELF_HASH_DOCTOR
    for old,new in changes:
        expected_count = 2 if old == "COORDINATOR_RECEIPT.json" else 1
        if text.count(old)!=expected_count:
            raise ValueError("SELF_HASH_TEMPLATE_DRIFT")
        text=text.replace(old,new)
    return text

def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _runtime_source() -> bytes:
    file=Path(__file__).with_name("model_eval.py")
    if file.is_symlink() or not file.is_file() or file.stat().st_size>65536:
        raise ValueError("MODEL_SOURCE_NOT_ADMITTED")
    return file.read_bytes()


def _sidecars(profile: Path) -> dict[str,bytes]:
    content={"README.md":README.encode("utf-8"),
             "scripts/doctor.py":_doctor().encode("utf-8")}
    for name in (*DOCUMENTS,"ROLE_PLAYBOOK.md","FAMILY_LINK.json"):
        path=profile/name
        if path.is_symlink() or not path.is_file():
            raise ValueError("PROFILE_SOURCE_NOT_REGULAR")
        content[f"system-files/{name}"]=path.read_bytes()
    for name,text in EXTRA.items():
        content[f"system-files/{name}"]=text.encode("utf-8")
    for name,settings in SKILLS.items():
        prefix=f"custom-skills/{name}/"
        content[prefix+"skill.yaml"]=(
            f"name: {name}\ntitle: Model Builder {settings['method'].title()}\n"
            f"description: {settings['description']}\ninclude_in_prompt: false\n"
        ).encode("utf-8")
        content[prefix+"SKILL.md"]=(
            f"---\nname: {name}\ndescription: {settings['description']}\n---\n\n"
            f"# Model Builder {settings['method'].title()}\n\n"
            "Execute run.py only for bounded synthetic or explicitly approved "
            "offline source inputs. No training, paid model call, publisher "
            "release, native host or independent examination is authorized. "
            "The package-local registry stays disabled.\n"
        ).encode("utf-8")
        content[prefix+"run.py"]=RUNNER.encode("utf-8")
    content["config/skills.yaml"]=(
        "version: 1\nentries:\n"+"".join(
            f"  {name}:\n    status: disabled\n" for name in sorted(SKILLS))
    ).encode("utf-8")
    content["config/host-binding.json"]=_serialized(BINDING)
    content["hooks/HOOKS.json"]=_serialized(HOOKS)
    manifest={"schema":"r33/model-builder-subchats-v1","subchats":{}}
    for name,details in ROOMS.items():
        prefix=f"subchats/{name}/"
        content[prefix+"ROLE.md"]=(
            f"# {name.replace('-',' ').title()}\n\n{details['purpose']}\n\n"
            "This is an unbound role folder; no native Muse subchat was created.\n"
        ).encode("utf-8")
        content[prefix+"CONTEXT.md"]=(
            f"# Scoped context\n\n{details['actions']}\n\n"
            "No personal donor state, protected final labels or unrelated task "
            "history is imported.\n"
        ).encode("utf-8")
        content[prefix+"MEMORY.md"]=(
            "# Memory custody\n\nNo prior memory. Preserve only explicitly "
            "approved source-scoped observations in a receiving owner-controlled store.\n"
        ).encode("utf-8")
        content[prefix+"TOOLS.md"]=(
            f"# Tools and refusals\n\n{details['stop']}\n\n"
            "Host grants, training engine, tokenizers, model weights and GPU "
            "drivers are NOT configured by this package.\n"
        ).encode("utf-8")
        row={"schema":"r33/model-builder-subchat-v1","role":name,
             "handoff_to":details["next"],"native_chat_id":None,
             "native_loaded":False,"enabled":False,"owner_user_id":None}
        content[prefix+"SUBCHAT.json"]=_serialized(row)
        manifest["subchats"][name]={"path":f"subchats/{name}",
                                     "enabled":False,"native_chat_id":None}
    content["config/subchats.json"]=_serialized(manifest)
    return content


def _receipt(root: Path, files: dict[str,bytes]) -> dict:
    observed={}
    for file in (root/"profile").iterdir():
        if file.is_symlink() or not file.is_file():
            raise ValueError("PROFILE_MEMBER_NOT_REGULAR")
        observed[file.relative_to(root).as_posix()]=_sha(file.read_bytes())
    for path,raw in files.items():
        observed[path]=_sha(raw)
    directories={"."}
    for path in [*observed,"receipts/MODEL_BUILDER_RECEIPT.json"]:
        node=Path(path).parent
        while str(node) not in (".",""):
            directories.add(node.as_posix())
            node=node.parent
    return {"schema":SCHEMA,"role_id":"model-builder",
            "files_sha256":dict(sorted(observed.items())),
            "directories":sorted(directories),
            "native_installed":False,"native_authenticated":False,
            "external_effect_authorized":False,"evidence_grade":"LOCAL_SOURCE_ONLY"}


def stage_model_builder_dropin(destination: Path) -> dict:
    target=Path(destination)
    _admitted_destination(target)
    frozen=_runtime_source()
    target.mkdir(exist_ok=False)
    marker=target/"STAGING_INCOMPLETE"
    marker.write_text("Local pack incomplete; do not install or retry blindly.\n")
    render_preset("model-builder",target/"profile",display_name="Model Builder")
    files={"runtime/model_eval.py":frozen,**_sidecars(target/"profile")}
    for relative,raw in sorted(files.items()):
        path=target/relative
        path.parent.mkdir(exist_ok=True,parents=True)
        with path.open("xb") as handle:
            handle.write(raw)
    if frozen!=_runtime_source():
        raise ValueError("MODEL_SOURCE_CHANGED_DURING_STAGE")
    manifest=_receipt(target,files)
    path=target/"receipts"/"MODEL_BUILDER_RECEIPT.json"
    path.parent.mkdir(exist_ok=False)
    with path.open("xb") as handle:
        handle.write(_serialized(manifest))
    marker.unlink()
    if inspect_model_builder_dropin(target)["status"]!="LOCAL_MODEL_BUILDER_MATCH":
        raise ValueError("PACK_SELF_READBACK_FAILED")
    return {"status":"SOURCE_ONLY_MODEL_BUILDER_STAGED",
            "role_id":"model-builder","custom_skill_count":len(SKILLS),
            "subchat_count":len(ROOMS),
            "native_installed":False,"external_effect_authorized":False}


def inspect_model_builder_dropin(destination: Path) -> dict:
    refused={"status":"REVIEW_REQUIRED","native_installed":False,
             "external_effect_authorized":False}
    root=Path(destination)
    if _unsafe_source_path(root) or not root.is_dir():
        return refused
    if (root/"STAGING_INCOMPLETE").exists() or (root/"STAGING_INCOMPLETE").is_symlink():
        return {**refused,"status":"INCOMPLETE_STAGE"}
    try:
        profile=root/"profile"
        if inspect_render(profile)["status"]!="LOCAL_MATCH":
            return refused
        sidecars={"runtime/model_eval.py":_runtime_source(),**_sidecars(profile)}
        expected=_receipt(root,sidecars)
        file=root/"receipts"/"MODEL_BUILDER_RECEIPT.json"
        if file.is_symlink() or not file.is_file() or file.stat().st_size>30000:
            return refused
        manifest=json.loads(file.read_bytes(),object_pairs_hook=_no_duplicate_json,
                            parse_constant=_reject_constant)
        if type(manifest) is not dict or manifest!=expected:
            return refused
        seen,dirs=_tree(root)
        if seen!=set(expected["files_sha256"])|{"receipts/MODEL_BUILDER_RECEIPT.json"}:
            return refused
        if dirs!=set(expected["directories"]):
            return refused
        if any((root/name).read_bytes()!=raw for name,raw in sidecars.items()):
            return refused
        if any(_sha((root/name).read_bytes())!=pin for name,pin in
               expected["files_sha256"].items()):
            return refused
        if file.read_bytes()!=_serialized(expected):
            return refused
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError):
        return refused
    return {"status":"LOCAL_MODEL_BUILDER_MATCH","role_id":"model-builder",
            "native_installed":False,"external_effect_authorized":False}

"""Source-pinned OPTIONAL first-party role donor fixtures, not a new controller.

The only real executable engines here are existing generic repo modules.
Animation has NO bundled renderer and is held. No original private donor
repo, agent memory, provider, connected account, model or OS sandbox is used.
Run only separately reviewed, synthetic local fixtures with explicit opt-in.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any

from .native_canary import _no_duplicate_json, _reject_constant
from .native_skill_binding import _unsafe_source_path

SCHEMA="muse-presets/optional-donor-source-v1"
PINS_SCHEMA="muse-presets/donor-source-pins-v1"
BASE="generic-first-party-source-v1"
# Immutable local source digest, NOT a publisher signature.
PINNED_MANIFEST_SHA256="f808e1e5b00345dbcb95e217a90199534aa0e71f0a53a204e981a9653cc84324"
MAX_MANIFEST=40_000
MAX_MODULE=300_000
MAX_OUTPUT=256_000
MAX_TOTAL=1_200_000
SHA64=re.compile(r"^[a-f0-9]{64}$")
SPECS={
 "animation":("creative-studio",()),
 "evaluation":("research-evaluator",(
   "src/muse_presets/research_evaluator.py",
   "src/muse_presets/finder.py",
   "src/muse_presets/native_skill_binding.py",
   "src/muse_presets/native_canary.py",
   "src/muse_presets/database_paths.py",
   "src/muse_presets/catalog.py",
   "src/muse_presets/playbooks.py",
   "src/muse_presets/neutrality.py",
   "examples/research_evaluator_demo.py")),
 "garden":("garden-companion",(
   "src/muse_presets/garden_calendar.py",
   "src/muse_presets/database_paths.py",
   "examples/garden_calendar_demo.py")),
 "study":("learning-coach",(
   "src/muse_presets/learning_session.py",
   "src/muse_presets/database_paths.py",
   "examples/learning_session_demo.py")),
 "claims":("claims-adjudicator",("src/muse_presets/claims.py",)),
 "security":("reverse-engineering-researcher",("src/muse_presets/reverse.py",)),
}
SCRIPTS={
 "evaluation":"examples/research_evaluator_demo.py",
 "garden":"examples/garden_calendar_demo.py",
 "study":"examples/learning_session_demo.py",
}
EXPECTED={
 "evaluation":"muse-presets/offline-demonstration-v1",
 "garden":"LOCAL_SQLITE_DEMO_PASSED",
 "study":"LOCAL_NONCLINICAL_STUDY_DEMO_PASSED",
}


def _require(ok:bool,code:str)->None:
    if not ok:
        raise ValueError(code)


def _sha(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()


def _root(value:object)->Path:
    _require(isinstance(value,(str,Path)),"DONOR_SOURCE_ROOT_TYPE_REFUSED")
    name=Path(value)
    _require(name.is_absolute() and ".." not in name.parts
             and not name.is_symlink()
             and not _unsafe_source_path(name),"DONOR_SOURCE_ROOT_UNSAFE")
    try:
        root=name.resolve(strict=True)
    except (ValueError,OSError,RuntimeError) as exc:
        raise ValueError("DONOR_SOURCE_ROOT_UNAVAILABLE") from exc
    _require(root.is_dir() and not _unsafe_source_path(root),
             "DONOR_SOURCE_ROOT_NOT_DIRECTORY")
    return root


def _read_regular(root:Path,relative:str,maximum:int)->bytes:
    _require(type(relative) is str and
             relative and not relative.startswith("/") and
             "\\" not in relative and ".." not in Path(relative).parts and
             ":" not in relative and relative==Path(relative).as_posix(),
             "DONOR_SOURCE_MEMBER_PATH_INVALID")
    path=root/relative
    _require(path.is_file() and not path.is_symlink() and
             not _unsafe_source_path(path) and
             path.stat().st_size<=maximum,
             "DONOR_SOURCE_MEMBER_NOT_REGULAR_OR_TOO_LARGE")
    return path.read_bytes()


def _load(root:Path)->dict:
    raw=_read_regular(root,"src/muse_presets/donor_sources.json",MAX_MANIFEST)
    _require(_sha(raw)==PINNED_MANIFEST_SHA256,
             "DONOR_MANIFEST_NOT_PINNED_TO_REVIEWED_SOURCE")
    try:
        doc=json.loads(raw.decode("utf-8"),
                       object_pairs_hook=_no_duplicate_json,
                       parse_constant=_reject_constant)
    except (ValueError,UnicodeError,TypeError) as exc:
        raise ValueError("DONOR_PIN_MANIFEST_PARSE_FAILED") from exc
    _require(type(doc) is dict and
       set(doc)=={"schema","source_repo","source_baseline","capabilities",
                  "native_muse_registered","original_animation_renderer_bundled",
                  "public_distribution_performed"} and
       doc["schema"]==PINS_SCHEMA and doc["source_baseline"]==BASE and
       doc["source_repo"]=="muse-ai-agent-presets" and
       doc["native_muse_registered"] is False and
       doc["original_animation_renderer_bundled"] is False and
       doc["public_distribution_performed"] is False and
       type(doc["capabilities"]) is dict and
       set(doc["capabilities"])==set(SPECS),
       "DONOR_PIN_MANIFEST_POLICY_REFUSED")
    return doc


def _capability(value:object)->str:
    _require(type(value) is str and value in SPECS,
             "DONOR_CAPABILITY_NOT_ADMITTED")
    return value


def _entry(root:Path, name:str, manifest:dict)->dict:
    item=manifest["capabilities"][name]
    expected_role,paths=SPECS[name]
    want="SOURCE_LINK_ONLY_NOT_BUNDLED" if name=="animation" else "LOCAL_EXISTING_ENGINE"
    _require(type(item) is dict and
      set(item)=={"role","grade","files_sha256","provider_authenticated",
                  "original_engine_invoked","external_effect_authorized"} and
      item["role"]==expected_role and item["grade"]==want and
      item["provider_authenticated"] is False and
      item["original_engine_invoked"] is False and
      item["external_effect_authorized"] is False and
      type(item["files_sha256"]) is dict and
      set(item["files_sha256"])==set(paths),
      "DONOR_SOURCE_ROLE_OR_POLICY_MISMATCH")
    hashes={}
    total=0
    for path in paths:
        pin=item["files_sha256"][path]
        _require(type(pin) is str and SHA64.fullmatch(pin) is not None,
                 "DONOR_SOURCE_PIN_INVALID")
        raw=_read_regular(root,path,MAX_MODULE)
        total+=len(raw)
        _require(total<=MAX_TOTAL and _sha(raw)==pin,
                 "DONOR_SOURCE_PIN_MISMATCH:"+path)
        hashes[path]=pin
    return {
        "capability":name,"role":expected_role,
        "status":"SOURCE_LINK_ONLY_NOT_BUNDLED" if name=="animation" else "SOURCE_PIN_MATCH",
        "executable":name!="animation",
        "files_sha256":hashes,
        "source_baseline":BASE,
        "source_owner_authenticated":False,
        "provider_authenticated":False,
        "native_tool_invoked":False,
        "actual_animation_rendered":False,
        "external_effect_authorized":False,
        "OS_sandbox_provided":False,
    }


def donor_catalog(source_root:object)->dict:
    """Report only source-backed capabilities and missing original animation."""
    root=_root(source_root)
    manifest=_load(root)
    return {
        "schema":SCHEMA,
        "capabilities":{name:_entry(root,name,manifest)
                        for name in sorted(SPECS)},
        "native_agent_installed":False,
        "provider_credentials_embedded":False,
        "external_effect_authorized":False,
        "original_donor_source_imported":False,
        "animation_engine_bundled":False,
        "source_owner_authenticated":False,
    }


def inspect_donor(source_root:object,capability:object)->dict:
    """Read-only, strict byte inspection; no native or local executable call."""
    name=_capability(capability)
    root=_root(source_root)
    return _entry(root,name,_load(root))


def _run_demo(root:Path,name:str)->dict:
    """Execute only a pinned synthetic script in the reviewed source tree."""
    relative=SCRIPTS[name]
    # -I drops PYTHONPATH/user site; -S disables site; only the verified
    # source root is added explicitly. This is NOT an OS sandbox.
    bootstrap=("import runpy,sys;"
               "sys.path.insert(0,sys.argv[1]);"
               "runpy.run_path(sys.argv[2],run_name='__main__')")
    command=[sys.executable,"-I","-S","-B","-c",bootstrap,
             str(root/"src"),str(root/relative)]
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE="1",GIT_TERMINAL_PROMPT="0")
    env.pop("PYTHONPATH",None)
    env.pop("PYTHONHOME",None)
    try:
        proc=subprocess.run(command,cwd=root,env=env,capture_output=True,
                            timeout=55)
    except (OSError,subprocess.TimeoutExpired) as exc:
        raise ValueError("DONOR_FIXTURE_EFFECT_UNKNOWN_OR_NOT_STARTED") from exc
    _require(proc.returncode==0 and
             len(proc.stdout)<=MAX_OUTPUT and len(proc.stderr)<=MAX_OUTPUT,
             "DONOR_REVIEWED_FIXTURE_FAILED_OR_TOO_LARGE")
    try:
        doc=json.loads(proc.stdout.decode("utf-8"),
                       object_pairs_hook=_no_duplicate_json,
                       parse_constant=_reject_constant)
    except (ValueError,UnicodeError,TypeError) as exc:
        raise ValueError("DONOR_FIXTURE_OUTPUT_NOT_ADMITTED") from exc
    _require(type(doc) is dict,
             "DONOR_FIXTURE_OUTPUT_NOT_OBJECT")
    if name=="evaluation":
        review=doc.get("research_evaluator")
        _require(doc.get("schema")==EXPECTED[name]
           and doc.get("native_muse_installed") is False
           and doc.get("external_effect_authorized") is False
           and type(review) is dict
           and review.get("status")=="LOCAL_SOURCE_TRACE_VERIFIED"
           and review.get("source_count")==2
           and review.get("scientific_hypothesis_proven") is False
           and review.get("tampered_source_refused") is True,
           "DONOR_EVALUATION_FIXTURE_SCOPE_INVALID")
    elif name=="garden":
        _require(doc.get("status")==EXPECTED[name]
           and doc.get("lost_ack_recovered") is True
           and doc.get("host_authenticated") is False
           and doc.get("external_calendar_writes") is False,
           "DONOR_GARDEN_FIXTURE_SCOPE_INVALID")
    elif name=="study":
        _require(doc.get("status")==EXPECTED[name]
           and doc.get("receipt_reopened") is True
           and doc.get("review_due_after_24h") is True
           and doc.get("clinical_release_ready") is False
           and doc.get("muse_native_authorized") is False,
           "DONOR_STUDY_FIXTURE_SCOPE_INVALID")
    return doc


def _pure_demo(name:str)->dict:
    """Reuse original, benign pure source functions with fixed toy values."""
    if name=="claims":
        from .claims import assess_scope
        data=assess_scope(
          "Fictional native integration is proven",
          "INDEPENDENT_USEFUL","LOCAL_TESTED",
          conditions=("No native receipt","Synthetic source only"))
        _require(data["disposition"]=="OVERCLAIM"
                 and data["independent_verified"] is False
                 and data["effect_authorized"] is False,
                 "DONOR_CLAIMS_FIXTURE_INVALID")
        return data
    if name=="security":
        from .reverse import compare_observed_flows
        before=[{"action":"click","target":"sample_button","outcome":"disabled"}]
        after=[{"action":"click","target":"sample_button","outcome":"enabled"}]
        data=compare_observed_flows(before,after)
        _require(data["changed"]==["click:sample_button"]
                 and data["network_activity"] is False
                 and data["native_invoked"] is False
                 and data["target_accessed"] is False,
                 "DONOR_SECURITY_FIXTURE_INVALID")
        return data
    raise ValueError("DONOR_PURE_DEMO_NOT_DEFINED")


def run_donor_fixture(source_root:object,capability:object,
                      *,allow_reviewed_fixture:bool=False)->dict:
    """Explicitly run a known synthetic fixture with no provider or native use.

    The caller must separately review the source and trust the OS account:
    Python fixtures can read its files/network; this is NOT a sandbox.
    """
    name=_capability(capability)
    _require(allow_reviewed_fixture is True,
             "EXPLICIT_DONOR_FIXTURE_OPTIN_REQUIRED")
    checked=inspect_donor(source_root,name)
    _require(checked["executable"],"DONOR_NOT_IMPORTED")
    root=_root(source_root)
    # The imported code performing a pure in-process fixture must come from
    # the same inspected repository, never this process's unrelated checkout.
    actual_runtime=Path(__file__).resolve().parents[2]
    _require(root==actual_runtime,"DONOR_RUNTIME_ROOT_MISMATCH")
    result=(_run_demo(root,name) if name in SCRIPTS else _pure_demo(name))
    # Detect code/source changes across the actual local fixture process.
    after=inspect_donor(root,name)
    _require(after["files_sha256"]==checked["files_sha256"],
             "DONOR_SOURCE_CHANGED_DURING_EXECUTION")
    return {
        "schema":"muse-presets/optional-donor-fixture-v1",
        "status":"LOCAL_SOURCE_FIXTURE_PASS",
        "capability":name,
        "role":checked["role"],
        "fixture_result":result,
        "source_files_sha256":checked["files_sha256"],
        "source_owner_authenticated":False,
        "original_donor_provider_invoked":False,
        "native_muse_invoked":False,
        "external_effect_authorized":False,
        "OS_sandbox_provided":False,
    }

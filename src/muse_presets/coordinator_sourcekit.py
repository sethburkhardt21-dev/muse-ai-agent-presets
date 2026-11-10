"""T19 source-only reusable Coordinator ZIP with existing R33 graph reviewer.

Wraps existing coordinator_dropin staging, not a new Omnium planner/compiler,
scheduler, state ledger, allocator or provider. Every exported file must equal
a fresh canonical source-generated pack, regardless of mutable local receipts.
"""
from __future__ import annotations

import hashlib
import json
import re
import stat
import tempfile
from pathlib import Path, PurePosixPath
import zipfile

from .coordinator_dropin import (
    stage_coordinator_dropin, inspect_coordinator_dropin,
)
from .coordinator_review import review_workgraph
from .native_canary import _no_duplicate_json, _reject_constant, _serialized
from .native_skill_binding import _unsafe_source_path

SCHEMA="r58/coordinator-executable-sourcekit-v1"
PREFIX="coordinator/"
MANIFEST="SOURCEKIT_MANIFEST.json"
RUNBOOK="START_HERE.md"
EXAMPLE_GRAPH="EXAMPLE_WORKGRAPH.json"
EXAMPLE_ASSERTIONS="EXAMPLE_ASSERTIONS.json"
MAX_FILES=160
MAX_UNPACKED=4*1024*1024
MAX_ARCHIVE=8*1024*1024
HEX=re.compile(r"^[0-9a-f]{64}$")

START_HERE="""# Coordinator — independently runnable offline source kit

The runnable Coordinator reviews an already-supplied, bounded workgraph,
finds dependency cycles and held external-effect tasks, and compares reported
actor/reviewer assertions. This is source-only advisory validation; it
DOES NOT compile, delegate or dispatch Atlas Omnium missions, authorize
tools, reserve worker hosts, create schedulers, run connected apps, or
deliver results. Genuine Omnium mission placement is a separate owner.

Requirements: Python 3.12+; no pip packages, provider account or paid API.

1. Obtain the ZIP SHA-256 from the trustworthy release page OUTSIDE the
   archive. Verify before safely extracting into a NEW directory.
2. Review EXAMPLE_WORKGRAPH.json, EXAMPLE_ASSERTIONS.json and the
   Coordinator disabled config/skills.yaml. All native chat IDs are null.
3. In the extracted directory (Windows: python; macOS: python3):

   python -I -B coordinator/custom-skills/coordinator_workgraph/run.py --operation demo

   This must print LOCAL_COORDINATOR_DEMO_PASSED.
4. Feed the workgraph into the same runner via stdin using --operation review.
   It must return LOCAL_PLAN_REVIEW_ONLY, order diagnose-1 then review-2,
   and hold review-2 because it requests an external effect.
5. Feed EXAMPLE_ASSERTIONS.json through
   coordinator/custom-skills/coordinator_evidence/run.py --operation evidence.
   It must say UNATTESTED_ASSERTIONS_ONLY with held_task_ids [review-2].
6. Review coordinator/scripts/doctor.py's LOCAL_SELF_HASH_MATCH but never
   treat this self-hash as a publisher signature or authenticated host grant.

The ZIP carries no live personal memory or provider identity. Printed
actor/reviewer claims are untrusted fictional samples. Returned order is
advisory and MUST NOT drive autonomous execution. Any unknown effect remains
held. All registered skills are DISABLED, no model routes or external
connectors are installed. Actual source and issuer authority are NOT PROVEN.
"""


def _sha(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()


def _serialized(value)->bytes:
    return (json.dumps(value,sort_keys=True,indent=2,ensure_ascii=False)+"\n").encode("utf-8")


def _base_example_graph()->dict:
    return {
        "schema":"r33/coordinator-workgraph-v1",
        "workspace":"fictional-offline",
        "budget_units":4,
        "tasks":[
            {"id":"diagnose-1","role":"software-engineer",
             "reviewer":"adversarial-verifier","requires":[],
             "estimated_units":2,"effect_class":"none",
             "source_sha256":"a"*64,
             "acceptance":["Exact local regression independently reviewed"]},
            {"id":"review-2","role":"claims-adjudicator",
             "reviewer":"research-evaluator","requires":["diagnose-1"],
             "estimated_units":2,"effect_class":"external",
             "source_sha256":"b"*64,
             "acceptance":["External recipient evidence requires original owner"]}
        ]
    }


def _examples()->tuple[bytes,bytes]:
    graph=_base_example_graph()
    plan=review_workgraph(graph)
    if (plan.get("status")!="LOCAL_PLAN_REVIEW_ONLY"
        or plan.get("execution_order")!=["diagnose-1","review-2"]
        or plan.get("held_effect_tasks")!=["review-2"]):
        raise ValueError("COORDINATOR_EXAMPLE_SOURCE_INVALID")
    assertions={
        "schema":"r33/coordinator-assertions-v1",
        "workgraph_sha256":plan["workgraph_sha256"],
        "items":[
            {"task_id":"diagnose-1","actor_role":"software-engineer",
             "reviewer_role":"adversarial-verifier",
             "source_sha256":"a"*64,"actor_claim":"completed",
             "reviewer_claim":"pass"},
            {"task_id":"review-2","actor_role":"claims-adjudicator",
             "reviewer_role":"research-evaluator",
             "source_sha256":"b"*64,"actor_claim":"unknown_effect",
             "reviewer_claim":"hold"}
        ]
    }
    return _serialized(graph),_serialized({"graph":graph,"assertions":assertions})


def _canonical_source_bytes()->dict[str,bytes]:
    """Fresh source-generated canonical bundle independent of caller's receipt."""
    with tempfile.TemporaryDirectory(prefix="r58-coordinator-canonical-") as scratch:
        d=Path(scratch)/"coordinator"
        receipt=stage_coordinator_dropin(d)
        if (receipt["status"]!="SOURCE_ONLY_COORDINATOR_STAGED"
            or inspect_coordinator_dropin(d)["status"]!="LOCAL_COORDINATOR_MATCH"):
            raise ValueError("COORDINATOR_CANONICAL_SOURCE_NOT_QUALIFIED")
        members={}
        for path in sorted(d.rglob("*"),key=lambda p:p.relative_to(d).as_posix()):
            if path.is_symlink() or (hasattr(path,"is_junction") and path.is_junction()):
                raise ValueError("CANONICAL_SYMLINK_REFUSED")
            if path.is_file():
                name=path.relative_to(d).as_posix()
                if path.stat().st_size>300000 or path.stat().st_nlink!=1:
                    raise ValueError("CANONICAL_INVALID_FILE")
                members[name]=path.read_bytes()
        if len(members)>MAX_FILES or sum(len(v) for v in members.values())>MAX_UNPACKED:
            raise ValueError("CANONICAL_SOURCE_TOO_LARGE")
        return members


def _portable_canonical_bytes(canonical:dict[str,bytes])->dict[str,bytes]:
    """Project only source-verified neutral files to canonical LF bytes.

    Windows render_preset writes CRLF by platform text defaults, while
    macOS writes LF. The sourcekit is an *independent source distribution*,
    not a mutation of the original staged bundle. Rehash both local receipts
    against the normalized bytes so the extracted runtime doctor still
    verifies exactly the same source on both platforms. An owner-edited
    source is rejected before this conversion by _validate_pack.
    """
    normalized={name:raw.replace(b"\r\n",b"\n")
                if (name.startswith("profile/") or
                    name.startswith("system-files/"))
                else raw for name,raw in canonical.items()}
    profile_name="profile/RECEIPT.json"
    if profile_name not in normalized:
        raise ValueError("COORDINATOR_PORTABLE_PROFILE_RECEIPT_MISSING")
    profile=json.loads(normalized[profile_name],
                       object_pairs_hook=_no_duplicate_json,
                       parse_constant=_reject_constant)
    if (type(profile) is not dict or
        profile.get("schema")!="muse-presets/render-v3" or
        type(profile.get("rendered_sha256")) is not dict):
        raise ValueError("COORDINATOR_PORTABLE_PROFILE_SCHEMA_INVALID")
    for name in profile["rendered_sha256"]:
        path="profile/"+name
        if path not in normalized or name=="RECEIPT.json":
            raise ValueError("COORDINATOR_PORTABLE_PROFILE_MEMBER_MISSING")
        profile["rendered_sha256"][name]=_sha(normalized[path])
    # render_preset writes json.dumps(indent=2) without sort_keys.
    normalized[profile_name]=(json.dumps(profile,indent=2)+"\n").encode("utf-8")
    # Original Coordinator sidecars mirror the staged profile files.
    for name in list(normalized):
        if name.startswith("profile/"):
            other="system-files/"+name.removeprefix("profile/")
            if other in normalized:
                normalized[other]=normalized[name]
    receipt_name="receipts/COORDINATOR_RECEIPT.json"
    if receipt_name not in normalized:
        raise ValueError("COORDINATOR_PORTABLE_RECEIPT_MISSING")
    receipt=json.loads(normalized[receipt_name],
                       object_pairs_hook=_no_duplicate_json,
                       parse_constant=_reject_constant)
    if (type(receipt) is not dict or
        receipt.get("schema")!="r33/coordinator-dropin-v1" or
        type(receipt.get("files_sha256")) is not dict or
        set(receipt["files_sha256"])!=set(normalized)-{receipt_name}):
        raise ValueError("COORDINATOR_PORTABLE_RECEIPT_FILE_SET_INVALID")
    for name in receipt["files_sha256"]:
        receipt["files_sha256"][name]=_sha(normalized[name])
    normalized[receipt_name]=_serialized(receipt)
    return normalized


def _validate_pack(pristine:Path, canonical:dict[str,bytes])->None:
    """Never trust the staged receipt as an independent owner-memory authority."""
    if (inspect_coordinator_dropin(pristine).get("status")!="LOCAL_COORDINATOR_MATCH"):
        raise ValueError("COORDINATOR_SOURCEKIT_PRISTINE_REQUIRED")
    if _unsafe_source_path(pristine):
        raise ValueError("COORDINATOR_SOURCEKIT_UNSAFE_SOURCE_PATH")
    files={}
    for p in pristine.rglob("*"):
        if p.is_symlink() or (hasattr(p,"is_junction") and p.is_junction()):
            raise ValueError("COORDINATOR_SOURCEKIT_PRISTINE_SYMLINK_REFUSED")
        if p.is_file():
            rel=p.relative_to(pristine).as_posix()
            if p.stat().st_nlink!=1:
                raise ValueError("COORDINATOR_SOURCEKIT_PRISTINE_HARDLINK_REFUSED")
            files[rel]=p.read_bytes()
    if files!=canonical:
        raise ValueError("COORDINATOR_SOURCEKIT_PRISTINE_CANONICAL_BYTES_REQUIRED")


def _source_members(pristine:Path)->dict[str,bytes]:
    canonical=_canonical_source_bytes()
    _validate_pack(pristine,canonical)
    for name,raw in canonical.items():
        if (pristine/name).read_bytes()!=raw:
            raise ValueError("COORDINATOR_SOURCEKIT_LATE_SOURCE_DRIFT")
    portable=_portable_canonical_bytes(canonical)
    graph,assertions=_examples()
    return {**{PREFIX+n:raw for n,raw in portable.items()},
            RUNBOOK:START_HERE.encode("utf-8"),
            EXAMPLE_GRAPH:graph,
            EXAMPLE_ASSERTIONS:assertions}


def _zip_member(archive:zipfile.ZipFile,name:str,raw:bytes)->None:
    info=zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0))
    info.create_system=3
    info.external_attr=(stat.S_IFREG|0o644)<<16
    info.compress_type=zipfile.ZIP_DEFLATED
    archive.writestr(info,raw,compress_type=zipfile.ZIP_DEFLATED,compresslevel=6)


def _manifest(members:dict[str,bytes])->dict:
    return {
        "schema":SCHEMA,"role_id":"coordinator",
        "source_grade":"LOCAL_OFFLINE_REVIEW_ONLY",
        "files_sha256":{name:_sha(raw) for name,raw in sorted(members.items())},
        "workgraph_example_sha256":_sha(members[EXAMPLE_GRAPH]),
        "assertions_example_sha256":_sha(members[EXAMPLE_ASSERTIONS]),
        "native_installed":False,"provider_authenticated":False,
        "external_effect_authorized":False,"omnium_mission_compiled":False,
        "reviewer_identity_authenticated":False,"public_release_published":False,
    }


def _require_new(path:Path)->Path:
    if not path.name or path.suffix.lower()!=".zip":
        raise ValueError("COORDINATOR_SOURCEKIT_DESTINATION_ZIP_REQUIRED")
    if _unsafe_source_path(path):
        raise ValueError("COORDINATOR_SOURCEKIT_UNSAFE_DESTINATION")
    if path.exists() or path.is_symlink() or (
        hasattr(path,"is_junction") and path.is_junction()):
        raise FileExistsError("COORDINATOR_SOURCEKIT_DESTINATION_OCCUPIED")
    if not path.parent.is_dir():
        raise FileNotFoundError("COORDINATOR_SOURCEKIT_PARENT_MISSING")
    return path


def export_coordinator_sourcekit(pristine:Path,destination:Path)->dict:
    """Create-only deterministic artifact from source-checked, blank profile."""
    src=Path(pristine)
    prepared=_source_members(src)
    if len(prepared)+1>MAX_FILES or sum(len(x) for x in prepared.values())>MAX_UNPACKED:
        raise ValueError("COORDINATOR_SOURCEKIT_MEMBER_BUDGET_EXCEEDED")
    all_members={**prepared,MANIFEST:_serialized(_manifest(prepared))}
    target=_require_new(Path(destination))
    with zipfile.ZipFile(target,"x",allowZip64=False) as z:
        for name,raw in sorted(all_members.items()):
            _zip_member(z,name,raw)
    digest=_sha(target.read_bytes())
    if verify_coordinator_sourcekit(target,digest)["status"]!="LOCAL_COORDINATOR_SOURCEKIT_VERIFIED":
        raise RuntimeError("COORDINATOR_SOURCEKIT_POST_EXPORT_INSPECTION_FAILED")
    return {
        "status":"LOCAL_COORDINATOR_SOURCEKIT_EXPORTED",
        "role_id":"coordinator","sha256":digest,
        "archive_bytes":target.stat().st_size,
        "archive_members":len(all_members),
        "native_installed":False,
        "external_effect_authorized":False,
        "omnium_mission_compiled":False,
    }


def verify_coordinator_sourcekit(path:Path,expected_sha256:str)->dict:
    """Require out-of-band expected ZIP hash; no issuer authenticity implied."""
    p=Path(path)
    if (not p.is_file() or p.is_symlink() or _unsafe_source_path(p) or
        type(expected_sha256) is not str or HEX.fullmatch(expected_sha256) is None or
        p.stat().st_size>MAX_ARCHIVE):
        raise ValueError("COORDINATOR_SOURCEKIT_ARCHIVE_NOT_ADMITTED")
    data=p.read_bytes()
    if _sha(data)!=expected_sha256:
        raise ValueError("COORDINATOR_SOURCEKIT_PIN_MISMATCH")
    canonical=_portable_canonical_bytes(_canonical_source_bytes())
    required={PREFIX+n for n in canonical}|{RUNBOOK,EXAMPLE_GRAPH,EXAMPLE_ASSERTIONS,MANIFEST}
    with zipfile.ZipFile(p,"r") as z:
        infos=z.infolist()
        if len(infos)!=len(required) or len(infos)>MAX_FILES:
            raise ValueError("COORDINATOR_SOURCEKIT_FILE_SET_INVALID")
        seen=set();casefold=set();total=0
        for info in infos:
            name=info.filename
            parts=PurePosixPath(name).parts
            if (not name or not parts or name.startswith("/") or ".." in parts
                or "\\" in name or ":" in parts[0] or info.is_dir()
                or name in seen or name.casefold() in casefold or name not in required
                or stat.S_IFMT(info.external_attr>>16)!=stat.S_IFREG):
                raise ValueError("COORDINATOR_SOURCEKIT_UNSAFE_ARCHIVE_MEMBER")
            seen.add(name);casefold.add(name.casefold())
            total+=info.file_size
        if seen!=required or total>MAX_UNPACKED or z.testzip() is not None:
            raise ValueError("COORDINATOR_SOURCEKIT_BAD_ZIP")
        raw={n:z.read(n) for n in sorted(required)}
    for name,original in canonical.items():
        if raw[PREFIX+name]!=original:
            raise ValueError("COORDINATOR_SOURCEKIT_ORIGINAL_CANONICAL_PIN_MISMATCH")
    graph,assertions=_examples()
    if (raw[RUNBOOK]!=START_HERE.encode("utf-8") or
        raw[EXAMPLE_GRAPH]!=graph or raw[EXAMPLE_ASSERTIONS]!=assertions):
        raise ValueError("COORDINATOR_SOURCEKIT_EXAMPLE_OR_DOCS_DRIFT")
    m=json.loads(raw[MANIFEST],object_pairs_hook=_no_duplicate_json,
                 parse_constant=_reject_constant)
    want={"schema","role_id","source_grade","files_sha256",
          "workgraph_example_sha256","assertions_example_sha256",
          "native_installed","provider_authenticated","external_effect_authorized",
          "omnium_mission_compiled","reviewer_identity_authenticated","public_release_published"}
    if (type(m) is not dict or set(m)!=want or m["schema"]!=SCHEMA or
        m["role_id"]!="coordinator" or m["source_grade"]!="LOCAL_OFFLINE_REVIEW_ONLY" or
        any(m[key] is not False for key in (
            "native_installed","provider_authenticated","external_effect_authorized",
            "omnium_mission_compiled","reviewer_identity_authenticated",
            "public_release_published")) or
        type(m["files_sha256"]) is not dict or
        set(m["files_sha256"])!=required-{MANIFEST}):
        raise ValueError("COORDINATOR_SOURCEKIT_MANIFEST_POLICY_INVALID")
    for name,digest in m["files_sha256"].items():
        if type(digest) is not str or digest!=_sha(raw[name]):
            raise ValueError("COORDINATOR_SOURCEKIT_MEMBER_SHA_DRIFT")
    if (m["workgraph_example_sha256"]!=_sha(graph) or
        m["assertions_example_sha256"]!=_sha(assertions)):
        raise ValueError("COORDINATOR_SOURCEKIT_EXAMPLE_SHA_DRIFT")
    return {
        "status":"LOCAL_COORDINATOR_SOURCEKIT_VERIFIED",
        "role_id":"coordinator","archive_sha256":expected_sha256,
        "member_count":len(raw),
        "native_installed":False,"external_effect_authorized":False,
        "omnium_mission_compiled":False,
    }

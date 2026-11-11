"""Reproducible standalone Claims Adjudicator ZIP: exact existing source.

Not a native assistant, independently attested judge, source of evidence, or
permission to contact any external system. Never copies owner state.
"""
from __future__ import annotations
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import stat
import zipfile
import zlib

from .coordinator_sourcekit import _zip_member
from .native_skill_binding import _unsafe_source_path

SCHEMA="muse-presets/claims-executable-sourcekit-v1"
PREFIX="claims-adjudicator/"
MANIFEST="SOURCEKIT_MANIFEST.json"
HEX64=re.compile(r"^[a-f0-9]{64}$")
MAX_ARCHIVE=1_000_000
MAX_UNPACKED=500_000
MAX_MEMBERS=20
SOURCE_SHA={
    "src/muse_presets/claims.py":"af6e5558024cbca4099d1f65ef2f68ae6d062df105db22eb34aa17da7d79a1e9",
    "presets/claims-adjudicator/preset.json":"0d9205ec0e107baf4600106d8b0815a9e2ab8ce1923cf869408ada75ececaca7",
    "presets/claims-adjudicator/playbook.json":"14934a1fda009f4ce6e822d17a02a2cf345d08ac53945837c08d5c93c57656cf",
    "LICENSE":"af30e586ca6503924d5e4d99894ec6c7ce61ba77a55ba081b7a129d33f43fddf",
}
EXAMPLE={
    "statement":"This fictional source kit operates as an independently verified native agent.",
    "asserted_grade":"INDEPENDENT_USEFUL",
    "evidence_grade":"LOCAL_TESTED",
    "conditions":["Only offline source tests passed.","No native owner or independent recipient is authenticated."],
}
START_HERE="""# Claims Adjudicator — executable local source kit

This ZIP includes the original small pure-Python claims/scope checker,
a standalone command-line runner, role profile, method playbook, example
and exact per-file SHA-256 receipt. It does not adjudicate factual truth,
look up sources, authenticate reviewers or install a Muse agent.

Requirements: Python 3.12+; no pip packages, Git, network or paid API.
Obtain this ZIP's SHA-256 from the official release page before extraction.
Extract to a NEW directory. From the extracted directory, run:

  python -I -B claims-adjudicator/run.py --operation demo

Expected status: LOCAL_CLAIMS_DEMO_PASSED, disposition OVERCLAIM.

For a specific supplied claim, review EXAMPLE_CLAIM.json first; pipe its
contents to the runner using --operation assess --allow-reviewed-local.
No flag means REVIEW_REQUIRED, and invalid inputs are refused. The
runner reads stdin only; it never publishes, downloads, or sends data.

The role's native config and Family Link remain disabled. A valid
embedded hash can detect changed local bytes but is NOT a publisher
signature, reviewer attestation or owner authorization. Verify the ZIP
digest from a separately trusted release page. Python -I is import
isolation, not an OS security sandbox. Run reviewed source only.

This is a local tool and can assess only an asserted grade against a
caller-supplied evidence grade; it cannot independently prove evidence.
"""
RUNNER=r'''"""Standalone claims-only runner; no account, provider, or native installation."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys

MANIFEST=Path(__file__).resolve().parent.parent/"SOURCEKIT_MANIFEST.json"

def _bad_pairs(pairs):
    out={}
    for k,v in pairs:
        if k in out:
            raise ValueError("DUPLICATE_JSON_KEY")
        out[k]=v
    return out

def _constant(value):
    raise ValueError("NONFINITE_NUMBER")

def _loads(raw):
    return json.loads(raw,object_pairs_hook=_bad_pairs,parse_constant=_constant)

def _refuse(reason):
    print(json.dumps({"status":"REFUSED","reason":reason,
          "provider_authenticated":False,"external_effect_authorized":False},sort_keys=True))
    return 2

def _engine():
    here=Path(__file__).resolve().parent
    source=here/"claims.py"
    if Path(__file__).is_symlink() or MANIFEST.is_symlink() or source.is_symlink():
        raise ValueError("LINKED_SOURCE_REFUSED")
    if not source.is_file() or source.stat().st_size>65536:
        raise ValueError("MISSING_CLAIMS_MODULE")
    manifest=_loads(MANIFEST.read_bytes())
    expected=manifest["files_sha256"]["claims-adjudicator/claims.py"]
    actual=hashlib.sha256(source.read_bytes()).hexdigest()
    if manifest["schema"]!="muse-presets/claims-executable-sourcekit-v1" or actual!=expected:
        raise ValueError("CLAIMS_SOURCE_PIN_CHANGED")
    if manifest["native_installed"] is not False or manifest["external_effect_authorized"] is not False:
        raise ValueError("NATIVE_AUTHORITY_NOT_ADMITTED")
    sys.path.insert(0,str(here))
    from claims import assess_scope
    return assess_scope

def main(argv=None):
    p=argparse.ArgumentParser(description="Local source-only claims scope checker")
    p.add_argument("--operation",choices=("demo","assess"),required=True)
    p.add_argument("--allow-reviewed-local",action="store_true")
    a=p.parse_args(argv)
    try:
        evaluate=_engine()
        if a.operation=="assess" and not a.allow_reviewed_local:
            print(json.dumps({"status":"REVIEW_REQUIRED",
                "native_installed":False,"external_effect_authorized":False},sort_keys=True))
            return 2
        if a.operation=="demo":
            claim={"statement":"A fictional local run proves independent native operation",
              "asserted_grade":"INDEPENDENT_USEFUL","evidence_grade":"LOCAL_TESTED",
              "conditions":["Local synthetic source only","No original independent review"]}
        else:
            source=sys.stdin.buffer.read(16385)
            if not source or len(source)>16384:
                raise ValueError("CLAIMS_INPUT_SIZE_REFUSED")
            claim=_loads(source)
            if type(claim) is not dict or set(claim)!={
              "statement","asserted_grade","evidence_grade","conditions"}:
                raise ValueError("CLAIMS_INPUT_SCHEMA_REFUSED")
        result=evaluate(claim["statement"],claim["asserted_grade"],
                claim["evidence_grade"],conditions=claim["conditions"])
        if a.operation=="demo" and result["disposition"]!="OVERCLAIM":
            raise ValueError("SOURCE_DEMO_DRIFT")
        print(json.dumps({"status":"LOCAL_CLAIMS_DEMO_PASSED" if a.operation=="demo"
             else "LOCAL_DECLARED_SCOPE_REVIEW_ONLY","result":result,
             "native_installed":False,"provider_authenticated":False,
             "external_effect_authorized":False},sort_keys=True))
        return 0
    except (ValueError,TypeError,KeyError,UnicodeError,OSError) as exc:
        return _refuse(type(exc).__name__+":"+str(exc)[:180])

if __name__=="__main__":
    raise SystemExit(main())
'''

def _sha(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()

def _json(value:object)->bytes:
    return (json.dumps(value,sort_keys=True,indent=2,ensure_ascii=False)+"\n").encode("utf-8")

def _require(ok:bool,msg:str)->None:
    if not ok:raise ValueError(msg)

def _read_source(root:Path)->dict[str,bytes]:
    root=Path(root)
    _require(root.is_dir() and not root.is_symlink() and
             not _unsafe_source_path(root),"CLAIMS_SOURCE_ROOT_UNSAFE")
    members={}
    for name,want in SOURCE_SHA.items():
        file=root/name
        _require(file.is_file() and not file.is_symlink() and
                 not _unsafe_source_path(file) and file.stat().st_size<65536
                 and file.stat().st_nlink==1,
                 "CLAIMS_SOURCE_FILE_NOT_ADMITTED:"+name)
        raw=file.read_bytes()
        _require(_sha(raw)==want,"CLAIMS_SOURCE_BASE_PIN_MISMATCH:"+name)
        members[name]=raw
    for name in ("preset.json","playbook.json"):
        doc=json.loads(members["presets/claims-adjudicator/"+name])
        if name=="preset.json":
            _require(doc.get("id")=="claims-adjudicator"
                     and doc.get("native_muse_status")=="UNBOUND"
                     and doc["family_link"]["enabled"] is False,
                     "CLAIMS_DISABLED_ROLE_PROFILE_CHANGED")
        else:
            _require(doc.get("role_id")=="claims-adjudicator",
                     "CLAIMS_ROLE_PLAYBOOK_CHANGED")
    return members

def _distribution(root:Path)->dict[str,bytes]:
    src=_read_source(root)
    members={
      PREFIX+"claims.py":src["src/muse_presets/claims.py"],
      PREFIX+"run.py":RUNNER.encode("utf-8"),
      PREFIX+"preset.json":src["presets/claims-adjudicator/preset.json"],
      PREFIX+"playbook.json":src["presets/claims-adjudicator/playbook.json"],
      "LICENSE":src["LICENSE"],
      "START_HERE.md":START_HERE.encode("utf-8"),
      "EXAMPLE_CLAIM.json":_json(EXAMPLE),
    }
    manifest={
       "schema":SCHEMA,"role_id":"claims-adjudicator",
       "files_sha256":{name:_sha(raw) for name,raw in sorted(members.items())},
       "source_grade":"LOCAL_DECLARED_SCOPE_REVIEW_ONLY",
       "native_installed":False,"provider_authenticated":False,
       "independent_verified":False,"external_effect_authorized":False,
       "public_release_published":False,
    }
    members[MANIFEST]=_json(manifest)
    return members

def export_claims_sourcekit(source_root:Path,destination:Path)->dict:
    dest=Path(destination)
    _require(dest.suffix.lower()==".zip"
             and dest.parent.is_dir() and not dest.parent.is_symlink()
             and not _unsafe_source_path(dest.parent)
             and not dest.exists() and not dest.is_symlink(),
             "CLAIMS_SOURCEKIT_DESTINATION_OCCUPIED_OR_UNSAFE")
    members=_distribution(Path(source_root))
    with zipfile.ZipFile(dest,"x",allowZip64=False) as z:
        for name,raw in sorted(members.items()):
            _zip_member(z,name,raw)
    digest=_sha(dest.read_bytes())
    verify_claims_sourcekit(source_root,dest,digest)
    return {"status":"LOCAL_CLAIMS_SOURCEKIT_EXPORTED",
      "archive_sha256":digest,"member_count":len(members),
      "archive_bytes":dest.stat().st_size,"native_installed":False,
      "external_effect_authorized":False}

def verify_claims_sourcekit(source_root:Path,archive_path:Path,
                            expected_sha256:str)->dict:
    file=Path(archive_path)
    _require(type(expected_sha256) is str and
             HEX64.fullmatch(expected_sha256) is not None,
             "CLAIMS_SOURCEKIT_PIN_INVALID")
    _require(file.is_file() and not file.is_symlink()
             and not _unsafe_source_path(file)
             and file.stat().st_size<=MAX_ARCHIVE,
             "CLAIMS_SOURCEKIT_ARCHIVE_UNSAFE")
    raw=file.read_bytes()
    _require(_sha(raw)==expected_sha256,"CLAIMS_SOURCEKIT_PIN_MISMATCH")
    expected=_distribution(Path(source_root))
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            infos=z.infolist()
            names=[x.filename for x in infos]
            _require(len(names)==len(expected) and len(names)<=MAX_MEMBERS
                     and len(set(names))==len(names)
                     and len(set(n.casefold() for n in names))==len(names)
                     and set(names)==set(expected),
                     "CLAIMS_SOURCEKIT_MEMBER_SET_INVALID")
            total=0
            # Admit every header before opening or decompressing any body.
            for member in infos:
                path=PurePosixPath(member.filename)
                _require(not member.is_dir() and path.parts
                         and not path.is_absolute() and ".." not in path.parts
                         and "\\" not in member.filename and ":" not in member.filename
                         and stat.S_IFMT(member.external_attr>>16)==stat.S_IFREG,
                         "CLAIMS_SOURCEKIT_UNSAFE_MEMBER")
                _require(member.file_size==len(expected[member.filename]),
                         "CLAIMS_SOURCEKIT_MEMBER_SIZE_INVALID")
                _require(member.compress_type in (zipfile.ZIP_STORED,zipfile.ZIP_DEFLATED),
                         "CLAIMS_SOURCEKIT_COMPRESSION_UNSUPPORTED")
                # UTF-8 names and data descriptors are supported, not encryption
                # or patched/masked headers requiring another decoder.
                _require(member.flag_bits & ~0x808 == 0,
                         "CLAIMS_SOURCEKIT_FLAGS_UNSUPPORTED")
                total+=member.file_size
                _require(total<MAX_UNPACKED,"CLAIMS_SOURCEKIT_UNPACK_BUDGET")
            for member in infos:
                wanted=expected[member.filename]
                with z.open(member,"r") as body:
                    _require(body.read(len(wanted)+1)==wanted,
                             "CLAIMS_SOURCEKIT_CANONICAL_BYTES_CHANGED")
    except (zipfile.BadZipFile,zipfile.LargeZipFile,EOFError,zlib.error,
            NotImplementedError,RuntimeError) as exc:
        raise ValueError("CLAIMS_SOURCEKIT_CORRUPT_ARCHIVE") from exc
    return {"status":"LOCAL_CLAIMS_SOURCEKIT_VERIFIED",
       "archive_sha256":expected_sha256,"member_count":len(expected),
       "source_grade":"LOCAL_DECLARED_SCOPE_REVIEW_ONLY",
       "native_installed":False,"external_effect_authorized":False,
       "independent_verified":False}

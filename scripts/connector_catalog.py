"""Source-pinned, read-only custom connector directory and create-only export.

No provider authentication, connector execution or native Muse enrollment occurs.
"""
from __future__ import annotations
import argparse,hashlib,json,re,sys,tempfile,zipfile,os
from pathlib import Path
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parents[1]
DIRECTORY=ROOT/"docs"/"connectors"
REPO="bluman1/muse-connectors"
PIN="73f302c2d8569fdc65e0e57c26b244c547fcd40e"
ID=re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
SHA=re.compile("[0-9a-f]{64}\\Z")
GIT_SHA=re.compile("[0-9a-f]{40}\\Z")
SCHEMA="muse-specialist-toolkit/connectors-v1"
MANDATORY={"id","name","description","category","auth","allowed_hosts","specialists",
           "source_url","source_sha256","source_git_blob","setup_prompt",
           "permissions","auth_details","operations","upstream_maturity","files","setup_guide"}
FORBIDDEN={"installed","connected","working","officially_endorsed","token","password","secret"}
FILES=("catalog.json","upstream-catalog.json","UPSTREAM_LICENSE.txt",
       "SOURCE_RECORDS.json","PROVENANCE.json","README.md","CATALOG.md",
       "index.html","app.css","app.js")

def _sha(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()

def _canonical(obj)->bytes:
    return (json.dumps(obj,sort_keys=True,indent=2,ensure_ascii=False)+"\n").encode("utf8")

def _roles()->set[str]:
    doc=json.loads((ROOT/"presets/catalog.json").read_bytes())
    return set(doc["presets"])

def validate_catalog(doc:object)->dict:
    if type(doc) is not dict or set(doc)!={"schema","source","connectors"} or doc["schema"]!=SCHEMA:
        raise ValueError("INVALID_CATALOG_SCHEMA")
    src=doc["source"]
    if type(src) is not dict or src.get("repository")!=REPO or src.get("commit")!=PIN:
        raise ValueError("SOURCE_PIN_MISMATCH")
    if src.get("license")!="MIT" or not isinstance(src.get("catalog_sha256"),str) or not SHA.fullmatch(src["catalog_sha256"]):
        raise ValueError("INVALID_SOURCE_LICENSE_OR_DIGEST")
    rows=doc["connectors"]
    if type(rows) is not list or len(rows)!=151:
        raise ValueError("CONNECTOR_COUNT_INVALID")
    roles=_roles();seen=set()
    for row in rows:
        if type(row) is not dict or not MANDATORY<=set(row) or FORBIDDEN&set(row):
            raise ValueError("INVALID_CONNECTOR_FIELDS")
        name=row["id"]
        if type(name) is not str or not ID.fullmatch(name) or name in seen:
            raise ValueError("INVALID_OR_DUPLICATE_CONNECTOR_ID")
        seen.add(name)
        for key in ("name","description","category","auth","setup_prompt","permissions","auth_details",
                    "operations","upstream_maturity","setup_guide"):
            if type(row[key]) is not str or not row[key].strip() or len(row[key])>20000:
                raise ValueError("INVALID_CONNECTOR_TEXT")
        for key in ("source_sha256","source_git_blob"):
            pattern=SHA if key=="source_sha256" else GIT_SHA
            if type(row[key]) is not str or not pattern.fullmatch(row[key]):
                raise ValueError("INVALID_CONNECTOR_DIGEST")
        expected=f"https://github.com/{REPO}/blob/{PIN}/connectors/{name}/SKILL.md"
        if row["source_url"]!=expected or row["source_url"] not in row["setup_prompt"]:
            raise ValueError("CONNECTOR_SOURCE_MISMATCH")
        for key in ("specialists","files","allowed_hosts"):
            value=row[key]
            if type(value) is not list or not value or len(value)!=len(set(map(str,value))):
                raise ValueError("INVALID_CONNECTOR_LIST")
            if not all(type(v) is str and v and len(v)<180 for v in value):
                raise ValueError("INVALID_CONNECTOR_LIST_VALUE")
        if not set(row["specialists"])<=roles:
            raise ValueError("UNKNOWN_SPECIALIST")
        if "SKILL.md" not in row["files"]:
            raise ValueError("MISSING_SKILL_FILE")
        for f in row["files"]:
            if not all(part and part not in (".","..") for part in f.split("/")) or "\\" in f or ":" in f or f.startswith("/"):
                raise ValueError("UNSAFE_MANIFEST_PATH")
        for host in row["allowed_hosts"]:
            if "://" in host or re.match(r"^[a-z]+:",host,re.I) or any(ord(ch)<32 or ord(ch)==127 for ch in host):
                raise ValueError("INVALID_ALLOWED_HOST")
        if row["setup_guide"]!=f"https://github.com/{REPO}/blob/{PIN}/INSTALL.md":
            raise ValueError("INSTALL_PIN_MISMATCH")
        if "credentials" not in row["setup_prompt"].lower() or "approval" not in row["setup_prompt"].lower():
            raise ValueError("UNSAFE_SETUP_PROMPT")
    if rows!=sorted(rows,key=lambda r:r["id"]):
        raise ValueError("CONNECTOR_ORDER_UNSTABLE")
    return doc

def load_catalog()->dict:
    doc=json.loads((DIRECTORY/"catalog.json").read_bytes(),parse_constant=lambda _ :(_ for _ in ()).throw(ValueError("NONFINITE")))
    return validate_catalog(doc)

def check()->dict:
    doc=load_catalog()
    proof=json.loads((DIRECTORY/"PROVENANCE.json").read_bytes())
    if proof.get("connector_count")!=151 or proof.get("source_commit")!=PIN or proof.get("source_repository")!=REPO:
        raise ValueError("PROVENANCE_CONFLICT")
    if proof.get("connector_code_vendored") is not False or proof.get("upstream_code_executed") is not False:
        raise ValueError("AUTHORITY_MISREPRESENTED")
    files=proof.get("distributed_files")
    if type(files) is not dict or len(files)<4:
        raise ValueError("INCOMPLETE_FILE_INTEGRITY")
    for key,digest in files.items():
        if type(key) is not str or not key.startswith("docs/connectors/") or ".." in key or type(digest) is not str or not SHA.fullmatch(digest):
            raise ValueError("INVALID_PROVENANCE_PATH")
        if not (ROOT/key).is_file() or _sha((ROOT/key).read_bytes())!=digest:
            raise ValueError("DISTRIBUTED_HASH_MISMATCH")
    upstream=(DIRECTORY/"upstream-catalog.json").read_bytes()
    if _sha(upstream)!=doc["source"]["catalog_sha256"]:
        raise ValueError("UPSTREAM_HASH_MISMATCH")
    rows=json.loads(upstream)
    if len(rows)!=151 or {r["id"] for r in rows}!={r["id"] for r in doc["connectors"]}:
        raise ValueError("UPSTREAM_CATALOG_MISMATCH")
    manifest=json.loads((DIRECTORY/"SOURCE_RECORDS.json").read_bytes())
    source_by_id={v["path"].split("/")[1]:v for v in manifest["documents"]}
    if len(source_by_id)!=151:
        raise ValueError("SOURCE_RECORD_COUNT")
    for r in doc["connectors"]:
        rec=source_by_id[r["id"]]
        if rec["sha256"]!=r["source_sha256"] or rec["git_blob"]!=r["source_git_blob"]:
            raise ValueError("SOURCE_RECORD_CONFLICT")
        if sorted(x["path"].rsplit("/",2)[-1] if "/" not in x["path"].replace("connectors/"+r["id"]+"/","") else x["path"].replace("connectors/"+r["id"]+"/","") for x in rec["files"])!=sorted(r["files"]):
            raise ValueError("SOURCE_FILE_MANIFEST_CONFLICT")
    if "muse-connectors contributors" not in (DIRECTORY/"UPSTREAM_LICENSE.txt").read_text(encoding="utf8"):
        raise ValueError("MISSING_UPSTREAM_ATTRIBUTION")
    if any(not (DIRECTORY/name).is_file() for name in FILES):
        raise ValueError("INCOMPLETE_DIRECTORY")
    return {"status":"CONNECTOR_CATALOG_VERIFIED","connectors":151,
            "categories":len({r["category"] for r in doc["connectors"]}),
            "specialist_roles":len(_roles()),"source_commit":PIN,
            "connector_code_executed":False,"external_effects":False}

def compare_catalogs(old:dict,new:dict)->dict:
    older={r["id"]:r for r in old["connectors"]}
    newer={r["id"]:r for r in new["connectors"]}
    return {"added":sorted(newer.keys()-older.keys()),"removed":sorted(older.keys()-newer.keys()),
            "changed":sorted(k for k in old_keys_and(newer,older) if older[k]!=newer[k]),"applied":False}

def old_keys_and(a,b):
    return a.keys()&b.keys()

def compare_upstream(candidate:Path)->dict:
    path=Path(candidate)
    if not path.is_file() or path.stat().st_size>2_000_000 or path.is_symlink():
        raise ValueError("UNSAFE_CANDIDATE")
    rows=json.loads(path.read_bytes())
    if type(rows) is not list or len(rows)>500 or not all(type(v) is dict and type(v.get("id")) is str and ID.fullmatch(v["id"]) for v in rows):
        raise ValueError("INVALID_UPSTREAM_CANDIDATE")
    if len(set(r["id"] for r in rows))!=len(rows):
        raise ValueError("DUPLICATE_SOURCE_IDS")
    current=json.loads((DIRECTORY/"upstream-catalog.json").read_bytes())
    a={r["id"]:r for r in current};b={r["id"]:r for r in rows}
    return {"added":sorted(b.keys()-a.keys()),"removed":sorted(a.keys()-b.keys()),
            "changed":sorted(k for k in a.keys()&b.keys() if a[k]!=b[k]),
            "applied":False,"source_code_executed":False}

def export_catalog(destination:Path)->dict:
    result=check()
    p=Path(destination)
    if not p.is_absolute() or not p.parent.is_dir() or p.is_symlink() or ".." in p.parts:
        raise ValueError("UNSAFE_OUTPUT_PATH")
    contents={name:(DIRECTORY/name).read_bytes() for name in FILES}
    hashes={"connectors/"+name:_sha(raw) for name,raw in sorted(contents.items())}
    manifest={"schema":"muse-specialist-toolkit/connector-export-v1","source_commit":PIN,
              "connector_count":151,"files":hashes}
    with tempfile.TemporaryDirectory(dir=str(p.parent)) as td:
        stage=Path(td)/"catalog.zip"
        with zipfile.ZipFile(stage,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=8) as z:
            for name,raw in sorted(contents.items()):
                info=zipfile.ZipInfo("connectors/"+name,date_time=(2026,1,1,0,0,0))
                info.compress_type=zipfile.ZIP_DEFLATED
                info.external_attr=0o644<<16
                z.writestr(info,raw)
            z.writestr("MANIFEST.json",_canonical(manifest))
        with zipfile.ZipFile(stage) as z:
            if z.testzip() is not None or set(z.namelist())!=set(hashes)|{"MANIFEST.json"}:
                raise ValueError("PACKAGE_VERIFICATION_FAILED")
            for name,expected in hashes.items():
                if _sha(z.read(name))!=expected:raise ValueError("PACKAGE_HASH_MISMATCH")
        # Exclusive hard-link admission refuses a preexisting destination, no overwrite.
        os.link(stage,p)
    return dict(result,status="CONNECTOR_PACKAGE_EXPORTED",path=str(p),sha256=_sha(p.read_bytes()))

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest="action",required=True)
    sub.add_parser("check")
    ex=sub.add_parser("export");ex.add_argument("--to",required=True,type=Path)
    cp=sub.add_parser("compare");cp.add_argument("--candidate",required=True,type=Path)
    args=parser.parse_args(argv)
    try:
        data=check() if args.action=="check" else export_catalog(args.to) if args.action=="export" else compare_upstream(args.candidate)
        print(json.dumps(data,sort_keys=True,ensure_ascii=False));return 0
    except (ValueError,OSError,TypeError,KeyError,json.JSONDecodeError) as error:
        print(json.dumps({"status":"REFUSED","reason":type(error).__name__+":"+str(error)[:150]}));return 2

if __name__=="__main__":raise SystemExit(main())

"""Build a source-bound, create-only Muse Specialist Toolkit v1.0.0 release.

A build is an artifact candidate, not publication. Publishing needs exact-head CI
and GitHub release readback. No private source, models or native account effects.
"""
from __future__ import annotations
import argparse,hashlib,json,os,re,subprocess,sys,tempfile,zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
VERSION="v1.0.0"
PREFIX="muse-specialist-toolkit-"+VERSION+"/"
SOURCE_ASSET="muse-specialist-toolkit-"+VERSION+".zip"
CONNECTOR_ASSET="muse-custom-connectors-"+VERSION+".zip"
COLLECTION_ASSET="muse-specialist-collection-"+VERSION+".zip"
MAX_PACKAGE_BYTES=50_000_000
SHA=re.compile("[0-9a-f]{40}\\Z")

def _digest(content:bytes)->str:
    return hashlib.sha256(content).hexdigest()

def make_checksums(files:dict[str,bytes])->dict[str,str]:
    if type(files) is not dict or not files:raise ValueError("NO_RELEASE_ASSETS")
    result={}
    for name,raw in files.items():
        if type(name) is not str or not re.fullmatch(r"[a-z0-9][a-z0-9_.-]*[.]zip",name):
            raise ValueError("INVALID_RELEASE_ASSET")
        if type(raw) is not bytes or not raw or len(raw)>MAX_PACKAGE_BYTES:
            raise ValueError("INVALID_RELEASE_BYTES")
        result[name]=_digest(raw)
    return dict(sorted(result.items()))

def _validate_files(files:dict[str,bytes])->None:
    if type(files) is not dict or not files or len(files)>800:
        raise ValueError("UNSAFE_PACKAGE_FILE_COUNT")
    total=0
    for name,raw in files.items():
        if (type(name) is not str or not name or name.startswith("/")
            or "\\" in name or ":" in name or
            any(part in ("",".","..") for part in name.split("/")) or
            type(raw) is not bytes or b"\0" in raw):
            raise ValueError("UNSAFE_PACKAGE_MEMBER")
        total+=len(raw)
        if len(raw)>2_000_000 or total>20_000_000:raise ValueError("PACKAGE_SIZE_BOUNDS")

def write_checked_zip(files:dict[str,bytes],destination:Path)->dict:
    _validate_files(files)
    path=Path(destination)
    if (not path.is_absolute() or not path.parent.is_dir() or path.is_symlink()
        or ".." in path.parts):raise ValueError("UNSAFE_OUTPUT_PATH")
    with tempfile.TemporaryDirectory(dir=path.parent) as directory:
        stage=Path(directory)/"release.zip"
        with zipfile.ZipFile(stage,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=8) as z:
            for name,raw in sorted(files.items()):
                info=zipfile.ZipInfo(name,date_time=(2026,1,1,0,0,0))
                info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o644<<16
                z.writestr(info,raw)
        with zipfile.ZipFile(stage) as z:
            if z.testzip() is not None or set(z.namelist())!=set(files):
                raise ValueError("PACKAGE_CRC_FAILED")
            for name,raw in files.items():
                if z.read(name)!=raw:raise ValueError("PACKAGE_CONTENT_MISMATCH")
        os.link(stage,path)
    return {"status":"CREATED","bytes":path.stat().st_size,"sha256":_digest(path.read_bytes())}

def _git(root:Path,*args:str)->str:
    p=subprocess.run(["git","-C",str(root),*args],capture_output=True,timeout=30)
    if p.returncode:raise ValueError("GIT_SOURCE_UNAVAILABLE")
    return p.stdout.decode("utf8").strip()

def verify_checkout(root:Path,expected_head:str)->dict:
    if type(expected_head) is not str or not SHA.fullmatch(expected_head):
        raise ValueError("SOURCE_HEAD_INVALID")
    actual=_git(root,"rev-parse","HEAD")
    if actual!=expected_head:raise ValueError("SOURCE_HEAD_CHANGED")
    dirty=_git(root,"status","--porcelain=v1","--untracked-files=all")
    if dirty:raise ValueError("SOURCE_DIRTY_REFUSE_RELEASE")
    manifest=json.loads((root/"PUBLIC_SOURCE_MANIFEST.json").read_bytes())
    from muse_presets.public_export import select_public_files
    files=select_public_files(root)
    if len(files)!=manifest["source_file_count"]:raise ValueError("SOURCE_MANIFEST_COUNT")
    if {k:_digest(v) for k,v in files.items()}!=manifest["files"]:
        raise ValueError("SOURCE_MANIFEST_CONTENT")
    return {"head":actual,"tree":_git(root,"rev-parse","HEAD^{tree}"),"source_files":len(files)}

def _run(root:Path,command:list[str])->str:
    env=dict(os.environ,PYTHONPATH=str(root/"src"),PYTHONIOENCODING="utf8")
    p=subprocess.run(command,cwd=root,env=env,capture_output=True,timeout=180)
    if p.returncode:raise ValueError("RELEASE_SUBPROCESS_FAILED:"+Path(command[2]).name+":"+p.stderr.decode("utf8","replace")[-200:])
    return p.stdout.decode("utf8","replace")

def _source_archive(root:Path,path:Path)->dict:
    p=subprocess.run(["git","-C",str(root),"archive","--format=zip",
                      "--prefix="+PREFIX,"HEAD"],capture_output=True,timeout=60)
    if p.returncode or not p.stdout:raise ValueError("GIT_ARCHIVE_FAILED")
    with tempfile.TemporaryDirectory(dir=path.parent) as d:
        stage=Path(d)/"source.zip";stage.write_bytes(p.stdout)
        manifest=json.loads((root/"PUBLIC_SOURCE_MANIFEST.json").read_bytes())
        with zipfile.ZipFile(stage) as z:
            if z.testzip():raise ValueError("SOURCE_ARCHIVE_CRC")
            members={name[len(PREFIX):] for name in z.namelist() if name.startswith(PREFIX) and not name.endswith("/")}
            if members!=set(manifest["files"])|{"PUBLIC_SOURCE_MANIFEST.json"}:
                raise ValueError("SOURCE_ARCHIVE_MEMBERS")
            for name,digest in manifest["files"].items():
                if _digest(z.read(PREFIX+name))!=digest:raise ValueError("SOURCE_ARCHIVE_DIGEST")
        os.link(stage,path)
    return {"files_verified":manifest["source_file_count"],"bytes":path.stat().st_size,
            "sha256":_digest(path.read_bytes())}

def build_release(root:Path,target:Path,expected_head:str)->dict:
    root=Path(root);target=Path(target)
    state=verify_checkout(root,expected_head)
    if not target.is_absolute() or not target.parent.is_dir() or target.exists() or ".." in target.parts:
        raise ValueError("OUTPUT_MUST_BE_NEW_ABSOLUTE_DIRECTORY")
    _run(root,[sys.executable,"-B","scripts/check_public.py"])
    _run(root,[sys.executable,"-B","scripts/connector_catalog.py","check"])
    # Admission is complete before creating the release directory.
    target.mkdir()
    source=_source_archive(root,target/SOURCE_ASSET)
    _run(root,[sys.executable,"-B","scripts/connector_catalog.py","export","--to",str(target/CONNECTOR_ASSET)])
    _run(root,[sys.executable,"-B","examples/export_specialist_collection.py","--to",str(target/COLLECTION_ASSET)])
    assets={name:(target/name).read_bytes() for name in (SOURCE_ASSET,CONNECTOR_ASSET,COLLECTION_ASSET)}
    checks=make_checksums(assets)
    sums="".join(digest+"  "+name+"\n" for name,digest in checks.items())
    (target/"SHA256SUMS.txt").write_text(sums,encoding="ascii",newline="\n")
    note=root/"docs/v1/RELEASE_NOTES.md"
    if not note.is_file():raise ValueError("MISSING_REVIEWED_RELEASE_NOTES")
    (target/"RELEASE_NOTES.md").write_bytes(note.read_bytes())
    for name,digest in checks.items():
        if _digest((target/name).read_bytes())!=digest:raise ValueError("ASSET_READBACK_FAILED")
        with zipfile.ZipFile(target/name) as z:
            if z.testzip():raise ValueError("ASSET_ZIP_CRC")
    result={"status":"V1_RELEASE_CANDIDATE_BUILT","source":state,"assets":checks,
            "source_archive":source,"release_tag_published":False,
            "native_installation":False,"external_accounts_changed":False}
    (target/"BUILD_RECEIPT.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",
                                              encoding="utf8",newline="\n")
    return result

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--to",required=True,type=Path)
    parser.add_argument("--expected-head",required=True)
    args=parser.parse_args(argv)
    try:
        result=build_release(ROOT,args.to,args.expected_head)
        print(json.dumps(result,sort_keys=True));return 0
    except (ValueError,OSError,TypeError,KeyError,zipfile.BadZipFile) as exc:
        print(json.dumps({"status":"REFUSED","reason":type(exc).__name__+":"+str(exc)[:240]}));return 2

if __name__=="__main__":raise SystemExit(main())

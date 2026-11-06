"""Create-only, offline Software Engineer runtime and profile stager.

No platform credentials, native Muse API, model call, external execution,
scheduler registration or existing user state is read or mutated.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat

from .catalog import ROOT,render_preset

PACK_ROOT=ROOT/"presets"/"software-engineer"
ENGINE_ROOT=PACK_ROOT/"runtime"/"claim-gate"
ENGINE_MANIFEST=ENGINE_ROOT/"ENGINE.json"
SKILL_ROOT=PACK_ROOT/"skills"/"claim-gate"
RUNTIME_FILES=frozenset({
    "claim_gate.py","gate_retention.py","distributed_claim_gate.py",
    "gate_token_guard.py","gate_approval.py","gate_composite.py",
    "gate_admission.py","gate_restart.py","engineering_claim_gate.py",
})
SKILL_FILES=frozenset({"SKILL.md","skill.yaml"})
HEX=re.compile(r'^[0-9a-f]{64}$')


def _sha(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()


def _bytes(path:Path,*,limit:int=300_000)->bytes:
    if path.is_symlink() or not path.is_file():
        raise ValueError('SOURCE_SYMLINK_OR_UNAVAILABLE')
    info=path.lstat()
    if not stat.S_ISREG(info.st_mode) or not 0 < info.st_size <= limit:
        raise ValueError('SOURCE_SIZE_OR_TYPE_REFUSED')
    return path.read_bytes()


def _manifest()->tuple[dict,dict[str,str]]:
    if ENGINE_ROOT.is_symlink() or SKILL_ROOT.is_symlink():
        raise ValueError('SOURCE_SYMLINK_OR_UNAVAILABLE')
    spec=json.loads(_bytes(ENGINE_MANIFEST,limit=20000))
    if not isinstance(spec,dict) or spec.get('schema')!='software-engineer/claim-gate-runtime-v1':
        raise ValueError('SOURCE_MANIFEST_INVALID')
    if (spec.get('role_id')!='software-engineer' or
        spec.get('native_muse_status')!='UNBOUND' or
        spec.get('external_effects_enabled') is not False or
        spec.get('original_owner_state_included') is not False or
        spec.get('registered_native_tools')!=[]):
        raise ValueError('SOURCE_MANIFEST_INVALID')
    listed=spec.get('files')
    if not isinstance(listed,dict) or set(listed)!=RUNTIME_FILES:
        raise ValueError('SOURCE_MANIFEST_INVALID')
    if any(type(value)is not str or not HEX.fullmatch(value) for value in listed.values()):
        raise ValueError('SOURCE_MANIFEST_INVALID')
    actual={p.name for p in ENGINE_ROOT.iterdir()
            if not (p.name=='__pycache__' and p.is_dir() and not p.is_symlink())}
    if actual != RUNTIME_FILES|{'ENGINE.json'}:
        raise ValueError('SOURCE_FILE_SET_MISMATCH')
    skills={p.name for p in SKILL_ROOT.iterdir()}
    if skills != SKILL_FILES:
        raise ValueError('SOURCE_FILE_SET_MISMATCH')
    for name,expected in listed.items():
        if _sha(_bytes(ENGINE_ROOT/name))!=expected:
            raise ValueError('SOURCE_PIN_MISMATCH')
    skill_pins=spec.get('skills')
    if (not isinstance(skill_pins,dict) or set(skill_pins)!=SKILL_FILES or
        any(type(value)is not str or not HEX.fullmatch(value)
            for value in skill_pins.values())):
        raise ValueError('SOURCE_MANIFEST_INVALID')
    for name in SKILL_FILES:
        if _sha(_bytes(SKILL_ROOT/name))!=skill_pins[name]:
            raise ValueError('SOURCE_PIN_MISMATCH')
    return spec,listed


def preview_engineer_pack()->dict:
    spec,files=_manifest()
    return {
        'status':'LOCAL_ENGINE_SOURCE_VERIFIED',
        'role_id':'software-engineer',
        'runtime_modules':len(files),
        'runtime_platform':'POSIX_FCNTL',
        'platform_execution_supported':os.name=='posix',
        'native_muse_status':'UNBOUND',
        'native_installed':False,
        'source_owner_authenticated':False,
        'external_effect_authorized':False,
        'schedulers_enabled':False,
        'source_manifest_sha256':_sha(_bytes(ENGINE_MANIFEST)),
    }


def _require_new(destination:Path)->Path:
    destination=Path(destination)
    if destination.exists() or destination.is_symlink():
        raise FileExistsError('DESTINATION_EXISTS_REFUSING_OVERWRITE')
    if not destination.parent.is_dir() or destination.parent.is_symlink():
        raise ValueError('DESTINATION_PARENT_NOT_ADMITTED')
    if destination.name in ('','.','..'):
        raise ValueError('DESTINATION_INVALID')
    return destination


def _write_new(path:Path,raw:bytes)->None:
    if path.exists() or path.is_symlink():
        raise FileExistsError('DESTINATION_EXISTS_REFUSING_OVERWRITE')
    with path.open('xb') as out:
        out.write(raw)
        out.flush()
        os.fsync(out.fileno())
    if _sha(path.read_bytes())!=_sha(raw):
        raise ValueError('COPY_READBACK_MISMATCH')


def stage_engineer_pack(destination:Path)->dict:
    spec,runtime_pins=_manifest()  # no disk writes before source pin check
    dest=_require_new(Path(destination))
    dest.mkdir(exist_ok=False)
    # No automatic cleanup on failure: if another writer touches the newly
    # created destination, do not destroy their unknown edits.
    (dest/'STAGING_INCOMPLETE').write_text(
        'A source-only staging operation did not finish. Do not activate.\n',
        encoding='utf-8')
    render_preset('software-engineer',dest/'profile')
    target=dest/'runtime'/'claim-gate'
    target.mkdir(parents=True)
    for name in sorted(RUNTIME_FILES):
        _write_new(target/name,_bytes(ENGINE_ROOT/name))
        if _sha((target/name).read_bytes())!=runtime_pins[name]:
            raise ValueError('SOURCE_PIN_MISMATCH')
    _write_new(target/'ENGINE.json',_bytes(ENGINE_MANIFEST,limit=20000))
    skills=dest/'skills'/'claim-gate'
    skills.mkdir(parents=True)
    for name in sorted(SKILL_FILES):
        _write_new(skills/name,_bytes(SKILL_ROOT/name))
    receipts=dest/'receipts'
    receipts.mkdir()
    data={}
    for folder in (dest/'profile',target,skills):
        for file in folder.iterdir():
            if file.is_symlink() or not file.is_file():
                raise ValueError('STAGED_MEMBER_INVALID')
            data[file.relative_to(dest).as_posix()]=_sha(file.read_bytes())
    result={
        'schema':'software-engineer/pack-v1',
        'role_id':'software-engineer',
        'source_manifest_sha256':_sha(_bytes(ENGINE_MANIFEST)),
        'files_sha256':dict(sorted(data.items())),
        'native_muse_status':'UNBOUND',
        'installed_native_tools':[],
        'native_installed':False,
        'external_effect_authorized':False,
        'schedulers_enabled':False,
        'profile_owner_memory_imported':False,
        'platform_execution_supported':os.name=='posix',
        'local_source_custody_verified':True,
        'evidence_grade':'LOCAL_FILE_STAGE_NOT_NATIVE_PROOF',
    }
    _write_new(receipts/'PACK_RECEIPT.json',
               (json.dumps(result,indent=2,sort_keys=True)+'\n').encode('utf-8'))
    (dest/'STAGING_INCOMPLETE').unlink()
    return {
        'status':'LOCAL_ENGINE_PACK_STAGED',
        'role_id':'software-engineer',
        'runtime_modules':len(runtime_pins),
        'destination':str(dest),
        'native_installed':False,
        'external_effect_authorized':False,
        'schedulers_enabled':False,
        'platform_execution_supported':os.name=='posix',
    }


def inspect_engineer_pack(destination:Path)->dict:
    dest=Path(destination)
    if dest.is_symlink() or not dest.is_dir():
        raise ValueError('PACK_DIRECTORY_INVALID')
    marker=dest/'STAGING_INCOMPLETE'
    if marker.exists() or marker.is_symlink():
        return {'status':'INCOMPLETE_STAGE','native_installed':False}
    receipt=dest/'receipts'/'PACK_RECEIPT.json'
    data=json.loads(_bytes(receipt,limit=30000))
    if data.get('schema')!='software-engineer/pack-v1' or data.get('native_installed') is not False:
        raise ValueError('PACK_RECEIPT_INVALID')
    files=data.get('files_sha256')
    if not isinstance(files,dict) or len(files)<23 or not all(
        isinstance(p,str) and type(digest)is str and HEX.fullmatch(digest)
        for p,digest in files.items()):
        raise ValueError('PACK_RECEIPT_INVALID')
    owner_modified=[];policy_modified=[];missing=[]
    for relative,pin in files.items():
        p=Path(relative)
        if p.is_absolute() or '..' in p.parts or len(p.parts)<2:
            raise ValueError('PACK_RECEIPT_PATH_INVALID')
        file=dest/p
        if file.is_symlink():raise ValueError('STAGED_SYMLINK_REFUSED')
        if not file.is_file():
            missing.append(relative)
        elif _sha(file.read_bytes())!=pin:
            if relative.startswith('profile/') and p.name not in (
                'FAMILY_LINK.json','ROLE_PLAYBOOK.md','RECEIPT.json'):
                owner_modified.append(relative)
            else:
                policy_modified.append(relative)
    if missing or policy_modified:
        status='REVIEW_REQUIRED'
    elif owner_modified:
        status='OWNER_CUSTOMIZED'
    else:
        status='LOCAL_MATCH'
    return {
        'status':status,
        'role_id':'software-engineer',
        'owner_modified':sorted(owner_modified),
        'policy_modified':sorted(policy_modified),
        'missing':sorted(missing),
        'native_installed':False,
        'external_effect_authorized':False,
    }


def main(argv:list[str] | None=None)->int:
    ap=argparse.ArgumentParser(description='Create-only local Software Engineer pack stager')
    ap.add_argument('--to',required=True,type=Path)
    args=ap.parse_args(argv)
    try:
        result=stage_engineer_pack(args.to)
        print(json.dumps(result,indent=2,sort_keys=True))
        return 0
    except (OSError,ValueError,KeyError) as error:
        print(json.dumps({'status':'REFUSED','reason':str(error),
                          'native_installed':False,'external_effect_authorized':False},
                         sort_keys=True))
        return 2


if __name__=='__main__':
    raise SystemExit(main())

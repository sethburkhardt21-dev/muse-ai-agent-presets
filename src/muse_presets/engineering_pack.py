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
import sys

from .catalog import ROOT,render_preset,DOCUMENTS

PACK_ROOT=ROOT/"presets"/"software-engineer"
ENGINE_ROOT=PACK_ROOT/"runtime"/"claim-gate"
ENGINE_MANIFEST=ENGINE_ROOT/"ENGINE.json"
SKILL_ROOT=PACK_ROOT/"skills"/"claim-gate"
VAULT_ROOT=PACK_ROOT/"runtime"/"provenance-vault"
VAULT_MANIFEST=VAULT_ROOT/"ENGINE.json"
VAULT_SOURCE=ROOT/"src"/"muse_presets"/"provenance_vault.py"
VAULT_SKILL_ROOT=PACK_ROOT/"skills"/"provenance-vault"
IRON_ROOT=PACK_ROOT/"runtime"/"iron-ledger"
IRON_MANIFEST=IRON_ROOT/"ENGINE.json"
IRON_SOURCE=ROOT/"src"/"muse_presets"/"iron_ledger_consumer.py"
IRON_SKILL_ROOT=PACK_ROOT/"skills"/"iron-ledger"
RUNTIME_FILES=frozenset({
    "claim_gate.py","gate_retention.py","distributed_claim_gate.py",
    "gate_token_guard.py","gate_approval.py","gate_composite.py",
    "gate_admission.py","gate_restart.py","engineering_claim_gate.py",
    "portable_lock.py","engineering_workflow.py","workflow_worker.py",
})
SKILL_FILES=frozenset({"SKILL.md","skill.yaml"})
PROFILE_FILES=frozenset((*DOCUMENTS,"FAMILY_LINK.json",
                          "RECEIPT.json","ROLE_PLAYBOOK.md"))
HEX=re.compile(r'^[0-9a-f]{64}$')


def _admitted_path(path:Path,*,must_exist:bool=True)->Path:
    """No arbitrary link/junction ancestors; only known macOS root aliases.

    This is local path admission, NOT authentication of an owner-approved root.
    """
    candidate=Path(path)
    if ".." in candidate.parts:
        raise ValueError('PATH_TRAVERSAL_REFUSED')
    candidate=candidate.absolute()
    for part in (candidate,*candidate.parents):
        if part.is_symlink() or (
            hasattr(part,'is_junction') and part.is_junction()):
            known_macos_alias=(sys.platform=='darwin' and
                str(part) in ('/var','/tmp','/etc') and
                str(part.resolve(strict=True))==
                    {'/var':'/private/var','/tmp':'/private/tmp',
                     '/etc':'/private/etc'}[str(part)])
            if not known_macos_alias:
                raise ValueError('SYMLINK_OR_JUNCTION_ANCESTOR_REFUSED')
    if must_exist and not candidate.exists():
        raise ValueError('PATH_UNAVAILABLE')
    return candidate


def _sha(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()


def _bytes(path:Path,*,limit:int=300_000)->bytes:
    _admitted_path(path)
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
        spec.get('registered_native_tools')!=[] or
        spec.get('portable_windows_runtime') is not True):
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


def _vault_manifest()->dict:
    """Validate portable Vault module and skill pins before any install writes."""
    if any(p.is_symlink() for p in (VAULT_ROOT, VAULT_SOURCE, VAULT_SKILL_ROOT)):
        raise ValueError('SOURCE_SYMLINK_OR_UNAVAILABLE')
    spec=json.loads(_bytes(VAULT_MANIFEST,limit=20000))
    if (not isinstance(spec,dict) or
        spec.get('schema')!='software-engineer/provenance-vault-runtime-v1' or
        spec.get('role_id')!='software-engineer' or
        spec.get('native_muse_status')!='UNBOUND' or
        spec.get('external_effects_enabled') is not False or
        spec.get('registered_native_tools')!=[] or
        spec.get('original_owner_state_included') is not False or
        spec.get('redistribution_rights_verified') is not False or
        spec.get('local_evidence_only') is not True):
        raise ValueError('SOURCE_MANIFEST_INVALID')
    files=spec.get('files')
    if not isinstance(files,dict) or set(files)!={'provenance_vault.py'}:
        raise ValueError('SOURCE_MANIFEST_INVALID')
    skills=spec.get('skills')
    if not isinstance(skills,dict) or set(skills)!=SKILL_FILES:
        raise ValueError('SOURCE_MANIFEST_INVALID')
    pins=list(files.values())+list(skills.values())
    if any(type(digest)is not str or not HEX.fullmatch(digest) for digest in pins):
        raise ValueError('SOURCE_MANIFEST_INVALID')
    if {p.name for p in VAULT_ROOT.iterdir()}!={'ENGINE.json'}:
        raise ValueError('SOURCE_FILE_SET_MISMATCH')
    if {p.name for p in VAULT_SKILL_ROOT.iterdir()}!=SKILL_FILES:
        raise ValueError('SOURCE_FILE_SET_MISMATCH')
    if _sha(_bytes(VAULT_SOURCE))!=files['provenance_vault.py']:
        raise ValueError('SOURCE_PIN_MISMATCH')
    for name in SKILL_FILES:
        if _sha(_bytes(VAULT_SKILL_ROOT/name))!=skills[name]:
            raise ValueError('SOURCE_PIN_MISMATCH')
    return spec


def _iron_manifest()->dict:
    """Check read-only Iron Ledger consumer and skill pins before writes."""
    if any(x.is_symlink() for x in (
        IRON_ROOT,IRON_SOURCE,IRON_SKILL_ROOT)):
        raise ValueError('SOURCE_SYMLINK_OR_UNAVAILABLE')
    spec=json.loads(_bytes(IRON_MANIFEST,limit=20000))
    if (not isinstance(spec,dict) or
        spec.get('schema')!='software-engineer/iron-ledger-consumer-runtime-v1' or
        spec.get('role_id')!='software-engineer' or
        spec.get('native_muse_status')!='UNBOUND' or
        spec.get('external_effects_enabled') is not False or
        spec.get('registered_native_tools')!=[] or
        spec.get('original_owner_state_included') is not False or
        spec.get('redistribution_rights_verified') is not False or
        spec.get('local_evidence_only') is not True or
        spec.get('second_persistent_evidence_ledger_created') is not False or
        spec.get('original_task_claims_enabled') is not False):
        raise ValueError('SOURCE_MANIFEST_INVALID')
    files=spec.get('files')
    if not isinstance(files,dict) or set(files)!={'iron_ledger_consumer.py'}:
        raise ValueError('SOURCE_MANIFEST_INVALID')
    skills=spec.get('skills')
    if not isinstance(skills,dict) or set(skills)!=SKILL_FILES:
        raise ValueError('SOURCE_MANIFEST_INVALID')
    if any(type(pin) is not str or not HEX.fullmatch(pin)
           for pin in list(files.values())+list(skills.values())):
        raise ValueError('SOURCE_MANIFEST_INVALID')
    if {x.name for x in IRON_ROOT.iterdir()}!={'ENGINE.json'}:
        raise ValueError('SOURCE_FILE_SET_MISMATCH')
    if {x.name for x in IRON_SKILL_ROOT.iterdir()}!=SKILL_FILES:
        raise ValueError('SOURCE_FILE_SET_MISMATCH')
    if _sha(_bytes(IRON_SOURCE))!=files['iron_ledger_consumer.py']:
        raise ValueError('SOURCE_PIN_MISMATCH')
    for name in SKILL_FILES:
        if _sha(_bytes(IRON_SKILL_ROOT/name))!=skills[name]:
            raise ValueError('SOURCE_PIN_MISMATCH')
    return spec


def _frozen_policy_payloads(
    spec:dict, runtime_pins:dict[str,str],
    vault_spec:dict, iron_spec:dict,
)->dict[str,bytes]:
    """Take a validated snapshot BEFORE creating any destination.

    Re-read every approved executable, runtime manifest and skill after
    preflight, check its original pin/policy and use ONLY these frozen bytes
    when staging. Concurrent source changes cannot be blessed by a receipt
    constructed from newly changed policy bytes. This is local pin
    continuity, not a signed publisher identity.
    """
    frozen:dict[str,bytes]={}

    def capture(relative:str,path:Path,pin:str,limit:int=300_000)->None:
        raw=_bytes(path,limit=limit)
        if _sha(raw)!=pin:
            raise ValueError('SOURCE_PIN_MISMATCH')
        frozen[relative]=raw

    def manifest(relative:str,path:Path,approved:dict)->None:
        raw=_bytes(path,limit=20_000)
        try:
            def unique_pairs(pairs):
                mapping={}
                for key,value in pairs:
                    if key in mapping:
                        raise ValueError('SOURCE_MANIFEST_DUPLICATE_KEY')
                    mapping[key]=value
                return mapping
            observed=json.loads(raw,object_pairs_hook=unique_pairs)
        except (ValueError,TypeError,UnicodeError) as exc:
            if str(exc)=='SOURCE_MANIFEST_DUPLICATE_KEY':
                raise
            raise ValueError('SOURCE_MANIFEST_CHANGED_AFTER_PREFLIGHT') from exc
        if observed!=approved:
            raise ValueError('SOURCE_MANIFEST_CHANGED_AFTER_PREFLIGHT')
        frozen[relative]=raw

    manifest('runtime/claim-gate/ENGINE.json',ENGINE_MANIFEST,spec)
    for name,pin in sorted(runtime_pins.items()):
        capture(f'runtime/claim-gate/{name}',ENGINE_ROOT/name,pin)
    for name,pin in sorted(spec['skills'].items()):
        capture(f'skills/claim-gate/{name}',SKILL_ROOT/name,pin)

    manifest('runtime/provenance-vault/ENGINE.json',
             VAULT_MANIFEST,vault_spec)
    capture('runtime/provenance-vault/provenance_vault.py',
            VAULT_SOURCE,vault_spec['files']['provenance_vault.py'])
    for name,pin in sorted(vault_spec['skills'].items()):
        capture(f'skills/provenance-vault/{name}',VAULT_SKILL_ROOT/name,pin)

    manifest('runtime/iron-ledger/ENGINE.json',
             IRON_MANIFEST,iron_spec)
    capture('runtime/iron-ledger/iron_ledger_consumer.py',
            IRON_SOURCE,iron_spec['files']['iron_ledger_consumer.py'])
    for name,pin in sorted(iron_spec['skills'].items()):
        capture(f'skills/iron-ledger/{name}',IRON_SKILL_ROOT/name,pin)
    return frozen


def preview_engineer_pack()->dict:
    spec,files=_manifest()
    vault=_vault_manifest()
    iron=_iron_manifest()
    frozen=_frozen_policy_payloads(spec,files,vault,iron)
    return {
        'status':'LOCAL_ENGINE_SOURCE_VERIFIED',
        'role_id':'software-engineer',
        'runtime_modules':len(files),
        'provenance_runtime_modules':len(vault['files']),
        'provenance_rights_verified':False,
        'iron_consumer_runtime_modules':len(iron['files']),
        'iron_ledger_rights_verified':False,
        'new_receipt_ledger_created':False,
        'runtime_platform':'PORTABLE_LOCAL_FILE_LOCK',
        'platform_execution_supported':os.name in ('nt','posix'),
        'native_muse_status':'UNBOUND',
        'native_installed':False,
        'source_owner_authenticated':False,
        'external_effect_authorized':False,
        'schedulers_enabled':False,
        'source_manifest_sha256':_sha(frozen['runtime/claim-gate/ENGINE.json']),
    }


def _require_new(destination:Path)->Path:
    destination=Path(destination)
    if destination.name in ('','.','..'):
        raise ValueError('DESTINATION_INVALID')
    if destination.exists() or destination.is_symlink() or (
            hasattr(destination,'is_junction') and destination.is_junction()):
        raise FileExistsError('DESTINATION_EXISTS_REFUSING_OVERWRITE')
    target=_admitted_path(destination,must_exist=False)
    if target.exists():
        raise FileExistsError('DESTINATION_EXISTS_REFUSING_OVERWRITE')
    if not target.parent.is_dir():
        raise ValueError('DESTINATION_PARENT_NOT_ADMITTED')
    _admitted_path(target.parent)
    return target


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
    spec,runtime_pins=_manifest()  # no disk writes before source pin checks
    vault_spec=_vault_manifest()
    iron_spec=_iron_manifest()
    frozen=_frozen_policy_payloads(spec,runtime_pins,vault_spec,iron_spec)
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
        _write_new(target/name,frozen[f'runtime/claim-gate/{name}'])
    _write_new(target/'ENGINE.json',frozen['runtime/claim-gate/ENGINE.json'])
    skills=dest/'skills'/'claim-gate'
    skills.mkdir(parents=True)
    for name in sorted(SKILL_FILES):
        _write_new(skills/name,frozen[f'skills/claim-gate/{name}'])
    vault_target=dest/'runtime'/'provenance-vault'
    vault_target.mkdir()
    _write_new(vault_target/'provenance_vault.py',
               frozen['runtime/provenance-vault/provenance_vault.py'])
    _write_new(vault_target/'ENGINE.json',
               frozen['runtime/provenance-vault/ENGINE.json'])
    vault_skills=dest/'skills'/'provenance-vault'
    vault_skills.mkdir()
    for name in sorted(SKILL_FILES):
        _write_new(vault_skills/name,frozen[f'skills/provenance-vault/{name}'])
    iron_target=dest/'runtime'/'iron-ledger'
    iron_target.mkdir()
    _write_new(iron_target/'iron_ledger_consumer.py',
               frozen['runtime/iron-ledger/iron_ledger_consumer.py'])
    _write_new(iron_target/'ENGINE.json',
               frozen['runtime/iron-ledger/ENGINE.json'])
    iron_skills=dest/'skills'/'iron-ledger'
    iron_skills.mkdir()
    for name in sorted(SKILL_FILES):
        _write_new(iron_skills/name,frozen[f'skills/iron-ledger/{name}'])
    for relative,original in frozen.items():
        if _sha(_bytes(dest/relative))!=_sha(original):
            raise ValueError('STAGED_SOURCE_PIN_MISMATCH')
    receipts=dest/'receipts'
    receipts.mkdir()
    data={}
    for folder in (dest/'profile',target,skills,vault_target,vault_skills,iron_target,iron_skills):
        for file in folder.iterdir():
            if file.is_symlink() or not file.is_file():
                raise ValueError('STAGED_MEMBER_INVALID')
            data[file.relative_to(dest).as_posix()]=_sha(file.read_bytes())
    result={
        'schema':'software-engineer/pack-v1',
        'role_id':'software-engineer',
        'source_manifest_sha256':_sha(frozen['runtime/claim-gate/ENGINE.json']),
        'provenance_manifest_sha256':_sha(frozen['runtime/provenance-vault/ENGINE.json']),
        'provenance_rights_verified':False,
        'iron_manifest_sha256':_sha(frozen['runtime/iron-ledger/ENGINE.json']),
        'iron_ledger_rights_verified':False,
        'new_receipt_ledger_created':False,
        'files_sha256':dict(sorted(data.items())),
        'native_muse_status':'UNBOUND',
        'installed_native_tools':[],
        'native_installed':False,
        'external_effect_authorized':False,
        'schedulers_enabled':False,
        'profile_owner_memory_imported':False,
        'platform_execution_supported':os.name in ('nt','posix'),
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
        'provenance_runtime_modules':len(vault_spec['files']),
        'iron_consumer_runtime_modules':len(iron_spec['files']),
        'destination':str(dest),
        'native_installed':False,
        'external_effect_authorized':False,
        'schedulers_enabled':False,
        'platform_execution_supported':os.name in ('nt','posix'),
    }


def _expected_pack_members()->dict[str,str | None]:
    """Exact staged paths, with independently verified source/policy pins.

    Only the owner-editable profile baseline is sourced from the local pack
    receipt. Runtime, engine manifests, and skills must match trusted source
    pins in the implementation checkout. A local checkout is NOT a signer.
    """
    claim,runtime=_manifest()
    vault=_vault_manifest()
    iron=_iron_manifest()
    expected={f'profile/{name}':None for name in PROFILE_FILES}
    expected.update({
        f'runtime/claim-gate/{name}':digest for name,digest in runtime.items()})
    expected['runtime/claim-gate/ENGINE.json']=_sha(_bytes(ENGINE_MANIFEST,limit=20000))
    expected.update({
        f'skills/claim-gate/{name}':claim['skills'][name] for name in SKILL_FILES})
    expected['runtime/provenance-vault/provenance_vault.py']=vault['files']['provenance_vault.py']
    expected['runtime/provenance-vault/ENGINE.json']=_sha(_bytes(VAULT_MANIFEST,limit=20000))
    expected.update({
        f'skills/provenance-vault/{name}':vault['skills'][name] for name in SKILL_FILES})
    expected['runtime/iron-ledger/iron_ledger_consumer.py']=iron['files']['iron_ledger_consumer.py']
    expected['runtime/iron-ledger/ENGINE.json']=_sha(_bytes(IRON_MANIFEST,limit=20000))
    expected.update({
        f'skills/iron-ledger/{name}':iron['skills'][name] for name in SKILL_FILES})
    return expected


def _pack_review_required(problem:str)->dict:
    return {
        'status':'REVIEW_REQUIRED',
        'role_id':'software-engineer',
        'owner_modified':[],
        'policy_modified':[problem],
        'missing':[],
        'native_installed':False,
        'external_effect_authorized':False,
    }


def inspect_engineer_pack(destination:Path)->dict:
    """Read-only, fail-closed closed-tree and independently source-pinned review.

    Owner-editable profile bytes remain customizable. Any added executable,
    unexpected directory, misleading receipt, symlink or junction is denied.
    """
    dest=_admitted_path(destination)
    if not dest.is_dir():
        raise ValueError('PACK_DIRECTORY_INVALID')
    marker=dest/'STAGING_INCOMPLETE'
    if marker.exists() or marker.is_symlink():
        return {'status':'INCOMPLETE_STAGE','native_installed':False}

    receipt=dest/'receipts'/'PACK_RECEIPT.json'
    data=json.loads(_bytes(receipt,limit=30000))
    receipt_keys={
        'schema','role_id','source_manifest_sha256','provenance_manifest_sha256',
        'provenance_rights_verified','iron_manifest_sha256','iron_ledger_rights_verified',
        'new_receipt_ledger_created','files_sha256','native_muse_status',
        'installed_native_tools','native_installed','external_effect_authorized',
        'schedulers_enabled','profile_owner_memory_imported','platform_execution_supported',
        'local_source_custody_verified','evidence_grade'}
    if (type(data) is not dict or set(data)!=receipt_keys or
        data['schema']!='software-engineer/pack-v1' or
        data['role_id']!='software-engineer' or
        data['native_muse_status']!='UNBOUND' or
        data['installed_native_tools']!=[] or
        data['evidence_grade']!='LOCAL_FILE_STAGE_NOT_NATIVE_PROOF' or
        data['local_source_custody_verified'] is not True or
        type(data['platform_execution_supported']) is not bool or
        any(data[key] is not False for key in (
            'provenance_rights_verified','iron_ledger_rights_verified',
            'new_receipt_ledger_created','native_installed',
            'external_effect_authorized','schedulers_enabled',
            'profile_owner_memory_imported')) or
        data['source_manifest_sha256']!=_sha(_bytes(ENGINE_MANIFEST,limit=20000)) or
        data['provenance_manifest_sha256']!=_sha(_bytes(VAULT_MANIFEST,limit=20000)) or
        data['iron_manifest_sha256']!=_sha(_bytes(IRON_MANIFEST,limit=20000))):
        return _pack_review_required('receipts/PACK_RECEIPT.json')

    source_pins=_expected_pack_members()
    files=data['files_sha256']
    if (type(files) is not dict or set(files)!=set(source_pins) or
        any(type(v) is not str or HEX.fullmatch(v) is None
            for v in files.values())):
        return _pack_review_required('receipts/PACK_RECEIPT.json')

    directory_children={
        '':{'profile','runtime','skills','receipts'},
        'profile':PROFILE_FILES,
        'runtime':{'claim-gate','provenance-vault','iron-ledger'},
        'runtime/claim-gate':RUNTIME_FILES|{'ENGINE.json'},
        'runtime/provenance-vault':{'provenance_vault.py','ENGINE.json'},
        'runtime/iron-ledger':{'iron_ledger_consumer.py','ENGINE.json'},
        'skills':{'claim-gate','provenance-vault','iron-ledger'},
        'skills/claim-gate':SKILL_FILES,
        'skills/provenance-vault':SKILL_FILES,
        'skills/iron-ledger':SKILL_FILES,
        'receipts':{'PACK_RECEIPT.json'},
    }
    policy_modified=[]
    missing=[]
    for relative,expected in directory_children.items():
        try:
            folder=_admitted_path(dest/relative) if relative else dest
        except ValueError:
            if relative.startswith(('runtime/','skills/')):
                return _pack_review_required(relative)
            raise
        if not folder.is_dir():
            return _pack_review_required(relative or 'root')
        actual={p.name for p in folder.iterdir()}
        missing.extend(f'{relative}/{name}'.lstrip('/')
                       for name in sorted(expected-actual))
        policy_modified.extend(f'{relative}/{name}'.lstrip('/')
                               for name in sorted(actual-expected))
        for child in folder.iterdir():
            try:
                _admitted_path(child)
            except ValueError:
                if child.relative_to(dest).parts[0] in ('runtime','skills'):
                    return _pack_review_required(child.relative_to(dest).as_posix())
                raise
    owner_modified=[]
    for relative,source_pin in sorted(source_pins.items()):
        file=dest/relative
        if not file.exists():
            if relative not in missing:
                missing.append(relative)
            continue
        try:
            _admitted_path(file)
        except ValueError:
            if relative.startswith(('runtime/','skills/')):
                return _pack_review_required(relative)
            raise
        if not file.is_file() or not stat.S_ISREG(file.lstat().st_mode):
            raise ValueError('STAGED_MEMBER_INVALID')
        actual=_sha(_bytes(file))
        if (source_pin is not None and
            (files[relative]!=source_pin or actual!=source_pin)):
            policy_modified.append(relative)
        elif actual!=files[relative]:
            if relative.startswith('profile/') and file.name not in (
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
        'owner_modified':sorted(set(owner_modified)),
        'policy_modified':sorted(set(policy_modified)),
        'missing':sorted(set(missing)),
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

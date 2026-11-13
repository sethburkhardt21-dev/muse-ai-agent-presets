"""Create-only, standards-format text skills from the existing role/shared sources.

This adapter preserves native underscore IDs and never registers a host skill.
It emits a separate hyphen-named instruction library, not an executable agent.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
from .catalog import ROOT, load_registry
from .native_skill_binding import _regular_bytes, _unsafe_source_path
from .role_skills import _build as _role_build

MANIFEST='PORTABLE_SKILLS_MANIFEST.json'
NAME=re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
MAX_FILE_BYTES=262144

def _sha(raw:bytes)->str:return hashlib.sha256(raw).hexdigest()
def _json(value)->bytes:return (json.dumps(value,sort_keys=True,indent=2,ensure_ascii=False)+'\n').encode('utf-8')
def _unique(pairs):
    value={}
    for key,item in pairs:
        if key in value:raise ValueError('DUPLICATE_MANIFEST_KEY')
        value[key]=item
    return value

def _build():
    files={};sources={};mapping={};shared=set();methods=set()
    roles=load_registry()['presets']
    for role in roles:
        exported,receipt,frozen=_role_build(role,None)
        for path,raw in frozen.items():
            digest=_sha(raw)
            if path in sources and sources[path]!=digest:raise ValueError('SOURCE_CHANGED_DURING_PLAN')
            sources[path]=digest
        shared.update(receipt['shared_skill_ids']);methods.update(receipt['skill_ids'])
        for native_id in receipt['skill_ids']+receipt['shared_skill_ids']:
            raw=exported[f'custom-skills/{native_id}/SKILL.md'].decode('utf-8')
            if not raw.startswith('---\n') or '\n---\n' not in raw[4:]:raise ValueError('SKILL_FRONTMATTER_REQUIRED')
            header,body=raw[4:].split('\n---\n',1)
            meta={}
            for line in header.splitlines():
                key,sep,value=line.partition(': ')
                if not sep or key in meta:raise ValueError('INVALID_SOURCE_FRONTMATTER')
                meta[key]=value
            if meta.get('name')!=native_id:raise ValueError('SOURCE_SKILL_ID_MISMATCH')
            name=native_id.replace('_','-');description=meta.get('description','')
            if not NAME.fullmatch(name) or len(name)>64 or not 1<=len(description)<=1024:
                raise ValueError('PORTABLE_METADATA_LIMIT')
            if name in mapping and mapping[name]!=native_id:raise ValueError('PORTABLE_NAME_COLLISION')
            mapping[name]=native_id
            rendered=('---\nname: '+json.dumps(name)+'\ndescription: '
                      +json.dumps(description,ensure_ascii=False)+'\nlicense: "MIT"\n---\n'+body).encode('utf-8')
            member=name+'/SKILL.md'
            if member in files and files[member]!=rendered:raise ValueError('SHARED_SKILL_CONTENT_DIVERGENCE')
            files[member]=rendered
    # Freeze source methods as well as data. No donor code is executed or bundled.
    for relative in ['presets/catalog.json','src/muse_presets/role_skills.py',
                     'src/muse_presets/portable_skill_export.py','LICENSE']:
        sources[relative]=_sha(_regular_bytes(ROOT/relative,MAX_FILE_BYTES))
    files['LICENSE']=_regular_bytes(ROOT/'LICENSE',MAX_FILE_BYTES)
    files['README.md']=(
        '# Portable skill instructions\n\n'
        f'This library contains {len(mapping)} unique instruction skills: '
        f'{len(methods)} specialist methods and {len(shared)} shared procedures.\n\n'
        'Each folder has a hyphenated name matching its SKILL.md frontmatter. '
        'Native-style Muse descriptor IDs are preserved in the source repository; '
        'this export neither changes them nor writes a host skills.yaml.\n\n'
        'Inspect a skill, then use the receiving assistant\'s documented upload or '
        'file-reading flow. Start with one non-sensitive task and verify the actual '
        'result. A valid file format does not prove native registration, model '
        'selection, persistent memory or permission to call tools. No host is '
        'contacted or configured by this export. No donor memory is included.\n\n'
        'All local files are source instructions under the included MIT license; '
        'no original product runtimes or external scripts are bundled.\n').encode('utf-8')
    source_sha=_sha(_json(sources))
    receipt={'schema':'muse-presets/portable-skills-v1','source_pins':sources,
             'source_sha256':source_sha,'native_to_portable':{v:k for k,v in sorted(mapping.items())},
             'unique_skills':len(mapping),'role_methods':len(methods),'shared_skills':len(shared),
             'files':{p:_sha(b) for p,b in sorted(files.items())},'native_installed':False,
             'external_effect_authorized':False,'provider_registered':False,
             'grade':'PORTABLE_INSTRUCTION_FILES_ONLY'}
    return files,receipt

def plan_portable_skills()->dict:
    _,r=_build()
    return {'status':'SOURCE_PLAN_ONLY','source_sha256':r['source_sha256'],
            'skills':sorted(r['native_to_portable'].values()),
            'unique_skills':r['unique_skills'],'role_methods':r['role_methods'],
            'shared_skills':r['shared_skills'],'native_installed':False,
            'external_effect_authorized':False}

def stage_portable_skills(destination:Path,*,expected_source_sha256:str|None=None)->dict:
    dest=Path(destination)
    if _unsafe_source_path(dest):raise ValueError('UNSAFE_PORTABLE_DESTINATION')
    if dest.exists() or dest.is_symlink():raise FileExistsError('PORTABLE_DESTINATION_EXISTS')
    if not dest.parent.is_dir():raise FileNotFoundError('PORTABLE_PARENT_REQUIRED')
    files,receipt=_build()
    if expected_source_sha256 is not None and expected_source_sha256!=receipt['source_sha256']:
        raise ValueError('PORTABLE_SOURCE_PIN_MISMATCH')
    dest.mkdir(exist_ok=False)
    marker=dest/'STAGING_INCOMPLETE'
    with marker.open('xb') as f:f.write(b'INCOMPLETE_LOCAL_SOURCE_STAGE_NO_AUTO_RETRY\n')
    for name,body in sorted(files.items()):
        path=dest/name;path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('xb') as f:f.write(body)
    if _build()[1]!=receipt:raise ValueError('PORTABLE_SOURCE_CHANGED_DURING_STAGE')
    with (dest/MANIFEST).open('xb') as f:f.write(_json(receipt))
    marker.unlink()
    return {'status':'LOCAL_PORTABLE_SKILLS_STAGED','unique_skills':receipt['unique_skills'],
            'source_sha256':receipt['source_sha256'],'native_installed':False,
            'external_effect_authorized':False}

def inspect_portable_skills(destination:Path)->dict:
    dest=Path(destination)
    reject={'status':'REVIEW_REQUIRED','native_installed':False,'external_effect_authorized':False}
    try:
        if _unsafe_source_path(dest) or not dest.is_dir():return reject
        if (dest/'STAGING_INCOMPLETE').exists() or (dest/'STAGING_INCOMPLETE').is_symlink():
            return {**reject,'status':'INCOMPLETE_STAGE'}
        files,receipt=_build()
        raw=_regular_bytes(dest/MANIFEST,MAX_FILE_BYTES)
        claimed=json.loads(raw.decode('utf-8'),object_pairs_hook=_unique)
        if claimed!=receipt or raw!=_json(receipt):return reject
        expected_files=set(files)|{MANIFEST}
        expected_dirs={str(Path(x).parent).replace('\\','/') for x in files if '/' in x}
        actual_files=set();actual_dirs=set()
        for index,p in enumerate(dest.rglob('*')):
            if index>160 or _unsafe_source_path(p):return reject
            relative=p.relative_to(dest).as_posix()
            if p.is_dir():actual_dirs.add(relative)
            elif p.is_file():actual_files.add(relative)
            else:return reject
        if actual_files!=expected_files or actual_dirs!=expected_dirs:return reject
        for name,expected in files.items():
            if _regular_bytes(dest/name,MAX_FILE_BYTES)!=expected:return reject
        return {**reject,'status':'LOCAL_PORTABLE_SKILLS_MATCH','unique_skills':receipt['unique_skills'],
                'source_sha256':receipt['source_sha256']}
    except (OSError,ValueError,TypeError,KeyError,UnicodeError):return reject

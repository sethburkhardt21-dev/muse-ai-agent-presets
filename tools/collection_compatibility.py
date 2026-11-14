"""Read-only compatibility check for two preserved instruction collections.

Checks source consistency, not publisher identity, native installation or model
performance. This is not a registry writer, installer, dispatcher or new catalog.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('collection_source_reader',ROOT/'tools/muse_collection.py')
if SPEC is None or SPEC.loader is None:raise RuntimeError('COLLECTION_READER_UNAVAILABLE')
_collection=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(_collection)
read_json=_collection.read_json
HEX=re.compile(r'^[0-9a-f]{64}$')
SHA=re.compile(r'^[0-9a-f]{40}$')
ALIASES={'data-engineer':'data-engineering-architect','reliability-engineer':'infrastructure-reliability-engineer'}
SHARED={'evidence_audit','safe_resume','research_verification','consent_and_effects','quality_handoff'}

class CompatibilityError(ValueError):pass

def require(condition:bool,reason:str)->None:
    if not condition:raise CompatibilityError(reason)

def validate_mapping(value:dict,legacy_ids:set[str],canonical_ids:set[str])->None:
    fields={'schema','public_base','collection_skill_count','legacy_procedure_count',
      'combined_unique_capability_count','role_count','starter_configurations',
      'workflow_recipes','native_installation','model_comparisons','role_aliases','procedure_links'}
    require(type(value) is dict and set(value)==fields,'SCHEMA')
    require(value['schema']=='muse-collection-public-compatibility/v1','SCHEMA')
    require(type(value['public_base']) is str and bool(SHA.fullmatch(value['public_base'])),'SCHEMA')
    for key,n in [('collection_skill_count',75),('legacy_procedure_count',50),
                  ('role_count',15),('starter_configurations',100),('workflow_recipes',25)]:
        require(type(value[key]) is int and value[key]==n,'COUNT')
    require(value['combined_unique_capability_count'] is None,'COUNT')
    require(len(legacy_ids)==50 and len(canonical_ids)==75,'COUNT')
    require(value['native_installation']=='NOT_PERFORMED' and
            value['model_comparisons']=='NOT_PERFORMED_BY_THIS_PROMOTION','NATIVE')
    require(value['role_aliases']==ALIASES,'ALIAS')
    links=value['procedure_links']
    require(type(links) is list and len(links)==50,'LEGACY')
    keys={'legacy_id','role','method','disposition','related_collection_skills',
          'claims_behavioral_equivalence','reason'}
    seen=set()
    for row in links:
        require(type(row) is dict and set(row)==keys,'SCHEMA')
        sid=row['legacy_id'];require(type(sid) is str and sid in legacy_ids and sid not in seen,'LEGACY');seen.add(sid)
        require(row['claims_behavioral_equivalence'] is False,'EQUIVALENCE')
        disposition='KEEP_COMPATIBILITY' if sid in SHARED else 'KEEP_ROLE_METHOD'
        require(row['disposition']==disposition,'DISPOSITION')
        related=row['related_collection_skills']
        require(type(related) is list and 1<=len(related)<=5 and
                all(type(x) is str for x in related),'RELATED')
        require(len(related)==len(set(related)) and set(related)<=canonical_ids,'RELATED')
        require(type(row['reason']) is str and 20<=len(row['reason'])<=800,'REASON')
        require(type(row['role']) is str and type(row['method']) is str,'SCHEMA')
    require(seen==legacy_ids,'LEGACY')

def _relative(root:Path,name:str)->Path:
    require(type(name) is str and name and not name.startswith('/') and
            '\\' not in name and ':' not in name and
            all(x not in ('','.','..') for x in name.split('/')),'UNSAFE_PATH')
    p=root/name
    _collection._safe_path(p)
    require(p.resolve().is_relative_to(root.resolve()),'UNSAFE_PATH')
    return p

def _bytes(root:Path,name:str)->bytes:
    return _collection._bounded_source(_relative(root,name),2_000_000)

def _digest(raw:bytes)->str:return hashlib.sha256(raw).hexdigest()

def check_repository(root:Path=ROOT)->dict:
    root=Path(root)
    # Never execute modules from a caller-selected tree. The checked source must
    # be the tree containing this program; an extracted copy is checked in place.
    require(root.resolve()==ROOT.resolve(),'SOURCE_ROOT_MISMATCH')
    prefix='collections/muse-starters-v1/'
    data=_collection.load_collection(root/prefix)
    mapping=read_json(root/(prefix+'PUBLIC_COMPATIBILITY.json'))
    registry=read_json(root/'presets/catalog.json');roles=registry['presets']
    require(type(roles) is list and len(roles)==len(set(roles))==15,'ROLE_COUNT')
    source=str(root/'src')
    if source not in sys.path:sys.path.insert(0,source)
    from muse_presets.role_skills import skill_id,SHARED_SKILLS
    require(set(SHARED_SKILLS)==SHARED,'SHARED_IDS_CHANGED')
    expected={sid:('shared',sid) for sid in SHARED_SKILLS}
    for role in roles:
        book=read_json(_relative(root,'presets/'+role+'/playbook.json'))
        require(book['role_id']==role and len(book['methods'])==3,'ROLE_METHOD_COUNT')
        for method in book['methods']:
            sid=skill_id(role,method['id']);require(sid not in expected,'DUPLICATE_LEGACY')
            expected[sid]=(role,method['id'])
    validate_mapping(mapping,set(expected),{s['id'] for s in data['skills']})
    for row in mapping['procedure_links']:
        require((row['role'],row['method'])==expected[row['legacy_id']],'LEGACY_SOURCE_JOIN')
    baseline=read_json(root/(prefix+'PUBLIC_BASELINE.json'))
    require(baseline['schema']=='muse-collection-public-baseline/v1' and
            baseline['source_commit']==mapping['public_base'],'PUBLIC_BASELINE')
    require(type(baseline['files']) is dict and len(baseline['files'])==198,'PUBLIC_BASELINE')
    for name,h in baseline['files'].items():
        require(type(h) is str and bool(HEX.fullmatch(h)),'PUBLIC_BASELINE')
        require(_digest(_bytes(root,name))==h,'PUBLIC_SOURCE_DRIFT:'+name)
    provenance=read_json(root/(prefix+'PROMOTION_PROVENANCE.json'))
    require(set(provenance)=={'schema','source_kind','private_history_included','upstream_code_imported','scope','incoming_files'},'PROVENANCE_SCHEMA')
    require(provenance['schema']=='muse-collection-promotion/v1' and
            provenance['source_kind']=='OWNER_AUTHORIZED_FIRST_PARTY','PROVENANCE_KIND')
    require(provenance['private_history_included'] is False and
            provenance['upstream_code_imported'] is False,'PROVENANCE_AUTHORITY')
    rows=provenance['incoming_files'];require(type(rows) is dict and 1<=len(rows)<=750,'PROVENANCE_COUNT')
    for name,row in rows.items():
        require(type(row) is dict and set(row)=={'sha256','source_sha256','rights','disposition'},'PROVENANCE_SCHEMA')
        require(all(type(row[k]) is str and HEX.fullmatch(row[k]) for k in ['sha256','source_sha256']),'PROVENANCE_HASH')
        require(row['rights'] in {'PROJECT_MIT_ORIGINAL','REFERENCE_ONLY_PUBLIC_SOURCE_METADATA'},'PROVENANCE_RIGHTS')
        require(row['disposition'] in {'BYTE_PRESERVED','REVIEWED_PUBLIC_ADAPTATION'},'PROVENANCE_DISPOSITION')
        require(_digest(_bytes(root,name))==row['sha256'],'IMPORTED_SOURCE_DRIFT:'+name)
        if row['disposition']=='BYTE_PRESERVED':require(row['sha256']==row['source_sha256'],'PROVENANCE_HASH')
    return {'status':'COLLECTION_COMPATIBILITY_VERIFIED','role_count':15,
            'collection_skills':len(data['skills']),'legacy_procedures':len(expected),
            'combined_unique_capabilities':None,'starters':len(data['starters']),
            'workflows':len(data['workflows']),'preserved_public_files':len(baseline['files']),
            'incoming_files_verified':len(rows),'native_installed':False,
            'model_called':False,'external_effects':False,
            'proof_limit':'SOURCE_SELF_CONSISTENCY_NOT_PUBLISHER_IDENTITY_OR_BEHAVIORAL_EQUIVALENCE'}

def main(argv=None)->int:
    argparse.ArgumentParser(description=__doc__).parse_args(argv)
    try:
        print(json.dumps(check_repository(),sort_keys=True,indent=2));return 0
    except (ValueError,OSError,KeyError,TypeError,UnicodeError) as exc:
        print(json.dumps({'status':'REVIEW_REQUIRED','reason':str(exc),'native_installed':False}),file=sys.stderr);return 2

if __name__=='__main__':raise SystemExit(main())

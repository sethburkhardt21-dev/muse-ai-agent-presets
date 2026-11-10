"""Deterministic product-distribution checks, separate from agent execution.

These checks reject operational artifacts, broken documentation and stale
capability claims. They never publish, activate a provider or grant permission.
"""
from __future__ import annotations
import hashlib,json,os,re,tempfile
from pathlib import Path
from urllib.parse import unquote

IGNORED={'.git','__pycache__','.pytest_cache','.mypy_cache','.ruff_cache','.venv','venv'}
PRIVATE_DIRS={'control','.atlas','scratch','evidence','receipts','checkpoints'}
OLD_DOCS={'STATUS.md','GITHUB_ROLE_ACCEPTANCE.md','GITHUB_RELEASE_SCOPE.md',
 'CAPABILITY_FIT_AUDIT.md','RELEASE_CHECKLIST.md','PRIVACY_RELEASE_ASSURANCE.md',
 'COMMUNITY_RESEARCH.md','NEUTRALITY_AND_PROVENANCE.md'}
WORK_ID=re.compile(r'\b(?:R\d{2,}|T\d{2,})(?:\b|_)|\bAsana\b|\bprepush\b|\bsource candidate\b',re.I)
MILESTONE=re.compile(r'^R\d{2,}[_-]',re.I)
LINK=re.compile(r'(?<!!)\[[^\]]+\]\(([^)]+)\)')
MODULE=re.compile(r'^muse_presets\.[a-z][a-z0-9_]*$')
MAX_TEXT=2_000_000

def _prose(text:str)->str:
 text=re.sub(r'```.*?```|~~~.*?~~~','',text,flags=re.S)
 text=re.sub(r'`[^`]*`','',text)
 return re.sub(r'\]\([^)]+\)',']()',text)

def product_findings(root:Path)->list[dict[str,str]]:
 """Check all product pages recursively; never follow symlinks."""
 root=Path(root)
 if root.is_symlink() or not root.is_dir():
  return [{'path':'.','reason':'UNSAFE_PRODUCT_ROOT'}]
 root=root.resolve();found=[]
 def add(path,reason):found.append({'path':path,'reason':reason})
 for current,dirs,files in os.walk(root,followlinks=False):
  base=Path(current)
  for name in list(dirs):
   p=base/name;rel=p.relative_to(root).as_posix()
   if name in IGNORED:dirs.remove(name);continue
   if p.is_symlink() or (hasattr(p,'is_junction') and p.is_junction()):
    add(rel,'SYMLINK_REFUSED');dirs.remove(name)
   elif name.lower() in PRIVATE_DIRS:
    add(rel,'INTERNAL_ARTIFACT');dirs.remove(name)
  for name in files:
   p=base/name;rel=p.relative_to(root).as_posix()
   if p.is_symlink():add(rel,'SYMLINK_REFUSED');continue
   doc=rel.startswith(('docs/','presets/','services/')) or '/' not in rel
   if rel.startswith('docs/') and (MILESTONE.match(name) or name.upper() in OLD_DOCS or re.search(r'(?:FINAL|CURRENT|RESTART)[_-]CHECKPOINT',name,re.I)):
    add(rel,'INTERNAL_ARTIFACT')
   if not (doc and p.suffix.lower()=='.md'):continue
   try:
    if p.stat().st_size>MAX_TEXT:raise ValueError('too large')
    body=p.read_text(encoding='utf-8')
   except (OSError,UnicodeError,ValueError):add(rel,'UNREADABLE_PRODUCT_PAGE');continue
   if '\ufffd' in body or '\u00e2\u20ac' in body:add(rel,'CORRUPTED_PRODUCT_TEXT')
   if WORK_ID.search(_prose(body)):add(rel,'INTERNAL_WORK_LANGUAGE')
   for match in LINK.finditer(body):
    target=match.group(1).strip().split('#',1)[0].split('?',1)[0]
    if not target or re.match(r'^[a-z][a-z0-9+.-]*:',target,re.I) or target.startswith('//'):continue
    try:
     path=(p.parent/unquote(target)).resolve()
     if not path.is_relative_to(root) or not path.exists():add(rel,'BROKEN_LOCAL_LINK')
    except (OSError,ValueError,RuntimeError):add(rel,'BROKEN_LOCAL_LINK')
 return sorted(found,key=lambda x:(x['path'],x['reason']))

def capability_findings(root:Path,catalog:object)->list[dict[str,str]]:
 """Validate advertised local functionality against actual shipped files."""
 root=Path(root);out=[]
 def add(p,r):out.append({'path':p,'reason':r})
 if type(catalog) is not dict or catalog.get('schema')!='specialist-capabilities/v1':
  return [{'path':'presets/capabilities.json','reason':'INVALID_CAPABILITY_CATALOG'}]
 if catalog.get('external_effects_enabled') is not False:add('catalog','NATIVE_AUTHORITY_NOT_ALLOWED')
 roles=catalog.get('roles');features=catalog.get('features')
 if type(roles) is not list or len(roles)!=11 or not all(type(x) is str for x in roles) or len(set(roles))!=11:
  add('roles','INVALID_ROLES')
 if type(features) is not list:return out+[{'path':'features','reason':'INVALID_FEATURES'}]
 ids=set()
 for feature in features:
  if type(feature) is not dict:add('features','INVALID_FEATURE');continue
  identifier=feature.get('id');module=feature.get('module');example=feature.get('example');role=feature.get('role')
  if type(identifier) is not str or identifier in ids:add('features','DUPLICATE_OR_INVALID_ID')
  else:ids.add(identifier)
  if type(module) is not str or MODULE.fullmatch(module) is None or not (root/'src'/Path(*module.split('.')).with_suffix('.py')).is_file():add(str(identifier),'MISSING_MODULE')
  if type(example) is not str or not example.startswith('examples/') or '..' in Path(example).parts or not (root/example).is_file():add(str(identifier),'MISSING_EXAMPLE')
  if not isinstance(roles,list) or role not in roles:add(str(identifier),'INVALID_ROLE')
  if feature.get('grade') not in ('local-executable','local-review-only','synthetic-training'):add(str(identifier),'INVALID_CAPABILITY_GRADE')
 return sorted(out,key=lambda x:(x['path'],x['reason']))

def refresh_manifest(root:Path)->dict:
 """Refresh exact public file hashes after product and privacy validation.

This is a local maintainer operation, not publication approval. No source
file is removed to evade checks; the prior manifest is replaced atomically.
"""
 from .public_export import SCHEMA,select_public_files
 from .neutrality import audit_public_tree
 root=Path(root)
 bad=product_findings(root)
 if bad:raise ValueError('PUBLIC_PRODUCT_POLICY_FAILED:'+json.dumps(bad[:12],sort_keys=True))
 cap=root/'presets/capabilities.json'
 if cap.exists():
  bad=capability_findings(root,json.loads(cap.read_text(encoding='utf-8')))
  if bad:raise ValueError('PUBLIC_CAPABILITY_POLICY_FAILED:'+json.dumps(bad))
 files=select_public_files(root,verify_manifest=False)
 bad=audit_public_tree(root)
 if bad:raise ValueError('PUBLIC_PRIVACY_POLICY_FAILED:'+json.dumps(bad[:8],sort_keys=True))
 manifest={'schema':SCHEMA,'release_kind':'GITHUB_SOURCE_ONLY',
  'source_file_count':len(files),'files':{n:hashlib.sha256(b).hexdigest() for n,b in files.items()},
  'native_host_verified':False,'public_git_pushed':False,'private_git_history_excluded':True,
  'internal_control_plane_excluded':True,'owner_state_included':False,'publisher_approval_granted':False}
 for name,data in files.items():
  if (root/name).read_bytes()!=data:raise ValueError('SOURCE_CHANGED_DURING_MANIFEST_REFRESH')
 raw=(json.dumps(manifest,sort_keys=True,indent=2,ensure_ascii=False)+'\n').encode('utf-8')
 destination=root/'PUBLIC_SOURCE_MANIFEST.json'
 if destination.exists() and destination.read_bytes()==raw:return manifest
 fd,temp=tempfile.mkstemp(prefix='.manifest-',suffix='.tmp',dir=root)
 try:
  with os.fdopen(fd,'wb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
  os.replace(temp,destination)
 finally:
  if os.path.exists(temp):os.unlink(temp)
 return manifest

def check_distribution(root:Path)->dict:
 from .public_export import select_public_files
 from .neutrality import audit_public_tree
 root=Path(root);findings=product_findings(root)
 try:
  catalog=json.loads((root/'presets/capabilities.json').read_text(encoding='utf-8'))
  findings+=capability_findings(root,catalog)
 except (OSError,ValueError):findings.append({'path':'presets/capabilities.json','reason':'MISSING_OR_INVALID_CAPABILITY_CATALOG'})
 try:
  files=select_public_files(root)
 except ValueError as exc:
  files={};findings.append({'path':'PUBLIC_SOURCE_MANIFEST.json','reason':str(exc)})
 findings+=audit_public_tree(root)
 return {'status':'FAIL' if findings else 'PASS','files':len(files),'findings':findings,
         'native_installed':False,'external_effect_authorized':False}

"""Pinned create-only Creative Studio kit; never imports or runs an external renderer."""
from __future__ import annotations
import hashlib
import io
import json
from pathlib import Path
import re
import stat
import zipfile
from .creative_production import canonical_bytes, read_regular, safe_path

SCHEMA='muse-presets/creative-sourcekit-v1'
MAX_ARCHIVE=500000
SOURCE_SHA={
    'LICENSE':'af30e586ca6503924d5e4d99894ec6c7ce61ba77a55ba081b7a129d33f43fddf',
    'src/muse_presets/creative_production.py':'ef195076d8c9c4cb85414f4db51a0cc592fc6b4c5a04fee596fbec1a10b02561',
    'src/muse_presets/creative_cli.py':'91a5fc7f4a359c70dc9c9fb601182ae886965e6f044d64cde562fe1e42f66584',
    'tests/test_creative_production.py':'cabb9b017d8a47cf6c0f1b0c7739693db509839a424b2ff6893bc423c860d488',
    'presets/creative-studio/preset.json':'d6b89a7f0851258af12afcbc224f822e4b0ec76e26e58ee993c789ee4b4ccd48',
    'presets/creative-studio/playbook.json':'3a1210f10e5b75f923e2db4a0e3955bb66d686fd50f042d9191a42da13508bcd',
    'examples/creative_brief.json':'ac766aa9e21313d6845051e485978e15e0dd058344f4e00bca6cb787e931a8ee',
    'docs/kits/CREATIVE_SOURCEKIT.md':'25eaeb0b044081120a4fd430739aebfc20aff8d2c9d9d17d7ef317f905c170c5',
}
SOURCE_MAP={
    'LICENSE':'LICENSE',
    'src/muse_presets/creative_production.py':'muse_presets/creative_production.py',
    'src/muse_presets/creative_cli.py':'muse_presets/creative_cli.py',
    'tests/test_creative_production.py':'tests/test_creative_production.py',
    'presets/creative-studio/preset.json':'preset.json',
    'presets/creative-studio/playbook.json':'playbook.json',
    'examples/creative_brief.json':'sample-brief.json',
    'docs/kits/CREATIVE_SOURCEKIT.md':'START_HERE.md',
}
RUNNER=r'''"""Integrity-check the offline kit before importing its production planner."""
from __future__ import annotations
import hashlib,json,os,stat,sys,unittest
from pathlib import Path
PINS=__PIN_MAP__
SCHEMA='muse-presets/creative-sourcekit-v1'
ALIASES={'/var':'/private/var','/tmp':'/private/tmp','/etc':'/private/etc'}
def require(ok,why):
    if not ok:raise ValueError(why)
def safe(p):
    for x in (p,*p.parents):
        junction=getattr(x,'is_junction',None)
        require(not (callable(junction) and junction()),'LINKED_KIT_PATH')
        if x.is_symlink():
            target=ALIASES.get(str(x))
            require(sys.platform=='darwin' and target and x.lstat().st_uid==0 and x.resolve(strict=True)==Path(target),'LINKED_KIT_PATH')
def bounded(p):
    safe(p);s=p.lstat()
    require(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=131072,'KIT_FILE_NOT_REGULAR_OR_BOUNDED')
    with p.open('rb') as f:raw=f.read(131073)
    require(len(raw)<=131072,'KIT_FILE_BUDGET')
    return raw
def pairs(items):
    data={}
    for k,v in items:
        require(k not in data,'DUPLICATE_JSON_KEY');data[k]=v
    return data
def constant(value):raise ValueError('NONFINITE_JSON_VALUE')
def checked_root():
    require(not sys.flags.optimize,'OPTIMIZED_VALIDATION_UNSUPPORTED')
    require(sys.flags.isolated and sys.dont_write_bytecode,'USE_ISOLATED_PYTHON_WITH_NO_BYTECODE')
    root=Path(__file__).absolute().parent;safe(root)
    expected=set(PINS)|{'run.py','SOURCEKIT_MANIFEST.json'}
    allowed_dirs={str(Path(n).parent).replace('\\','/') for n in expected}- {'.'}
    observed=set();count=0
    for here,dirs,files in os.walk(root,followlinks=False):
        for name in dirs:
            p=Path(here)/name;safe(p)
            require(p.relative_to(root).as_posix() in allowed_dirs,'UNKNOWN_KIT_DIRECTORY')
        for name in files:
            count+=1;require(count<=32,'KIT_ENTRY_BUDGET')
            p=Path(here)/name;safe(p);observed.add(p.relative_to(root).as_posix())
    require(observed==expected,'KIT_FILE_SET_CHANGED')
    for name,pin in PINS.items():require(hashlib.sha256(bounded(root/name)).hexdigest()==pin,'KIT_SOURCE_PIN_CHANGED')
    pins=dict(PINS,**{'run.py':hashlib.sha256(bounded(root/'run.py')).hexdigest()})
    manifest=json.loads(bounded(root/'SOURCEKIT_MANIFEST.json'),object_pairs_hook=pairs,parse_constant=constant)
    required={'schema':SCHEMA,'role_id':'creative-studio','files_sha256':pins,
              'capability':'OFFLINE_PRODUCTION_PLANNING','native_installed':False,
              'media_renderer_bundled':False,'external_effects_authorized':False,
              'rights_independently_verified':False,'public_release_published':False}
    require(manifest==required,'KIT_MANIFEST_CHANGED')
    return root
def main():
    try:
        root=checked_root();sys.path.insert(0,str(root))
        if sys.argv[1:]==['--operation','self-test']:
            suite=unittest.defaultTestLoader.discover(str(root/'tests'),pattern='test_creative_production.py')
            r=unittest.TextTestRunner(verbosity=1).run(suite)
            good=r.wasSuccessful() and r.testsRun==39
            print(json.dumps({'status':'CREATIVE_SELF_TEST_PASSED' if good else 'CREATIVE_SELF_TEST_FAILED',
                  'tests_run':r.testsRun,'failures':len(r.failures),'errors':len(r.errors),'skipped':len(r.skipped),
                  'media_rendered':False,'native_installed':False,'external_effects_authorized':False},sort_keys=True))
            return 0 if good else 1
        from muse_presets.creative_cli import main as execute
        return execute(sys.argv[1:],sample_path=root/'sample-brief.json',kit_root=root)
    except (ValueError,OSError,TypeError,KeyError,UnicodeError,RecursionError,ImportError) as e:
        print(json.dumps({'status':'REFUSED','reason':type(e).__name__+':'+str(e)[:200],
                         'native_installed':False,'media_rendered':False,'external_effects_authorized':False},sort_keys=True))
        return 2
if __name__=='__main__':raise SystemExit(main())
'''


def _require(ok,message):
    if not ok:raise ValueError(message)


def _distribution(source_root: Path) -> dict[str,bytes]:
    root=safe_path(source_root)
    _require(root.is_dir(),'CREATIVE_SOURCE_ROOT_INVALID')
    files={}
    for name,pin in SOURCE_SHA.items():
        raw=read_regular(root/name,131072)
        _require(hashlib.sha256(raw).hexdigest()==pin,'CREATIVE_SOURCE_PIN_MISMATCH:'+name)
        files[SOURCE_MAP[name]]=raw
    profile=json.loads(files['preset.json'])
    _require(profile['id']=='creative-studio' and profile['native_muse_status']=='UNBOUND' and
             profile['family_link']['enabled'] is False,'CREATIVE_PROFILE_CAPABILITY_DRIFT')
    files['muse_presets/__init__.py']=b'"""Pinned offline creative production planning only."""\n'
    pins={n:hashlib.sha256(b).hexdigest() for n,b in sorted(files.items())}
    files['run.py']=RUNNER.replace('__PIN_MAP__',repr(pins)).encode('utf-8')
    files['SOURCEKIT_MANIFEST.json']=canonical_bytes({'schema':SCHEMA,'role_id':'creative-studio',
        'files_sha256':{n:hashlib.sha256(b).hexdigest() for n,b in sorted(files.items())},
        'capability':'OFFLINE_PRODUCTION_PLANNING','native_installed':False,
        'media_renderer_bundled':False,'external_effects_authorized':False,
        'rights_independently_verified':False,'public_release_published':False})
    return files


def _archive(source_root: Path) -> bytes:
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,'w',compression=zipfile.ZIP_STORED,allowZip64=False) as out:
        for name,raw in sorted(_distribution(source_root).items()):
            member=zipfile.ZipInfo(name,date_time=(2026,11,10,0,0,0))
            member.create_system=3;member.external_attr=(stat.S_IFREG|0o644)<<16
            member.compress_type=zipfile.ZIP_STORED;out.writestr(member,raw)
    raw=buf.getvalue();_require(len(raw)<=MAX_ARCHIVE,'CREATIVE_ARCHIVE_BUDGET')
    return raw


def verify_creative_sourcekit(source_root: Path, archive: Path, expected_sha256: str) -> dict:
    _require(type(expected_sha256) is str and re.fullmatch(r'[a-f0-9]{64}',expected_sha256) is not None,'CREATIVE_EXTERNAL_DIGEST_REQUIRED')
    raw=read_regular(archive,MAX_ARCHIVE)
    _require(hashlib.sha256(raw).hexdigest()==expected_sha256,'CREATIVE_EXTERNAL_DIGEST_MISMATCH')
    # Deliberately never parse or decompress a caller-supplied archive.
    _require(raw==_archive(source_root),'CREATIVE_CANONICAL_ARCHIVE_CHANGED')
    return {'status':'CREATIVE_SOURCEKIT_VERIFIED','archive_sha256':expected_sha256,'bytes':len(raw),
            'native_installed':False,'media_rendered':False,'external_effects_authorized':False}


def export_creative_sourcekit(source_root: Path, destination: Path) -> dict:
    out=safe_path(destination)
    _require(out.suffix.lower()=='.zip' and out.parent.is_dir() and not out.exists() and not out.is_symlink(),'CREATIVE_DESTINATION_OCCUPIED_OR_UNSAFE')
    raw=_archive(source_root)
    with out.open('xb') as stream:stream.write(raw)
    result=verify_creative_sourcekit(source_root,out,hashlib.sha256(raw).hexdigest())
    return dict(result,status='CREATIVE_SOURCEKIT_EXPORTED')

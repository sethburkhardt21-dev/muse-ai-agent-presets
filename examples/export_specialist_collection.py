"""Build the current starter collection and four executable extension kits.

The bundle contains 100 starter ZIPs, four standalone toolkits and nine actual
local example reports. The catalog references all 15 source specialist packages;
it does not imply that the original eleven engine sourcekits are rebuilt here.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('collection_bundle_exporter', ROOT/'tools/muse_collection.py')
if SPEC is None or SPEC.loader is None:
    raise RuntimeError('collection exporter unavailable')
collection = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(collection)


def json_bytes(value) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False)+'\n').encode()


def verify_package(raw: bytes) -> int:
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        if archive.testzip() is not None:
            raise ValueError('PACKAGE_CRC_FAILURE')
        manifest = json.loads(archive.read('MANIFEST.json'))
        if set(archive.namelist()) != set(manifest['files']) | {'MANIFEST.json'}:
            raise ValueError('PACKAGE_MEMBER_ROSTER_MISMATCH')
        for name, expected in manifest['files'].items():
            if hashlib.sha256(archive.read(name)).hexdigest() != expected:
                raise ValueError('PACKAGE_MEMBER_HASH_MISMATCH')
        return len(manifest['files'])


def build_bundle() -> bytes:
    data = collection.load_collection(collection.DEFAULT_ROOT)
    counts = (len(data['specialists']), len(data['skills']), len(data['workflows']), len(data['starters']))
    if counts != (15, 75, 25, 100):
        raise ValueError('COLLECTION_INVENTORY_CHANGED_REVIEW_BUNDLE_CONTRACT')
    files = {}
    verified_entries = 0
    for starter in data['starters']:
        payload = collection.build_bytes(data, starter['id'])
        verified_entries += verify_package(payload)
        files['starters/'+starter['id']+'.zip'] = payload
    for role in collection.EXTENSION_ROLES:
        payload = collection.build_file_map_bytes(collection.specialist_kit_files(data, role))
        verified_entries += verify_package(payload)
        files['kits/'+role+'.zip'] = payload
        files['reports/'+role+'.json'] = json_bytes(collection.specialist_demo(data, role))
    for workflow in data['workflows']:
        if workflow.get('tool_bindings'):
            files['reports/'+workflow['id']+'.json'] = json_bytes(collection.workflow_demo(data, workflow['id']))
    files['SPECIALISTS.json'] = json_bytes(data['specialists'])
    files['COUNTS.json'] = json_bytes({'specialists_catalogued':15, 'skills':75,
        'workflows':25, 'starters_packaged':100, 'standalone_extensions_packaged':4})
    files['LICENSE'] = collection.PROJECT_LICENSE.encode()
    files['START_HERE.md'] = '''# Specialist collection: start with a useful result

This bundle contains 100 task starter packages, four new standalone executable
specialist toolkits and nine reports produced by actual local example runs.
The source catalog has 15 specialists. The original eleven engine packages keep
their existing source/export routes and are not silently rebuilt into this ZIP.

## Run one of the four executable toolkits

Choose a ZIP inside `kits/`, extract it into a fresh directory, and run:

```sh
python run.py --demo
```

The choices are `data-engineer`, `reliability-engineer`, `automation-engineer`
and `product-interface-designer`. No API key, dependency installation, account
connection or source repository is required; use Python 3.10 or newer.
Each kit contains its exact input examples, role contract and detailed playbook.
For your own input object, use `python run.py --tool SKILL_ID --input input.json`.

## Use a task starter

Choose one ZIP in `starters/` and read `START_HERE.md`. These are optional skill
and workflow selections for your existing assistant, not new identities or 100
background agents. Preserve its memory, preferences and actual tool permissions.

## Inspect the demonstrations

`reports/` contains actual calculated JSON from the four toolkits and the local
stages of five workflows. The workflow reports name unexecuted host/human stages
and do not claim that a complete production operation ran. All inputs are authored
public examples, not private account records or native model benchmark results.

`SPECIALISTS.json` is the 15-role source catalog. Its contract/example paths refer
to the source repository, not extra executables hidden in this bundle. Source
instructions and the original eleven exporters are described in the repository's
specialist catalog and quickstart.

## Integrity and scope

`BUNDLE_MANIFEST.json` hashes every included file. Each nested ZIP has its own
manifest and was reopened and checked during this build. These hashes establish
self-consistency, not publisher authentication. No package grants approval,
retries uncertain effects, connects to a provider or installs a native assistant.
The original TaskGuard/retention production hold remains separate.
'''.encode()
    manifest = {'schema':'muse-collection-distribution/v1', 'specialists_catalogued':15,
        'skills':75, 'workflows':25, 'starters_packaged':100, 'standalone_extensions_packaged':4,
        'nested_file_entries_verified':verified_entries, 'local_example_reports':9,
        'native_agents_installed':False, 'public_release_performed':False,
        'files':{name:hashlib.sha256(raw).hexdigest() for name,raw in sorted(files.items())}}
    files['BUNDLE_MANIFEST.json'] = json_bytes(manifest)
    return collection.build_file_map_bytes(files)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--to', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.to.exists() or args.to.is_symlink():
            raise ValueError('EXISTING_OUTPUT_PRESERVED')
        payload = build_bundle()
        collection.write_new_pack(args.to, payload)
        print(json.dumps({'status':'COLLECTION_BUNDLE_BUILT_AND_REOPENED',
            'path':str(args.to), 'bytes':len(payload), 'sha256':hashlib.sha256(payload).hexdigest(),
            'starters':100, 'standalone_extension_kits':4, 'native_agents_installed':False},sort_keys=True))
        return 0
    except (ValueError, OSError, UnicodeError, KeyError, zipfile.BadZipFile) as exc:
        print(json.dumps({'error':str(exc), 'public_release_performed':False}),file=sys.stderr)
        return 2

if __name__ == '__main__':
    raise SystemExit(main())

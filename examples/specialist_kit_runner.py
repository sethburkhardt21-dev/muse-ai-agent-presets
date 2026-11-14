"""Standalone entrypoint copied into each exported specialist kit as run.py.

The manifest is a package self-consistency check, not publisher authentication.
No network calls, subprocesses, host dispatch or automatic output writes occur.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys

MAX_BYTES = 2_000_000
MODULES = ('__init__.py', 'common.py', 'data.py', 'reliability.py', 'automation.py', 'interface.py')


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def read_bytes(path: Path) -> bytes:
    require(not path.is_symlink(), 'SYMLINK_INPUT_REFUSED')
    require(not (getattr(path.lstat(), 'st_file_attributes', 0) & 0x400), 'REPARSE_INPUT_REFUSED')
    flags = os.O_RDONLY | getattr(os, 'O_NONBLOCK', 0) | getattr(os, 'O_NOFOLLOW', 0)
    with os.fdopen(os.open(path, flags), 'rb') as stream:
        info = os.fstat(stream.fileno())
        require(stat.S_ISREG(info.st_mode) and info.st_size <= MAX_BYTES, 'REGULAR_BOUNDED_FILE_REQUIRED')
        raw = stream.read(MAX_BYTES + 1)
    require(len(raw) <= MAX_BYTES, 'INPUT_SIZE_LIMIT')
    return raw


def read_json(path: Path):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'DUPLICATE_JSON_KEY')
            result[key] = value
        return result
    def nonfinite(_):
        raise ValueError('NONFINITE_JSON_NUMBER')
    try:
        return json.loads(read_bytes(path).decode('utf-8'), object_pairs_hook=pairs, parse_constant=nonfinite)
    except (json.JSONDecodeError, RecursionError) as exc:
        raise ValueError('INVALID_JSON') from exc


def verify_kit(root: Path) -> None:
    manifest = read_json(root / 'MANIFEST.json')
    require(type(manifest) is dict and manifest.get('schema') == 'muse-specialist-kit/v1', 'KIT_MANIFEST_REQUIRED')
    files = manifest.get('files')
    require(type(files) is dict and 1 <= len(files) <= 512, 'INVALID_MANIFEST_ROSTER')
    critical = {'run.py', 'SPECIALIST.json', 'EXAMPLE.json'} | {'specialist_extensions/' + n for n in MODULES}
    require(critical <= files.keys(), 'MISSING_EXECUTABLE_MANIFEST_MEMBER')
    for name, expected in files.items():
        require(type(name) is str and name and len(name) <= 400 and '\\' not in name and ':' not in name,
                'UNSAFE_MANIFEST_PATH')
        member = PurePosixPath(name)
        require(not member.is_absolute() and '..' not in member.parts and member.as_posix() == name,
                'UNSAFE_MANIFEST_PATH')
        require(type(expected) is str and re.fullmatch(r'[a-f0-9]{64}', expected) is not None, 'INVALID_MEMBER_HASH')
        path = root / name
        for parent in [path, *path.parents]:
            if parent == root: break
            require(not parent.is_symlink() and not (getattr(parent.lstat(), 'st_file_attributes', 0) & 0x400),
                    'LINKED_KIT_MEMBER_REFUSED')
        require(hashlib.sha256(read_bytes(path)).hexdigest() == expected, 'KIT_MEMBER_CHANGED:' + name)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description='Run a bounded local specialist calculation on supplied JSON.')
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--demo', action='store_true')
    mode.add_argument('--tool')
    parser.add_argument('--input', type=Path)
    args = parser.parse_args(argv)
    try:
        root = Path(__file__).resolve().parent
        verify_kit(root)
        contract = read_json(root / 'SPECIALIST.json')
        sys.path.insert(0, str(root))
        from specialist_extensions import evaluate, SPECIALIST_TOOLS
        from specialist_extensions.common import bounded_json, canonical
        role = contract.get('id')
        require(role in SPECIALIST_TOOLS and contract.get('skills') == list(SPECIALIST_TOOLS[role]),
                'ROLE_TOOL_CONTRACT_MISMATCH')
        require(contract.get('native_installed') is False and contract.get('external_actions_performed') is False,
                'KIT_MUST_NOT_CLAIM_NATIVE_AUTHORITY')
        if args.demo:
            require(args.input is None, 'DEMO_DOES_NOT_ACCEPT_CUSTOM_INPUT')
            example = read_json(root / 'EXAMPLE.json')
            bounded_json(example)
            require(type(example) is dict and example.get('specialist') == role,
                    'EXAMPLE_ROLE_MISMATCH')
            jobs = example.get('jobs')
            require(type(jobs) is list and 2 <= len(jobs) <= 12, 'EXAMPLE_JOB_BUDGET')
        else:
            require(args.input is not None, 'CUSTOM_TOOL_REQUIRES_INPUT_FILE')
            jobs = [{'skill_id': args.tool, 'inputs': read_json(args.input)}]
        results = []
        for job in jobs:
            require(type(job) is dict and set(job) == {'skill_id', 'inputs'}, 'INVALID_JOB_FIELDS')
            require(job['skill_id'] in SPECIALIST_TOOLS[role], 'TOOL_OUTSIDE_SPECIALIST_SCOPE')
            output = evaluate(job['skill_id'], job['inputs'])
            results.append({'skill_id': job['skill_id'],
                            'input_sha256': hashlib.sha256(canonical(job['inputs']).encode()).hexdigest(),
                            'output': output})
        print(json.dumps({'specialist': role, 'results': results, 'external_actions_performed': False,
                          'scope': 'executed_local_calculations_on_supplied_inputs', 'model_called': False},
                         sort_keys=True, indent=2, allow_nan=False))
        return 0
    except (ValueError, TypeError, KeyError, OSError, UnicodeError, RecursionError) as exc:
        print(json.dumps({'error': str(exc), 'external_actions_performed': False, 'model_called': False}), file=sys.stderr)
        return 2

if __name__ == '__main__':
    raise SystemExit(main())

"""Run a real repair through a staged, source-pinned Software Engineer runtime.

No model, credentials, publication, native agent or deployment. The supplied
Python fixture is reviewed code, not hostile code in a security sandbox.
Use --to NEW_ABSOLUTE_DIRECTORY to retain original RED/GREEN logs for review.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

from muse_presets.engineering_pack import _require_new, stage_engineer_pack, inspect_engineer_pack


from muse_presets.workflow_fixture import fixture_case


def demonstrate(destination):
    root = _require_new(Path(destination))
    root.mkdir(exist_ok=False)
    engine = root / 'engine'
    stage = stage_engineer_pack(engine)
    if stage['status'] != 'LOCAL_ENGINE_PACK_STAGED' or inspect_engineer_pack(engine)['status'] != 'LOCAL_MATCH':
        raise ValueError('STAGED_WORKFLOW_SOURCE_UNVERIFIED')
    case = fixture_case()
    raw = (json.dumps(case, sort_keys=True, separators=(',', ':'), ensure_ascii=False) + '\n').encode('utf-8')
    case_path = root / 'reviewed-case.json'
    case_path.write_bytes(raw)
    expected = hashlib.sha256(raw).hexdigest()
    cli = engine / 'runtime/claim-gate/engineering_workflow.py'
    process = subprocess.run([sys.executable, '-I', '-B', str(cli), 'execute', '--case', str(case_path),
                              '--case-sha256', expected, '--to', str(root / 'work'), '--reviewed-code'],
                             capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=80)
    if process.returncode != 0:
        raise ValueError('REAL_WORKFLOW_FAILED:' + (process.stdout + process.stderr)[-500:])
    result = json.loads(process.stdout)
    if (result.get('status') != 'GREEN_TESTED' or result['red']['exit_code'] != 1
        or result['green']['exit_code'] != 0 or result['red']['result']['failures'] != case['expected_failures']
        or result['green']['result']['tests_run'] != 4 or result['green']['result']['failures']
        or result['green']['result']['errors'] or result['green']['result']['skipped']
        or result.get('native_muse_invoked') is not False or result.get('external_effect_authorized') is not False):
        raise ValueError('WORKFLOW_EVIDENCE_NOT_ACCEPTED')
    candidate = root / 'work/candidate.json'
    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    if result['candidate_sha256'] != digest:
        raise ValueError('FROZEN_WORKFLOW_CANDIDATE_DRIFT')
    return {'schema': 'r55/software-engineer-workflow-demo-v1',
            'status': 'LOCAL_ENGINEERING_WORKFLOW_GREEN',
            'workflow': {'red_exit': 1, 'green_exit': 0, 'green_tests': 4,
                         'original_failure': case['expected_failures'][0],
                         'baseline_commit': result['baseline_commit'], 'patched_commit': result['patched_commit'],
                         'patch_sha256': result['patch_sha256'], 'candidate_sha256': digest},
            'candidate_file': str(candidate), 'independent_review_status': 'PENDING_EXTERNAL_REVIEWS',
            'native_muse_invoked': False, 'external_effect_authorized': False, 'os_sandboxed': False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--to', type=Path)
    args = parser.parse_args(argv)
    if args.to is not None:
        result = demonstrate(args.to)
    else:
        with tempfile.TemporaryDirectory(prefix='software-engineer-red-green-') as temporary:
            result = demonstrate(Path(temporary) / 'demo')
        result['candidate_file'] = None
        result['temporary_artifacts_removed'] = True
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

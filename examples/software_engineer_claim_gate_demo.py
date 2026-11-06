"""Run one real local Claim Gate workflow from a fresh generic Software Engineer pack.

Synthetic inputs, temporary state, no network or native Muse tool effect.
Requires POSIX fcntl. On Windows staging still works, but this demo refuses.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from muse_presets.engineering_pack import stage_engineer_pack


def main() -> int:
    if os.name != 'posix':
        print('UNSUPPORTED_PLATFORM_POSIX_FCNTL_REQUIRED; no local engine invoked')
        return 2
    with tempfile.TemporaryDirectory(prefix='public-engineer-demo-') as temp:
        root = Path(temp)
        pack = root / 'software-engineer'
        result = stage_engineer_pack(pack)
        assert result['status'] == 'LOCAL_ENGINE_PACK_STAGED'
        state = root / 'state'
        source = root / 'sources'
        state.mkdir()
        source.mkdir()
        (source / 'patch.txt').write_bytes(b'fictional parser repair, source revision 1')
        cli = pack / 'runtime' / 'claim-gate' / 'engineering_claim_gate.py'

        def call(action: str, *options: str) -> dict:
            cmd = [sys.executable, '-I', '-B', str(cli), '--state-dir', str(state),
                   '--scope', 'engineering', '--claim-id', 'demo-claim', action, *options]
            process = subprocess.run(cmd, capture_output=True, text=True, timeout=8)
            if process.returncode != 0:
                raise RuntimeError(process.stderr + process.stdout)
            return json.loads(process.stdout)

        first = call('claim', '--source-root', str(source), '--payload', 'patch.txt')
        same = call('claim', '--source-root', str(source), '--payload', 'patch.txt')
        hold = call('hold-unknown', '--reason', 'synthetic worker result not observed')
        recovered = call('inspect')
        assert first['status'] == 'LOCAL_CLAIM_RECORDED'
        assert same['status'] == 'LOCAL_CLAIM_REUSED'
        assert hold['state'] == recovered['state'] == 'UNKNOWN'
        assert not recovered['external_effect_authorized']
        assert not recovered['native_muse_invoked']
        print('Software Engineer: source-derived local Claim Gate executed')
        print('Atomic first claim, no-replay, UNKNOWN recovery: PASS')
        print('Original engine source: source-pinned neutral edition')
        print('Native Muse account, host permissions and external effects: NOT INVOKED')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

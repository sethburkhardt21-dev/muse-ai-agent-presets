"""Offline public Evidence Finder example: fictional source, no Muse account.

Run: PYTHONPATH=src python examples/evidence_ledger_demo.py
"""
from __future__ import annotations

import hashlib
import tempfile
from pathlib import Path

from muse_presets.evidence_ledger import EvidenceLedger, EvidenceScope


def main() -> None:
    with tempfile.TemporaryDirectory(prefix='muse-evidence-demo-') as temp:
        home = Path(temp)
        source = home / 'source'
        source.mkdir()
        sample = source / 'observation.txt'
        sample.write_bytes(b'Fictional source: a garden observation was recorded.\n')
        original_sha = hashlib.sha256(sample.read_bytes()).hexdigest()

        # A real host MUST authenticate this scope at every call.
        # This callback is intentionally a synthetic local demonstration.
        context = EvidenceScope('demo-owner', 'demo-workspace',
                                'evidence-finder', 'demo-operator')
        resolver = lambda: context
        with EvidenceLedger(home / 'receipts.sqlite3', authority=resolver) as store:
            found = store.capture(source, 'observation.txt', 'garden',
                                  operation_id='demo-found')
            missing = store.capture(source, 'observation.txt', 'missing-word',
                                    operation_id='demo-nohit')
            assert found['finding']['source_sha256'] == original_sha
            assert missing['finding']['result'] == 'NOT_FOUND'

        sample.unlink()  # Demonstrate custody independent of the original file.

        with EvidenceLedger(home / 'receipts.sqlite3', authority=resolver) as reopened:
            finding = reopened.read('demo-found')
            nohit = reopened.read('demo-nohit')
            receipt = reopened.verify()
        assert finding['finding']['observation'] == (
            'Fictional source: a garden observation was recorded.\n'
        )
        assert nohit['finding']['observation'] == ''
        assert receipt['receipt_count'] == 2
        assert receipt['chain_verified_locally'] is True
        assert receipt['chain_externally_anchored'] is False
        print('Evidence Finder: exact finding recovered after source deletion')
        print('Honest no-hit recorded without inventing a finding')
        print('Locally verified receipt chain: 2 entries')
        print('Native Muse permissions, source owner, and delivery: NOT VERIFIED')


if __name__ == '__main__':
    main()

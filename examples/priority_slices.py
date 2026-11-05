"""Five source-only specialist micro-examples. No native Muse or network calls.

Run from the repository root with: PYTHONPATH=src python examples/priority_slices.py
"""
from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from muse_presets.finder import find_exact_text
from muse_presets.claims import assess_scope
from muse_presets.garden import preview_date_shift
from muse_presets.learning import draft_supported_card
from muse_presets.reverse import compare_observed_flows


def main() -> None:
    with TemporaryDirectory(prefix='muse-presets-demo-') as tmp:
        evidence = Path(tmp) / 'example.txt'
        evidence.write_text('Demo finding: the local source parser completed.\n', encoding='utf-8')
        found = find_exact_text(Path(tmp), 'example.txt', 'local source parser')
        claimed = assess_scope(
            'All native integrations work.', 'NATIVE_USED', 'LOCAL_TESTED',
            conditions=('Only local fixture code was exercised',),
        )
        garden = preview_date_shift(
            {'id': 'seedling-1', 'owner_id': 'fictional-owner', 'date': '2026-11-10', 'revision': 1},
            owner_id='fictional-owner', expected_revision=1, days=2,
        )
        learning = draft_supported_card(
            'A plant absorbs light through chlorophyll.',
            source_id='sample-lesson', question='What pigment is mentioned?', answer='chlorophyll',
        )
        reverse = compare_observed_flows(
            [{'action': 'click', 'target': 'save', 'outcome': 'dialog'}],
            [{'action': 'click', 'target': 'save', 'outcome': 'toast'}],
        )
    output = {
        'schema': 'muse-presets/offline-demonstration-v1',
        'native_muse_installed': False,
        'family_link_sent': False,
        'sandbox_only': True,
        'evidence_finder': found,
        'claims_adjudicator': claimed,
        'garden_companion': garden,
        'learning_coach': learning,
        'reverse_engineering_researcher': reverse,
    }
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()

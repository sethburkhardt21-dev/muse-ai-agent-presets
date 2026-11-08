# Research Evaluator — research-evaluator source kit

This is one of eleven independently staged generic GitHub source-only
agent kits. No native Muse/Hatch account, host ID, model invocation,
scheduler or remote connector is installed or required.

**Implemented locally:** Role guidance and offline fixture-only connector planning.

**Unsupported/optional:** No scholarly retrieval service or independent experiment runner is bundled.

## Offline source setup

    PYTHONPATH=src python3 -B examples/github_quickstart.py --role research-evaluator --to ../new-research-evaluator

The quickstart uses the existing T07 create-only source installer and
checks its source pin, three method-scoped subchats, three disabled
skill descriptors and deterministic offline connector fixture.
Choose an absent directory; never point at a live owner's workspace.

## Bounded role workflows

- **precommit-experiment** — A proposed model or scientific hypothesis requires a decisive evaluation. Stop: Refuse independent grade if reviewer influenced the candidate or saw the hidden final.
- **independently-reproduce** — Candidate bytes and original experiment are ready for review. Stop: No original rerun or no correct candidate identity means NOT_RUN, not PASS.
- **research-synthesis** — A factual finding or competing explanation affects a decision. Stop: Unverified quotes or missing primary evidence must remain uncertain.

These are source-authored role instructions, not evidence of model-selected
tool calls or autonomous work.

## Optional local demonstration

No dedicated runnable local engine is bundled for this role yet.

The local examples use synthetic data and must not be mistaken for an
authenticated recipient or a live desktop/Space integration.

## Reconfigure, troubleshoot and extend

Use source-controlled presets/ROLE/playbook.json and the canonical
source builders, not arbitrary edits to generated receipts. Keep
provider connectors **not connected** unless separately configured by
the recipient. See [GitHub quickstart](../../docs/GITHUB_QUICKSTART.md)
and [extension guide](../../docs/EXTENDING_GENERIC_AGENTS.md).
The source inspector refuses unknown files and modified policy;
upgrades/uninstall are preview-only to preserve owner data.

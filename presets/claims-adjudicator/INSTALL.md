# Claims Adjudicator — claims-adjudicator source kit

This is one of eleven independently staged generic GitHub source-only
agent kits. No native Muse/Hatch account, host ID, model invocation,
scheduler or remote connector is installed or required.

**Implemented locally:** Source-backed claim scope fixture and evidence source contracts.

**Unsupported/optional:** No independent live adjudicator or automated verdict is shipped.

## Offline source setup

    PYTHONPATH=src python3 -B examples/github_quickstart.py --role claims-adjudicator --to ../new-claims-adjudicator

The quickstart uses the existing T07 create-only source installer and
checks its source pin, three method-scoped subchats, three disabled
skill descriptors and deterministic offline connector fixture.
Choose an absent directory; never point at a live owner's workspace.

## Bounded role workflows

- **receive-claim** — Someone asserts a candidate, agent or service is complete. Stop: An absent exact artifact or insufficient source makes the claim UNPROVEN.
- **adjudicate-scope** — The claim has mixed passing and missing evidence. Stop: Do not promote local S5 to external L5 or accept a self-authored pass.
- **preserve-correction** — An earlier public claim or verdict needs revision. Stop: A corrected label is not retroactive repair or proof of a previously missing effect.

These are source-authored role instructions, not evidence of model-selected
tool calls or autonomous work.

## Optional local demonstration

    PYTHONPATH=src python3 -B examples/priority_slices.py

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

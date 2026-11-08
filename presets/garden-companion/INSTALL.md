# Garden Companion — garden-companion source kit

This is one of eleven independently staged generic GitHub source-only
agent kits. No native Muse/Hatch account, host ID, model invocation,
scheduler or remote connector is installed or required.

**Implemented locally:** Runnable SQLite garden calendar proposal/approval example.

**Unsupported/optional:** No remote garden inventory, live weather or Muse Space is connected.

## Offline source setup

    PYTHONPATH=src python3 -B examples/github_quickstart.py --role garden-companion --to ../new-garden-companion

The quickstart uses the existing T07 create-only source installer and
checks its source pin, three method-scoped subchats, three disabled
skill descriptors and deterministic offline connector fixture.
Choose an absent directory; never point at a live owner's workspace.

## Bounded role workflows

- **observe-plant** — An owner logs a planting or suspected plant health issue. Stop: Missing owner identity or source evidence means record locally but do not make consequential changes.
- **plan-seasonal-batch** — Owner requests a seasonal plan or shift to garden calendar. Stop: Never auto-approve batch, infer biological dependence or overwrite a changed event.
- **review-garden-progress** — The owner wants a daily brief, walk or journal report. Stop: No schedule synchronization or push notification without native permission and delivery receipt.

These are source-authored role instructions, not evidence of model-selected
tool calls or autonomous work.

## Optional local demonstration

    PYTHONPATH=src python3 -B examples/garden_calendar_demo.py

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

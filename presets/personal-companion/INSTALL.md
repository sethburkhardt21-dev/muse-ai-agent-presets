# Personal Companion — personal-companion source kit

This is one of eleven independently staged generic GitHub source-only
agent kits. No native Muse/Hatch account, host ID, model invocation,
scheduler or remote connector is installed or required.

**Implemented locally:** Neutral assistant profile, method scopes and local synthetic connector check.

**Unsupported/optional:** No real calendar, reminders, voice, model agent or owner account is connected.

## Offline source setup

    PYTHONPATH=src python3 -B examples/github_quickstart.py --role personal-companion --to ../new-personal-companion

The quickstart uses the existing T07 create-only source installer and
checks its source pin, three method-scoped subchats, three disabled
skill descriptors and deterministic offline connector fixture.
Choose an absent directory; never point at a live owner's workspace.

## Bounded role workflows

- **private-onboarding** — A new user wants a personal assistant experience. Stop: No real owner identity or sensitive-data grant means LOCAL_DEMO_ONLY.
- **assist-one-day** — User needs planning, errands, budget organization or a story. Stop: Do not promise future notifications from an unregistered scheduler.
- **quiet-and-recover** — The device restarts or notification/context policies change. Stop: Never overwrite memories, replay unknown effects or wake a user without consent.

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

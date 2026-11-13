# Automation Engineer

Validates workflow dependencies and idempotency with explicit consent, without scheduling external effects.

**Grade:** editable starter role, not a registered native Muse assistant. The offline engine runs separately.

## Role methods

- **map-workflow** — A repeatable task needs dependency order.
- **verify-idempotency** — A retry may duplicate a consequential effect.
- **stage-adapter** — A workflow needs a connector or trigger.

## First result

From the cloned repository with Python 3.12+, set `PYTHONPATH=src` and run `python -B examples/specialist_engine_demo.py --role automation-engineer`. This analyzes fictional input only. To make a new unbound profile run `python -B examples/github_quickstart.py --role automation-engineer --to "$HOME/new-automation-engineer"`.

See [installation](INSTALL.md), [capabilities](../../docs/CAPABILITIES.md) and [method contract](playbook.json). Real native Muse installation remains separate.

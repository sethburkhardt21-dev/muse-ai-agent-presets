# Data Engineering & Database Architect

Profiles local datasets, validates schema and identity risks, and plans reversible data changes without production writes.

**Grade:** editable starter role, not a registered native Muse assistant. The offline engine runs separately.

## Role methods

- **profile-dataset** — A local CSV or table needs a quality assessment.
- **validate-schema** — An ingestion contract needs deterministic schema checks.
- **plan-migration** — A schema change impacts data consumers.

## First result

From the cloned repository with Python 3.12+, set `PYTHONPATH=src` and run `python -B examples/specialist_engine_demo.py --role data-engineering-architect`. This analyzes fictional input only. To make a new unbound profile run `python -B examples/github_quickstart.py --role data-engineering-architect --to "$HOME/new-data-engineering-architect"`.

See [installation](INSTALL.md), [capabilities](../../docs/CAPABILITIES.md) and [method contract](playbook.json). Real native Muse installation remains separate.

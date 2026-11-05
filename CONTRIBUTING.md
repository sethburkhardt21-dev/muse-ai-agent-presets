# Contributing to Muse AI Agent Presets

Contributions should be reusable, neutral, rights-cleared and source-tested. Do not submit private host data, personal memory, credentials, unapproved assets or proprietary SDK implementations.

1. Open an issue with the user-visible capability and target Muse host profile.
2. State origin/commit/license, permissions, connector scopes and exact tests. Prefer existing modules and source references to duplicate implementations.
3. Add a failing test for behavior changes, implement a narrow repair, run local full suite.
4. If you claim host compatibility, include original native registration, execution and recipient evidence, not just file installation.
5. Preserve negative tests, unsupported platforms and failure receipts. Do not silently promote statuses.

Code style: Python stdlib, small explicit modules, fail-closed input validation and create-only outputs. Avoid schedules, agents and credential access in the shared core.

## Adding or improving a specialist

Each source-only specialist has a `preset.json` and exactly one `playbook.json` with three specific methods. The contract validator checks trigger, executable **procedure description** (not actual tool code), two or more evidence obligations, stop condition, and a proposed handoff target permitted by `preset.json`. Provide a first source-only test and a negative case. Do not raise maturity or native-host status without real host evidence.

Run `PYTHONPATH=src python -m muse_presets.cli doctor`, `PYTHONPATH=src python -m muse_presets.cli audit-neutrality`, and the full unittest suite before publishing. For external code, consult [capability fit audit](docs/CAPABILITY_FIT_AUDIT.md), [community intake](docs/COMMUNITY_ROLE_INTEGRATIONS.md), and [rights and provenance](docs/NEUTRALITY_AND_PROVENANCE.md). Preserve original notices; keep third-party implementations optional until independently admitted.

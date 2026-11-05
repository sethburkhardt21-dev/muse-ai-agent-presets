# Contributing to Muse AI Agent Presets

Contributions should be reusable, neutral, rights-cleared and source-tested. Do not submit private host data, personal memory, credentials, unapproved assets or proprietary SDK implementations.

1. Open an issue with the user-visible capability and target Muse host profile.
2. State origin/commit/license, permissions, connector scopes and exact tests. Prefer existing modules and source references to duplicate implementations.
3. Add a failing test for behavior changes, implement a narrow repair, run local full suite.
4. If you claim host compatibility, include original native registration, execution and recipient evidence, not just file installation.
5. Preserve negative tests, unsupported platforms and failure receipts. Do not silently promote statuses.

Code style: Python stdlib, small explicit modules, fail-closed input validation and create-only outputs. Avoid schedules, agents and credential access in the shared core.

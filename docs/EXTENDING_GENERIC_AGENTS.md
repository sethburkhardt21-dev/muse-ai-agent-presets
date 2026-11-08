# Extend a generic agent without disturbing owner data

This GitHub source project contains **11 fixed neutral role IDs**, their
playbooks, a shared Evidence Finder service and optional source-level adapters.
It is **not** an installed Muse/Hatch runtime, and provider accounts are not
needed to customize or test the repository.

Begin with the [GitHub quickstart](GITHUB_QUICKSTART.md). Use a fresh branch,
an isolated test folder, and a known commit. The exact source code and
generated manifests, not mutable local receipts, define the expected policy.

## Edit role instructions or a method

Each role is declared in presets/catalog.json, presets/ROLE/preset.json and
presets/ROLE/playbook.json. The playbook currently requires exactly **three**
distinct method IDs with trigger, steps, evidence, stop rule and proposed
handoff. The role's T04 profile, T05 subchats and T06 disabled skill
descriptors are derived from those same source files.

To customize an existing role's instructions:

1. Create a source-control branch and edit presets/ROLE/playbook.json.
2. Keep the role ID fixed, preserve method IDs unless intentionally migrating
   a contract, and keep optional_tool_categories bounded and exact.
3. Run the role and catalog tests plus the source doctor and neutrality scan.
4. Regenerate into a new empty directory; do **not** overwrite the old
   owner's MEMORY.md, preferences, agent files or skill registry.
5. Compare the old and new packages using dropin-upgrade-preview. Resolve
   conflicts manually; the source tool does not apply upgrades.

Changing a method creates new source hashes and invalidates prior local
manifests. A previous hash is not permission to bypass source drift.

## Add or modify a SKILL.md descriptor

The source file src/muse_presets/role_skills.py derives three custom
SKILL.md + skill.yaml pairs for each role from its playbook, with a
version-one config/skills.yaml whose entries are **disabled**.

Editing only a generated SKILL.md or its local receipt will not survive
source-backed inspection. Change the canonical method definition, then
regenerate the package and rerun tests/test_role_skills.py and
tests/test_subchat_scopes.py.

To add a *fourth* method requires a conscious schema migration: update
the playbook validator, bound cardinality checks, corresponding source
builders and their tests. Merely adding a folder does not register a new
native skill or grant any runtime tool.

## Add an actual local engine

Place a narrow standard-library module under src/muse_presets and add a
test under tests. Prefer reusing the first-party source-tested engines
rather than duplicating their state machines.

Follow the pattern of a reproducible local command, a synthetic positive
fixture, a negative/forged input fixture, a bounded result with stable
source identity, and a documented reset/rollback. The Software Engineer's
POSIX Claim Gate, Coordinator graph reviewer, Model Builder metrics,
Garden calendar and Learning study engines show what *local and tested*
means. Do not claim real model training, browser control or research retrieval
without a corresponding running backend.

Source links in src/muse_presets/role_skills.py refer to selected local
modules only; they are not automatic working executables in every package.

## Add an optional connector

src/muse_presets/portable_connectors.py derives allowed capability
categories from presets/ROLE/playbook.json. It supplies a default-deny
plan, deterministic local fixtures and consistency checks.

To add a real connector:

1. Scope it to an exact role and declared category; test a wrong-role
   refusal, missing owner authority, malformed input and timeout.
2. Implement a separate provider adapter behind an explicit opt-in boundary.
   Document what user configuration and provider permissions are required.
3. Bind request/operation IDs, the original effect and recipient receipts.
   Reconcile UNKNOWN effects before retry; never infer success from a local
   JSON claim or expired credential.
4. Use no external paid service by default; preserve clean offline tests.
5. Mark the provider not connected until an actually authorized receiver
   configures and tests it.

A desktop-commander or browser-cua plan label is *not* a live desktop
driver, and SSH requires the user's own account/device authorization.

## Add another role or shared service

The v1 catalog is deliberately fixed at **11** roles. A twelfth persona is
not added by inserting an arbitrary folder; change catalog validation,
role source files, role-specific installer/CLI contracts and the relevant
fixed-size safety tests in a dedicated versioned migration. Evidence Finder
is a shared service, not a twelfth role. Avoid copying private original-agent
memories or credentials into any new role.

## Recovery, upgrades and maintenance

For local recovery, treat the exact source commit and clean file receipts as
advisory evidence, not permission to replay uncertain external effects.

Use git to preserve source history, exact commit SHA and changed files.
Each source package is create-only; if a stage stops unexpectedly it leaves
STAGING_INCOMPLETE and must be reconciled rather than blindly replayed.

The CLI operations dropin-inspect, dropin-upgrade-preview and
dropin-uninstall-plan are read-only. Clean exports omit owner-customized
memory. Actual native uninstall and owner-state rollback require a separate,
supported host procedure and are **not** implemented by this repository.

After every change run:

    PYTHONPATH=src python3 -B -m unittest discover -s tests -q
    PYTHONPATH=src python3 -B -m muse_presets.cli doctor
    PYTHONPATH=src python3 -B -m muse_presets.cli audit-neutrality
    PYTHONPATH=src python3 -B examples/github_quickstart.py --all

On Windows PowerShell set $env:PYTHONPATH="src", then use python in
place of python3. Record skipped platform tests honestly; do not mark
an unavailable POSIX engine as Windows-qualified.

## GitHub release safety

First-party owner-authored source reuse is authorized; there is no blanket
legal blocker. Check any third-party dependency or asset that is actually
added. Keep credentials, owner files, machine identifiers and local historical
private commits out of public distributions. T31/T32 qualify the clean source
snapshot, and T34 publishes only an explicitly verified public commit or
release artifact; **never push the full private repository history**.

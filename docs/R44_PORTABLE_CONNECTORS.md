# R44 — Portable role-scoped connector contracts (GitHub source release)

**Status:** source-tested, offline fixture and proposal API. Every provider is
**not connected** by default; this is not a remote Desktop Commander, CUA,
browser, terminal, SSH, Space or other live-tool driver.

This module is a useful, portable starting contract for the eleven neutral
agents delivered as GitHub source. Each role's actual source-pinned
presets/ROLE/playbook.json determines its connector categories.
The module does not maintain a competing tool catalog or dispatch controller.

## Offline setup and examples

From a fresh GitHub clone, with Python 3.10+ and PYTHONPATH=src:

    python -B -m muse_presets.cli connector-plan --preset coordinator --capability source-control --request-id demo-001
    python -B -m muse_presets.cli connector-fixture --preset coordinator --capability source-control --request-id demo-001 --file ./synthetic-observations.json

The second command expects a **synthetic, caller-supplied, read-only JSON** list
with each object containing only id, sha256, and observation. The
SHA-256 value is the UTF-8 digest of the exact observation string.
For example, generate an input in a throwaway test folder:

    python -c "import json,hashlib; s='Synthetic checked input'; print(json.dumps([{'id':'example-1','sha256':hashlib.sha256(s.encode()).hexdigest(),'observation':s}]))"

Save the printed JSON into synthetic-observations.json before running the
fixture command. No outside file or account is read except this explicitly
provided input and the checked-in local repository playbook. The
fixture result is deterministic, normalized by input ID and includes an
observation digest; no network requests, model calls or GUI actions occur.

## Role-specific allowlist

The following role IDs are resolved from their source-pinned
playbook tool categories (never arbitrary user-provided claims):

- coordinator: task registry, source control, evidence and bounded handoffs
- software-engineer: source control, local tests and dependency analysis
- model-builder: local model/data evaluation and hardware preflight
- research-evaluator: scholarly retrieval and source-integrity interfaces
- creative-studio: rendering, asset custody and preview interfaces
- adversarial-verifier: defensive review, mutation tests and evidence
- personal-companion: personal notebook, reminders and accessibility
- garden-companion: garden observation and optional weather references
- learning-coach: document ingestion, scoring and study records
- claims-adjudicator: evidence, independent reports and claim records
- reverse-engineering-researcher: authorized desktop observation and offline traces

A role cannot request an undeclared category, even when another role has it.

## Provider extension contract

Supported *proposal labels* are offline-fixture, terminal,
desktop-commander, browser-cua, and ssh. They are interface labels only,
**not connected** provider integrations or executable tools.

A connector-plan returns the exact role, requested capability and
request ID, source playbook digest and a non-authorizing plan digest.
Owner, agent, host, provider operation and session IDs remain null.
can_execute, provider_connected, external_effect_authorized, and
recipient_readback_verified remain false, regardless of provider label.

To implement a provider later, create a separate optional adapter under
the receiving user's own authenticated runtime with explicit owner/capability
grants, request IDs, bounded inputs, original effect and recipient receipts,
stop/cancel and UNKNOWN-effect reconciliation. Never infer authorization from
these local JSON records. Do not automatically retry an uncertain external
effect. A plugin SDK, desktop CUA driver or remote terminal may need separate
installation and user permission; this repository supplies integration points.

## Refusals and security posture

The fixture and plan APIs reject wrong-role categories, unknown providers,
non-canonical request IDs, arbitrary extra fields, duplicate observations,
oversized payloads, invalid source hashes, tampered source playbooks, and
forged execution or provider-success claims. The supplied JSON fixture is
read-only with a strict size limit and no symlink traversal.

reconcile_fixture can assert only CONSISTENT_OFFLINE_FIXTURE_ONLY.
It does not authenticate who issued the data, prove independent reviewer
authority, register native skills, authorize a GUI action or confirm external
delivery. The real Desktop Commander and CUA controls are not included
as silently activated dependencies.

Source acceptance targets GitHub: reproducible CLI and tests,
Windows/macOS/Linux compatibility, scoped permission boundaries, no
owner-specific hostnames or private personal state, and honest feature
labels. Live Hatch registration and provider-issued recipient evidence
are outside this source-release milestone.

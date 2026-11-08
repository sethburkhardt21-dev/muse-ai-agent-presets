# Software Engineer — runnable generic specialist

A neutral, configurable Muse-oriented engineering specialist with real offline execution-safety modules, reproducible tests and a source-controlled role playbook.

## Implemented today

The runtime/claim-gate directory contains nine Python source files: the original-source-neutralized atomic Claim Gate and its retention, lease, fencing, approval, composite and restart dependencies, plus a source-bounded CLI. The skills/claim-gate directory contains neutral skill metadata and a runbook.

Stage a brand-new local pack:

    PYTHONPATH=src python -m muse_presets.engineering_pack --to ./my-software-engineer

Run the synthetic example on POSIX:

    PYTHONPATH=src python examples/software_engineer_claim_gate_demo.py

The original locking uses POSIX fcntl, so execution on native Windows is not supported. Staging is source-only; this does not register a native Muse skill, grant any host permission or execute an external effect.

**R32 release-blocker repair candidate:** The pack inspector now checks a
closed file/directory set and source-pinned runtime/skill hashes, rejects
unknown executables, forged receipt authority claims and symlink/junction
ancestors, while retaining OWNER_CUSTOMIZED for owner-editable profile files.
Claim Gate's explicit terminal prune uses a per-scope local retention-log
anchor; damaged, missing or unanchored retention history holds further
claims for reconciliation. These are source-level safety checks, not a
cryptographic publisher identity or a native host authorization. A caller
with write access to every local state file can still erase both a log and
its local anchor; production effects require independent durable recipient
receipts/fencing. Redistribution rights remain on HOLD.

**R32 source-pin continuity:** The stager now takes a second checked
snapshot of all nine Claim Gate modules, the Vault and Iron Ledger modules,
their three ENGINE.json policies and every SKILL.md/skill.yaml. It rejects
post-preflight changes **before creating a destination** and copies only
frozen, already-pinned bytes. An injected change to a skill, enabled
`include_in_prompt`, or manifest-declared external tools cannot become a
successfully staged policy. The built package is read back against those
frozen bytes before its completion marker clears. These guarantees are local
and still do not prove publisher-signed code origin or host authorization.

## Local Provenance Vault candidate (R32, release review pending)

The create-only stager now carries a separate, source-pinned local provenance
component with digest-qualified file references, bounded donor-manifest
admission, source inventories, and locally checkable seals bound to the
existing Evidence Finder receipt-chain head. It also emits strictly
unsigned local subject statements and produces read-only adoption
membership previews; these can be recomputed against the original Finder
head but are NOT signed, installed or approved. The new R32.1c local writer
can copy only preview-verified bytes into a new caller-approved scratch
quarantine with a recovery marker and self-checked local receipt. The
R32.1d source-only ZIP export/restore path verifies a finite whitelist of
stored members, refuses malformed/changed archives before restore, and
preserves incomplete destinations without an automatic retry. R32.1e adds
read-only source-drift and dependent-quarantine reviews: a changed donor
source produces a local invalidation RECOMMENDATION, while missing evidence,
new Evidence Finder receipts, expired pins and corrupted custody produce
HOLD. It never changes the original adoption registry or a native skill. These are
offline custody tools, not a distribution/license approval.
It does not write another ledger, shared admission registry or native host state. It does not make native Muse calls,
access remote source, certify signatures, authenticate donor owners or
grant redistribution rights.
The local runtime and opt-in skill are staged with source+instruction hashes.

This is a narrowly tested original-source-guided adaptation, **not** a complete
port of the original Provenance Vault (full source-state tracking, signed
attestation, independent seals, original drift-log transport,
authenticated adoption registry, release-grade export/restore, donor drift
invalidation, authenticated roles, reconciliation and host hooks remain pending). Its
local seal and unsigned subject statement are not the donor's full
threshold-seal or authenticated attestation engines. Public publication
of this additional derivative requires its own source/rights review. Its output is local evidence only, not approval of any task/effect.

## Iron Ledger consumer — R32.2 local candidate (NOT public or native)

The source-only pack now stages an additional **read-only** Iron Ledger
consumer, adapted from the original consumer/registry/task-guard contracts.
It accepts an already-opened, owner-scoped Evidence Finder EvidenceLedger
from the host, verifies an exact list of receipt operation IDs, derives a
bounded in-memory index of digest/sequence and FOUND/NOT_FOUND metadata
(without copying finding text or source paths), then refuses an outdated
snapshot if the existing chain head changes. There is NO second SQLite
database, JSONL chain, registry sidecar, claim writer or task executor.

The module and opt-in skill are SHA-256 pinned before any destination is
created, and the source-only pack does not register it in native Muse.
Its caller-injected ledger resolver is NOT itself host authentication.
The R32.2b local TaskGuard recovery adapter can now classify an exact
task/run's **existing** Claim Gate record read-only, conservatively holding
UNKNOWN, corrupt, absent, unclaimed, unverified and local terminal states.
It never claims, releases, resumes, retries, certifies recipient success
or adds a second task-state controller. R32.2c additionally offers a
read-only comparison across the existing Claim Gate, an injected actor
assertion and an injected recipient outcome assertion. It strictly binds
owner/actor/session/recipient IDs and task/run/payload, rechecks the local
claim to detect changes, and always holds execution authority. Even
`LOCAL_CONSISTENT_UNAUTHENTICATED_HELD` is NOT a verified native host
principal or independent external recipient ACK: actual host adapters
must authenticate those separately. The original full Iron Ledger
ReceiptLogger, persistent RegistryIndex, mutating TaskGuard, authenticated
ProvenanceIndexer and native consumer binding remain unported.
Redistribution review of this additional original-guided capability is
separately held. Local success does not establish source rights or a
recipient-used skill.

## Still remaining for the full specialist

The original agent has additional engineering, source-provenance, evidence-ledger, collaboration, recovery and host-effect skills to qualify and neutralize. This release is the first functional vertical slice, not the entire original agent. Never install or merge this pack over an existing owner's memories or active services.

See INSTALL.md, playbook.json, and the shared Evidence Finder documentation in docs/EVIDENCE_LEDGER.md.

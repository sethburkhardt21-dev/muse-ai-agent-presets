# R33 Software Engineer — portable native-format bundle (private source candidate)

**Scope:** The Software Engineer is the first richer, role-specific generic
package. It is deliberately distinct from an existing personal Muse agent.
No donor identity, memory, host registry, native subchat ID, model account,
connector token or historical recipient state is copied or modified.

**Status:** Source-only, create-only, independently testable. Its local
Claim Gate is REAL and runnable on POSIX Python 3.12+. The native Muse
model/host invocation and receiver authority are **NOT CONNECTED**. This
bundle is PRIVATE_REVIEW_ONLY while the original-derived provenance and
rights review remains incomplete. Do not publish or install it into an
existing personal agent without a separate approved native-host pathway.

## Stage and inspect offline

From the generic repository root:

    PYTHONPATH=src python -B -m muse_presets.cli engineer-dropin --to ./new-engineer
    PYTHONPATH=src python -B -m muse_presets.cli engineer-dropin-inspect --path ./new-engineer

The destination must be absent and have an existing, admitted parent. Never
stage into a user's active Muse home or any original donor VM. Both commands
perform local file operations only. A zero exit is **not** Muse installation.

On Windows PowerShell, set $env:PYTHONPATH='src' first; use the same
python -B -m muse_presets.cli commands. Windows can stage and inspect but
the original POSIX fcntl Claim Gate refuses native Windows execution.

## Contents and genuine executable capability

- **engine/** — previously qualified, source-pinned Software Engineer pack.
  engine/runtime/claim-gate/engineering_claim_gate.py is executable
  source code, backed by Claim Gate modules. Vault and Iron source are
  pinned; Iron consumes an existing Evidence Finder ledger and cannot
  create a competing receipt authority.
- **custom-skills/** — three specific skill descriptors with source-derived
  instructional bodies, pinned names, skill.yaml, and a bounded
  engineering_claim_gate/run.py executable. The latter runs an actual
  claim/reuse/UNKNOWN/inspect sequence in temporary synthetic state.
- **config/skills.yaml** — all three role skills recorded as disabled.
  This is a package-local draft, not the receiving host's live registry.
- **system-files/** — neutral, editable-on-install profile drafts
  (AGENTS, IDENTITY, SOUL, USER, TOOLS, MEMORY, HEARTBEAT,
  preferences, system instructions, role playbook, and CONNECTORS/BROWSER/
  VOICE policy). No existing profile is overwritten.
- **subchats/** — separate diagnostics, implementation, and
  verification role/context/memory/tool contracts plus unbound
  SUBCHAT.json. Every native chat ID remains null until obtained from
  an authenticated receiving host, and no chat is actually spawned.
- **hooks/HOOKS.json** — opt-in declaration, enabled=false.
- **scripts/doctor.py** — standalone read-only self-hash and closed-tree
  inspector. It can detect accidental or unsophisticated tampering, but
  a self-hash is NOT a publisher signature against a malicious party
  capable of changing all files and the manifest.
- **receipts/R33_DROPIN_RECEIPT.json** — exact local file and directory
  inventory, source integrity, default-deny host policy, rights HOLD.

Run the exact source canary on macOS/Linux with Python 3.12+:

    python3 -I -B ./new-engineer/custom-skills/engineering_claim_gate/run.py --canary

Expected result: LOCAL_CLAIM_GATE_CANARY_PASSED, with observed statuses
LOCAL_CLAIM_RECORDED, LOCAL_CLAIM_REUSED, LOCAL_UNKNOWN_HELD,
LOCAL_CLAIM_OBSERVED. This is an actual execution of the staged
Claim Gate code against fiction-only temporary files. It does NOT call
a Muse model, claim owner grants, touch a recipient, or invoke an external
software change.

Run the portable offline doctor without repository Python imports:

    python -I -B ./new-engineer/scripts/doctor.py

Expect LOCAL_SELF_HASH_MATCH with native and effect flags false.
For a high-confidence source readback, additionally use the repo CLI
engineer-dropin-inspect: that compares the nested original-source
runtime/skills to the current repository's pinned source, not only to
the mutable local receipt.

## Receiving-host integration remains an explicit future gate

The supported owner-authenticated host must independently prove (1)
native file/profile ingestion and instruction precedence, (2) native skill
registration and opt-in catalog changes, (3) authenticated subchat IDs
and per-subchat memory ownership, (4) a genuine model-selected tool call
with provider-issued event and actual claim/engine invocation, and (5)
independently verified recipient result/negative wrong-owner refusal.

No hidden shell API, forged owner ID, ephemeral CLI record, local
registered:true label or direct modification to a donor VM can
substitute. The existing staging CLI intentionally does not perform a
receiving-owner install or register the three source-only skills.

## Upgrade, rollback, and partial-stage recovery

The stager refuses a destination that exists. An interrupted stage
leaves STAGING_INCOMPLETE and must be reconciled instead of auto-retried.
Before any receiving-owner adoption, retain a separate copy of their
actual profile/state and compare path-by-path with this source pack.
No automated installer, upgrade, rollback or uninstall is claimed here;
those are the separate R32.S3 work item and require an authorized host
transport. To discard only your own disposable staging directory, verify
its exact path and ownership first. Never delete a user's existing Muse
account, memory, original skill tree or live scheduler.

### Qualification checklist

The required source gates are a fresh local stage, inspector readback,
unsupported-Windows refusal, real POSIX Claim Gate canary, corrupted file,
forged grant, disabled native catalog, changed policy, missing subchat,
symlink/extra file refusal, archive extraction/reopen, and full A/B/iMac
regressions. Native loaded-state, authenticated invocation, durable
recipient readback, operating permissions and public licensing remain
NOT_RUN / HOLD until independently proven.

# Software Engineer — runnable local engine pack

This is a neutral, source-derived engineering specialist package. It contains real executable claim and recovery machinery plus a create-only profile and skill stager. It is NOT a natively activated Muse assistant.

## Create-only offline staging

From the repository root:

    PYTHONPATH=src python -m muse_presets.engineering_pack --to ./my-software-engineer

Choose an absent destination whose parent already exists. The staging command creates a profile from the public role templates, copies only the source-pinned runtime and neutral skill, and writes a local receipt. It refuses existing destinations. It never reads, imports or modifies a recipient's installed memory, skills, chats, connectors or schedules.

For the R32 safety-repair candidate, the staging path and the source/state
paths of the POSIX Claim Gate CLI also refuse arbitrary symlink ancestors
and Windows NTFS junction/reparse points. Only exact, verified macOS
system-level /var, /tmp or /etc aliases may be followed. An authorized
canonical root is still a separate host requirement.

The package inspector validates the complete expected staged layout and
the runtime/skill files against the implementation checkout's source-pinned
manifests, not just a mutable PACK_RECEIPT checksum. It refuses unlisted
executables, changed policy code and impossible receipt claims. It retains
the limited OWNER_CUSTOMIZED classification for owner-editable profiles;
a LOCAL_MATCH result is NOT an independently authenticated release seal.

The R32 source-policy TOCTOU fix freezes an independently rechecked snapshot
of every approved executable, SKILL.md, skill.yaml and ENGINE.json *before
creating the destination*. The stager copies **only** those pinned bytes,
rechecks staged policy bytes before writing a receipt, and leaves a failure
or interrupted destination for reconciliation rather than declaring
LOCAL_ENGINE_PACK_STAGED. Race-injection tests deny late changes to all three
skills and Iron Ledger's invocation/authority metadata. The local checkout
and its manifests are not independent signatures; native Muse owner grants
and public-source licensing remain separate.

## Offline demonstration on a POSIX host

    PYTHONPATH=src python examples/software_engineer_claim_gate_demo.py

The eight original-source-neutralized engine files and the bounded CLI are in runtime/claim-gate. The original Claim Gate uses POSIX fcntl locking and does not run on native Windows. Staging on Windows is allowed, but no native-Windows runtime qualification is claimed.

Explicit operator pruning of terminal claims now writes a local per-scope
digest-log anchor and then removes the old terminal record. If that log
or anchor is missing, malformed or inconsistent, claims are HELD; no new
effect can be inferred from an absence. Existing unanchored legacy logs
must be reconciled by an operator, not silently migrated. These two
locally writable files are not independent tamper-proof evidence. Without
an externally controlled witness, a malicious deletion of both cannot be
distinguished from a truly fresh state; disable destructive pruning for
such production scopes until recipient-side durability is established.

The R32 local candidate also stages one neutralized source-provenance module,
its pinned manifest, and an opt-in skill. This component verifies digest
references and matches donor-manifest assertions against a caller-supplied
local registry. It also supports bounded read-only inventories and pure
local source seals correlated to an existing Evidence Finder verify() head,
not a second receipt ledger. Inventory requires an owner-approved absolute
path and refuses symbolic-link ancestors, Windows junctions, and unbounded
source trees. macOS may expose temporary paths through the system `/var`
symlink; use an explicitly authorized, canonical resolved root rather than
weakening symlink-parent checks. This cannot detect coordinated rewrites of
both the seal and the original database without an external trusted anchor.
The R32 statement API emits only UNSIGNED local observations with strict
subject digests; its adoption preview API is read-only. The separately
opted-in R32.1c local quarantine writer copies preview-pinned bytes into an
exclusively absent directory under an existing, canonical, caller-authorized
scratch parent. Its caller-provided action-time guard is not host-issued
authenticated authority. Each copied file is rehashed, the local manifest
and receipt contain no absolute private donor path, and an interrupted
stage is preserved for manual inspection rather than automatically retried.
R32.1d also offers guarded offline local ZIP export/restore of that
already-verified quarantine, but requires an absent archive and restore
destination. Every archive member and source digest is checked before a
restore directory is created. Interrupted archive/restore files remain in
place for manual reconciliation; no automatic retry or overwrite is allowed.
The expected archive SHA-256 comes from a separately observed local export
receipt, NOT a signed publisher identity. R32.1e can subsequently check a
local quarantine's dependent-source snapshot and current Evidence Finder
head without modifying any files: exact source drift recommends manual
invalidation, while unknown source, changed receipt chain or expired seal
holds it for independent review. A receipt that calls a dependency CURRENT
is local evidence only, not a release/native validation or a guarantee
against later source changes. It does not revoke an original adoption or
install any Muse tool. This does NOT approve builders, implement the
original authoritative adoption registry, or install native Muse tools. Verify each preview against fresh source and the existing Finder
head before any effect. It does not independently authenticate
that registry or license the code it describes. Its extra source/rights
gate remains pending
before any subsequent public release.

## Iron Ledger read-only consumer (R32.2 candidate)

The new runtime/iron-ledger module is a *read-only adapter* for a separately
existing, owner-scoped Evidence Finder EvidenceLedger. The pack does not
install Evidence Finder's own SQLite service or create another receipt store.
The adapter can only inspect explicitly requested operation IDs and
validate those records against the same existing hash-linked head. It does
not persist an index; any head change requires a fresh explicit review.

The adapter is importable standalone from the staged Python file, but
the caller must provide the actual opened Evidence Ledger service and
separate real host permissions. A synthetic injected resolver is an offline
test fixture, not a credential or native Muse authorization. The R32.2b TaskGuard recovery adapter reads existing Claim Gate
`reconcile_unknown` only, binding exact task/run and payload digest,
but does not change claim state. In particular a missing claim is held,
a local terminal claim does not constitute an independently verified
recipient acknowledgment, and UNKNOWN never allows retry or release.
The original private TaskGuard's unsafe release/reclaim methods were
not ported. R32.2c adds a three-reader **observation-only** contract
using the existing Claim Gate plus explicit host actor and recipient
report readers. Only exact matching scope/task/run/payload/owner/actor/
session/recipient IDs are accepted. A fresh final Claim Gate read
detects changed local claim history. The returned status remains held,
even if all caller-supplied reports are consistent: no native Muse
authentication, independent recipient signature, live host credential,
lease, permission or effect has been verified here. This feature does
not replace existing Claim Gate lease/fencing machinery and has no
automatic effect or source redistribution rights.

## R33 neutral standalone native-format composition

In addition to this original source-only engine package, the R33 Software
Engineer builder stages a **separate** portable drop-in with actual neutral
system-file drafts, three native-style custom skill descriptors, a disabled
host-local skills.yaml proposal, structured diagnostics/implementation/
verification subchat contracts with NO host IDs, hooks OFF, a verified source
engine, and a real POSIX Claim Gate canary.

    PYTHONPATH=src python -B -m muse_presets.cli engineer-dropin --to ./new-engineer-dropin
    PYTHONPATH=src python -B -m muse_presets.cli engineer-dropin-inspect --path ./new-engineer-dropin

The R33 pack does not automatically install into personal Muse, enable
skills/schedules, attach models or make external effects. Original-derived
source rights remain PRIVATE_REVIEW_ONLY. See
[Capabilities](../../docs/CAPABILITIES.md).

## Pack contents

- profile/: a new generic owner-editable profile generated by the existing public renderer, with no imported donor memory
- runtime/claim-gate/: source modules, local CLI and hash manifest
- skills/claim-gate/: neutral skill procedure plus opt-in source metadata
- runtime/provenance-vault/: bounded, locally callable Python source checks and a SHA-pinned manifest (candidate)
- skills/provenance-vault/: disabled-by-default instructions and source-pinned skill metadata
- runtime/iron-ledger/: source-pinned read-only Evidence Finder receipt consumer, with no persistent database
- skills/iron-ledger/: opt-in, disabled-by-default scoped receipt verification procedure and hash-pinned metadata
- receipts/PACK_RECEIPT.json: exact local hashes, legacy source metadata only, not an owner-first-party licensing blocker; explicit source-only grade

An external action must be separately authorized through the true host at the effect boundary. The CLI never runs shell code, deploys changes, signs approvals or sends messages. A claim is only local idempotency state.

## Before native admission

Verify the supported Muse API, real owner/session/tool scope, a model-originated tool invocation, denial for an unauthorized principal, original recipient readback and restart/UNKNOWN reconciliation. Mere disk installation, rendered profiles, hashes and scripts cannot prove a live skill is wired or used.

## Portability

The live-source gate was qualified with POSIX locks. A Windows lock implementation would require a distinct implementation and concurrency/crash suite. All external effects remain disabled. The user owns their local profile and must approve any future native registration.

## GitHub source-only quickstart (R45)

From the repository root with PYTHONPATH=src, run:

    python -B examples/github_quickstart.py --role software-engineer --to ../new-software-engineer

The destination must not exist. This stages and inspects the neutral
source profile/subchats/disabled skills and runs a local synthetic
connector fixture. It does not install a native Muse agent or enable
a provider. See [GitHub quickstart](../../docs/GITHUB_QUICKSTART.md)
and [extension methods](../../docs/EXTENDING_GENERIC_AGENTS.md).

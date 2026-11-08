# R40 / T04: complete portable system-profile drafts for eleven roles

This layer composes the existing neutral profile templates and role-specific
playbook renderer. It adds shared CONNECTORS, BROWSER and VOICE procedures,
an explicit disabled host-binding proposal, source pins, closed-tree inspection,
and a read-only change preview. It does not install a Muse agent or claim that
a model has loaded these files.

## Create and inspect a role

Use Python 3.10+ with the repository source on PYTHONPATH. In PowerShell set
`$env:PYTHONPATH='src'`; on POSIX prefix commands with `PYTHONPATH=src`.

    python -B -m muse_presets.cli system-profile-plan --preset software-engineer
    python -B -m muse_presets.cli system-profile --preset software-engineer --name "Engineering Helper" --to ./new-profile
    python -B -m muse_presets.cli system-profile-inspect --path ./new-profile
    python -B -m muse_presets.cli system-profile-preview --path ./new-profile --target ./existing-owner-profile

All eleven role IDs from `presets/catalog.json` are supported. Replace the role
with coordinator, model-builder, research-evaluator, creative-studio,
adversarial-verifier, personal-companion, garden-companion, learning-coach,
claims-adjudicator or reverse-engineering-researcher as appropriate. Evidence
Finder remains a shared service, not a twelfth profile.

To bind staging to an earlier plan, repeat its role and display name and supply
`--source-sha256` with the plan's exact digest. A mismatch is refused before
creating the destination. The destination must be absent; its parent must exist.

## File layout and ownership

`profile/` contains AGENTS, SOUL, IDENTITY, USER, TOOLS, MEMORY, HEARTBEAT,
PROACTIVE_PREFERENCES, SYSTEM_INSTRUCTIONS, SUBCHATS, HOOKS, CONNECTORS,
BROWSER, VOICE, ROLE_PLAYBOOK and disabled FAMILY_LINK metadata. Each role's
playbook contains its own actual methods, triggers, evidence and refusal rules.
The original base renderer and existing role packs remain compatible.

`config/host-binding.json` is a declaration, not a live host registry. Owner,
agent and provider-session IDs are null. Native loading/registration, effects,
hooks, scheduling, Family Link and voice are all disabled. The receiving
platform's actual policies always take precedence over draft instructions.

`PROFILE_MANIFEST.json` records role, display name, exact source hashes and
rendered-file hashes. Inspecting from a trusted repository recomputes expected
outputs; altering both a draft policy and its local hash cannot hide the change.
These hashes are not publisher signatures or provider-issued credentials.

IDENTITY, SOUL, USER, MEMORY and PROACTIVE_PREFERENCES are receiving-owner
customizations. Inspection reports changes without replacing them. Changes to
AGENTS, tool/connector/browser/voice policy, the role playbook or the disabled
host binding require explicit review. No donor memory, credential or real host
identity is copied into any profile.

## Preview semantics

The preview reads only the named profile files in an explicitly selected target.
It labels each proposed file CREATE, UNCHANGED, PRESERVE_OWNER_EDIT or
REVIEW_CONFLICT. It never writes, merges, deletes or activates anything; unknown
owner files remain untouched. `can_apply` is always false. The native installer,
subchat ownership and skill registration belong to later host-specific gates.

Expected inspection statuses:

- `LOCAL_SYSTEM_PROFILE_MATCH`: exact source-derived draft, no native claim.
- `OWNER_CUSTOMIZED`: personal draft files changed; preserve those bytes.
- `SOURCE_DRIFT`: upstream source pins differ; review before regenerating.
- `INCOMPLETE_STAGE`: interrupted operation remains fenced for recovery.
- `REVIEW_REQUIRED`: missing/extra files, modified policy, forged receipt or unsafe path.

A partial stage is not automatically deleted or retried. Recover its original
operation before choosing a new explicit destination. Symlinks/junctions and
literal traversal are refused according to the shared path-admission checks;
this is not a sandbox against another privileged process racing the filesystem.

## Verification boundary

Source acceptance covers eleven distinct generated profiles, exact source pins,
owner-state preservation, mutation/refusal cases, CLI behavior and cross-OS tests.
It does not establish supported native loader precedence, installed chat IDs,
model-selected native tools, actual callbacks or recipient readback. Those
require an authorized disposable receiving host and separate provider evidence.
The owner has already authorized reuse of their first-party code; retain privacy
and actual third-party dependency checks without inventing a new rights blocker.

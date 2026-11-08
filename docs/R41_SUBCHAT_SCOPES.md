# R41 - Scoped subchat source packs for eleven generic agents

**Grade:** LOCAL_SCOPED_SUBCHATS_ONLY. This is a portable, create-only
source artifact, **not** a Muse/Hatch subchat installation, identity grant,
native model invocation, scheduler, delivery transport or memory database.

The T04 system profiles (R40_SYSTEM_PROFILES.md) provide the root
AGENTS/SOUL/IDENTITY/TOOLS/MEMORY/prompt drafts. R41 creates method-scoped
subchat folders with independent context and owner-editable memory/preferences.
The T05 source milestone can proceed while the authenticated provider
discovery/recipient proofs remain open in T02/T32.

## Exact construction

Each of the **11** neutral role IDs from presets/catalog.json has exactly
three distinct role-playbook methods. R41 creates **33** nonempty subchat
directories, named after their validated method IDs, and one read-only
config/subchats.json host-binding proposal.

Each method folder contains:

- ROLE.md: role, purpose, trigger and method identity
- CONTEXT.md: its actual procedure, evidence, stop rule and next-role proposal
- AGENTS.md: independent scoped instructions, subordinate to host policy
- TOOLS.md: capability categories only, never actual tool grants
- MEMORY.md and PREFERENCES.md: new owner-editable blanks, never imported
  from original Muse agents or another receiving owner
- HEARTBEAT.md: disabled; nothing scheduled
- skills.yaml: version-one registry with **no active entries**, awaiting
  the separate T06 native registration contract
- SUBCHAT.json: unbound owner, agent, session and chat IDs with
  native_installed, native_loaded, model invocation, recipient readback
  and external effects all disabled

Root SUBCHAT_RECEIPT.json is a source-pin and closed-tree comparison
manifest, not a signature, issued chat ID or runtime permission.
It is recomputed against current repository source; changing a policy
and its self-reported receipt cannot conceal that modification.

## Commands - source only

Run from a fresh, owner-approved disposable directory, with an existing
parent, Python 3.10+ and PYTHONPATH=src. On PowerShell configure
$env:PYTHONPATH='src' first.

    python -B -m muse_presets.cli subchat-scopes-plan --preset garden-companion
    python -B -m muse_presets.cli subchat-scopes --preset garden-companion --to ./garden-rooms --profile-source-sha256 SHA_FROM_PLAN
    python -B -m muse_presets.cli subchat-scopes-inspect --path ./garden-rooms
    python -B -m muse_presets.cli subchat-scopes-preview --path ./garden-rooms --target ./receiving-owner-rooms

Use any of the eleven existing role IDs. Optional --name must match
the T04 main profile display name when binding its source hashes.
The profile_source_sha256 from T04's plan is checked before any
destination is created. No command installs into an original live agent.

## Owner state, source drift and recovery

Occupied destinations are refused, not overwritten. Existing owner
memory and preferences are never copied, deleted or merged.
Preview is read-only and labels each file CREATE, UNCHANGED,
PRESERVE_OWNER_EDIT or REVIEW_CONFLICT; can_apply is always false.
Unknown receiving-owner files remain untouched.

Inspection reports LOCAL_SUBCHATS_MATCH for pristine drafts;
OWNER_CUSTOMIZED for changes restricted to owner memory/preferences;
SOURCE_DRIFT for admitted source hash changes; and REVIEW_REQUIRED
for modified method/tool/role policy, missing files, extra executables,
invented native IDs or unapproved skills. Symlinks, junctions,
traversal and unsafe destinations are refused at source scope.

Interrupted staging retains STAGING_INCOMPLETE; never automatically
delete or retry until its original operation is reconciled. No
task database, persistent live chat transcript or actual per-subchat
owner-memory service is represented by these text templates.

## Native adoption remains a separate host gate

1. Discover provider-issued receiving-owner, agent and side-chat IDs
   through an authenticated supported personal Hatch interface.
2. With owner consent, register exact admitted profiles, scoped method
   folders, skills and policy using supported host APIs.
3. Demonstrate host-loaded effective prompt and precedence, distinct
   subchat memory ownership, model-selected invocation and provider ID.
4. Independently reopen actual recipient output, restart/persist state,
   demonstrate wrong-owner refusal and safe rollback.

Original reference-host side-chat folders are only structural evidence,
not authorization to copy its owner identity or assert newly generated
subchats have been installed. Current local probes did not establish
native registration or recipient readback.

T06 may add role-scoped skill-registration proposals, but must not mark
skills.yaml connected or available without provider-issued evidence.
T07/T32 own native installation, upgrade and end-to-end acceptance.
No new model, cron, connector or external transport is activated.

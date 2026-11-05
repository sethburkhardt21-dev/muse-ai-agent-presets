# Install, customize, update, recover

## What is available today

Run `PYTHONPATH=src python -m muse_presets.cli render --preset learning-coach --to ./my-learning-coach --name "My Learning Coach"`. This creates a **local draft**. It does not deploy into Muse. `doctor` checks local source only.

## Offline inspection of rendered drafts (source increment after v0.1.0-alpha)

A new `render` includes a `render-v2` local receipt recording the exact preset/template hashes and generated managed-file hashes. Run:

```bash
PYTHONPATH=src python -m muse_presets.cli inspect --path ./my-learning-coach
```

The command is **read-only**. `LOCAL_MATCH` means its files match the untrusted original local receipt; `OWNER_CUSTOMIZED` names changed personal/instruction files without altering them; `REVIEW_REQUIRED` flags missing files, source drift or changed Family Link policy; `LEGACY_UNVERIFIABLE` preserves older v1 profile drafts without guessing their baseline. Symlinked managed files and malformed manifest entries are refused. An altered receipt could be forged together with the files: hashes are not signatures or host attestation. **None of these statuses prove Muse installed, loaded, refreshed or used the draft.** Source updates and user changes require a later, owner-authorized three-way merge; `inspect` never performs one.

## Planned host-aware installation

1. Identify the correct receiving account, host type, current SDK/schema and callable tools. Stop on mismatch.
2. Back up owner-controlled configuration and record original hashes. Do not export personal memory or tokens into source releases.
3. Stage the approved package in a new path. Never blind-sync over a live tree.
4. Apply only permitted package-owned files through supported host interfaces; obtain real version/registration receipt.
5. Read the loaded instruction or skill in a new turn, not merely the file on disk.
6. For hooks, schedules, subchats, Spaces or connectors, obtain separate approvals and original host IDs. No automatic activation.
7. Run a representative native task and verify the recipient outcome before marking `WIRED/USED/USEFUL`.

## Files and ownership

`AGENTS.md`, `SOUL.md`, `IDENTITY.md`, `USER.md`, `TOOLS.md`, `MEMORY.md`, `HEARTBEAT.md`, `PROACTIVE_PREFERENCES.md`, optional instructions, hooks, scripts, Spaces and generated artifacts have **different write owners**. The package owns defaults; the person owns overrides and private memories; Muse owns host IDs/credentials/scheduled registrations; the original task ledger owns receipts. They must never be silently merged into one mutable file.

## Regeneration / persistence

For a managed-file refresh or VM replacement: observe current loaded source, compare approved template + prior installed baseline + current user edits (three-way), restore only authorized package-owned portions and revalidate the new host. Preserve conflicts with their original hashes; do not resolve them by guessing. An auto-generated file may overwrite external edits; move durable user configuration to an owner-controlled supported path, then verify how the host loads it.

A saved `HEARTBEAT.md` is advisory. A script is not an active hook. An ID in a manifest is not a native chat. Home disk persistence is not equivalent to full prompt injection or correct memory indexing.

## Recovery and uninstall

No blind retry of unknown external effects. Release only owned reservations, stop only owned child processes, retain failure evidence. Uninstall package-owned files only after checking hashes and current user changes; do not delete native private state or existing jobs without explicit owner authority. No automatic wake or hook is shipped in this alpha.

# Neutrality, owner-state separation and provenance

A preset is **Muse-compatible by design**, not bound to a private creator, a specific account, a particular model, a named family, or a single machine. Host-specific facilities remain optional adapters, not secretly required defaults.

## Auditable contract

- Every `presets/<id>/preset.json` uses a stable neutral role ID, `SOURCE_TEMPLATE_ONLY` maturity, `UNBOUND` native state, an empty set of required secrets/permissions and disabled Family Link transport.
- Every `presets/<id>/playbook.json` has three clearly scoped specialist procedures, original evidence expectations, a stop rule and only allowlisted proposed recipients. The renderer converts this into owner-readable `ROLE_PLAYBOOK.md`.
- `render` creates a fresh local draft with blank owner memory and `render-v3` content hashes. `inspect` detects changed playbook/Family Link policy as `REVIEW_REQUIRED` and preserves owner edits. It supports older v2 drafts without inventing a missing playbook.
- `audit-neutrality` is a **bounded, fail-closed source heuristic** for the entire public distribution: role presets, templates, shared services, source modules, examples, tests, scripts, workflows and top-level files. It checks local machine paths, credential-shaped content, personal email addresses, symlinks, oversized files, non-UTF-8 assets and unreviewed binaries, without exposing matched contents. Git internals and generated tool caches are excluded. It is not a full secret/PII scanner, Git history audit, license audit or malware detector.
- CI executes the full-distribution check explicitly with read-only repository permissions. A private maintainer-side screen supplies any restricted names separately; a public release must never embed original personal names just to blacklist them.
- Before public release, review historical blobs and commit attribution separately: a clean HEAD does not erase an earlier commit. Never rewrite public history, revoke keys or change Git authorship silently.
- No generated configuration contains original Muse chat IDs, host secrets, private user profiles, system-level prompts or live permission grants. Owner configuration is created by the receiving account and never committed by the installer.

## Ownership across updates

| Surface | Source owner | Mutable by recipient? | Safe update rule |
| --- | --- | --- | --- |
| Preset manifest and role playbook | Public package | Locally configurable draft; policy changes require explicit review | Compare version/hash, revalidate, never silently overwrite |
| Identity/personality and owner preferences | Recipient | Yes | Three-way merge with owner choice; preserve custom text |
| Personal memory, contacts and actual chat history | Recipient/Muse native runtime | Yes, according to host controls | Never export, replace or regenerate from the public repository |
| Real tool registration, hooks, schedules, Spaces and chat IDs | Muse native host | Only through authorized APIs | Observe original host effect and readback; no fake IDs |
| Cross-agent messaging and Family Link | Independent named recipient/controller | Explicit opt-in | Keep disabled unless real identity, permissions, transport and receipt are verified |

## Portability tests

The source suite checks consistent role IDs and handoff policies, refusal of private paths/secrets, separation of user edits and policy drift, and compatibility of old v2 receipts. A future clean-host suite must additionally change the display name, locale, timezone, account, model, OS and machine path, then prove the actual loaded behavior rather than merely the file copy.

Public redistribution requires a clean Git history, independently reviewed license/asset notices and a separate human/automated secret review. A source template is never a right to publish proprietary Muse SDK internals or personally identifiable files found in original development trees.

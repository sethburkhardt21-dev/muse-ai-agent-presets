# Daily Desk — reusable full-stack design contract

**State: design qualified for the next source slice; new Daily Desk task UI, task persistence and archive restoration are NOT_IMPLEMENTED by this collection promotion.** No native Space is deployed here. This document prevents a second backend from being built while an existing reusable implementation is available.

## Existing baseline to recover, not recreate

The owner-maintained full-stack Space starter already implements `SpaceCompanion`, using the existing `PersonalCompanion` storage helpers. Its source contract is `space-starter/1`: local SQLite notebook persistence, guarded request state, stable operation identity, cancellation, UNKNOWN recovery and an opt-in injected callback boundary. A loopback HTTP adapter and browser assets already exist. These source components were previously qualified separately; this public skill-collection update does not copy them into a new app or relabel their historical tests as fresh runs.

The next implementation writer must recover the exact current starter source, tests, runtime policy and ownership before creating a task schema. Preserve its Host/Origin/body/CSP checks, default-disabled effects and prohibition on browser-supplied callback authority. Do not introduce another scheduler, account identity or generic agent service.

## First useful result

A new owner-controlled local desk should create **3 tasks** and **2 notes**, edit one task and one note, close/reopen the client, export an archive and restore it into a new empty store. The restored IDs, fields, revision numbers and content hashes must equal the exported snapshot. This is an application-storage test, not a native model call or a sync guarantee.

The screen is a toolbench: task list and filters, note editor, source/version panel, review and export controls. Conversation may offer an optional command surface but must not be the persistence store. All seed content is fictional. Calendar, email, reminders and provider jobs remain off until separately authorized.

## Proposed operations and ownership

Reuse existing authenticated/injected owner and Space scopes in the storage/service boundary. Add task creation, read, revision-checked update, completion/reopen, soft archive and list filters. Each mutation needs a stable operation ID bound to the exact payload. Identical retries return the original result; conflicting reuse refuses; a stale expected revision must not overwrite a newer edit.

A task record needs a stable ID, title, explicit status, optional due time with timezone, revision, creation/update timestamps and source note references. A note needs stable ID, body, revision and attachment references, not raw embedded credentials. Existing IDs and migration records must survive upgrade. Do not trust owner identity sent in browser JSON as proof of authority.

## Verify

Required checks: fresh database creation and migration; canonical input validation; wrong owner/Space; duplicate request; conflicting operation ID; stale revision; lost acknowledgment; cancellation; interruption with UNKNOWN rather than auto-replay; consistent export snapshot; archive corruption; restore to occupied destination; traversal and symlink rejection; and reopen in a separate process. Test source export without private data.

Browser acceptance covers empty/loading/success/error/recovery states, keyboard navigation, meaningful labels, narrow-screen overflow, persistent edits and wrong-target refusal. A receipt from synthetic callbacks must be labeled synthetic. A static publish or working local page is not proof of a native Muse bridge.

## Failure and recovery

Never restore over an existing owner's database. Make a new destination, verify the manifest and migration compatibility, then present the result for a deliberate owner selection. If an update's outcome is uncertain, query its original operation before issuing a new ID. Keep conflicting versions and let the owner reconcile; do not silently pick the newest timestamp.

## Scope and evidence

This is a source-bound extension plan for the existing `SpaceCompanion` / `PersonalCompanion` implementation. The first shipping milestone is the narrow persistence journey above with a working UI, not five unfinished dashboards. The broader five-foundation/fifteen-toolbench plan remains separate. Native deployment, client account binding, real connector effects and Watch acceptance are not prerequisites for the local source milestone and are not claimed by it.

# Daily Desk — reusable full-stack design contract

**State: the first local Daily Desk slice is implemented** with three tasks/two notes, editing, reopen, stale-revision refusal and create-only export/restore. [Run Daily Desk](../spaces/DAILY_DESK.md). Native Muse deployment, connector effects and the remaining dashboard families are NOT_IMPLEMENTED by this slice. This is a local toolbench on the existing backend, not a new hosted service.

## Existing baseline to recover, not recreate

The owner-maintained full-stack Space starter already implements `SpaceCompanion`, using the existing `PersonalCompanion` storage helpers. Its source contract is `space-starter/1`: local SQLite notebook persistence, guarded request state, stable operation identity, cancellation, UNKNOWN recovery and an opt-in injected callback boundary. A loopback HTTP adapter and browser assets already exist. Daily Desk now reuses these first-party components and their original regression suites, with its own task/note extension and new tests. Historical tests are not substituted for fresh qualification.

The implementation recovers the original starter source, tests, runtime policy and ownership before extending its schema. Preserve its Host/Origin/body/CSP checks, default-disabled effects and prohibition on browser-supplied callback authority. Do not introduce another scheduler, account identity or generic agent service.

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

## Implemented boundary

The runnable UI and archive API are in the [Daily Desk guide](../spaces/DAILY_DESK.md). A restored store preserves task/note IDs, revisions and receipt history, but intentionally gets a new database-instance identity so pending browser writes cannot target a replacement store. Existing Space request/callback policy stays separate and disabled by default. Future iterations must retain that distinction.

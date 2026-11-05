# Garden Companion: offline, owner-scoped calendar engine

**Grade: `LOCAL_SQLITE_TESTED` only.** The source uses only the Python standard library. It does not register a Muse skill, verify a native identity, deploy a Space, send Family Link messages or synchronize an external calendar.

This new, neutral implementation retains the most useful behavior from an existing design brief: bounded seasonal edits, explicit owner review, revision fencing, all-or-nothing SQLite transactions, durable operation IDs and readback after interruption. It is not a copy of the original application, its private assets, user data, migrations, or proprietary runtime code.

## Run the exact local vertical

From the repository root:

```bash
PYTHONPATH=src python examples/garden_calendar_demo.py
PYTHONPATH=src python -m unittest discover -s tests -p 'test_garden_calendar.py' -v
```

The demo creates a disposable SQLite file for a fictional owner. The owner records a planting event; a separate, scoped specialist proposes a two-day shift; the owner reviews the exact before/after change and authorizes it; a fresh process context reopens the event and original operation receipt. It prints a *local-only* grade and removes the temporary data.

## Original trust boundary (not yet connected)

`GardenCalendar(database, authority=host_resolver)` rejects missing authority, and calls `host_resolver` on every operation. The resolver **must** be supplied by the authenticated Muse server using independently verified current account/Space/garden and actor identities. Do not build it from request JSON, a chat message, a browser-supplied ID, a copied assistant name, or a client token. The local demo's `GardenScope` objects are **simulated fixtures, not secure credentials**. Anyone able to instantiate arbitrary scopes in their own Python process can forge them; therefore this library alone is not a production authorization boundary.

`owner_browser=True` is required for direct event edits, cancellation, review, approval, decline and receipt readback. A scoped specialist with `owner_browser=False` may read the correct site's events and **propose**, never approve or mutate an event. The receiving host must enforce this separately before exposing methods.

The event list returns at most 100 events and includes an explicit `truncated` flag; it never represents a partial result as complete. All records are keyed by the owner, Space and garden identity; changing any one key isolates the entire event/proposal/receipt namespace. Event IDs, proposal IDs, operation IDs, event titles, dates, shifts, and batch sizes are validated. A proposal can shift 1–21 distinct events by at most 30 days per event, and expires after one hour by default (configurable within 1 minute–24 hours). A default per-garden quota holds at most 1,000 active, unexpired pending batch proposals (configurable up to 10,000); declined and expired history does not count toward this limit. No event is changed on proposal or review.

## Transaction and recovery rules

1. Read current event revisions and original dates before writing a proposal. An existing proposal ID with the same digest and proposer is returned without modification; conflicting reuse is refused.
2. Display the owner's `review_batch()` result with before/after records and explicit stale/expired findings. The review is read-only and **does not lock the future outcome**.
3. On approval, use one SQLite `BEGIN IMMEDIATE` transaction. Validate *every* event's scope, state, revision and original date; update all event rows; mark the proposal decided; and insert one immutable receipt. Any detected stale/cancelled event or injected SQL failure rolls back the entire transaction.
4. On lost acknowledgement, use the **original operation ID** and `receipt()` first. Repeating the same operation ID/decision returns the original receipt without repeating effects. Changing its decision, digest or proposal is an `OPERATION_CONFLICT`.
5. `OUTCOME_UNKNOWN_RECONCILE_BY_OPERATION_ID` is **not** permission to try again under another operation ID. Verify the original receipt and authoritative event revisions before proceeding.

The API-level receipt is durable across local reopen; it is not cryptographically signed or protected against someone with direct database-file write access. Direct owner cancellation and seed creation are local demonstrations and need native receipt/authorization review before production use. The schema is intentionally isolated and minimal; this is **not** a drop-in migration for an existing owner's Garden Space. Do not install it over a live database. Host storage, native session authorization, migrations, backup/restore, secure storage, UI approval and device readback require separate qualification.

## Evidence to claim all five layers

| Layer | Current state / required proof |
| --- | --- |
| EXISTS | `src/muse_presets/garden_calendar.py` and the independent regression suite are present |
| CORRECT | Local SQLite positive, negative, restart and injected-failure tests pass on exact source |
| WIRED | **Not proven:** real Muse owner/session resolver, managed Space actions and authorized database binding |
| USED | **Not proven:** original Muse assistant or owner performs the sequence on real persisted records |
| USEFUL | **Not proven:** independently tested real planting workflow on an authorized receiving account/device |

See [host compatibility](HOST_COMPATIBILITY.md), [lifecycle](INSTALL_AND_PERSISTENCE.md) and [five-layer definitions](FIVE_LAYERS_AND_DOORS.md). Family Link remains proposal-only and disabled in every preset.

## macOS portability regression

A clean iMac run of the R6 source found that the original SQLite file guard rejected macOS's standard root-owned `/var` → `/private/var` temporary-directory alias. The shared `database_paths` validator now recognizes only the fixed, root-owned macOS `/var`, `/tmp` and `/etc` system aliases while retaining rejection of user-controlled file, parent and grandparent symlinks. The existing Garden API and error codes are preserved. This check is not an authentication or filesystem-sandbox grant.

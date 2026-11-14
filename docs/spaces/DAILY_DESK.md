# Daily Desk: tasks, notes and a way back

Daily Desk is a small full-stack local workbench on the existing `PersonalCompanion` SQLite backend and `SpaceCompanion` loopback server. It provides task and note editors, exact revision checks, interrupted-write recovery, checked backups and restoration into a new store. It is **not a deployed native Muse Space**, cloud sync service, scheduler or connected account.

## First useful result — no setup or account

From a source checkout with Python 3.12+:

```sh
python -B examples/daily_desk.py
```

Use `python3` on macOS/Linux where appropriate. No pip install or `PYTHONPATH` setting is needed. This creates **3 tasks** and **2 notes** in temporary storage, edits a task and note, reopens them, refuses stale revisions, repeats one identical operation safely, exports an archive, restores into a new database and compares the restored records. The output must report `DAILY_DESK_VERTICAL_SLICE_PASS`. It does not start a server or keep the fictional data.

## Open your own local desk

```sh
python -B examples/daily_desk.py --serve --database "$HOME/daily-desk.sqlite"
```

The same command works in PowerShell. The parent directory must already exist and be owner-controlled. Choose a new database name for a fresh desk, or the same path to reopen an existing desk. The launcher creates a sibling `daily-desk-restores` directory for new restored stores; use `--restore-directory` with a safe absolute path to choose another local restore directory.

The terminal prints a loopback URL and a random local-session token. Open that URL **on the same computer** and enter the token. Keep the terminal running while you use the desk; Ctrl+C stops this foreground server. The token is not a Muse credential and is never written into the page, a URL, cookie or persistent browser-token store. Reloading requires entering it again; restarting the launcher creates a new token.

The UI is usable at narrow viewport widths, but phone-to-computer networking is not implemented. Do not tunnel the development server or expose it to the internet. Python's standard-library HTTP server is not a production web service.

## The everyday flow

Create a task with a concrete title; its due time is optional and displayed in your local time zone. A due time is only a stored timestamp, not a scheduled reminder. Edit a task to mark it done. Notes are plain text, not executable HTML or instructions to another agent.

Each saved record displays its revision. Selecting a record loads that version into the editor. If another tab or authorized writer saves a newer version, your old save is refused with `STALE_REVISION`. Your draft stays in the editor. Choose **Load saved version** deliberately before applying another edit; the application does not silently overwrite the newer work.

**Refresh saved work** reloads the list without replacing an open draft. **Lock session** hides the workspace and drops the token from page memory; it does not delete saved records. Tasks and notes remain in the local SQLite database after reopening.

## When the reply disappears

Every task/note mutation binds one operation ID to the exact content and expected revision in the same SQLite transaction. If the reply is lost after commit, an identical retry returns the original result instead of inserting again. Reusing the ID with a changed kind, record or content is refused.

The page keeps only an uncertain write's payload, ID and store binding in tab session storage until confirmation. The token is not included. This means unsent or uncertain note text can remain in that tab's storage; browser session restoration policies may retain it. Close or clear the tab according to your browser's privacy controls when appropriate.

Choose **Check saved receipt** first. If the receipt exists, the page reads back the result without replaying the write. Otherwise, **Retry the exact write** resends the same operation and payload. A different database served on the same port has a different instance identity; the pending write is blocked rather than sent to the replacement store. Do not change storage records to bypass that protection.

## Back up and restore

**Download backup** produces a strict JSON archive containing task records, note records (including deleted-note tombstones) and local write receipts. Its SHA-256 digest covers a canonical payload. The digest detects accidental or unexplained changes; it does **not** prove the publisher's identity or grant access.

Choose the backup file and a new store name in the restore panel. Restoration fully validates the archive, creates a staging database, checks it, then publishes a new database without replacing an existing file. The active desk remains unchanged. **Check restore result** reads the chosen destination without creating or migrating it. A missing reply does not justify using another name and creating duplicate stores.

To reopen the restored store, stop the original launcher and use the printed database path:

```sh
python -B examples/daily_desk.py --serve --database "$HOME/daily-desk-restores/desk-restored.sqlite"
```

You can also restore an archive from the terminal, without a listener:

```sh
python -B examples/daily_desk.py --restore "$HOME/daily-desk-backup.json" --database "$HOME/restored-desk.sqlite"
```

The destination must be new. Restoration preserves record IDs, content, revisions and operation receipts, but intentionally creates a **new database-instance identity**. This prevents a pending browser mutation from an old instance reaching the restored store unintentionally. Exporting it again yields the same canonical record payload.

## Storage, limits and security

The local reference uses injected owner/space scope; a browser-supplied owner ID is not authority. The HTTP adapter preserves strict loopback, Host/Origin, token, JSON, body and content-security-policy checks. Daily Desk routes expose neither native claim/callback authority nor the Space adapter's request-enabling controls.

This first slice has explicit bounds: 256 task records, 256 note records, 1,024 task/note operation receipts and a 16 MiB archive limit. It refuses over-budget operations rather than silently dropping history. Receipt retention/compaction is not implemented. Task titles are at most 160 characters, notes at most 8,000, and invalid identifiers, control characters, nonfinite or incorrectly typed numbers are refused. Export can refuse a data set whose serialized size exceeds its bound; records are not deleted to make it fit.

SQLite and archives are plaintext. Write receipts may retain earlier note text. Logical deletion is not secure erasure. Use owner-controlled local storage and operating-system access controls; this is not encryption, a multitenant sandbox or a network filesystem guarantee. Restore path checks reject traversal, unsafe aliases, existing destinations and sidecar collisions. Publishing uses a same-filesystem no-replace hard link. A process or power failure after publication may leave a staging name or an unconfirmed readback; inspect the original destination instead of automatically replaying. Abrupt power-loss durability and filesystem-adversary resistance are not certified here.

The archive excludes session tokens, browser state, reminders/preferences, provider request queues and callback records. Restoring it does not reconnect services, change the original store or activate external work.

## Implementation and verification

`DailyDesk` extends `PersonalCompanion` using the same scope, path admission, SQLite connection and transaction machinery. Existing notes remain in `companion_notes`; tasks, operation receipts and a store-instance identifier use additional tables. The existing `make_server` accepts an opt-in desk mode; its original Space UI and request/callback protocol remain available unchanged by default.

```sh
PYTHONPATH=src python3 -B -m unittest discover -s tests -p 'test_daily_desk*.py' -v
```

On PowerShell, set `$env:PYTHONPATH='src'` and use `python`. Tests cover atomic writes and rollback, concurrent/stale edits, duplicate and conflicting operations, owner isolation, migrations, reopen, strict archives, read-only restore inspection, no-overwrite races and actual HTTP refusals. The client fixture tests lost acknowledgments; real browser and cross-platform evidence are separate from those assertions.

See the [original Space starter](OPTIONAL_SPACE_STARTER.md), [durable-document guide](../handbook/durable-documents.md) and [design contract](../handbook/daily-desk-design.md). Official implementation references: [SQLite transactions](https://www.sqlite.org/lang_transaction.html) and [SQLite isolation](https://www.sqlite.org/isolation.html). This slice does not replace native Muse installation or broader connector/device acceptance.

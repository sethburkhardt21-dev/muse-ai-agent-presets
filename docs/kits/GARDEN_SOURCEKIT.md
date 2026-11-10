# Garden Companion executable source kit

This independent offline kit bundles the unchanged, source-pinned Garden SQLite engine, database-path helper, original demo, original regression suite, neutral role/playbook and license. It needs Python 3.12+ but no repository checkout, Git, pip dependencies, network or paid service after extraction.

## Build and verify

From this repository, with a new output filename outside the source directory:

    PYTHONPATH=src python3 -B examples/export_garden_sourcekit.py --to ../garden-sourcekit.zip
    PYTHONPATH=src python3 -B examples/export_garden_sourcekit.py --verify ../garden-sourcekit.zip --sha256 <trusted-sha256>

On Windows PowerShell, set `$env:PYTHONPATH='src'` and use `python` instead of `python3`. Output is create-only. Verification requires both an external archive digest and exact equality with a regenerated canonical artifact. It does not parse or decompress the supplied archive. Recompressed equivalents, appended bytes, modified manifests and any noncanonical ZIP are refused rather than interpreted.

## Use the extracted kit

Verify the archive digest from a separately trusted release record before extraction. Extract into a new directory, then run:

    python -I -B run.py --operation demo
    python -I -B run.py --operation self-test

The demo creates an actual disposable SQLite database, proposes and approves a date shift through explicit synthetic scopes, reopens state and recovers the operation receipt. The original bundled tests cover local owner/specialist separation, cross-owner isolation, wrong decisions, stale events, transaction rollback and interrupted/repeated operations. The source-pinned runner refuses modified source, rehashed altered manifests, extra import-shadow files and linked kit paths before importing package code.

The bundled `muse_presets.garden_calendar` API is reusable for an independently reviewed local integration. Its authority resolver must come from the host; a caller-created GardenScope is not authentication. Do not make that resolver a model/browser parameter. Keep user databases outside the immutable kit. SQLite storage is unencrypted and host permissions apply. Python isolated mode is not an operating-system sandbox.

## Boundaries and updates

This is a source-only library and runnable demonstration, not an installed native assistant or a connected calendar. Native Muse/Space identity, live weather, biological diagnosis, voice, messaging, jobs and Family Link are not connected. The owner role in tests is a fixture, not a provider-authenticated user. No external calendar writes occur.

Package checksums detect drift; they are not publisher signatures or grants. Updates use a fresh reviewed kit and preserve existing user databases. No auto-update, database migration or destructive uninstall is bundled.

Run packaging and original engine regressions:

    PYTHONPATH=src python3 -B -m unittest discover -s tests -p "test_garden*.py" -v

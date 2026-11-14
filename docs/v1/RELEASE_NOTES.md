# Muse Specialist Toolkit v1.0.0

**Your Muse. Your Specialists. Your Possibilities.**

A first cohesive product release of the public, MIT-licensed toolkit for configuring and extending your Muse personal assistant with specialist capabilities and practical first-use experiences.

## What's included

- **15 customizable AI specialist role profiles** for engineering, research, creative work, planning, learning, personal assistance and more.
- **100 selectable task-focused starter configurations**. Together these provide 100+ ways to start work with an existing assistant, not 115 separately installed agents.
- **75 developed task skills and 25 workflows**, with 50 original role/shared procedures retained and overlap explicitly accounted for.
- **Executable specialist tools** with local sample inputs, inspectable outputs and source code. Four expanded specialist kits and nine worked example reports are included in the separately distributable collection.
- **151 custom connectors**, a version-pinned searchable directory across 42 categories with service descriptions, permission notes, specialist relevance, original upstream guides and copy-ready setup messages.
- **Daily Desk**, Personal Companion's first persistent full-stack local application: task and note editing, exact revisions, safe interrupted writes, export, restore into a new store and original-state preservation.
- A practical four-way first-use guide, expanded technical documentation, source/manifest verification and cross-platform qualification.

## First use

From the extracted source or source checkout, using Python 3.12+:

```sh
python -B tools/muse_collection.py check
python -B tools/muse_collection.py demo data-engineer
python -B examples/daily_desk.py
python -B scripts/connector_catalog.py check
```

Read the [first-use guide](START_HERE.md) for using skills in Muse, running tools, opening Daily Desk and choosing custom connectors. Open `docs/connectors/index.html` locally for interactive filtering, or browse `docs/connectors/CATALOG.md` on GitHub.

## Release assets

- `muse-specialist-toolkit-v1.0.0.zip`: full, history-free public source tree and examples at the release commit.
- `muse-specialist-collection-v1.0.0.zip`: portable task starters, four expanded executable specialist kits and worked reports.
- `muse-custom-connectors-v1.0.0.zip`: complete locally searchable connector catalog, setup documents, provenance and attribution; third-party connector code is not redistributed or executed by this directory.
- `SHA256SUMS.txt`: release asset byte checksums, plus these release notes.

Verify each ZIP against its listed SHA-256 and use the instructions matching the actual downloaded release. The older `v0.4.1-alpha` eight-executable/eleven-starter assets are preserved, not overwritten.

## Source and integration scope

The source code and local demonstrations are usable without a paid API. An assistant's live tool permissions and account connections depend on its supported host setup. A role configuration does not create a native Muse agent; the Daily Desk web server binds only to local loopback, stores unencrypted SQLite, and does not run a hosted agent. Online integrations are possible through supported custom connectors and host tools; none is silently enabled by viewing this catalog.

The connector metadata is adapted from the MIT-licensed [muse-connectors project](https://github.com/bluman1/muse-connectors) at fixed source commit `73f302c2d8569fdc65e0e57c26b244c547fcd40e`. Its license and source hashes are included in the connector package.

## Compatibility and verification

Maintain the public source's existing 15 role IDs, skill/workflow selection contracts and original executable behavior. Validate the release source on Windows, macOS and Linux with the provided tests and source-integrity checks. CI and cross-machine results apply to the exact candidate commit and do not substitute for independent native Muse acceptance or account-permission review.

## After V1

The next product decision is based on the [30-day observation guide](POST_RELEASE.md): measure real first-use outcomes and interest before expanding every specialist into its own Space or importing hundreds of additional skills.

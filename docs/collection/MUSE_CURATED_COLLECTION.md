# Curated specialist collection

The current collection provides **15 specialist packages, 75 skills, 25 workflows and 100 starters**. Begin with the [working quickstart](SPECIALIST_QUICKSTART.md) and [specialist catalog](SPECIALIST_CATALOG.md).

Four new standard-library toolkits add actual schema/event/query review, reliability calculations, automation preflight and interface-contract checks. They are shipped as self-contained executable ZIPs with playbooks and examples. The original eleven-role protocol and existing sourcekits remain unchanged; no new agent identity, scheduler or provider authority is introduced.

The implementation spans `collections/muse-starters-v1/`, the existing collection exporter, four additional `presets/` directories, `src/muse_presets/specialist_extensions/`, an exported-kit runner, documentation and focused regression tests. All original starter IDs, 64 skill objects and 20 workflow objects are preserved, with only explicit additive starter selections.

## Public compatibility and the two libraries

Use these methods with your existing assistant: preserve its identity, memory and permissions. The public `quickstart.py` continues to create 15 optional role-home drafts. The existing portable exporter continues to emit its original 50 role/shared procedures. This collection adds a separate task-first library of 75 skills; the procedures overlap and are **not 125** independently unique capabilities.

`PUBLIC_COMPATIBILITY.json` records all 50 existing procedure IDs, related collection methods and two role aliases. `data-engineer` is the richer toolkit associated with public `data-engineering-architect`; `reliability-engineer` maps to `infrastructure-reliability-engineer`. The aliases add no agents and do not silently replace the old local fixtures. The collection starter export contains neither a new identity nor personal memory.

Run `python -B tools/collection_compatibility.py` to check source relationships, original public bytes and the incoming-file manifest. The result is source consistency, not a publisher signature or proof that native Muse loaded the files. See [the operating handbook](../handbook/README.md) for practical use.

## Run and inspect

```sh
python tools/muse_collection.py check
python tools/muse_collection.py specialists
python tools/muse_collection.py demo data-engineer
python tools/muse_collection.py kit data-engineer --to ./data-engineer.zip
python tools/muse_collection.py workflow-demo pipeline-validation
```

New kit exports are create-only and run independently from the repository. Local-stage demonstrations return actual calculated JSON and explicitly identify unexecuted host/human steps. They are not native Muse enrollment, external effects or competitive benchmark results.

## Upgrade and scope

Preserve user-customized copies and create a fresh export. Do not overwrite unrelated work or rewrite older qualification evidence. The new original skills have no admitted upstream comparator; plain/candidate task packets are available without inventing an empty competitor arm. Existing three-arm practice packets retain their original supported references.

The production TaskGuard and retention hold remains separate. Native comparative evaluation, independent semantic review and public release require their own evidence; source qualification does not erase those obligations.

## Historical development records

The records below describe earlier milestones and historical tool availability. They are retained for provenance, not current runtime claims.

## R2 — preserved source, focused depth

The original additive archive was rehashed and expanded, not regenerated. The 100 starter IDs, 64 skill IDs, 20 workflows and original 11 family bindings remain. Eight skills gain conditional methods, worked examples, recovery diagnoses and 24 concrete public cases. A standard-library checker validates supplied outputs; a three-arm packet exporter excludes answers from participant material. Six exact upstream entrypoints have item-level review records.

The source suite contains 95 test methods, including the original 46. These are local source/package tests, not a parent-repository full suite, independent semantic review or matched Muse result. As of this candidate, GitHub main has not been changed. Host A was offline during initial recovery and appeared online in the final device listing. That listing does not establish shell health or source parity. This session's connected remote/GitHub actions do not expose writes or command starts; original remote WIP remains untouched. The isolated source and guarded import/upgrade patches are delivered for the existing authorized writer to qualify and land.

No Omnium route was dispatched: its current mission registry was read, and no substitute planner or execution authority was invented. Native installation is not a release dependency for this source collection.


## R3 depth wave

R3 preserves the existing catalog and expands 28 selected foundation skills: 36 depth-expanded, 28 foundation. It adds 84 concrete cases without claiming model performance. See `collections/muse-starters-v1/R3_ACCEPTANCE.md` for scope and `R3_ITEM_REVIEWS.md` for inspected upstream entrypoints. No native assistant installation is required for this source deliverable.


## Starter packaging, not agent identities

The **100 selectable starters are Muse skill/workflow bundles**, not 100 separately installed assistants. Select one starter for the current task; Muse retains its existing identity, preferences, memory, permissions and tools. The ZIP's `PROFILE.md` describes the chosen workflow and expected result; it is **not** a replacement agent identity or persistent profile. The bundles do not ship `IDENTITY.md`, `SOUL.md`, `AGENTS.md`, `MEMORY.md`, `HEARTBEAT.md`, `USER.md` or `TOOLS.md`. Adding a skill cannot authorize a new tool connection, background job, send or other external action.

## R4 source qualification

The final 28 foundation-only skills received R4 depth and 84 new public exercises. All 64 existing skill instructions are now depth-expanded; the collection still has 100 selectable starters and 20 optional workflows. The original R4 source was qualified on A/B/C (397 focused tests and 2,041 full-suite tests per host, with platform skips reported), then privately integrated at commit 82abced781e2603a022e1c378a486b5a2e49cf7e. GitHub Actions run 43262169201 passed on that exact commit. These are historical source checks, not installed-assistant or native-model performance certification.

R2 and R3 procedures, all starter IDs and the existing 11 specialist-family bindings remain preserved. The 192 public case examples are development fixtures, not unseen held-out tests. Actual independently validated Muse superiority and public release are not established; the starter packages do not install a new agent identity, memory or execution runtime.

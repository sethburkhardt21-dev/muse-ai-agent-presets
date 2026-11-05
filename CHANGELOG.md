## Post-alpha source increment — R6 local Learning Coach

- Implemented a new, nonclinical SQLite study ledger for source-identity, held literal cards, owner approval, session-isolated protected challenges, exact-answer scoring, original-ID restart recovery, and explicitly heuristic due review.
- Added source/draft digest checks, stale-source refusal, approval separation, wrong owner/learner/session denials, exact-expiry/quota boundary tests and atomic rollback on failed grading.
- Adapted design lessons without copying private study-engine code or materials; the model-less demo uses fictional source text and deletes its data. Native Muse host identity, learning validity and clinical release are NOT PROVEN.

## Post-alpha source increment — R5 local garden calendar

- Added a new, generic SQLite calendar transaction engine and disposable example for Garden Companion: owner/site-scoped events, verified-resolver injection contract, specialist proposal-only access, owner browser approval, 1–21-event atomic date edits, stale-revision and cancellation refusal, duplicate/replay-safe immutable receipts, and original-operation recovery after restart.
- Test-first suite includes cross-owner/Space/garden isolation, declined proposals, operation conflicts, expiration, invalid dates and Unicode controls, simultaneous approvals on distinct SQLite connections, and rollback under a deliberately failing SQL trigger.
- **No private donor code, private data or host SDK was imported.** Native Muse authentication, Space UI, installation and external calendar writes remain NOT_PROVEN.

## Post-alpha candidate — R4 role differentiation and neutrality (source only)

- Added eleven distinct validated role playbooks (three procedures each) covering task evidence, refusal rules, compatible peer handoffs and first negative-control acceptance exercises.
- `render-v3` now includes `ROLE_PLAYBOOK.md` and pins its source/managed hashes. The read-only inspector treats playbook drift as policy review and remains compatible with existing v2 drafts.
- Added a bounded `audit-neutrality` command and release-surface negative tests; no private donor code, external capability, Muse tool or connector was installed.
- Added capability-fit decisions, source-intake matrix and owner-state neutralization/portability guidance.

# Changelog

## Unreleased source increment — offline lifecycle inspection

- New v2 renderer receipts record a preset source digest, per-template source digests, generated-file digests and the chosen display name. The renderer remains create-only and offline.
- `inspect --path` checks local drafts without touching their contents: it differentiates unmodified, owner-customized, changed Family Link policy, upstream template drift, missing file, unsafe symlink and unverifiable legacy receipts.
- Nine lifecycle regression cases added; **native Muse loading and automatic regeneration remain NOT IMPLEMENTED**. The existing `v0.1.0-alpha` release remains pinned to its original source.

## 0.1.0-alpha — November 5, 2026

First public, independent-source edition of Muse AI Agent Presets.

- Eleven generically named specialist profile templates and one separate Evidence Finder service.
- Create-only offline renderer, catalog doctor and optional default-denied Family Link proposal contract.
- Profile templates for agent instructions, identity, soul, user, tools, memory, preferences, heartbeat, custom instructions, hooks and subchats.
- Five new source-only reference implementations: bounded evidence finding; evidence-scope checking; garden date previews; source-backed learning card drafts; and supplied-fixture UI-flow comparison.
- Synthetic offline demonstration and 40 source regression tests. Linux passes all 40; Windows runs 39 with a symlink-creation test skipped where unavailable.
- Source/host-compatibility, provenance, rights, persistence, five-layer maturity and roadmap documents.
- Free MIT-licensed newly authored generic starter source; not an official Meta product, native Muse integration, live Family Link transport or a production skill registry.

**Not included:** private assistant code or memory, any embedded third-party engines, native host grants, actual model training, live reverse-engineering probes, credential-handling implementations or deployment to a Muse account.

See [current status](docs/STATUS.md) and [release checklist](docs/RELEASE_CHECKLIST.md).

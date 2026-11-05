# Priority transfers — reuse existing work instead of rewriting it

**Source-intake decision:** The five priority roles and one shared finder service have substantial reusable *private* foundations. This public shell **does not copy that source**. The owner-side implementation plan maps exact internal paths and pins; after rights/host review, import only the minimum self-contained, tested modules and source attribution. Do not publish old personal data, character art, protected provider files or unrelated app source.

| Public role | Highest-value engine/code patterns to adapt | Other related systems to inspect | Native test to earn next grade |
| --- | --- | --- | --- |
| **Garden Companion** | Owner/site-scoped garden records; revision-fenced seasonal batches; idempotent calendar proposals; linked-event graph | Existing personal-companion UI/Notebook, neutral task-model patterns, evidence finder for plant references | Create new owner garden; submit/approve a synthetic seasonal proposal; reject stale revision and wrong owner; phone/Mac view |
| **Learning Coach** | Grounded draft/flashcard generation; numeric oracle; adaptive practice; event-scoped scoring; due review projection; evidence assurance | Dataset identities, eval contamination checks, independent question review and generic document extraction | From licensed nonclinical source, create cited practice item; score, persist, reopen; reject invented citation and leaked answers |
| **Claims Adjudicator** | Sentence vs conclusion; immutable conditions; correction alongside original; source-byte concordance; reviewed decision records | Governed claims/lease gates, independent test receipts, evidentiary ledger and provenance modules | Reject broad unqualified claim when evidence is narrow; preserve every condition after publication-format conversion |
| **Reverse Engineering Researcher** | Authorized UI observation/reconstruction; documented traffic/PCAP interpretation; behavioral differential analysis; evidence custody | Runtime Anatomy, source/bug triage, adversarial test rig, Desktop Commander permissioned GUI; optional offline Ghidra/tshark/Zeek tools | Reconstruct harmless owned toy interface and its protocol from trace fixtures; prove sandbox scope and no access to unrelated data |
| **Evidence Finder service** | Source-identity finder; preserved full findings or truthful null; read-only scoped search | Evidence/index tools, source provenance, research retrieval, independent adjudication | Locate planted record 1:1; pass bytes/hash intact; honest no-match; reject injected verdict and unauthorized effect |

A specialist is not complete because its original donor had an impressive test count. Each adapted slice requires **source pin → license audit → isolated test → host canary → useful consumer proof**. Data and Artifacts belong to the receiving user, not the publicly published role.

## R5 — New local Garden Companion transaction engine

`src/muse_presets/garden_calendar.py` now provides a separate, generic SQLite transaction reference alongside the original read-only preview. It implements revision-fenced proposals, explicit owner review, multi-event atomic decisions and durable recovery receipts. See [the runnable Garden contract](GARDEN_LOCAL_CALENDAR.md). **Source tested only**: no recipient Muse session, credential validation, managed Space or external calendar is bound. The original private Garden donor source remains separately governed and has not been copied into this repository.

## R6 — New local Learning Coach source-to-review engine

`src/muse_presets/learning_session.py` is the second complete local owner-scoped SQLite reference slice. It creates literal, source-bound held cards from owner-admitted text, requires separate owner review before issuing a question, scores within a learner session, preserves original operation receipts, and projects transparent nonvalidated due intervals. Its protected source, answer and review histories remain in the user-owned local database, never the public repo. See [Learning Coach local study contract](LEARNING_LOCAL_STUDY.md). The independent private study donor is not vendored. **Native Muse learner identity, production cryptographic custody, educational validity and clinical approval are NOT claimed.**

## Alpha implementation increment — clean-room local slices

The following newly authored, dependency-free reference functions are implemented in this repository. They **adapt architectural ideas**, not private donor source, weights or personal records. All are bounded, source-only, and require separate native Muse adoption:

| Module | Public callable | Tested scope | Deliberately missing |
| --- | --- | --- | --- |
| `src/muse_presets/finder.py` | `find_exact_text` | Exact UTF-8 evidence, read-only bounded file, full source preserved, honest null, traversal/symlink refusals | Indexer, signed evidence, remote access, automatic searching, verdict |
| `src/muse_presets/claims.py` | `assess_scope` | Overclaim detection and condition preservation | Trusted external evidence, authoritative court/release admission |
| `src/muse_presets/garden.py` | `preview_date_shift` | Revision/owner-bound proposal-only schedule preview | Host-side SQLite transaction, actual garden account, event publishing |
| `src/muse_presets/learning.py` | `draft_supported_card` | Verbatim quoted answer, source digest and span, review hold | Real assessment engine, full evidence provenance, subject approval |
| `src/muse_presets/reverse.py` | `compare_observed_flows` | Deterministic comparison of benign supplied UI traces | Desktop/browser capture, live protocol interception, malware execution |

Run `PYTHONPATH=src python examples/priority_slices.py` and the full `tests/` suite. Each result explicitly lacks native authority, external effects, and downstream adoption. These slices **do not replace** the separately tested engines: Garden's batch calendar, Study's adaptive scorer, the Court's evidence review, the larger reverse-engineering sandbox, or the Finder's eventual recipient-verified transport. Their eventual upstream integration requires file-level rights/provenance and changed-seam regression, followed by the real original Muse gates.

# Learning Coach — local study ledger (R6)

**Source-tested only.** `src/muse_presets/learning_session.py` is a newly authored, standard-library Python/SQLite reference implementation. It does **not** install a Muse personal assistant, claim approved educational/clinical content, prove model or connector authorization, or create a native reminder. The original private learning engine was used as a design/evaluation reference, **not copied**.

## Runnable vertical slice

```bash
PYTHONPATH=src python examples/learning_session_demo.py
PYTHONPATH=src python -m unittest discover -s tests -p test_learning_session.py -v
PYTHONPATH=src python -m unittest discover -s tests -v
```

The demo deletes its fabricated SQLite database when complete. `LearningSession` requires an absolute path inside an already existing folder and an injected `authority: () -> LearningScope` callback. It will not use account labels or session IDs directly from model/browser input to authenticate a person. The shared path checker permits the root-owned standard macOS `/var`/`/tmp`/`/etc` aliases while rejecting user-controlled symlinks; it is not a race-free OS sandbox. The sample callback **simulates** that protected host behavior.

### Source → draft → review → challenge → score → review

1. **Owner admits source.** `register_source(source_id, version, text)` freezes the supplied local text, SHA-256 digest and active version within one owner/Space. Historical versions remain for audit; a different body under an existing version is refused. The text is *owner-supplied, unverified content*—not validated truth or a vetted license.
2. **Specialist proposes.** `propose_source_facts(source_id, limit=20)` only recognizes literal source lines in the `Term :: Definition.` form, rejects ambiguous prose/control characters, maintains line-level locators, and gives deterministic draft IDs and digests. `limit` caps **new writes as well as returned candidates**; total eligible versus skipped lines and truncation are explicit. It never invokes a language model, invents a missing fact, interprets charts or imports proprietary teaching material.
3. **Owner reviews.** Only an owner role from the injected host resolver can `review` an exact draft and digest to approve/decline. The effect uses one SQLite transaction and an immutable operation ID. Approved source version and quote are rechecked against current source bytes.
4. **Learner practices.** Only a role-scoped learner session can `issue` an approved question. The challenge contains a question, source locator/hash and expiration—but **not** the answer or stored source body. Source-version change or expired challenge refuses grading.
5. **Scoring and replay.** `submit` compares trimmed/case-folded whitespace-normalized answers literally against the approved expected answer. It is **not semantic grading**. One transaction writes the attempt, the bounded response and the answered state. Repeated use of the original operation ID within the original learner session returns the same receipt; a changed answer, another session, or a new attempt against the answered challenge is rejected. `score_receipt` supports explicit lost-acknowledgment reconciliation without retrying under a new operation ID.
6. **Review projection.** `review_queue` reads only current approved cards and durable attempt history. Unattempted/wrong answers are due now, correct answers after 24 hours. `HEURISTIC_V1_NOT_FSRS` means this is **not** a calibrated learning or mastery model, and does not schedule a notification or background task.

## Responsibility and security boundaries

| Boundary | Enforced by the local reference | Required from real Muse integration |
| --- | --- | --- |
| Owner, Space, learner and session | Explicit scoped queries and role checks on callback-produced `LearningScope` | Original host-issued identity, session verification, server-only role/owner admission; do not trust caller-constructed scope objects |
| Learning material | Bounded source lines, version and SHA-256 consistency | Source rights, ingestion/extraction trust, separate instructor or qualified subject review for higher stakes |
| Questions | Held until explicit owner review and unchanged source version | Vetted question quality, learner suitability and protected key custody |
| Grades | Single SQLite transaction, replay ID and scope fencing | Tamper-resistant storage, current host session verification, authenticated signing if grading has external consequences |
| Persistence | Local SQLite file with reopen and concurrent-connection tests | Actual Muse Space database/migration, physical device readback, backups and retention controls |
| Schedule | Pure due calculation over local attempts | Approved native scheduler/reminder registration and effect receipts, if requested |
| Family Link | Not called | Optional per-account opt-in, authenticated recipient and source-bound delivery/acceptance |

The plain SQLite file stores owner-provided study text and protected answers in **unencrypted local storage**. Keep it outside public Git, shared directories and untrusted machines. It is not suitable for PHI, exam secrets, regulated assessment or untrusted user input as an authentication source. A row hash detects some drift but cannot authenticate the person or stop deliberate DB tampering.

Failure cases tested include changed source bytes, modified draft content, stale versions, wrong owner/Space/learner, wrong or changed session, changed operation IDs, duplicate grades, exact expiry, bad clock, hidden extra draft writes, symlinked parent, and mid-transaction SQL errors. Tests are local fixtures, not proof of real native Muse or learner outcomes.

## Next original-host gates

- Discover the currently supported personal Muse/Hatch skill and artifact interfaces on an explicitly authorized **disposable** account; no modification of existing private specialist accounts.
- Bind `LearningScope` to real server-verified owner/Space/learner/session identity and protect the SQLite database behind host rights. Prove cross-account and role denial in original native calls.
- Build one approved nonclinical study source/card and execute an actual practice attempt via native UI; reopen on another device, retrieve the same operation receipt, and measure question usefulness independently.
- Introduce release and review scoring only after a separate independent domain reviewer, consent/rights review and real host acceptance. Clinical materials remain excluded.

No paid APIs or hosted cloud models are required for the local reference.

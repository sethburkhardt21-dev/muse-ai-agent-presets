# Run Feedback-Rich Retrieval Practice — operational depth

Read only the branch needed for the current task. These are working methods, not a demand for additional approvals on ordinary reading or drafting.

## Domain method

Use a frozen rubric and record how an answer was obtained. Independent retrieval, a response after a hint, an answer after feedback and a repeated prompt are different observations. Preserve item identity, attempt identity, rubric version and source scope; a correct prompted answer is not proof of durable mastery.

## Output contract

Return one question at a time, the learner's original answer, rubric-item credit, hint level, concise corrective feedback and the next targeted item. Keep practice results distinct from retention or credential claims; no schedule or grade is posted automatically.

## Choose the right action

### The answer uses different words but the same meaning.
Compare semantic elements against the rubric; give credit for supported equivalence and explain any scoring judgment.

**Avoid:** Do not use substring matching as the whole assessment.

### A hint was given before the final answer.
Record assisted correctness separately from first-attempt correctness.

**Avoid:** Do not add the assisted success to an independent score.

### The rubric conflicts with the supplied source.
Hold grading for the affected item, preserve the answer and repair the rubric from the source.

**Avoid:** Do not punish the learner for a broken key.

### A previously graded response arrives again after reconnect.
Use its original attempt ID and show the existing result.

**Avoid:** Do not increment attempts or mastery twice.

### The learner repeatedly misses one prerequisite.
Step back to a smaller diagnostic question and then test a different application.

**Avoid:** Do not repeat the same explanation indefinitely or change all topics at once.

## Worked example (authored, synthetic)

**Input:** A rubric gives one point each for naming evaporation and condensation. The learner names evaporation only; after a hint, names both.

**Method:** First attempt earns 1/2; the prompted response is recorded separately.

**Result:** Independent score: 1/2. Assisted score: 2/2. Feedback targets condensation. Next question uses a different water-cycle example; no mastery claim.

## Edge or recovery example 1 (authored, synthetic)

**Input:** The same first attempt arrives again with the same attempt ID after a timeout.

**Method:** Read the original grade rather than creating a new attempt.

**Result:** One original attempt remains; score and denominator are unchanged. A new transfer answer must have a new attempt ID.

## Failure diagnosis

### The score rises after every hint but independent answers do not improve.
**Likely cause:** Assisted and unassisted attempts were pooled.

**Repair:** Split the performance record and add an unseen transfer prompt.

**Recheck:** Report both denominators and no unsupported mastery label.

### An answer is marked wrong for an omitted keyword.
**Likely cause:** A lexical checker replaced the conceptual rubric.

**Repair:** Evaluate the actual concept and preserve a rationale for equivalence.

**Recheck:** No credit decision depends solely on exact wording.

### One response is counted twice.
**Likely cause:** Retry processing lacked stable attempt identity.

**Repair:** Reconcile the original stored attempt and remove only the duplicate derived count.

**Recheck:** Unique attempt IDs determine the denominator.

## Preserve for the next turn

Preserve learner-local item, attempt and rubric IDs, raw first answers, hint levels, source anchors and unresolved scoring conflicts. On resume, reuse accepted scores and never leak another learner's history.

## Practice and mechanical checks

Three authored public exercises cover a standard task, an edge condition and recovery or changed evidence. Their answers are development examples, not held-out results. Supplied-output checks cover only declared facts and invariants; language quality, visual quality and real provider behavior remain separate.

Practice case IDs: `retrieval-practice-r3-standard`, `retrieval-practice-r3-edge`, `retrieval-practice-r3-recovery`.
Packaged exercises live under `practice/`. The optional `practice/check_outputs.py` checks supplied JSON outputs; it does not call Muse or certify semantic/visual quality.

## Evidence boundary

Original specialist synthesis with source and fixture checks. No matched Muse comparison has been executed; greater domain detail is not measured superiority over upstream packages.

# Plan an Exam Preparation Cycle — operational depth

Read only the branch needed for the current task. These are working methods, not a demand for additional approvals on ordinary reading or drafting.

## Domain method

Exam preparation is a coverage-and-capacity allocation problem, not a page-count schedule. Use the actual syllabus and exam blueprint as scope, diagnostic evidence as a provisional estimate of weakness, and prerequisite order to decide what must precede application. Separate source coverage, retrieval attempts, feedback and timed integration practice. A score observed once is not a stable mastery estimate.

## Output contract

Return a topic-by-source coverage matrix, finite session budget, explicitly allocated study and practice blocks, deferred scope, checkpoints and a rescheduling rule. Show arithmetic in minutes and label diagnostic weights as planning heuristics, not validated predictions of exam performance.

## Choose the right action

### The exam is near and the requested scope cannot fit.
Protect required prerequisites and the highest-priority objectives; name what remains uncovered and offer a specific tradeoff.

**Avoid:** Do not claim complete preparation after compressing all topics into unreadable summaries.

### An instructor blueprint conflicts with a generic study template.
Use the current supplied blueprint for exam scope and keep outside enrichment separate.

**Avoid:** Do not silently add or remove examinable content based on generic expectations.

### A diagnostic response used notes or hints.
Track it as assisted and schedule an independent follow-up.

**Avoid:** Do not treat a coached answer as evidence that a topic needs no study.

### One session is missed.
Recalculate remaining capacity, carry forward only unfinished objectives, and drop optional work first.

**Avoid:** Do not restart the entire plan or double the next day without available time.

### The learner wants only a short overview today.
Deliver the overview and a compact next-session option.

**Avoid:** Do not force a full calendar workflow on a bounded study request.

## Worked example (authored, synthetic)

**Input:** An exam covers A, B and C. There are 360 available minutes; the learner reserves 60 for mixed practice and 30 for feedback. A needs 120 minutes before B can start; B needs 90 and C needs 60.

**Method:** Compute 270 topic minutes and sequence A before B; keep the reserved 90 separate.

**Result:** Plan A 120, B 90, C 60, mixed practice 60 and feedback 30. Total 360. The plan covers the supplied scope but does not certify readiness until independent checkpoints are observed.

## Edge or recovery example 1 (authored, synthetic)

**Input:** A 120 is complete, then a 90-minute window is lost. There are 150 minutes left, including a protected 60-minute mixed-practice session. B is required and C is optional.

**Method:** Preserve A, allocate B 90 and mixed practice 60, and explicitly defer C.

**Result:** The revised plan fits 150 minutes; C remains uncovered. Do not call the full original blueprint completed or repeat A as new work.

## Failure diagnosis

### The plan has more minutes than the calendar.
**Likely cause:** Topic weights were converted to sessions without subtracting practice and breaks.

**Repair:** Recompute the capacity ledger and shorten scope, not the declared task duration.

**Recheck:** Allocated minutes plus reserve do not exceed available minutes.

### Every topic is marked mastered after a sample quiz.
**Likely cause:** A small or assisted sample was overgeneralized.

**Repair:** Replace mastery labels with observed attempts and untested objectives.

**Recheck:** Every readiness statement traces to relevant independent evidence.

### A rescheduled plan repeats already completed work.
**Likely cause:** The scheduler used the original backlog instead of the completion record.

**Repair:** Subtract completed objectives and preserve their source and attempt records.

**Recheck:** No completed block reappears unless an explicitly justified review is planned.

## Preserve for the next turn

Preserve the blueprint version, source map, independent attempt IDs, completed blocks, reserve choices and remaining windows. Resume from the next unfinished prerequisite; never infer a reminder or calendar write from the plan itself.

## Practice and mechanical checks

Three authored public exercises cover a standard task, an edge condition and recovery or changed evidence. Their answers are development examples, not held-out results. Supplied-output checks cover only declared facts and invariants; language quality, visual quality and real provider behavior remain separate.

Practice case IDs: `exam-plan-r3-standard`, `exam-plan-r3-edge`, `exam-plan-r3-recovery`.
Packaged exercises live under `practice/`. The optional `practice/check_outputs.py` checks supplied JSON outputs; it does not call Muse or certify semantic/visual quality.

## Evidence boundary

Original specialist synthesis with source and fixture checks. No matched Muse comparison has been executed; greater domain detail is not measured superiority over upstream packages.

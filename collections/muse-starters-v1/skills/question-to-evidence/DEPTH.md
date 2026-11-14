# Turn a Question Into an Evidence Plan — operational depth

Read only the branch needed for the current task. These are working methods, not a demand for additional approvals on ordinary reading or drafting.

## Domain method

Turn the decision into a set of falsifiable subquestions, each with a required evidence type and a stop condition. Separate descriptive, causal, predictive and normative questions: their supporting evidence is not interchangeable. Define the population, comparison, time horizon and outcome before selecting sources. An evidence plan is useful only when each unresolved question has a feasible next retrieval or measurement.

## Output contract

Deliver a decision question, scoped subquestions, inclusion rules, search or measurement routes, source-access status, and a claim ledger distinguishing supported, disputed, inferred and unresolved conclusions. A requested research answer still requires the answer, not only this plan.

## Choose the right action

### The user asks whether an intervention caused an outcome.
Identify a comparison or design that addresses plausible alternative causes and state residual confounding.

**Avoid:** Do not promote a before/after association into causal proof.

### The question is too broad for the available budget.
Choose a decision-relevant boundary and show what is excluded; retain the broader question as a separate backlog item.

**Avoid:** Do not hide a narrow search behind a comprehensive-review label.

### The only source is inaccessible.
Record not accessed and separate any available abstract or metadata from full-text evidence.

**Avoid:** Do not manufacture methods or limitations from the title.

### A newer authoritative update changes a rule.
Record the supersession relation for the specific rule and preserve the older source as history.

**Avoid:** Do not average incompatible versions or assume newest always means authoritative.

### The user supplied enough evidence and a clear decision rule.
Use it directly and verify the answer against the existing rule.

**Avoid:** Do not reopen an unnecessary research interview or alter the criterion after seeing outcomes.

## Worked example (authored, synthetic)

**Input:** A nonprofit asks which grant it qualifies for. S1 is current Program A guidance, allowing organizations older than one year. S2 is old Program B guidance requiring two years; S3 is its authoritative update requiring three. The nonprofit is 2.5 years old.

**Method:** Map eligibility separately from award value; use S3 for B because it explicitly supersedes S2.

**Result:** A meets the supplied age criterion; B does not. Award comparisons remain unresolved if no award data was supplied. Cite S1 and S3, with S2 retained as superseded history.

## Edge or recovery example 1 (authored, synthetic)

**Input:** The user instead asks whether the grant caused organizations to grow, but supplies only a press release about successful recipients.

**Method:** Classify the claim as causal and the source as selective descriptive reporting.

**Result:** The causal claim remains unresolved. A suitable next step is a comparable nonrecipient group or a credible evaluation design; do not treat recipient success stories as a causal estimate.

## Failure diagnosis

### The research produces many links but no decision.
**Likely cause:** Sources were gathered without mapping them to the decision claims.

**Repair:** Build a claim-to-evidence map and identify which unanswered claim actually changes the recommendation.

**Recheck:** Every retained source has a stated role in the decision.

### A conclusion cites an unread document.
**Likely cause:** Discovery metadata was confused with inspected content.

**Repair:** Remove the unsupported citation and mark the claim unresolved pending access.

**Recheck:** Cited evidence locations are actually readable and support the stated claim.

### Supportive sources dominate despite contrary evidence.
**Likely cause:** The search had only confirmation-seeking terms.

**Repair:** Run one bounded alternative-hypothesis search and preserve its result, including no hits.

**Recheck:** The ledger includes relevant counterevidence and transparent search limits.

## Preserve for the next turn

Save the decision rule, subquestion IDs, source versions and access states, exclusions, counterevidence and stopping budget. Resume with the first decision-changing gap, not another unrestricted search.

## Practice and mechanical checks

Three authored public exercises cover a standard task, an edge condition and recovery or changed evidence. Their answers are development examples, not held-out results. Supplied-output checks cover only declared facts and invariants; language quality, visual quality and real provider behavior remain separate.

Practice case IDs: `question-to-evidence-r3-standard`, `question-to-evidence-r3-edge`, `question-to-evidence-r3-recovery`.
Packaged exercises live under `practice/`. The optional `practice/check_outputs.py` checks supplied JSON outputs; it does not call Muse or certify semantic/visual quality.

## Evidence boundary

Original specialist synthesis with source and fixture checks. No matched Muse comparison has been executed; greater domain detail is not measured superiority over upstream packages.

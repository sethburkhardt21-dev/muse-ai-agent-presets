# Synthesize Interviews Without Inventing Consensus — operational depth

Read only the branch needed for the current task. These are working methods, not a demand for additional approvals on ordinary reading or drafting.

## Domain method

Qualitative synthesis preserves the chain from participant and context to excerpt, code, theme and interpretation. Count distinct participants, not repeated quotations, when reporting within-sample prevalence. Separate what someone said from what they did and what the researcher inferred. Negative cases and minority needs can be decision-critical even when uncommon; purposive interview samples do not estimate population prevalence.

## Output contract

Return a theme table with participant IDs and exact excerpt references, observed behavior versus interpretation, divergent evidence, sampling limits and a next research or product decision. Remove identifying details not necessary to the finding. Do not invent demographic personas or effect sizes.

## Choose the right action

### One participant repeats the same concern five times.
Count one participant contribution to that theme and keep the repeated excerpts as detail.

**Avoid:** Do not turn quote frequency into participant prevalence.

### Participants disagree.
Describe the conditions and segment context behind both positions; preserve the negative case.

**Avoid:** Do not manufacture consensus by omitting dissent.

### A topic was not asked in every session.
Use an asked-and-answered denominator or state the unbalanced coverage.

**Avoid:** Do not label unasked participants as having no concern.

### A quotation contains identifying or sensitive details.
Use the minimum necessary excerpt and a consent-compatible pseudonymous ID.

**Avoid:** Do not publish private raw transcripts merely to demonstrate traceability.

### A recommendation implies a numeric conversion or satisfaction gain.
Label it a hypothesis and define a subsequent measurement.

**Avoid:** Do not infer effect size from interview enthusiasm.

## Worked example (authored, synthetic)

**Input:** P1 raises navigation difficulty in two excerpts, P2 raises it once, and P3 reports no difficulty. All three were asked.

**Method:** Code the excerpts, deduplicate participant support and keep P3 as a negative case.

**Result:** Navigation difficulty is supported by 2 of3 interviewed participants, with 1 dissenting participant. This is a within-sample finding, not a population rate or a proven conversion effect.

## Edge or recovery example 1 (authored, synthetic)

**Input:** P3 was not asked about navigation and has no relevant observation.

**Method:** Separate not asked from dissent and recompute the asked-and-answered denominator.

**Result:** Support is 2 of2 asked participants; coverage is 2 of3 overall. P3 is unknown on this theme, not a negative case.

## Failure diagnosis

### The summary says all users agree but one transcript disagrees.
**Likely cause:** Theme compression erased a negative case.

**Repair:** Restore the dissenting evidence and narrow the conclusion.

**Recheck:** Participant-level support and dissent remain visible.

### A percentage changes when duplicate excerpts are removed.
**Likely cause:** The denominator was quotations rather than people.

**Repair:** Recompute unique participant counts and state the sampling limitation.

**Recheck:** Counts can be reproduced from participant IDs.

### The report contains a quote that cannot be found.
**Likely cause:** Paraphrase was formatted as direct speech or an excerpt was fabricated.

**Repair:** Replace it with a supported paraphrase or exact source quotation.

**Recheck:** Every direct quote matches its inspected source span.

## Preserve for the next turn

Save transcript versions, consent scope, codebook revisions, excerpt locators, participant-level support/dissent and unasked topics. Resume with the missing evidence or decision, not another synthetic persona.

## Practice and mechanical checks

Three authored public exercises cover a standard task, an edge condition and recovery or changed evidence. Their answers are development examples, not held-out results. Supplied-output checks cover only declared facts and invariants; language quality, visual quality and real provider behavior remain separate.

Practice case IDs: `interview-synthesis-r3-standard`, `interview-synthesis-r3-edge`, `interview-synthesis-r3-recovery`.
Packaged exercises live under `practice/`. The optional `practice/check_outputs.py` checks supplied JSON outputs; it does not call Muse or certify semantic/visual quality.

## Evidence boundary

Original specialist synthesis with source and fixture checks. No matched Muse comparison has been executed; greater domain detail is not measured superiority over upstream packages.

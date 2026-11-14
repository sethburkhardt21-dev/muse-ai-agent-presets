# Triage a Literature Set Without Losing Its Limits — operational depth

Read only the branch needed for the current task. These are working methods, not a demand for additional approvals on ordinary reading or drafting.

## Domain method

Triage distinguishes records, reports and underlying studies. Deduplicate bibliographic copies before screening, then group multiple reports of one study before interpreting replication. Apply prespecified eligibility in two stages and retain exclusion reasons. Evaluate methodological relevance and risk of bias separately from publication prestige; a count of favorable abstracts is not evidence synthesis.

## Output contract

Return record dispositions, study-family groupings, eligibility reasons, access limitations and a bounded synthesis by question. Keep inaccessible full text unresolved rather than excluded for an invented methodological reason. Report search coverage accurately; a supplied-paper triage is not a systematic review of the whole literature.

## Choose the right action

### Two records share a DOI but differ in downloaded filename.
Treat them as one bibliographic record and retain both source locations.

**Avoid:** Do not count two downloads as two independent studies.

### Two papers report different follow-ups from the same cohort.
Group them into one study family while retaining the distinct time points and outcomes.

**Avoid:** Do not discard the later report or count it as independent replication.

### An eligibility criterion requires unavailable full text.
Mark the report awaiting full-text review with the exact missing criterion.

**Avoid:** Do not infer inclusion or methodological exclusion from a missing PDF.

### A study reports an incompatible outcome scale.
Keep a narrative comparison or a justified conversion with the original units intact.

**Avoid:** Do not average raw scores with different meanings.

### The task is a rapid map of supplied papers.
Bound the claim to that corpus and state the single-screening limitation.

**Avoid:** Do not label the result exhaustive or PRISMA-complete merely because a flow table exists.

## Worked example (authored, synthetic)

**Input:** Records R1 and R2 share DOI D1. R3 has DOI D2 but reports the same registered cohort K1 at 12 months. R4 is a distinct eligible cohort K2.

**Method:** Deduplicate R1/R2, then group D1 and D2 as K1 while retaining both follow-ups.

**Result:** There are three unique reports and two independent study families, not four studies. K1 has multiple reports; K2 is an independent contribution.

## Edge or recovery example 1 (authored, synthetic)

**Input:** R4 has only an abstract and the protocol requires a verified adult population from full text.

**Method:** Keep its eligibility unresolved until the required population detail can be inspected.

**Result:** R4 is awaiting full text, not an invented exclusion for wrong age. The synthesis uses the confirmed eligible family and explicitly describes the unresolved candidate.

## Failure diagnosis

### The synthesis claims many replications from one cohort.
**Likely cause:** Reports were counted instead of independent study families.

**Repair:** Reconstruct the family map from recruitment, registry and author-described cohort links.

**Recheck:** Independent counts use families, and report-level outcomes remain traceable.

### Exclusion reasons change after the results are read.
**Likely cause:** Eligibility is being adapted to favor a conclusion.

**Repair:** Restore the original criteria and document any protocol amendment separately.

**Recheck:** The same rule is applied to supportive and contrary studies.

### A numerical synthesis has no common denominator or endpoint.
**Likely cause:** Unlike measures were pooled without a transformation rationale.

**Repair:** Undo the pooled estimate and give a structured narrative until comparability is established.

**Recheck:** Every numerical comparison retains its population, unit and follow-up.

## Preserve for the next turn

Preserve the protocol version, original record IDs, dedup and study-family map, exact screening reasons, access flags and extracted locators. Resume unresolved full-text decisions without rescreening settled records.

## Practice and mechanical checks

Three authored public exercises cover a standard task, an edge condition and recovery or changed evidence. Their answers are development examples, not held-out results. Supplied-output checks cover only declared facts and invariants; language quality, visual quality and real provider behavior remain separate.

Practice case IDs: `literature-triage-r3-standard`, `literature-triage-r3-edge`, `literature-triage-r3-recovery`.
Packaged exercises live under `practice/`. The optional `practice/check_outputs.py` checks supplied JSON outputs; it does not call Muse or certify semantic/visual quality.

## Evidence boundary

Original specialist synthesis with source and fixture checks. No matched Muse comparison has been executed; greater domain detail is not measured superiority over upstream packages.

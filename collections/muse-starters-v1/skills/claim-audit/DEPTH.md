# Audit a Claim Against Its Actual Evidence — operational depth

Read only the branch needed for the current task. These are working methods, not a demand for additional approvals on ordinary reading or drafting.

## Choose the right action

### A paragraph contains several different assertions.
Split it into independently checkable claims: identity, date, measurement, cause and completion. Keep the requested scope.

**Avoid:** Do not attach one citation to a sentence containing unsupported extra conclusions.

### Evidence is direct but stale or superseded.
Record its observation date and the applicable version. Prefer the source that governs the claim's time window, not whichever supports the desired conclusion.

**Avoid:** Do not erase the older record or present a prediction as a later observed result.

### Sources conflict.
Quote only the minimum relevant passages, identify what differs, and test whether population, version or time explains it. Preserve unresolved conflict.

**Avoid:** Do not average incompatible facts or invent a deciding authority.

### A citation exists but does not entail the claim.
Downgrade that claim to insufficient or contradicted and propose the narrow supported wording.

**Avoid:** Do not promote source presence, a passing unit test or a checksum into proof of all behavior.

### The user needs a decision before all evidence is available.
Separate the reversible recommendation from unresolved factual claims and identify the evidence that would change the recommendation.

**Avoid:** Do not manufacture certainty or block unrelated supported work.

## Worked example (authored, synthetic)

**Input:** Build log says 12 local checks passed. The deployment record says deployment was not run. The draft claims “The application is deployed and all checks passed.”

**Method:** Split local tests from deployment. Local tests are supported by the actual log; deployment is contradicted by the release record. Give a corrected sentence and retain the unresolved distribution status.

**Result:** “The 12 recorded local checks passed; deployment has not been run.” The result cites each record separately and makes no claim about user adoption.

## Failure diagnosis

### A long citation appears authoritative but says something else.
**Likely cause:** Source relevance was not checked against the exact proposition.

**Repair:** Read the cited span and narrow the claim to what it supports.

**Recheck:** Every claim has an entailment judgment, not only a URL.

### A successful fixture is described as production success.
**Likely cause:** Environment boundaries were omitted.

**Repair:** Restore the actual environment and named test scope.

**Recheck:** Confirm the report does not cross a source/runtime boundary.

### An old failed run is replaced by a new green summary.
**Likely cause:** Correction was treated as permission to rewrite history.

**Repair:** Keep both and explain the source change that led to the new result.

**Recheck:** The record is auditable without relying on the author's confidence.

## Preserve for the next turn

Preserve atomic claim IDs, exact source identity and locators, observation time, disposition, correction and unresolved counterevidence. New evidence changes the current finding without erasing the prior finding.

## Practice and mechanical checks

Public regression exercises. Worked answers are for learning; exclude them from comparison sessions.

Practice case IDs: `claim-audit-standard`, `claim-audit-scope`, `claim-audit-superseded`.
Packaged exercises live under `practice/`. The optional `practice/check_outputs.py` checks supplied JSON outputs; it does not call Muse or certify semantic/visual quality.

## Evidence boundary

More explicit procedures and checkable examples; comparative Muse performance has not been measured.

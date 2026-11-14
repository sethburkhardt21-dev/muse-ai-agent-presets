# Review a Change for Concrete Failure Paths — operational depth

Read only the branch needed for the current task. These are working methods, not a demand for additional approvals on ordinary reading or drafting.

## Choose the right action

### A patch and acceptance contract are available.
Review changed behavior and the paths that call it. Trace one valid input and one boundary input through the code.

**Avoid:** Do not substitute a generic checklist or review untouched modules without a reason.

### A potential defect cannot be reproduced.
Show the prerequisite and source trace, label confidence, and propose the smallest discriminating test.

**Avoid:** Do not declare a vulnerability or outage from a keyword alone.

### The review is meant to be independent.
Use a separate reviewer/context where actually available; otherwise call this a second pass by the same reviewer.

**Avoid:** Do not obtain independence merely by renaming the role.

### A requested change is style-only.
Respect the project's formatter and conventions; keep nits below behavior changes or omit them.

**Avoid:** Do not block delivery on personal taste.

### A fix is applied after review.
Recheck the exact changed region and regression, then close only the corresponding finding.

**Avoid:** Do not declare unrelated risk categories fixed.

## Worked example (authored, synthetic)

**Input:** Function subtotal(items) adds items[:-1] although its contract includes every item. A PR also changes the variable name but not behavior.

**Method:** Report the slice on line 2, demonstrate [5,7] gives 5 rather than 12, and explain that every nonempty invoice loses its last entry. Do not demand an unrelated architecture rewrite.

**Result:** One blocking correctness finding: total.py:2; evidence input [5,7], observed 5, expected 12; repair sum(items), then test empty, singleton and multiple entries. A clean version must receive no fabricated blocker.

## Failure diagnosis

### The reviewer reports many vague issues.
**Likely cause:** A checklist replaced source tracing.

**Repair:** For each issue, write the specific input, location and consequence; remove unsupported claims.

**Recheck:** The developer can act without asking what failed.

### A correct patch gets a blocker about an absent framework.
**Likely cause:** Review criteria drifted beyond the brief.

**Repair:** Remove the invented criterion and evaluate the original contract.

**Recheck:** Every blocker maps to a requirement or demonstrable risk.

### All findings disappear after one fix.
**Likely cause:** Finding identity and source revisions were not tracked.

**Repair:** Reopen the original findings against the new exact revision individually.

**Recheck:** Each closure has evidence specific to that finding.

## Preserve for the next turn

Preserve base/head identity, allowed paths, the accepted contract, finding IDs with location and impact, reproduction evidence and the actual reviewer provenance. Revalidate on drift; do not silently review a different change.

## Practice and mechanical checks

Public regression exercises. Worked answers are for learning; exclude them from comparison sessions.

Practice case IDs: `code-review-standard`, `code-review-clean`, `code-review-boundary`.
Packaged exercises live under `practice/`. The optional `practice/check_outputs.py` checks supplied JSON outputs; it does not call Muse or certify semantic/visual quality.

## Evidence boundary

More explicit procedures and checkable examples; comparative Muse performance has not been measured.

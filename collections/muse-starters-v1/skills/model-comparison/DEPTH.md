# Compare Model Candidates on the Same Frozen Task — operational depth

Read only the branch needed for the current task. These are working methods, not a demand for additional approvals on ordinary reading or drafting.

## Choose the right action

### The decision, cases and rubric already exist.
Use the frozen protocol instead of replanning it. Bind outputs to the exact inputs and candidate revisions.

**Avoid:** Do not change metrics or delete difficult cases after seeing results.

### Candidates differ in model, tools, context or budget.
Name the confound and withhold a head-to-head winner. Finish any descriptive calculations that remain valid.

**Avoid:** Do not credit a skill for a stronger model or additional tools.

### A candidate times out or returns no answer.
Preserve that result in the denominator under the predeclared rule. Distinguish execution failure from incorrect content.

**Avoid:** Do not silently remove failed cases to improve the average.

### Small numerical differences appear.
Apply the predeclared decision threshold and report sample size and per-case outcomes. Use an inconclusive result when the evidence does not separate the options.

**Avoid:** Do not translate a tiny public fixture gain into a broad capability claim.

### The evaluator also authored the candidate and examples.
Label the suite as public regression/development evidence and seek a separate task set/reviewer before a superiority claim.

**Avoid:** Do not call self-authored answer keys independent ground truth for subjective quality.

## Worked example (authored, synthetic)

**Input:** Four closed-label cases have labels A,B,A,B. Plain candidate predicts A,B,B,A (2/4), new candidate predicts A,B,A,A (3/4). The frozen improvement threshold is 0.20 and conditions match.

**Method:** Compute 0.50 and 0.75 accuracy with delta 0.25; the candidate crosses this narrow fixture threshold. If one run used another dataset or a different model, report no decision despite the difference.

**Result:** The candidate is selected for this four-case protocol only. This does not establish that it is generally better, and these authored inputs are not a protected holdout.

## Failure diagnosis

### A missing answer disappears from the report.
**Likely cause:** Only successful rows were normalized.

**Repair:** Restore every planned case and apply the frozen missing-output rule.

**Recheck:** Case coverage and denominator match the plan.

### The winner changes when a metric is edited.
**Likely cause:** Post-hoc scoring favored a desired result.

**Repair:** Restore the frozen metric; label the edited analysis exploratory.

**Recheck:** The decision can be regenerated from the original plan and raw results.

### Provider authenticity is claimed from a JSON field.
**Likely cause:** Metadata declarations were treated as identity evidence.

**Repair:** Describe local consistency only and retain original provider evidence separately.

**Recheck:** The report contains no fabricated authentication or model-run claim.

## Preserve for the next turn

Preserve the frozen plan and case hashes, candidate revisions, raw outputs including failures, model/tools/context/budgets, randomization order, reviewer provenance, scores and decision rule. Resume only missing work under the same protocol; new cases need a new version.

## Practice and mechanical checks

Public regression exercises. Worked answers are for learning; exclude them from comparison sessions.

Practice case IDs: `model-comparison-standard`, `model-comparison-confounded`, `model-comparison-missing`.
Packaged exercises live under `practice/`. The optional `practice/check_outputs.py` checks supplied JSON outputs; it does not call Muse or certify semantic/visual quality.

## Evidence boundary

More explicit procedures and checkable examples; comparative Muse performance has not been measured.

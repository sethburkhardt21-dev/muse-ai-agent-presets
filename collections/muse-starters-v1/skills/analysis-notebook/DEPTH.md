# Build a Reproducible Analysis Narrative — operational depth

Read only the branch needed for the current task. These are working methods, not a demand for additional approvals on ordinary reading or drafting.

## Domain method

Build an analysis as a reproducible sequence from identified inputs to transformations, checks and conclusions. Preserve the raw dataset, its schema and the unit of observation. Record missing-value handling, exclusions, joins, grouping and the denominator used for every reported metric.

An executable notebook is not automatically a trustworthy analysis. Re-run from a clean state where the tool allows it, detect hidden execution-order dependence, and reconcile totals with independent controls. Separate descriptive results from causal claims and exploratory patterns from a predeclared test. Never silently impute missing data or drop a group to improve a result.

## Output contract

Deliver the analysis artifact with data provenance, transformation steps, validation checks, interpretable tables and a conclusion linked to actual results. Provide a clear environment and rerun instruction where code is used. State unavailable inputs or unexecuted cells rather than filling in plausible outputs.

## Choose the right action

### The data is complete and the question is descriptive.
Compute the requested summaries with an explicit unit of analysis and denominator.

**Avoid:** Do not expand a simple summary into unsupported prediction.

### Observations contain missing values.
Show missingness and choose a stated treatment appropriate to the question.

**Avoid:** Do not treat missing values as zero without justification.

### A notebook depends on cells run out of order.
Restart in a disposable environment and execute the documented sequence.

**Avoid:** Do not call a stale visible output a fresh execution.

### A join changes the row count unexpectedly.
Inspect key uniqueness and join cardinality before interpreting the result.

**Avoid:** Do not accept duplicated observations as increased sample size.

### The user asks for a causal explanation from observational data.
Distinguish association, assumptions and alternative explanations.

**Avoid:** Do not infer causation from an attractive chart or a correlation alone.

## Worked example (authored, synthetic)

**Input:** Rows contain values 2, 4 and one missing value.

**Method:** Keep observed and missing rows separate; compute the mean over the declared observed set.

**Result:** Three input rows, two observed, one missing; sum 6 and observed mean 3. No imputation has been performed.

## Edge or recovery example 1 (authored, synthetic)

**Input:** All values in a group are missing.

**Method:** Treat the group as unobserved rather than inventing a zero average.

**Result:** The group’s mean is undefined, with zero observed rows and explicit missingness.

## Failure diagnosis

### The mean changes when blank cells are filled with zero.
**Likely cause:** The denominator and missingness policy changed silently.

**Repair:** Restore explicit missing-value handling and recompute both quantities.

**Recheck:** Observed count, missing count and metric agree.

### A rerun produces a different result.
**Likely cause:** Environment, random state or execution order is uncontrolled.

**Repair:** Record the relevant settings and isolate the nondeterministic step.

**Recheck:** The difference has an identified cause or remains an explicit limitation.

### A conclusion is unsupported by the displayed table.
**Likely cause:** Narrative was written before the checked result.

**Repair:** Recompute the claim from the final table and source scope.

**Recheck:** Every quantitative statement reconciles to actual output.

## Preserve for the next turn

Preserve raw input identity, schema, transformation code or formulas, environment, execution order, exclusions, denominators and unresolved checks. Resume from the last verified transformation, not a stale rendered notebook state.

## Practice and mechanical checks

Three authored public exercises cover a routine case, a constraint or ambiguity, and a changed-evidence recovery. Their answers are teaching and regression material, not hidden benchmarks. The checker tests supplied structured records only; a person must still assess usefulness, source fidelity and actual visual or interpersonal quality.

Practice case IDs: `analysis-notebook-r4-standard`, `analysis-notebook-r4-edge`, `analysis-notebook-r4-recovery`.
Packaged exercises live under `practice/`. The optional `practice/check_outputs.py` checks supplied JSON outputs; it does not call Muse or certify semantic/visual quality.

## Evidence boundary

Original task procedures and input-derived public exercise checks. No real Muse comparison, independent semantic superiority, clinical effectiveness or consumer adoption has been established.

# Inspect a Dataset Before Using It — operational depth

Read only the branch needed for the current task. These are working methods, not a demand for additional approvals on ordinary reading or drafting.

## Domain method

Dataset intake establishes what one row means, how identities and labels were obtained, and whether the data can support the intended use. Separate record IDs from entity or source-family IDs. Duplicate or related entities crossing train/test partitions can invalidate an evaluation even when rows are unique. Provenance, allowed use, temporal ordering, missingness and target leakage are distinct checks; a clean schema alone does not make data fit for modeling.

## Output contract

Deliver a bounded data card: source and use scope, schema, row and entity counts, duplicate/conflict findings, missingness, partition leakage, temporal limitations and an admit/hold decision for the stated use. Preserve raw input and do not train or upload automatically.

## Choose the right action

### Different rows represent the same person, source or event family.
Keep the related group in one evaluation partition or explain an appropriate alternative design.

**Avoid:** Do not treat unique row IDs as proof of independent holdout data.

### Two rows share a key but disagree on payload.
Quarantine the conflict and seek the source-owned version or resolution rule.

**Avoid:** Do not choose the latest file arrival as ground truth.

### A feature is only known after the outcome.
Flag target leakage and remove or redesign it for the intended prediction time.

**Avoid:** Do not retain it because it increases validation accuracy.

### The license or allowed use is unclear.
Record the uncertainty and hold the proposed use requiring that permission; continue non-sensitive schema work where authorized.

**Avoid:** Do not infer rights from public download availability.

### The dataset is a small convenience sample.
Bound conclusions to its observed population and identify missing coverage.

**Avoid:** Do not declare representative performance without evidence.

## Worked example (authored, synthetic)

**Input:** Rows r1 and r2 have different record IDs but entityE 1 appears in train and test; E2 appears only in train.

**Method:** Group by entity before checking partition independence.

**Result:** Hold the evaluation split because E1 crosses partitions. Unique row IDs do not remove leakage; propose a group-aware split without deleting the original records.

## Edge or recovery example 1 (authored, synthetic)

**Input:** A later intake has no group overlap, but feature final_status is recorded after the target event.

**Method:** Check feature availability at the intended prediction time.

**Result:** The split can pass entity isolation while the feature set remains held for target leakage. Do not promote the whole dataset to model-ready from one passing check.

## Failure diagnosis

### Held-out performance is implausibly high.
**Likely cause:** Entity overlap or post-outcome leakage may be present.

**Repair:** Inspect grouping and feature availability at prediction time before accepting the score.

**Recheck:** No prohibited entity or target information crosses the defined boundary.

### Deduplication silently deletes conflicting records.
**Likely cause:** Conflict handling was replaced with keep-first behavior.

**Repair:** Restore the originals and separate identical repeats from contradictions.

**Recheck:** Every discarded or held row has a traceable reason.

### The data card says approved but no use scope exists.
**Likely cause:** Technical cleanliness was confused with permission.

**Repair:** Remove the approval claim and name the unresolved use requirement.

**Recheck:** Technical and rights states are reported separately.

## Preserve for the next turn

Preserve raw digests, data dictionary, grouping and timing rules, allowed-use evidence, conflict list and partition decisions. Resume the specific unresolved check; do not silently resplit a consumed test set.

## Practice and mechanical checks

Three authored public exercises cover a standard task, an edge condition and recovery or changed evidence. Their answers are development examples, not held-out results. Supplied-output checks cover only declared facts and invariants; language quality, visual quality and real provider behavior remain separate.

Practice case IDs: `dataset-intake-r3-standard`, `dataset-intake-r3-edge`, `dataset-intake-r3-recovery`.
Packaged exercises live under `practice/`. The optional `practice/check_outputs.py` checks supplied JSON outputs; it does not call Muse or certify semantic/visual quality.

## Evidence boundary

Original specialist synthesis with source and fixture checks. No matched Muse comparison has been executed; greater domain detail is not measured superiority over upstream packages.

# Explain What Changed and Why It Matters — operational depth

Read only the branch needed for the current task. These are working methods, not a demand for additional approvals on ordinary reading or drafting.

## Domain method

Compare two explicitly identified states and report meaningful differences without inventing causes. Distinguish added, removed, modified and unchanged items, with stable identifiers where possible. An observation date, publication date and effective date are different fields and should not be silently substituted.

A change summary should explain impact on the user’s actual task, including reversions and uncertainty. Keep observed differences separate from hypotheses about why they happened. When records have been renamed, use evidence of identity rather than guessing that every similar label is the same object.

## Output contract

Deliver a concise what-changed table with before/after values, source revisions, affected decisions and unresolved identity or date questions. Include a practical next action only when the observed change warrants it. Preserve unchanged controls rather than implying everything moved.

## Choose the right action

### Both source snapshots are available.
Compare their stable IDs and relevant fields and cite the exact versions.

**Avoid:** Do not compare a current file with an unlabeled memory of the old state.

### A prior item disappears.
Mark removal only within the observed scope and check whether the source listing is complete.

**Avoid:** Do not equate a truncated result with confirmed deletion.

### Only a label changes.
Resolve identity from IDs or documented history before counting it as a new item.

**Avoid:** Do not inflate change counts through cosmetic renaming.

### A value reverts to an earlier value.
Report the reversion as a change from the immediate baseline and preserve the sequence.

**Avoid:** Do not erase the intervening state from history.

### The user asks why the change happened.
Separate supported explanation from plausible hypotheses and name the evidence needed to distinguish them.

**Avoid:** Do not present causal inference as a retrieved fact.

## Worked example (authored, synthetic)

**Input:** A changes from 1 to 3, B disappears, and C appears in complete snapshots v1 and v2.

**Method:** Classify by stable IDs and compare values only on shared records.

**Result:** A modified; B removed; C added. Reasons for the changes remain unestablished unless separately evidenced.

## Edge or recovery example 1 (authored, synthetic)

**Input:** A later snapshot restores A to 1.

**Method:** Use v2 as the immediate baseline, not the original value alone.

**Result:** Report A’s reversion from 3 to 1 at v3; do not label the latest transition unchanged.

## Failure diagnosis

### The brief says a record was removed when it still exists.
**Likely cause:** The second snapshot was incomplete or differently scoped.

**Repair:** Reconcile scope and pagination before classifying absence.

**Recheck:** Confirmed removal has complete comparable observations.

### A date in the summary is misleading.
**Likely cause:** Publication and effective dates were conflated.

**Repair:** Label each date by meaning and preserve unknowns.

**Recheck:** The user can tell when the change applies.

### A summary loses a rollback.
**Likely cause:** Only the oldest and newest state were compared.

**Repair:** Include the immediate predecessor and the relevant transition.

**Recheck:** The record preserves the actual change sequence.

## Preserve for the next turn

Preserve both snapshot identities, scope completeness, stable IDs, observed differences, date semantics and unresolved explanations. Resume with the next comparable snapshot, not an inferred history.

## Practice and mechanical checks

Three authored public exercises cover a routine case, a constraint or ambiguity, and a changed-evidence recovery. Their answers are teaching and regression material, not hidden benchmarks. The checker tests supplied structured records only; a person must still assess usefulness, source fidelity and actual visual or interpersonal quality.

Practice case IDs: `change-brief-r4-standard`, `change-brief-r4-edge`, `change-brief-r4-recovery`.
Packaged exercises live under `practice/`. The optional `practice/check_outputs.py` checks supplied JSON outputs; it does not call Muse or certify semantic/visual quality.

## Evidence boundary

Original task procedures and input-derived public exercise checks. No real Muse comparison, independent semantic superiority, clinical effectiveness or consumer adoption has been established.

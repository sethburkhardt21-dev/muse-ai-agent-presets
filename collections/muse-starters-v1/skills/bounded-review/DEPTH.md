# Review Against the Actual Brief — operational depth

Read only the branch needed for the current task. These are working methods, not a demand for additional approvals on ordinary reading or drafting.

## Domain method

Review the artifact against the actual brief and the current version, not an imagined ideal product. Freeze the review scope, mandatory requirements, evidence available and decision owner. Distinguish a reproduced defect from a plausible risk, missing evidence and a stylistic preference.

A useful review prioritizes consequence and gives the smallest corrective action. Verify positive controls as well as defects: an intentionally correct case should remain accepted. Independent review is a property of how the reviewer and evidence were obtained, not a label attached to a second script or a second machine.

## Output contract

Return a requirement-to-evidence matrix, prioritized findings with exact locations and counterexamples, passed checks, unobserved checks and a scope-limited verdict. Include repairs that address the demonstrated issue. Explicitly separate source review, runtime verification and aesthetic judgment.

## Choose the right action

### All stated requirements have current supporting evidence.
Accept only the reviewed scope and name the artifact revision.

**Avoid:** Do not promote a local review to deployment, safety certification or market superiority.

### A mandatory check has not been observed.
Mark that requirement unverified and identify the smallest evidence-producing step.

**Avoid:** Do not count an absent result as a pass or automatic product failure.

### A specific defect is reproduced.
Document the triggering input, location, consequence and minimal correction.

**Avoid:** Do not bury a concrete correctness issue among stylistic comments.

### A requested improvement is outside the brief.
Record it separately as an optional suggestion with cost and impact.

**Avoid:** Do not fail the artifact for an unagreed requirement.

### The artifact changes after review.
Invalidate affected findings and repeat only the relevant checks on the new revision.

**Avoid:** Do not reuse stale approval for materially different bytes.

## Worked example (authored, synthetic)

**Input:** Requirement A has a passing observation; requirement B has a reproduced failure.

**Method:** Keep the outcome specific to the two requirements and include the failure evidence.

**Result:** Verdict: changes needed for B. A remains passed; neither the whole project nor unrelated functions are declared broken.

## Edge or recovery example 1 (authored, synthetic)

**Input:** B has no test result rather than a failing result.

**Method:** Distinguish unknown from false and request the one missing check.

**Result:** Verdict: insufficient evidence for B. Do not fabricate a failure or silently pass it.

## Failure diagnosis

### A review produces many findings but little useful action.
**Likely cause:** Preferences were mixed with defects and evidence gaps.

**Repair:** Classify each item and rank by observable impact.

**Recheck:** The recipient can identify what must change and why.

### The same correct control is repeatedly rejected.
**Likely cause:** The rubric rewards finding faults rather than correctness.

**Repair:** Include an intentionally correct control and examine the rejection logic.

**Recheck:** A valid artifact can receive an evidence-backed acceptance.

### A previously approved output fails after editing.
**Likely cause:** Review identity was not bound to the artifact revision.

**Repair:** Recheck the changed portions and record a new decision.

**Recheck:** The final verdict names the version actually inspected.

## Preserve for the next turn

Preserve the reviewed revision, requirement IDs, exact evidence locations, findings, completed repairs and unobserved checks. Resume on the changed or unverified requirements; do not restart an unchanged full review without reason.

## Practice and mechanical checks

Three authored public exercises cover a routine case, a constraint or ambiguity, and a changed-evidence recovery. Their answers are teaching and regression material, not hidden benchmarks. The checker tests supplied structured records only; a person must still assess usefulness, source fidelity and actual visual or interpersonal quality.

Practice case IDs: `bounded-review-r4-standard`, `bounded-review-r4-edge`, `bounded-review-r4-recovery`.
Packaged exercises live under `practice/`. The optional `practice/check_outputs.py` checks supplied JSON outputs; it does not call Muse or certify semantic/visual quality.

## Evidence boundary

Original task procedures and input-derived public exercise checks. No real Muse comparison, independent semantic superiority, clinical effectiveness or consumer adoption has been established.

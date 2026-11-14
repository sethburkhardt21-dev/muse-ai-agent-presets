# Check a Release Without Confusing Build and Delivery — operational depth

Read only the branch needed for the current task. These are working methods, not a demand for additional approvals on ordinary reading or drafting.

## Domain method

Release readiness is a conjunction of independently scoped obligations: exact artifact identity, required source tests, package usability, migration/rollback conditions and intended destination. Source, runtime, deployment and user acceptance are different gates. Bind each result to the candidate it tested. A historical green build does not qualify new bytes, and a ready package is not a published release.

## Output contract

Deliver a gate matrix with candidate hash, required checks, observed outcomes, skips and missing evidence, plus a scoped GO/HOLD decision. Report publication separately. A successful check cannot silently waive another required gate.

## Choose the right action

### One required check is skipped on this platform.
Use an applicable qualified platform or keep that gate unresolved; show the supported-platform contract.

**Avoid:** Do not count a skip as a passing execution.

### A package changed after its tests.
Recompute its identity and rerun the checks affected by the changed bytes.

**Avoid:** Do not attach the old green receipt to the new artifact.

### Only source distribution is being released.
Require source, packaging, rights and relevant test gates without demanding an unrelated deployed assistant.

**Avoid:** Do not recreate the rejected native-installation acceptance criterion.

### A release request follows an uncertain publish attempt.
Read the original provider state and artifact identity before retrying.

**Avoid:** Do not publish twice because the local acknowledgment is absent.

### All checks pass but publication was not authorized.
Report ready for the stated scope and leave publication not performed.

**Avoid:** Do not equate readiness with a public release.

## Worked example (authored, synthetic)

**Input:** Candidate H2 needs unit, package and privacy checks. Unit and privacy pass on H2; package passed on H1. No publication occurred.

**Method:** Bind the three obligations to their tested artifact identities.

**Result:** HOLD: package evidence is stale for H2. Unit and privacy remain valid for H2; publication remains not performed. Rerun the package check against H2 rather than repeating unrelated valid checks.

## Edge or recovery example 1 (authored, synthetic)

**Input:** The package check now passes on H2, but an attempted upload timed out.

**Method:** Read the original upload target and compare its digest before any retry.

**Result:** Source readiness can be GO while publication remains unknown until original-provider readback. Do not announce a public release or upload a second copy blindly.

## Failure diagnosis

### The report says GO despite a required not-run check.
**Likely cause:** The gate used majority voting instead of conjunction.

**Repair:** List the missing obligation and hold the scoped release.

**Recheck:** Every required applicable gate has a passing result on the correct candidate.

### A reviewer assessed a different file set.
**Likely cause:** Review boundaries were implicit or stale.

**Repair:** Provide the exact diff and repeat only the affected review.

**Recheck:** The reviewed paths and candidate hash match the intended release.

### A published asset differs from the tested package.
**Likely cause:** Distribution bytes were rebuilt or replaced after qualification.

**Repair:** Preserve both artifacts, hold the release claim and reconcile the actual uploaded digest.

**Recheck:** Independent download matches the qualified artifact before release is claimed.

## Preserve for the next turn

Keep the candidate digest, obligation matrix, exact commands and results, qualified package, original publication identifier and rollback conditions. Resume the earliest unresolved gate without rebuilding accepted bytes.

## Practice and mechanical checks

Three authored public exercises cover a standard task, an edge condition and recovery or changed evidence. Their answers are development examples, not held-out results. Supplied-output checks cover only declared facts and invariants; language quality, visual quality and real provider behavior remain separate.

Practice case IDs: `release-readiness-r3-standard`, `release-readiness-r3-edge`, `release-readiness-r3-recovery`.
Packaged exercises live under `practice/`. The optional `practice/check_outputs.py` checks supplied JSON outputs; it does not call Muse or certify semantic/visual quality.

## Evidence boundary

Original specialist synthesis with source and fixture checks. No matched Muse comparison has been executed; greater domain detail is not measured superiority over upstream packages.

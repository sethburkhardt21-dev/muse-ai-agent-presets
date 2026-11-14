# Repair the Smallest Causal Boundary — operational depth

Read only the branch needed for the current task. These are working methods, not a demand for additional approvals on ordinary reading or drafting.

## Domain method

A minimal repair is the smallest change that restores the violated invariant without changing unrelated contracts. Minimal does not mean fewest characters: a short workaround can be less maintainable than a narrow causal fix. Bind the patch to the reproduced source revision and distinguish a regression assertion from the implementation it checks. Preserve controls for behavior that must not change.

## Output contract

Deliver the reproduced failure, causal explanation, exact changed files, focused and relevant broader test results, limitations and rollback instructions. A patch is proposed until executed evidence shows the intended behavior; deployment is a separate effect.

## Choose the right action

### The regression passes before any patch.
Recheck input, environment and revision; classify the defect as not currently reproduced.

**Avoid:** Do not edit speculative code merely to create a visible change.

### The source changed after reproduction.
Reproduce against the new revision or rebase the authorized candidate and retest.

**Avoid:** Do not apply a stale patch to a different baseline without reconciliation.

### A fix requires touching an unrelated module.
Explain the dependency and expand scope only when it is necessary and authorized.

**Avoid:** Do not sneak cleanup or feature work into the repair.

### A boundary test fails after the main case passes.
Keep the repair incomplete and inspect the invariant across both cases.

**Avoid:** Do not weaken the boundary assertion to preserve a green report.

### The full suite contains a pre-existing failure.
Compare the same failure at the parent revision and distinguish unchanged debt from regression.

**Avoid:** Do not erase the failure or claim an all-green suite.

## Worked example (authored, synthetic)

**Input:** At revision r1, an inclusive range parser omits the final value. The regression expects [2, 3, 4] for 2..4; an empty-input control already passes.

**Method:** Repair the endpoint calculation in parser.py only, then rerun the inclusive, singleton and empty-input cases.

**Result:** The candidate changes parser.py, passes the reproduced case and both controls, and reports broader tests separately. No deployment is implied by the local repair.

## Edge or recovery example 1 (authored, synthetic)

**Input:** Before applying the patch, HEAD becomes r2 and parser.py has another owner's edit.

**Method:** Do not overwrite r2; preserve the diff and rerun the reproduction on the new source.

**Result:** Status is source-drift review required, with no applied patch and no stale test result promoted to r2 acceptance.

## Failure diagnosis

### The patch changes many files without a causal link.
**Likely cause:** Refactoring was mixed with repair.

**Repair:** Isolate the narrow change and defer independent cleanup.

**Recheck:** Every changed file has a demonstrated role in restoring the invariant.

### Tests pass only after the expected answer is altered.
**Likely cause:** The test was changed to match the bug.

**Repair:** Restore the accepted contract and derive a legitimate correction.

**Recheck:** The regression still expresses the original intended behavior.

### A stale patch appears to fix a different revision.
**Likely cause:** Source identity was not checked at application.

**Repair:** Stop application, inspect the current diff and reproduce anew.

**Recheck:** The reported tests and artifact refer to the same exact source.

## Preserve for the next turn

Preserve the base and candidate identities, failing command, invariant, patch, unaffected controls, full-suite results and unmerged work. Resume from the first unverified gate, never by resetting the owner's tree.

## Practice and mechanical checks

Three authored public exercises cover a standard task, an edge condition and recovery or changed evidence. Their answers are development examples, not held-out results. Supplied-output checks cover only declared facts and invariants; language quality, visual quality and real provider behavior remain separate.

Practice case IDs: `minimal-repair-r3-standard`, `minimal-repair-r3-edge`, `minimal-repair-r3-recovery`.
Packaged exercises live under `practice/`. The optional `practice/check_outputs.py` checks supplied JSON outputs; it does not call Muse or certify semantic/visual quality.

## Evidence boundary

Original specialist synthesis with source and fixture checks. No matched Muse comparison has been executed; greater domain detail is not measured superiority over upstream packages.

# Reproduce a Defect Before Repairing It — operational depth

Read only the branch needed for the current task. These are working methods, not a demand for additional approvals on ordinary reading or drafting.

## Choose the right action

### A defect comes with a failing input and expected result.
Freeze the exact input, source revision and caller expectation; run the smallest original entrypoint that exhibits the mismatch.

**Avoid:** Do not begin by broad refactoring or changing the expected behavior to match the implementation.

### The report only says “sometimes wrong.”
Narrow the environment and input dimensions. Use an unaffected control and a bounded repeated run; record not reproduced when no failure appears.

**Avoid:** Do not turn a plausible theory into a reproduced diagnosis.

### The observed failure is an import, setup or permission error.
Report that distinct setup failure and repair the test environment within scope before diagnosing product logic.

**Avoid:** Do not count any red process exit as reproduction of the reported bug.

### A source edit occurs between reproduction and patch.
Re-read the revision and compare the affected code. Rebase the minimal reproducer on the current candidate before editing.

**Avoid:** Do not apply a stale repair or discard another writer's changes.

### The bug is reproduced and code changes are authorized.
Write the failing regression, then the smallest fix and controls. Keep the red output and actual green output tied to source.

**Avoid:** Do not mark a proposed patch tested or rebuild completed unrelated features.

## Worked example (authored, synthetic)

**Input:** A supplied total(items) function returns sum(items[:-1]). The contract says every input item contributes. For [5, 7], expected 12 but observed 5.

**Method:** Compare [5, 7] with the empty-list control, then run an assertion on the original function. The missing final slice element is a specific causal hypothesis. Repair to sum(items), then check empty, singleton, mixed sign and multi-item cases.

**Result:** The original regression fails with 5 != 12. The minimal patch changes one expression; the five-case fixture suite passes after the patch. This is an owned demonstration, not a claim that a Muse model produced the repair.

## Failure diagnosis

### The red test fails before reaching the function.
**Likely cause:** The environment rather than the behavior is broken.

**Repair:** Repair or report the setup issue, then rerun the original assertion.

**Recheck:** The log identifies the product assertion and actual mismatched values.

### The patch passes but the control changed.
**Likely cause:** The fix broadened behavior beyond the contract.

**Repair:** Inspect the causal boundary and add a control-specific regression.

**Recheck:** Controls remain unchanged and the reported failure is closed.

### The report contains a green badge without a command.
**Likely cause:** Evidence was summarized away.

**Repair:** Include source revision, command, exit, assertion, stdout/stderr location and scope.

**Recheck:** A fresh reader can reproduce the original defect without the chat.

## Preserve for the next turn

Keep exact input, expected and actual output, source version, environment, regression path, full observed command and exit, controls, patch boundary, and unrun checks. Resume from the current source rather than replaying the old command against changed bytes.

## Practice and mechanical checks

Public regression exercises. Worked answers are for learning; exclude them from comparison sessions.

Practice case IDs: `bug-reproduction-standard`, `bug-reproduction-setup`, `bug-reproduction-not-reproduced`.
Packaged exercises live under `practice/`. The optional `practice/check_outputs.py` checks supplied JSON outputs; it does not call Muse or certify semantic/visual quality.

## Evidence boundary

More explicit procedures and checkable examples; comparative Muse performance has not been measured.

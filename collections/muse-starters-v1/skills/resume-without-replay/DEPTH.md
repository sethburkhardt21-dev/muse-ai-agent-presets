# Resume Work Without Duplicating Effects — operational depth

Read only the branch needed for the current task. These are working methods, not a demand for additional approvals on ordinary reading or drafting.

## Choose the right action

### A prior operation has a provider-confirmed completed result.
Read the original result and continue from it using its operation ID; do not execute it again.

**Avoid:** Do not infer incompletion merely because a local receipt was lost.

### The request was sent but its outcome is unknown.
Reconcile the original operation at the original provider. Hold only the dependent action; continue independent authorized drafts.

**Avoid:** Do not issue a fresh idempotency key or repeat a send, purchase, write or publication.

### A planned step never started.
Check its current inputs and permission, then perform it once if still needed.

**Avoid:** Do not mark it completed from a plan or assume old approval covers a changed action.

### Source or recipient identity changed.
Compare the new state to the preserved source and stop the affected effect until the mismatch is resolved.

**Avoid:** Do not blindly sync, reset, delete scratch or substitute a different account.

### A step was denied.
Keep the denial and explain the exact affected action. Complete useful independent work without bypassing the denied route.

**Avoid:** Do not use another agent or machine to evade a refusal.

## Worked example (authored, synthetic)

**Input:** A report draft is saved. A send request mail-42 timed out with unknown outcome. A chart was planned but never started.

**Method:** Reopen the draft, look up mail-42 using the original mail route, and build the independent chart from preserved data. Do not send a duplicate email while the original outcome is unresolved.

**Result:** Actions: draft -> read_existing; mail-42 -> reconcile_original; chart -> execute_once_after_precheck. The missing send acknowledgment is a localized hold, not a reason to restart the whole project.

## Failure diagnosis

### A duplicate message appears after a timeout.
**Likely cause:** A retry used a new operation identity before reconciliation.

**Repair:** Inspect the original operation, preserve both observations and stop further duplicate attempts.

**Recheck:** Resume logic reuses the original effect identity.

### All progress is discarded after interruption.
**Likely cause:** Restart was mistaken for rebuild.

**Repair:** Inventory completed artifacts and verify their hashes or current versions.

**Recheck:** Only actually unfinished work is scheduled.

### An unrelated task is blocked by one unknown operation.
**Likely cause:** Dependencies were not distinguished.

**Repair:** Separate independent read/draft work from effect-dependent work.

**Recheck:** The next useful action does not depend on the unresolved effect.

## Preserve for the next turn

Preserve original provider operation IDs, scope and recipients, actual effect observations, exact source/artifact identity, uncommitted work, grants and the next dependent step. A handoff records existing authority; it never grants it.

## Practice and mechanical checks

Public regression exercises. Worked answers are for learning; exclude them from comparison sessions.

Practice case IDs: `resume-without-replay-standard`, `resume-without-replay-denied`, `resume-without-replay-resolved`.
Packaged exercises live under `practice/`. The optional `practice/check_outputs.py` checks supplied JSON outputs; it does not call Muse or certify semantic/visual quality.

## Evidence boundary

More explicit procedures and checkable examples; comparative Muse performance has not been measured.

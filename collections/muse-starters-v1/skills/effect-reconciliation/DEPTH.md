# Reconcile an Uncertain Operation Without Replaying It — operational depth

Read only the branch needed for the current task. These are working methods, not a demand for additional approvals on ordinary reading or drafting.

## Domain method

Bind every observation to the original operation, request digest and target before considering its state. Deduplicate identical observations, preserve mismatches and classify contradictory terminal reports as conflict. A missing receipt or uncertain observation remains unknown; do not invent a terminal outcome. Even a consistent supplied success record is only a supplied observation, not authenticated provider proof. The original authority must perform provider readback and decide any permitted continuation.

## Output contract

Return a consistency observation, retained receipt IDs and explicit requirements for provider readback. retry_authorized, provider_evidence_authenticated and external_actions_performed are always false. Preserve original operation identity and unresolved records; never manufacture a replacement ledger, claim or grant.

## Choose the right action

### No terminal provider record is available.
Keep the observation unknown and require readback under the original operation identity.

**Avoid:** Do not infer failure or no-effect from a timeout or missing local file.

### A receipt refers to another request digest or target.
Classify the evidence set as conflicting and retain the mismatch.

**Avoid:** Do not reuse a successful receipt from a different operation.

### Success and failure are both reported for the same bound operation.
Return conflict and ask the original provider to reconcile its durable state.

**Avoid:** Do not select the latest arrival as truth without a provider-owned ordering contract.

### An identical observation appears multiple times.
Deduplicate the observation without treating repetition as independent confirmation.

**Avoid:** Do not count copied receipts as extra evidence of execution.

### A supplied record consistently reports success with a receipt ID.
Report the supplied success observation while preserving unauthenticated-evidence and no-retry boundaries.

**Avoid:** Do not upgrade a locally provided JSON record into an authenticated completion or grant.

## Worked example (authored, synthetic)

**Input:** An operation has a request digest but only an unknown observation with no receipt.

**Method:** Match the original identity and retain the missing terminal outcome.

**Result:** The result remains unknown, requires provider readback and never authorizes retry.

## Edge or recovery example 1 (authored, synthetic)

**Input:** Two bound records declare success and failure under the same request digest.

**Method:** Preserve the contradiction rather than choosing a winner.

**Result:** The result is conflict with both evidence identities retained and no external action performed.

## Failure diagnosis

### An operation is executed twice after a network timeout.
**Likely cause:** The caller retried before recovering the original provider outcome.

**Repair:** Stop new retries and inspect the original operation and target readback.

**Recheck:** The unresolved effect remains fenced and no second operation is created by this tool.

### A completion report points to unrelated output.
**Likely cause:** Receipt identity was matched only by a display name or partial key.

**Repair:** Rebind operation ID, full request digest and target to the exact original record.

**Recheck:** Mismatched evidence produces conflict rather than successful completion.

### Deleted history is interpreted as permission to start over.
**Likely cause:** Retention erased the evidence needed to distinguish a replay from new work.

**Repair:** Preserve the hold and consult original retention/tombstone policy instead of fabricating history.

**Recheck:** No local absence can make retry_authorized true.

## Preserve for the next turn

Preserve the exact supplied input and tool version, the returned report, any unresolved source assumptions and the next authorized check. Return a consistency observation, retained receipt IDs and explicit requirements for provider readback. retry_authorized, provider_evidence_authenticated and external_actions_performed are always false. Preserve original operation identity and unresolved records; never manufacture a replacement ledger, claim or grant.

## Practice and mechanical checks

Three authored public exercises cover a standard input, an edge condition and changed evidence or recovery. Expected outputs are development examples, not hidden model evaluations.

Practice case IDs: `effect-reconciliation-r5-standard`, `effect-reconciliation-r5-edge`, `effect-reconciliation-r5-recovery`.
Packaged exercises live under `practice/`. The optional `practice/check_outputs.py` checks supplied JSON outputs; it does not call Muse or certify semantic/visual quality.

## Evidence boundary

Original first-party source and supplied-input calculations. No native Muse performance or superiority claim follows from the source examples.

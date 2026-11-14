# Review a Bounded Automation Plan Before Execution — operational depth

Read only the branch needed for the current task. These are working methods, not a demand for additional approvals on ordinary reading or drafting.

## Domain method

Model the requested workflow as an inert directed acyclic graph, separating read/draft steps from write, send, publish and delete effects. Validate identities and dependency closure before producing a deterministic topological order. Record declared approval and idempotency gaps, propagate blocked dependencies and retain independent admissible preparation work. The report is not permission: the original host must authenticate the actor, target, approval and current operation state immediately before each effect.

## Output contract

Return ordered step IDs, blocked steps with concrete reasons and a ready-for-host-review or blocked classification. execution_authorized and external_actions_performed are always false. A useful handoff includes the original user request, exact target identities, observable success conditions, failure reconciliation and evidence required by the existing executor.

## Choose the right action

### A step only reads supplied data or drafts a result.
Keep it separate from external effects and allow useful preparation under the actual request.

**Avoid:** Do not invent a permission barrier for ordinary reasoning or drafting.

### A write or send lacks declared approval.
Mark the step blocked and identify exactly which effect needs the host approval check.

**Avoid:** Do not turn a planner default into user consent.

### A required effect has no stable operation identity.
Require an idempotency key and original-provider reconciliation strategy.

**Avoid:** Do not assume retrying after a timeout is safe.

### A dependency is blocked but another branch is independent.
Propagate the block only along real dependency edges and continue independent preparation.

**Avoid:** Do not stop the entire workflow because one optional integration is absent.

### The plan has all declared approvals and keys.
Return ready_for_host_review while leaving execution_authorized false.

**Avoid:** Do not treat self-reported plan fields as authenticated execution authority.

## Worked example (authored, synthetic)

**Input:** A read step feeds a send step whose approval is false and whose idempotency key is once.

**Method:** Topologically order the graph and check the send effect separately.

**Result:** The report orders read then send, blocks send for approval_missing and grants no execution authority.

## Edge or recovery example 1 (authored, synthetic)

**Input:** The same plan declares approval true and a stable operation key.

**Method:** Validate the supplied contract while retaining the real host as the only authority.

**Result:** The review is ready_for_host_review, but execution_authorized and external_actions_performed remain false.

## Failure diagnosis

### The automation performs a send during what was described as a draft.
**Likely cause:** The workflow failed to classify effects explicitly.

**Repair:** Split drafting and sending into separate steps with separate observable outcomes.

**Recheck:** The plan lists the send as an effect and the checker still performs no external action.

### A downstream action runs after its prerequisite failed.
**Likely cause:** The implementation ignored dependency state or treated a planned output as actual output.

**Repair:** Propagate blocked predecessors and require source-bound result evidence before dispatch.

**Recheck:** Blocked steps cannot become ready solely because they appear later in a list.

### A connector timeout causes a duplicate operation.
**Likely cause:** The host retried without reconciling the original operation identity.

**Repair:** Inspect the original provider result under the same target and request digest.

**Recheck:** The plan preserves the unresolved effect and does not create a second operation automatically.

## Preserve for the next turn

Preserve the exact supplied input and tool version, the returned report, any unresolved source assumptions and the next authorized check. Return ordered step IDs, blocked steps with concrete reasons and a ready-for-host-review or blocked classification. execution_authorized and external_actions_performed are always false. A useful handoff includes the original user request, exact target identities, observable success conditions, failure reconciliation and evidence required by the existing executor.

## Practice and mechanical checks

Three authored public exercises cover a standard input, an edge condition and changed evidence or recovery. Expected outputs are development examples, not hidden model evaluations.

Practice case IDs: `automation-contract-r5-standard`, `automation-contract-r5-edge`, `automation-contract-r5-recovery`.
Packaged exercises live under `practice/`. The optional `practice/check_outputs.py` checks supplied JSON outputs; it does not call Muse or certify semantic/visual quality.

## Evidence boundary

Original first-party source and supplied-input calculations. No native Muse performance or superiority claim follows from the source examples.

# Automation Engineer

Prepare bounded application workflows, review target observations and reconcile uncertain effects through the existing host authority.

## Operating contract
Start with the current task and supplied evidence. These tools produce local reports, not a new assistant identity, scheduler, credential, or permission grant.
Use only available, authorized host tools for external work. Return useful read-only results when an optional provider is missing. Preserve uncertainty and original effect identities.

## Tools and domain methods

### Review a Bounded Automation Plan Before Execution (`automation-contract`)
Model the requested workflow as an inert directed acyclic graph, separating read/draft steps from write, send, publish and delete effects. Validate identities and dependency closure before producing a deterministic topological order. Record declared approval and idempotency gaps, propagate blocked dependencies and retain independent admissible preparation work. The report is not permission: the original host must authenticate the actor, target, approval and current operation state immediately before each effect.

Return ordered step IDs, blocked steps with concrete reasons and a ready-for-host-review or blocked classification. execution_authorized and external_actions_performed are always false. A useful handoff includes the original user request, exact target identities, observable success conditions, failure reconciliation and evidence required by the existing executor.

1. Recover the actual user goal, target account or application, existing tools and previously attempted operations.
2. Assign stable step identities and distinguish observations and drafts from consequential external effects.
3. Validate every dependency and reject cycles, unknown predecessors and undeclared target scope.
4. Check declared approval and idempotency coverage for effects, then propagate blocked prerequisites.
5. Prepare the largest independent read-only output without treating missing optional integrations as global failure.
6. Hand the inert plan to the original qualified executor with actor, approval, readback and stop conditions; do not dispatch from this checker.

### Choose a Locator From Actual Target Observations (`selector-resilience`)
Evaluate locator evidence rather than selector string cleverness. A candidate is eligible only when it refers to the intended target, matches exactly one element, is visible and is reported stable. Prefer semantic role, explicit test ID and label strategies before CSS where evidence is otherwise equivalent. Keep rejected candidates with reasons. The supplied observations can become stale; the browser owner must re-observe the target and surrounding context immediately before an authorized action.

Return the selected candidate ID or null, all eligible IDs, rejected IDs with reasons and whether more observation is needed. The report never claims a browser action or authenticated target observation. Include actual page/frame identity and observation age in the host handoff where available.

1. State the exact intended control, page and frame instead of guessing from a vague button label.
2. Read actual candidate match counts, visibility, stability and target binding; label fixture observations honestly.
3. Reject missing, duplicated, hidden, unstable or wrong-target observations before considering preference order.
4. Choose a deterministic eligible candidate using semantic strategy preference and stable candidate identity.
5. Have the existing browser adapter refresh the observation immediately before the approved action and verify the resulting state.
6. Preserve rejected candidates and any page drift so a later turn does not reuse an obsolete locator blindly.

### Reconcile an Uncertain Operation Without Replaying It (`effect-reconciliation`)
Bind every observation to the original operation, request digest and target before considering its state. Deduplicate identical observations, preserve mismatches and classify contradictory terminal reports as conflict. A missing receipt or uncertain observation remains unknown; do not invent a terminal outcome. Even a consistent supplied success record is only a supplied observation, not authenticated provider proof. The original authority must perform provider readback and decide any permitted continuation.

Return a consistency observation, retained receipt IDs and explicit requirements for provider readback. retry_authorized, provider_evidence_authenticated and external_actions_performed are always false. Preserve original operation identity and unresolved records; never manufacture a replacement ledger, claim or grant.

1. Recover the exact original operation ID, target and request digest before issuing any new call.
2. Read existing provider records and retain their raw source locations and observation times.
3. Check all three binding fields and quarantine wrong-request or wrong-target evidence.
4. Separate unknown, started and terminal declarations; detect contradictory terminal outcomes without choosing a convenient winner.
5. Return the consistency result with retry_authorized false and request original-provider readback.
6. Continue independent safe work while preserving the unresolved effect and exact resume instructions.

## Integration and recovery
Keep source inputs immutable. Save the output report and its input digest. A consistent local result is not a provider acknowledgment. Resolve ambiguous effects through the original authority before any retry.
The original eleven-role protocol remains unchanged. This is a real additional toolkit with its own methods and tools, not a renamed starter or live-agent enrollment.

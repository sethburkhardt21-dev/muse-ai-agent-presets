# Design a Service Workflow With Recoverable Handoffs — operational depth

Read only the branch needed for the current task. These are working methods, not a demand for additional approvals on ordinary reading or drafting.

## Domain method

Design a service as explicit states, owners, handoffs and acceptance conditions rather than a checklist that assumes every step succeeded. Distinguish ready work from blocked work, proposed ownership from accepted responsibility, and an unknown external outcome from a never-started task.

Use a small state model that fits the actual service. A handoff closes when the recipient acknowledges the required artifact, not when the sender writes a note. Define a recovery path for delays, missing inputs and ambiguous effects. Escalation should identify the specific decision owner and preserve useful independent work.

## Output contract

Deliver a service map with step IDs, inputs, outputs, owners, readiness, acceptance and exception paths. Include a compact case record and the next safe action. Do not replace a service’s real task system or invent authority to dispatch people or providers.

## Choose the right action

### A step has verified completion evidence.
Reuse its output and make dependent work eligible.

**Avoid:** Do not repeat a completed effect because a later local note is missing.

### A handoff has no accepted owner.
Mark the responsibility unassigned or awaiting acceptance and identify who must decide.

**Avoid:** Do not assign responsibility merely because someone was mentioned.

### An external operation timed out.
Reconcile the original operation identity and hold only dependent effects.

**Avoid:** Do not start a replacement with a new identity before knowing the original outcome.

### A prerequisite is incomplete.
Keep the dependent step held while continuing independent ready work.

**Avoid:** Do not flatten the entire service into a single blocked status.

### A denial or explicit stop exists.
Preserve it, explain the affected scope and seek the proper decision owner when necessary.

**Avoid:** Do not route through another account to evade the restriction.

## Worked example (authored, synthetic)

**Input:** A draft is complete, sending has an unknown outcome, and an independent chart is planned with an accepted owner.

**Method:** Classify the steps from actual state and dependencies.

**Result:** Reuse the draft, reconcile the original send, and proceed with the independent chart. Do not resend.

## Edge or recovery example 1 (authored, synthetic)

**Input:** The original service later confirms the send completed.

**Method:** Use the confirmation to settle that operation rather than creating another.

**Result:** Draft and send are completed; the chart remains the next ready action.

## Failure diagnosis

### A task appears complete but the recipient has nothing usable.
**Likely cause:** Sending and accepted handoff were conflated.

**Repair:** Inspect the actual artifact and acknowledgment.

**Recheck:** The state distinguishes prepared, sent, received and accepted.

### The service duplicates work after interruption.
**Likely cause:** Original operation IDs and completion evidence were lost.

**Repair:** Recover the last confirmed state before dispatching again.

**Recheck:** No completed or unknown effect is blindly repeated.

### A small exception stalls every customer.
**Likely cause:** The workflow lacks independent paths.

**Repair:** Separate affected dependencies and continue unaffected cases.

**Recheck:** The hold is limited to the actual prerequisite.

## Preserve for the next turn

Preserve service case IDs, accepted owners, artifact locations, actual state transitions, unresolved original operation IDs and dependency relationships. Resume from the last confirmed state without inventing acknowledgments.

## Practice and mechanical checks

Three authored public exercises cover a routine case, a constraint or ambiguity, and a changed-evidence recovery. Their answers are teaching and regression material, not hidden benchmarks. The checker tests supplied structured records only; a person must still assess usefulness, source fidelity and actual visual or interpersonal quality.

Practice case IDs: `service-playbook-r4-standard`, `service-playbook-r4-edge`, `service-playbook-r4-recovery`.
Packaged exercises live under `practice/`. The optional `practice/check_outputs.py` checks supplied JSON outputs; it does not call Muse or certify semantic/visual quality.

## Evidence boundary

Original task procedures and input-derived public exercise checks. No real Muse comparison, independent semantic superiority, clinical effectiveness or consumer adoption has been established.

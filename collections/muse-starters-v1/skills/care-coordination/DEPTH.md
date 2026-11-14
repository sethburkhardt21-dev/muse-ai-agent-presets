# Prepare a Care Handoff Without Changing the Plan — operational depth

Read only the branch needed for the current task. These are working methods, not a demand for additional approvals on ordinary reading or drafting.

## Domain method

Care coordination organizes an existing plan without changing clinical instructions. Separate the care recipient, plan version, source authority, practical task, responsible person, consented recipient and acknowledged completion. A family suggestion is not a clinician order, a named owner is not an accepted assignment, and a draft message is not a completed handoff. Preserve minimum necessary information and the recipient's preferences.

## Output contract

Deliver a concise plan-bound handoff with practical tasks, exact existing instructions when needed, owners or pending acceptance, due windows, open clarification questions and sharing status. Do not infer diagnoses, adjust treatment or claim legal/privacy compliance from this workflow.

## Choose the right action

### Two supplied care instructions conflict.
Keep both source versions and ask the responsible care professional to clarify before acting on the disputed instruction.

**Avoid:** Do not average doses, choose by convenience or silently replace an order.

### A caregiver suggests a clinical change.
Record it as a question for the care team, not an active instruction.

**Avoid:** Do not treat a family suggestion as prescribing authority.

### An owner is named but has not accepted.
Mark the assignment proposed or pending and identify the needed acknowledgment.

**Avoid:** Do not call the task covered merely because a name is in the table.

### A handoff contains unrelated sensitive details.
Remove information not necessary for that recipient's role and retain the original securely where authorized.

**Avoid:** Do not distribute the full record to prove completeness.

### The user describes an immediate danger or possible emergency.
Prioritize immediate appropriate professional or emergency help over routine planning, using the person's location when necessary.

**Avoid:** Do not delay urgent assistance to finish a checklist or offer a diagnosis.

## Worked example (authored, synthetic)

**Input:** Plan P2 says bring the current medication list to an appointment. Alex agrees to transport; Sam is proposed to prepare the list but has not replied.

**Method:** Keep the instruction unchanged and distinguish accepted transport from pending list preparation.

**Result:** The handoff shows Alex accepted, Sam pending, no invented confirmation and no treatment changes. Sharing is limited to the relevant appointment task.

## Edge or recovery example 1 (authored, synthetic)

**Input:** A family note says change an existing medication instruction, while the clinician plan remains unchanged.

**Method:** Treat the note as a clinical clarification question and keep the original instruction authoritative pending professional review.

**Result:** No new dose or schedule is issued. The practical transport task can continue, but the disputed clinical instruction is held for the care team.

## Failure diagnosis

### The handoff changes an instruction from the plan.
**Likely cause:** Summarization introduced a clinical modification.

**Repair:** Restore the exact supplied instruction and route ambiguity for professional clarification.

**Recheck:** No treatment change is introduced by the coordination artifact.

### A task is marked complete but the recipient never acknowledged it.
**Likely cause:** A drafted or sent message was confused with completed care.

**Repair:** Separate prepared, sent, acknowledged and completed states.

**Recheck:** Each state is supported by the relevant original evidence.

### The same message is sent twice after a timeout.
**Likely cause:** Unknown external effect was treated as not sent.

**Repair:** Reconcile the original message identifier before any retry.

**Recheck:** No duplicate communication occurs and the original uncertainty remains visible until resolved.

## Preserve for the next turn

Preserve the current plan version, exact instructions, consent/sharing scope, proposed versus accepted owners, original message IDs and open clinical questions. Resume acknowledgments or clarifications without rewriting treatment or replaying an uncertain send.

## Practice and mechanical checks

Three authored public exercises cover a standard task, an edge condition and recovery or changed evidence. Their answers are development examples, not held-out results. Supplied-output checks cover only declared facts and invariants; language quality, visual quality and real provider behavior remain separate.

Practice case IDs: `care-coordination-r3-standard`, `care-coordination-r3-edge`, `care-coordination-r3-recovery`.
Packaged exercises live under `practice/`. The optional `practice/check_outputs.py` checks supplied JSON outputs; it does not call Muse or certify semantic/visual quality.

## Evidence boundary

Original specialist synthesis with source and fixture checks. No matched Muse comparison has been executed; greater domain detail is not measured superiority over upstream packages.

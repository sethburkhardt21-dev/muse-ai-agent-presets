# Plan an Event Around Guests and Constraints — operational depth

Read only the branch needed for the current task. These are working methods, not a demand for additional approvals on ordinary reading or drafting.

## Domain method

Plan an event around confirmed people, capacity, access needs, schedule, responsibilities and complete costs. Separate an invitation, a tentative response and confirmed attendance. Staff, facilitators and other occupants can matter for capacity even when they are not counted as guests.

Build a run-of-show with dependencies, setup and teardown, not only the headline activity. Distinguish a quoted venue from a booked venue and a proposed owner from accepted responsibility. Preserve contingency decisions for weather, cancellation, accessibility and late changes without claiming that reservations or messages were executed.

## Output contract

Deliver a practical event brief, confirmed/pending guest ledger, capacity and budget calculations, run-of-show, assigned or unassigned responsibilities and contingency triggers. Flag unresolved accessibility or supplier commitments. Use actual service records before reporting a booking or delivery.

## Choose the right action

### Attendance is partly confirmed.
Calculate the confirmed scenario and keep pending guests visible.

**Avoid:** Do not treat every invitation as an accepted attendee.

### Capacity is tight.
Count all relevant occupants and review the venue’s actual rules.

**Avoid:** Do not omit staff or assume a capacity figure applies to every layout.

### A guest has stated access needs.
Include those needs in the plan and verify the relevant venue or service feature.

**Avoid:** Do not infer needs from identity or assume a generic accessible label is sufficient.

### The budget includes uncertain attendance.
Show scenarios and separate fixed, per-person and reserve amounts.

**Avoid:** Do not present a single estimate as a final supplier total.

### A booking or supplier outcome is ambiguous.
Reconcile the existing reservation or order before replacing it.

**Avoid:** Do not create duplicate commitments after a timeout.

## Worked example (authored, synthetic)

**Input:** Two guests are confirmed, one is pending, and one staff member will attend a venue with capacity three.

**Method:** Count confirmed guests and staff separately and retain the pending response.

**Result:** The confirmed scenario fits capacity; the pending guest is not silently admitted. Fixed 100, per-guest 20 and reserve 10 give a confirmed-scenario cost of 150.

## Edge or recovery example 1 (authored, synthetic)

**Input:** The third guest confirms without a capacity change.

**Method:** Update the headcount and per-person costs before changing commitments.

**Result:** The scenario now exceeds capacity and costs 170. Resolve capacity before claiming the plan is ready; no booking is performed by the calculation.

## Failure diagnosis

### The final headcount exceeds the venue limit.
**Likely cause:** Pending guests or staff were counted inconsistently.

**Repair:** Reconcile attendee state and all relevant occupants.

**Recheck:** Capacity is checked for the actual planned scenario.

### The budget grows unexpectedly.
**Likely cause:** Mandatory setup, supplier or reserve costs were missing.

**Repair:** Rebuild the itemized scenario and identify unconfirmed charges.

**Recheck:** The total is reproducible and its uncertainty explicit.

### A task falls between organizers.
**Likely cause:** Ownership was mentioned but never accepted.

**Repair:** Assign an explicit decision owner and verify acceptance.

**Recheck:** The run-of-show distinguishes accepted and unresolved responsibilities.

## Preserve for the next turn

Preserve attendee states, access requirements, venue rules, supplier and booking IDs, costs, accepted owners and contingency decisions. Resume from confirmed commitments and changed conditions, not a fresh set of duplicate bookings.

## Practice and mechanical checks

Three authored public exercises cover a routine case, a constraint or ambiguity, and a changed-evidence recovery. Their answers are teaching and regression material, not hidden benchmarks. The checker tests supplied structured records only; a person must still assess usefulness, source fidelity and actual visual or interpersonal quality.

Practice case IDs: `event-plan-r4-standard`, `event-plan-r4-edge`, `event-plan-r4-recovery`.
Packaged exercises live under `practice/`. The optional `practice/check_outputs.py` checks supplied JSON outputs; it does not call Muse or certify semantic/visual quality.

## Evidence boundary

Original task procedures and input-derived public exercise checks. No real Muse comparison, independent semantic superiority, clinical effectiveness or consumer adoption has been established.

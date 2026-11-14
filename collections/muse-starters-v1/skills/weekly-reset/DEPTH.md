# Reset a Week Around Real Capacity — operational depth

Read only the branch needed for the current task. These are working methods, not a demand for additional approvals on ordinary reading or drafting.

## Domain method

A weekly commitment ledger is a capacity model, not a carry-forward list. Separate available minutes, fixed events, deliberate reserve, dependency waits and outcomes already completed. Work backwards from hard deadlines; choose the next executable action rather than budgeting an entire vaguely named project. Record estimate uncertainty rather than disguising it as spare capacity.

## Output contract

Deliver a capacity calculation; selected, blocked, completed and explicitly deferred task IDs; proposed time allocations; a next action; and one tradeoff when the sum cannot fit. Each commitment retains its original owner and source. Proposed allocations are not new calendar events.

## Choose the right action

### Several calendars describe the same event.
Reconcile event identity and time range before calculating availability. Count the union of occupied intervals, then make unresolved overlaps visible.

**Avoid:** Do not count the same appointment twice or assume two differently titled events are duplicates.

### A priority depends on another person.
Retain it in the dependency queue; select an independent next action. Draft a specific unblock request without sending it automatically.

**Avoid:** Do not allocate implementation time before a prerequisite can be met.

### There are more commitments than capacity.
Protect user-stated non-negotiables; defer lower-ranked whole tasks and name the shortfall. Ask for one tradeoff only if every remaining item is mandatory.

**Avoid:** Do not shrink estimates to make a visually complete calendar.

### The previous week contains uncertain completion.
Check the original artifact or task state. Treat confirmed completion as history and an uncertain action as a reconciliation item.

**Avoid:** Do not repeat a send, booking or submission simply because a report is missing.

### The user has only ten minutes for review.
Use an abbreviated pass: capacity, hard commitments, top executable outcome and one consciously deferred item. Keep the full ledger for later.

**Avoid:** Do not demand a full productivity interview before returning a workable next step.

## Worked example (authored, synthetic)

**Input:** A week has 600 available minutes, 120 reserved, and priority-ordered actions A=180, B=240, C=120. None has prerequisites.

**Method:** Usable capacity is 480. A and B consume 420, leaving 60. C cannot be shortened to fit.

**Result:** Select A and B; reserve 120 minutes; leave 60 minutes unallocated; defer C with a 60-minute capacity shortfall. Start A. No calendar was changed.

## Edge or recovery example 1 (authored, synthetic)

**Input:** A is already complete; only 300 minutes remain, including 60 reserve. B needs approval that has not arrived; C requires 120 minutes.

**Method:** Remove A from the remaining load, keep B blocked and allocate C within 240 usable minutes.

**Result:** Completed: A. Blocked: B, awaiting named approval. Selected: C, 120 minutes. Unallocated: 120 minutes; no duplicate work or invented approval.

## Failure diagnosis

### The plan contains twelve hours of tasks in eight hours.
**Likely cause:** Tasks were ranked without a capacity subtotal.

**Repair:** Recompute estimated minutes plus reserve; defer complete items rather than hiding the excess.

**Recheck:** Selected minutes never exceed usable minutes and every omitted item has a disposition.

### A recurring task appears completed twice.
**Likely cause:** The recurrence identity was confused with the project identity.

**Repair:** Recover the occurrence date and original completion record.

**Recheck:** Only the current occurrence is eligible; past completion remains unchanged.

### The highest priority is stalled but consumes the whole week.
**Likely cause:** Importance was mistaken for present executability.

**Repair:** Expose the missing prerequisite and select work that can proceed.

**Recheck:** No blocked item is described as ready, and no external message is claimed sent.

## Preserve for the next turn

Keep the as-of timestamp, availability basis, reserve, estimates, task IDs, prerequisites, completion evidence and deferred reasons. On resume, refresh changed commitments and recompute only affected allocations.

## Practice and mechanical checks

Three authored public exercises cover a standard task, an edge condition and recovery or changed evidence. Their answers are development examples, not held-out results. Supplied-output checks cover only declared facts and invariants; language quality, visual quality and real provider behavior remain separate.

Practice case IDs: `weekly-reset-r3-standard`, `weekly-reset-r3-edge`, `weekly-reset-r3-recovery`.
Packaged exercises live under `practice/`. The optional `practice/check_outputs.py` checks supplied JSON outputs; it does not call Muse or certify semantic/visual quality.

## Evidence boundary

Original specialist synthesis with source and fixture checks. No matched Muse comparison has been executed; greater domain detail is not measured superiority over upstream packages.

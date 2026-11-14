# Build a Time-Aware Daily Brief — operational depth

Read only the branch needed for the current task. These are working methods, not a demand for additional approvals on ordinary reading or drafting.

## Choose the right action

### The calendar and priorities are already supplied.
Read them once, reconcile time zones, and immediately propose the day. Ask only for a constraint that changes feasibility.

**Avoid:** Do not restart onboarding or request calendar access merely to use supplied appointments.

### The requested work exceeds free time.
Protect fixed commitments and hard deadlines. Rank the remaining work using the user's priority order, place complete work blocks, and name what will not fit. Offer one tradeoff.

**Avoid:** Do not fill every gap, shorten estimates silently, or mark deferred work completed.

### A meeting has travel, setup or recovery time.
Treat the stated buffers as occupied intervals. Explain the conflict if they collide with another commitment. Use explicit offsets across time zones.

**Avoid:** Do not schedule a task at a meeting end when the travel buffer still runs.

### An optional weather or email source is unavailable.
Finish from supplied inputs; label the missing source and do not imply it was checked.

**Avoid:** Do not delay the whole plan or invent a morning digest.

### The user asks for execution, not a draft.
Separate plan generation from the particular authorized calendar/message operation; confirm the actual effect at its original service.

**Avoid:** Do not treat a proposed block as a booked event or install a recurring schedule implicitly.

## Worked example (authored, synthetic)

**Input:** Work window 09:00–12:00, a 10:00–11:00 meeting, a 60-minute report due 10:00, a 20-minute call due noon, and 30 minutes of shopping preparation. All times have the same UTC offset.

**Method:** Put the deadline-constrained report before the meeting, then the call, then the preparation; keep the remaining ten minutes unallocated. If preparation grows to 60 minutes, defer it instead of taking time from the meeting.

**Result:** 09:00–10:00 report; 10:00–11:00 existing meeting; 11:00–11:20 call; 11:20–11:50 shopping preparation; 11:50–12:00 buffer. These are proposed work blocks, not calendar writes.

## Failure diagnosis

### Two tasks overlap.
**Likely cause:** The plan was formed from a list rather than interval arithmetic.

**Repair:** Sort all fixed and proposed intervals and move the lower-priority proposal.

**Recheck:** Check each neighboring pair and every fixed-event buffer.

### Everything is declared urgent.
**Likely cause:** Inferred deadlines were mixed with confirmed ones.

**Repair:** Restore the user's deadline and priority fields; label real unknowns.

**Recheck:** Every urgency claim has an input source.

### The briefing is longer than the workday plan.
**Likely cause:** Source details were copied rather than prioritized.

**Repair:** Lead with the top outcomes, conflict, and first action; move optional context below.

**Recheck:** The user can act without reading the appendix.

## Preserve for the next turn

Preserve the as-of time, explicit timezone offsets, source event IDs, task estimates, protected buffers, deferred items and whether any external write actually occurred. On resume, refresh only changed events and recalculate affected intervals.

## Practice and mechanical checks

Public regression exercises. Worked answers are for learning; exclude them from comparison sessions.

Practice case IDs: `daily-briefing-standard`, `daily-briefing-overload`, `daily-briefing-buffer`.
Packaged exercises live under `practice/`. The optional `practice/check_outputs.py` checks supplied JSON outputs; it does not call Muse or certify semantic/visual quality.

## Evidence boundary

More explicit procedures and checkable examples; comparative Muse performance has not been measured.

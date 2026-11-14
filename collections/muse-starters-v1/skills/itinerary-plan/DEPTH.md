# Build a Feasible Itinerary With Contingencies — operational depth

Read only the branch needed for the current task. These are working methods, not a demand for additional approvals on ordinary reading or drafting.

## Domain method

Itinerary feasibility is a time-and-location constraint problem before it is a list of attractions. Distinguish local clock time from absolute instants, include transfer and check-in buffers, and check opening or admission windows for the actual date. A plan uses estimates; a reservation requires a separate confirmed provider action. Preserve hard accessibility, rest and budget constraints rather than optimizing only nominal travel time or price.

## Output contract

Deliver a sequenced itinerary with explicit dates/time zones, travel and buffer intervals, costs and assumptions, mandatory versus optional stops, contingency and booking status. Use current official sources for live schedules, entry rules or availability; fictional fixtures must remain labeled fictional.

## Choose the right action

### Two locations use different time zones.
Compare absolute instants and show local times with offsets or zone names.

**Avoid:** Do not infer a connection from clock labels alone.

### An arrival leaves less than the required transfer buffer.
Reject or replace that connection and show the shortfall.

**Avoid:** Do not silently shrink the buffer to retain a preferred option.

### A venue's current hours are unavailable.
Mark the stop provisional and choose a verified alternative where possible.

**Avoid:** Do not treat old search snippets as confirmed admission.

### A low-price option violates a hard accessibility or rest constraint.
Remove it from the viable set and explain the tradeoff.

**Avoid:** Do not bury the violated constraint in a footnote.

### A booking attempt has an unknown result.
Read the original reservation reference or account state before retrying.

**Avoid:** Do not place a second booking merely because a confirmation message was lost.

## Worked example (authored, synthetic)

**Input:** A fictional arrival is 14:00-05:00 and the next departure is 15:00-05:00; the required transfer buffer is 75 minutes.

**Method:** Compare the 60-minute interval with the 75-minute requirement.

**Result:** Reject the connection as 15 minutes short. Do not call it feasible because the departure clock is later.

## Edge or recovery example 1 (authored, synthetic)

**Input:** An arrival is 10:00+01:00 and departure is 10:30+02:00 on the same date.

**Method:** Convert both to UTC:09:00 and 08:30.

**Result:** The departure is 30 minutes before arrival, so the connection is impossible. No booking is made or implied.

## Failure diagnosis

### A connection appears feasible but arrives after departure in absolute time.
**Likely cause:** Local clock labels were compared without offsets or date rollover.

**Repair:** Normalize the instants and rebuild the sequence.

**Recheck:** Every connection has nonnegative travel and the required buffer.

### The day plan is full but impossible to walk or rest through.
**Likely cause:** Only activity duration was counted.

**Repair:** Add transport and rest intervals and defer optional stops.

**Recheck:** The full timeline, not just attraction times, fits the available window.

### The itinerary says booked but contains only a quote.
**Likely cause:** Research output was confused with a reservation.

**Repair:** Restore estimated/proposed status and require actual provider readback for booking claims.

**Recheck:** Each confirmed reservation has its original identifier and observed status.

## Preserve for the next turn

Preserve exact dates, offsets, source observation times, travel and buffer assumptions, hard constraints and original booking references. Resume the unverified leg or provider readback without duplicating reservations.

## Practice and mechanical checks

Three authored public exercises cover a standard task, an edge condition and recovery or changed evidence. Their answers are development examples, not held-out results. Supplied-output checks cover only declared facts and invariants; language quality, visual quality and real provider behavior remain separate.

Practice case IDs: `itinerary-plan-r3-standard`, `itinerary-plan-r3-edge`, `itinerary-plan-r3-recovery`.
Packaged exercises live under `practice/`. The optional `practice/check_outputs.py` checks supplied JSON outputs; it does not call Muse or certify semantic/visual quality.

## Evidence boundary

Original specialist synthesis with source and fixture checks. No matched Muse comparison has been executed; greater domain detail is not measured superiority over upstream packages.

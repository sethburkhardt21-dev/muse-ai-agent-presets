# Calculate an Event-Based Reliability Budget — operational depth

Read only the branch needed for the current task. These are working methods, not a demand for additional approvals on ordinary reading or drafting.

## Domain method

Define the unit of reliability before doing arithmetic: eligible requests, jobs or another source-owned event population. Compute bad events as total minus good, allowed bad events as total multiplied by one minus target, and burn as observed bad events divided by that allowance. Keep fractional budgets exact rather than rounding them into whole-event permission. An empty population has an undefined SLI and burn rate. Window calculation is not a paging policy; paging requires explicit multi-window and operational evidence.

## Output contract

Return the exact supplied-window SLI, bad-event count, allowed and remaining bad-event budgets, burn rate and no-traffic state. Decimal-string outputs preserve calculation meaning. Include eligibility exclusions, data freshness and target provenance in the human report. No monitor, alert or service setting is created.

## Choose the right action

### The event population is empty.
Return no-traffic with null SLI and burn; investigate whether the service is idle or measurement is missing.

**Avoid:** Do not report 100 percent reliability from a zero denominator.

### Good events exceed total eligible events.
Reject the inconsistent input and reconcile windows or filters before calculation.

**Avoid:** Do not clamp counts into a plausible answer.

### The budget is fractional.
Preserve the decimal allowance and compare the actual bad-event count directly.

**Avoid:** Do not round up an error allowance and change the objective.

### The remaining budget is negative.
Report the deficit and consult the existing change or incident policy.

**Avoid:** Do not automatically roll back, scale or page from a calculator output.

### The objective uses time availability rather than request outcomes.
Use the correct time-based measurement contract instead of this event-ratio calculator.

**Avoid:** Do not reuse a request ratio as an uptime percentage.

## Worked example (authored, synthetic)

**Input:** A window contains 1000 eligible requests, 998 good, with target 0.999.

**Method:** Calculate two bad events against an allowance of one, then divide bad events by allowance.

**Result:** The remaining budget is -1 event and burn rate is 2; the tool marks the budget exhausted without configuring alerts.

## Edge or recovery example 1 (authored, synthetic)

**Input:** A 60-minute window has zero good and zero total requests.

**Method:** Preserve the zero denominator and avoid interpreting absent traffic as success.

**Result:** The result is no_traffic with null SLI and burn rate; operational interpretation remains with the service owner.

## Failure diagnosis

### The reliability percentage changes when irrelevant events are added.
**Likely cause:** The eligible population was not frozen before counting.

**Repair:** Reconstruct the denominator from the service definition and record exclusions.

**Recheck:** Good and total counts describe the same eligible event population.

### A very small service appears to have a large unused budget.
**Likely cause:** Fractional allowed errors were rounded into whole errors.

**Repair:** Recalculate the target allowance with decimal arithmetic.

**Recheck:** The reported budget matches total multiplied by one minus the target exactly.

### A report says a service is healthy while telemetry is absent.
**Likely cause:** Missing observations were encoded as zero errors or perfect uptime.

**Repair:** Separate no traffic, missing telemetry and observed successful events.

**Recheck:** No-traffic output retains null SLI and null burn with monitoring still unconfigured.

## Preserve for the next turn

Preserve the exact supplied input and tool version, the returned report, any unresolved source assumptions and the next authorized check. Return the exact supplied-window SLI, bad-event count, allowed and remaining bad-event budgets, burn rate and no-traffic state. Decimal-string outputs preserve calculation meaning. Include eligibility exclusions, data freshness and target provenance in the human report. No monitor, alert or service setting is created.

## Practice and mechanical checks

Three authored public exercises cover a standard input, an edge condition and changed evidence or recovery. Expected outputs are development examples, not hidden model evaluations.

Practice case IDs: `service-objectives-r5-standard`, `service-objectives-r5-edge`, `service-objectives-r5-recovery`.
Packaged exercises live under `practice/`. The optional `practice/check_outputs.py` checks supplied JSON outputs; it does not call Muse or certify semantic/visual quality.

## Evidence boundary

Original first-party source and supplied-input calculations. No native Muse performance or superiority claim follows from the source examples.

# Infrastructure & Reliability Engineer

Turn service measurements into explicit error budgets, capacity estimates and incident timelines without changing infrastructure.

## Operating contract
Start with the current task and supplied evidence. These tools produce local reports, not a new assistant identity, scheduler, credential, or permission grant.
Use only available, authorized host tools for external work. Return useful read-only results when an optional provider is missing. Preserve uncertainty and original effect identities.

## Tools and domain methods

### Calculate an Event-Based Reliability Budget (`service-objectives`)
Define the unit of reliability before doing arithmetic: eligible requests, jobs or another source-owned event population. Compute bad events as total minus good, allowed bad events as total multiplied by one minus target, and burn as observed bad events divided by that allowance. Keep fractional budgets exact rather than rounding them into whole-event permission. An empty population has an undefined SLI and burn rate. Window calculation is not a paging policy; paging requires explicit multi-window and operational evidence.

Return the exact supplied-window SLI, bad-event count, allowed and remaining bad-event budgets, burn rate and no-traffic state. Decimal-string outputs preserve calculation meaning. Include eligibility exclusions, data freshness and target provenance in the human report. No monitor, alert or service setting is created.

1. Identify the service, event population, good-event condition and exact observation window.
2. Validate nonnegative integer counts, good not exceeding total, and a finite target strictly between zero and one.
3. Calculate SLI, bad-event allowance, remaining budget and burn with decimal arithmetic.
4. Treat zero eligible events as no traffic with unknown SLI and burn, not a perfect score.
5. Compare the result with the existing service-owned response policy; distinguish an exhausted budget from an authorized incident action.
6. Return a dated report and retain raw count provenance so another reviewer can reproduce the result.

### Size Capacity With Explicit Utilization and Reserve (`capacity-planning`)
Translate a workload measurement into a capacity bound, not a purchasing instruction. Effective per-instance capacity is measured throughput multiplied by target utilization; required serving instances are the ceiling of demand divided by effective capacity. Add reserve instances only after sizing serving capacity. State linearity and load-balancing assumptions, and distinguish a reserve that remains unavailable for normal load from active redundancy. Latency, queues, storage and shared dependencies need separate measurements.

Return required serving instances, total including reserve, additional instances relative to the current count, effective throughput per instance and currently available throughput after reserve. Record workload identity and assumptions in the handoff. No scale action is performed and the estimate is not a price quote.

1. Verify demand units and that the per-instance measurement represents the same endpoint mix and latency target.
2. Separate serving instances from reserve capacity and confirm whether reserve may carry normal traffic.
3. Multiply sustainable throughput by the chosen utilization target before dividing demand.
4. Round required serving instances upward, then add reserve and compare with current capacity.
5. Check non-linear bottlenecks, failure-domain requirements and measured saturation behavior before proposing changes.
6. Deliver the calculation with assumptions, a load-test plan and an explicit no-scale-action status.

### Reconstruct One Incident From Dated Evidence (`incident-triage`)
Normalize explicit offsets to a common timeline while preserving event identities. Require one incident start and at most one resolution boundary; reject future events, duplicate IDs and inconsistent chronology. Compute time to first mitigation and time to resolution only when those events are supplied. An unresolved incident has a running elapsed duration, not a fabricated end time. Correlation on the timeline informs hypotheses but does not establish causation or authorize a remediation.

Return the ordered event IDs, open/resolved state, time to mitigation, time to resolution and elapsed interval for this one incident. The narrative must distinguish observed impact, hypotheses and actions actually performed. Preserve absent resolution as null and describe the record as supplied evidence rather than authenticated telemetry.

1. Recover the original incident identifier, as-of time and actual response owner without starting another controller.
2. Read source events and require explicit offsets, unique IDs and a single start boundary.
3. Normalize times and reject events after the observation time or inconsistent mitigation/resolution ordering.
4. Calculate durations for this incident and retain missing milestones as unknown.
5. Separate likely causes from discriminating observations; propose the smallest reversible diagnostic within the existing authority.
6. Deliver the timeline, evidence gaps, scoped next action and exact resume record without claiming an unobserved repair.

## Integration and recovery
Keep source inputs immutable. Save the output report and its input digest. A consistent local result is not a provider acknowledgment. Resolve ambiguous effects through the original authority before any retry.
The original eleven-role protocol remains unchanged. This is a real additional toolkit with its own methods and tools, not a renamed starter or live-agent enrollment.

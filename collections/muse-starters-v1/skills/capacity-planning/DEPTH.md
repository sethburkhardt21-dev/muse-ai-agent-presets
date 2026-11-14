# Size Capacity With Explicit Utilization and Reserve — operational depth

Read only the branch needed for the current task. These are working methods, not a demand for additional approvals on ordinary reading or drafting.

## Domain method

Translate a workload measurement into a capacity bound, not a purchasing instruction. Effective per-instance capacity is measured throughput multiplied by target utilization; required serving instances are the ceiling of demand divided by effective capacity. Add reserve instances only after sizing serving capacity. State linearity and load-balancing assumptions, and distinguish a reserve that remains unavailable for normal load from active redundancy. Latency, queues, storage and shared dependencies need separate measurements.

## Output contract

Return required serving instances, total including reserve, additional instances relative to the current count, effective throughput per instance and currently available throughput after reserve. Record workload identity and assumptions in the handoff. No scale action is performed and the estimate is not a price quote.

## Choose the right action

### Demand is exactly divisible by effective capacity.
Keep the exact serving count without adding an unnecessary extra instance.

**Avoid:** Do not use approximate floating-point division that crosses a ceiling boundary.

### A reserve is required during normal operation.
Subtract it from current serving capacity and add it after sizing the required serving pool.

**Avoid:** Do not double-count reserve as both spare and available throughput.

### Demand is zero.
Return zero serving instances plus any explicitly required reserve.

**Avoid:** Do not invent nonzero traffic or silently remove a declared reserve.

### Throughput measurements come from different workload mixes.
Hold the recommendation until comparable measurements or an explicit conservative assumption are recorded.

**Avoid:** Do not average incompatible benchmarks into apparent certainty.

### A shared database or queue saturates before the service instances.
Model and measure that dependency separately and state that horizontal scaling may not help.

**Avoid:** Do not extrapolate linearly through a known shared bottleneck.

## Worked example (authored, synthetic)

**Input:** Demand is 900 requests/second, measured capacity 250, utilization target 0.6, four current instances and one reserve.

**Method:** Effective capacity is 150 per serving instance; six serve demand and one remains reserve.

**Result:** Seven total instances are required, three more than current; no infrastructure change is performed.

## Edge or recovery example 1 (authored, synthetic)

**Input:** Demand is zero and the owner still requires one standby instance.

**Method:** Keep the reserve requirement separate from serving demand.

**Result:** The estimate needs zero serving instances and one total instance, without assuming a scale-down is authorized.

## Failure diagnosis

### The scaled fleet still misses the latency target.
**Likely cause:** The calculation used peak throughput rather than sustainable throughput at the required latency.

**Repair:** Repeat a representative load test and update the measured per-instance input.

**Recheck:** The capacity estimate names the latency objective and actual sustainable measurement.

### An instance failure leaves insufficient headroom.
**Likely cause:** Reserve capacity was included in normal serving capacity.

**Repair:** Recalculate available throughput after removing the reserved instances.

**Recheck:** The declared failure reserve remains available at the planned demand.

### A tiny input change unexpectedly removes an instance.
**Likely cause:** Binary floating-point rounding crossed the serving-count boundary.

**Repair:** Use finite decimal inputs and an explicit ceiling operation.

**Recheck:** Boundary cases at and just above effective capacity produce the correct integer count.

## Preserve for the next turn

Preserve the exact supplied input and tool version, the returned report, any unresolved source assumptions and the next authorized check. Return required serving instances, total including reserve, additional instances relative to the current count, effective throughput per instance and currently available throughput after reserve. Record workload identity and assumptions in the handoff. No scale action is performed and the estimate is not a price quote.

## Practice and mechanical checks

Three authored public exercises cover a standard input, an edge condition and changed evidence or recovery. Expected outputs are development examples, not hidden model evaluations.

Practice case IDs: `capacity-planning-r5-standard`, `capacity-planning-r5-edge`, `capacity-planning-r5-recovery`.
Packaged exercises live under `practice/`. The optional `practice/check_outputs.py` checks supplied JSON outputs; it does not call Muse or certify semantic/visual quality.

## Evidence boundary

Original first-party source and supplied-input calculations. No native Muse performance or superiority claim follows from the source examples.

# Reconstruct One Incident From Dated Evidence — operational depth

Read only the branch needed for the current task. These are working methods, not a demand for additional approvals on ordinary reading or drafting.

## Domain method

Normalize explicit offsets to a common timeline while preserving event identities. Require one incident start and at most one resolution boundary; reject future events, duplicate IDs and inconsistent chronology. Compute time to first mitigation and time to resolution only when those events are supplied. An unresolved incident has a running elapsed duration, not a fabricated end time. Correlation on the timeline informs hypotheses but does not establish causation or authorize a remediation.

## Output contract

Return the ordered event IDs, open/resolved state, time to mitigation, time to resolution and elapsed interval for this one incident. The narrative must distinguish observed impact, hypotheses and actions actually performed. Preserve absent resolution as null and describe the record as supplied evidence rather than authenticated telemetry.

## Choose the right action

### Events use different valid time-zone offsets.
Normalize them to UTC for ordering and calculate durations from actual instants.

**Avoid:** Do not sort timestamp strings lexically and misorder equivalent local times.

### No resolution event exists.
Keep the incident open and report elapsed time through the explicit as-of timestamp.

**Avoid:** Do not use the last observation as an implicit successful resolution.

### Two records reuse an event ID.
Refuse ambiguous identity and reconcile the original records.

**Avoid:** Do not overwrite an inconvenient observation with the later row.

### A mitigation is dated after resolution.
Treat the boundary contract as inconsistent and request source reconciliation.

**Avoid:** Do not silently reorder or clamp timestamps to make a positive report.

### The caller asks for mean time to recovery from one incident.
Report this incident duration and explain the missing population needed for a mean.

**Avoid:** Do not label a single observation as a service-level average.

## Worked example (authored, synthetic)

**Input:** Start at 07:00-05:00, mitigation at 12:05Z and resolution at 12:20Z.

**Method:** Normalize the start to 12:00Z and calculate both elapsed intervals.

**Result:** The incident has 300 seconds to mitigation and 1200 seconds to resolution, not a population-average MTTR.

## Edge or recovery example 1 (authored, synthetic)

**Input:** Only a 12:00Z start exists at an as-of time of 12:10Z.

**Method:** Keep the missing mitigation and resolution boundaries explicit.

**Result:** The incident remains open with 600 seconds elapsed and null mitigation/resolution durations.

## Failure diagnosis

### The timeline places recovery before impact began.
**Likely cause:** Offsets were ignored or raw local-time strings were sorted.

**Repair:** Normalize all source times and replay the ordering from unchanged records.

**Recheck:** The ordered IDs and computed intervals agree with actual instants.

### An open incident appears completed.
**Likely cause:** The report inferred resolution from an absence of later alerts.

**Repair:** Remove the invented terminal event and retain an open state.

**Recheck:** Time to resolution is null until an explicit resolution record is supplied.

### A corrective action is reported without a receipt.
**Likely cause:** A proposed response was confused with an executed host operation.

**Repair:** Separate proposal, approval, execution and observed effect in the handoff.

**Recheck:** The report lists only actual effects and keeps remediation_performed false for this read-only tool.

## Preserve for the next turn

Preserve the exact supplied input and tool version, the returned report, any unresolved source assumptions and the next authorized check. Return the ordered event IDs, open/resolved state, time to mitigation, time to resolution and elapsed interval for this one incident. The narrative must distinguish observed impact, hypotheses and actions actually performed. Preserve absent resolution as null and describe the record as supplied evidence rather than authenticated telemetry.

## Practice and mechanical checks

Three authored public exercises cover a standard input, an edge condition and changed evidence or recovery. Expected outputs are development examples, not hidden model evaluations.

Practice case IDs: `incident-triage-r5-standard`, `incident-triage-r5-edge`, `incident-triage-r5-recovery`.
Packaged exercises live under `practice/`. The optional `practice/check_outputs.py` checks supplied JSON outputs; it does not call Muse or certify semantic/visual quality.

## Evidence boundary

Original first-party source and supplied-input calculations. No native Muse performance or superiority claim follows from the source examples.

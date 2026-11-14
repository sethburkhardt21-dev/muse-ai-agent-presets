# Review Metrics Without Inventing the Story — operational depth

Read only the branch needed for the current task. These are working methods, not a demand for additional approvals on ordinary reading or drafting.

## Domain method

A metric is a numerator, denominator, population, time window and measurement definition. Compare like with like before explaining a change. Distinguish absolute change, relative percentage change and percentage-point change. Decompose aggregate movement by exposure or segment mix where possible; a count can fall while the per-unit rate rises. Causal attribution requires evidence beyond temporal coincidence.

## Output contract

Deliver the original figures, reproducible calculations, comparability assessment, supported interpretation, alternative explanations and a decision-relevant next check. Preserve unknown or zero denominators explicitly. Label any recommendation as judgment rather than a measured effect.

## Choose the right action

### The denominator changed between periods.
Report both count and rate changes and explain the different questions they answer.

**Avoid:** Do not credit a falling count as improved performance without exposure context.

### The baseline value is zero.
Report the absolute change and mark relative percentage change undefined.

**Avoid:** Do not divide by zero, report infinity as a meaningful gain or invent a baseline.

### Metric definitions or collection coverage differ.
Mark the comparison noncomparable until a justified common definition is available.

**Avoid:** Do not combine unlike periods into a precise trend.

### A change occurred after a product intervention.
Describe timing and plausible alternatives; require an appropriate design for causal attribution.

**Avoid:** Do not replace after with because.

### A checked analytical source is authoritative and editing is presentation-only.
Preserve its numbers and return calculation disputes to the analysis owner.

**Avoid:** Do not silently recompute or change governed analysis while polishing a chart.

## Worked example (authored, synthetic)

**Input:** Tickets fall from 100 to90 while active accounts fall from 1000 to600.

**Method:** Compute counts and per-account rates separately:0.10 to0.15.

**Result:** Ticket count fell 10%; tickets per account rose 50%, an increase of 0.05 per account. This does not establish that a redesign helped or harmed users.

## Edge or recovery example 1 (authored, synthetic)

**Input:** The prior period has zero incidents and the current period has three.

**Method:** Use an absolute difference and preserve the zero baseline.

**Result:** Incidents increased by 3; relative percentage change is undefined. Do not report 300% or infinity as a valid comparison.

## Failure diagnosis

### The headline improves while the rate worsens.
**Likely cause:** A count was interpreted without its denominator.

**Repair:** Calculate per-unit exposure and rewrite the headline to preserve both findings.

**Recheck:** The direction of each reported change matches its own calculation.

### A rate difference is mislabeled a percentage.
**Likely cause:** Percentage points and relative change were confused.

**Repair:** Show the two formulas and correct the label.

**Recheck:** Units and denominators accompany every change.

### The report attributes all movement to one release.
**Likely cause:** Concurrent changes or selection were ignored.

**Repair:** Narrow the statement to observation and define a discriminating comparison.

**Recheck:** Causal language appears only with appropriate supporting evidence.

## Preserve for the next turn

Keep metric definitions, source versions, period and population filters, numerators/denominators, formulas and open alternative explanations. Resume the missing comparison or calculation, not an unsupported causal narrative.

## Practice and mechanical checks

Three authored public exercises cover a standard task, an edge condition and recovery or changed evidence. Their answers are development examples, not held-out results. Supplied-output checks cover only declared facts and invariants; language quality, visual quality and real provider behavior remain separate.

Practice case IDs: `metrics-review-r3-standard`, `metrics-review-r3-edge`, `metrics-review-r3-recovery`.
Packaged exercises live under `practice/`. The optional `practice/check_outputs.py` checks supplied JSON outputs; it does not call Muse or certify semantic/visual quality.

## Evidence boundary

Original specialist synthesis with source and fixture checks. No matched Muse comparison has been executed; greater domain detail is not measured superiority over upstream packages.

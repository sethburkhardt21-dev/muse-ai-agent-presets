# Choose a Chart That Preserves the Data’s Meaning — operational depth

Read only the branch needed for the current task. These are working methods, not a demand for additional approvals on ordinary reading or drafting.

## Domain method

Select a chart from the question and data structure: changes over ordered time, a relationship between measurements, or comparisons among categories require different encodings. Preserve units, denominators, missing values and uncertainty. A chart’s persuasive appearance must not outrun the underlying observations.

Use position, length and color deliberately. For bar charts, the baseline affects the encoded length; a truncated baseline can exaggerate differences and must be corrected or explicitly handled. A nonzero axis is not automatically wrong for every other chart. Provide an accessible title, explanatory text and, when useful, a data table. Review the actual render for labels, clipping and distinguishability.

## Output contract

Deliver a chart or a concrete chart specification with the supporting data, axis units, denominator, source, uncertainty and a brief evidence-bounded takeaway. Include accessible explanatory text. State when only a specification exists rather than claiming a rendered chart was inspected.

## Choose the right action

### The question is change over ordered time.
Use a time-aware view with the actual intervals and mark missing observations.

**Avoid:** Do not connect absent data as if it were observed without explanation.

### The question is category magnitude.
Use a comparison encoding and check the bar baseline and units.

**Avoid:** Do not exaggerate a small difference with a misleading truncated bar axis.

### The question is a relationship between variables.
Use an appropriate scatter view and preserve independent observations.

**Avoid:** Do not label association as causation.

### Important groups have different denominators.
Show rates or denominators explicitly and retain relevant group context.

**Avoid:** Do not compare raw totals as if exposure were equal.

### The chart is generated for a different screen or document size.
Inspect labels, contrast, overlap and the final reading order in that output.

**Avoid:** Do not certify visual quality from the code alone.

## Worked example (authored, synthetic)

**Input:** Four category values are shown with a bar axis beginning at 50.

**Method:** Recognize that bar length encodes magnitude and examine the baseline.

**Result:** Use a bar comparison with a corrected baseline and explicit units; do not infer causation from the differences.

## Edge or recovery example 1 (authored, synthetic)

**Input:** The same records instead describe paired measurements and units are missing.

**Method:** Change the encoding to a relationship view and retain the missing-unit issue.

**Result:** Propose a scatter chart, request or recover the units, and hold any causal interpretation.

## Failure diagnosis

### A chart’s headline claims more than the data shows.
**Likely cause:** Narrative and encoding were optimized for persuasion.

**Repair:** Rewrite the takeaway to match the observed comparison and uncertainty.

**Recheck:** The headline survives a direct check against the data.

### The visual comparison is distorted.
**Likely cause:** Axis baseline or aggregation changed the apparent magnitude.

**Repair:** Correct the encoding or make the limitation explicit.

**Recheck:** The displayed geometry does not misrepresent the quantities.

### The chart is technically correct but unreadable.
**Likely cause:** The final render was not inspected.

**Repair:** Review the actual display size and adjust labels and layout.

**Recheck:** Critical information remains legible without relying only on color.

## Preserve for the next turn

Preserve the data revision, transformations, chart specification, units and denominators, source attribution, final render evidence and unresolved readability checks. Resume from verified data rather than recreating an unsupported narrative.

## Practice and mechanical checks

Three authored public exercises cover a routine case, a constraint or ambiguity, and a changed-evidence recovery. Their answers are teaching and regression material, not hidden benchmarks. The checker tests supplied structured records only; a person must still assess usefulness, source fidelity and actual visual or interpersonal quality.

Practice case IDs: `chart-story-r4-standard`, `chart-story-r4-edge`, `chart-story-r4-recovery`.
Packaged exercises live under `practice/`. The optional `practice/check_outputs.py` checks supplied JSON outputs; it does not call Muse or certify semantic/visual quality.

## Evidence boundary

Original task procedures and input-derived public exercise checks. No real Muse comparison, independent semantic superiority, clinical effectiveness or consumer adoption has been established.

# Choose a Locator From Actual Target Observations — operational depth

Read only the branch needed for the current task. These are working methods, not a demand for additional approvals on ordinary reading or drafting.

## Domain method

Evaluate locator evidence rather than selector string cleverness. A candidate is eligible only when it refers to the intended target, matches exactly one element, is visible and is reported stable. Prefer semantic role, explicit test ID and label strategies before CSS where evidence is otherwise equivalent. Keep rejected candidates with reasons. The supplied observations can become stale; the browser owner must re-observe the target and surrounding context immediately before an authorized action.

## Output contract

Return the selected candidate ID or null, all eligible IDs, rejected IDs with reasons and whether more observation is needed. The report never claims a browser action or authenticated target observation. Include actual page/frame identity and observation age in the host handoff where available.

## Choose the right action

### A locator matches more than one visible element.
Reject it as nonunique and inspect a narrower semantic scope or frame.

**Avoid:** Do not choose the first matching element by index without a target justification.

### A candidate is unique but points to another control.
Reject the target mismatch even if the selector syntax is valid.

**Avoid:** Do not confuse a successful selector query with correct user intent.

### A control is hidden or still moving.
Request a fresh stable observation before action.

**Avoid:** Do not click through an overlay or compensate with forced interaction.

### Several candidates are eligible for the same target.
Prefer role, test ID or label evidence before CSS and retain the alternatives.

**Avoid:** Do not claim that a strategy preference proves future stability.

### The page navigates or re-renders after inspection.
Invalidate stale observations and rebind the target through the original browser context.

**Avoid:** Do not reuse a cached match count as current evidence.

## Worked example (authored, synthetic)

**Input:** A role locator matches two submit buttons; a unique test ID points to delete instead.

**Method:** Reject the first for ambiguity and the second for target mismatch.

**Result:** No candidate is selected and the report requests more observation without performing a click.

## Edge or recovery example 1 (authored, synthetic)

**Input:** A role locator has one visible stable match bound to submit.

**Method:** Admit it as an observed candidate under the supplied contract.

**Result:** The selected ID is returned, but browser_action_performed remains false until a separate real action occurs.

## Failure diagnosis

### The wrong submit control is activated.
**Likely cause:** A broad locator matched several forms or frames.

**Repair:** Inspect the correct form/frame and bind the candidate to the intended target identity.

**Recheck:** The refreshed locator has one visible stable match for the intended control.

### A formerly stable selector stops finding the control.
**Likely cause:** The UI changed or a transient CSS class was treated as stable identity.

**Repair:** Reinspect semantic labels and explicit test identifiers without guessing a new action.

**Recheck:** The new candidate is backed by current observation, not a fabricated DOM claim.

### The report says a click succeeded but no state changed.
**Likely cause:** Locator eligibility was mistaken for execution and effect verification.

**Repair:** Separate candidate selection, actual host action and resulting-state readback.

**Recheck:** browser_action_performed stays false in this checker and actual effects require separate receipts.

## Preserve for the next turn

Preserve the exact supplied input and tool version, the returned report, any unresolved source assumptions and the next authorized check. Return the selected candidate ID or null, all eligible IDs, rejected IDs with reasons and whether more observation is needed. The report never claims a browser action or authenticated target observation. Include actual page/frame identity and observation age in the host handoff where available.

## Practice and mechanical checks

Three authored public exercises cover a standard input, an edge condition and changed evidence or recovery. Expected outputs are development examples, not hidden model evaluations.

Practice case IDs: `selector-resilience-r5-standard`, `selector-resilience-r5-edge`, `selector-resilience-r5-recovery`.
Packaged exercises live under `practice/`. The optional `practice/check_outputs.py` checks supplied JSON outputs; it does not call Muse or certify semantic/visual quality.

## Evidence boundary

Original first-party source and supplied-input calculations. No native Muse performance or superiority claim follows from the source examples.

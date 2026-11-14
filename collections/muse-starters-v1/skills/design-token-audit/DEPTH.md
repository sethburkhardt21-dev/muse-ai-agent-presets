# Check Real Color Tokens Before Interface Handoff — operational depth

Read only the branch needed for the current task. These are working methods, not a demand for additional approvals on ordinary reading or drafting.

## Domain method

Calculate contrast from the actual foreground and background values, using sRGB linearization and relative luminance rather than visual intuition. Keep pair identity and caller-selected thresholds explicit. Compare the unrounded ratio to the threshold and round only the displayed value. Reject unsupported alpha, gradient and non-sRGB inputs instead of approximating them silently. A token pass says nothing by itself about font size, focus, semantics, keyboard behavior or the real composited screen.

## Output contract

Return every checked pair with token identities, calculated ratio, threshold and pass/fail result. Include an overall calculation result while keeping conformance_certified and rendered_ui_inspected false. The design handoff should also identify real component states and any missing browser, keyboard or visual inspection.

## Choose the right action

### A pair passes numerically but the rendered UI uses opacity.
Reconstruct or measure the actual composited colors before claiming that rendered pair passes.

**Avoid:** Do not apply opaque-token arithmetic to translucent layers without qualification.

### The displayed rounded ratio equals the minimum.
Use the unrounded computed ratio for the decision.

**Avoid:** Do not round a slightly failing value upward into a pass.

### A token uses a gradient, alpha channel or unsupported color space.
Refuse the bounded calculation and request the actual supported colors or an appropriate renderer measurement.

**Avoid:** Do not silently discard alpha or convert color spaces by guessing.

### All supplied pairs pass.
Report those calculated pairs as passing and keep other accessibility dimensions open.

**Avoid:** Do not certify keyboard navigation, semantics or focus behavior from a color check.

### A correction would damage the product hierarchy or brand intent.
Offer measured alternatives that preserve semantic role and compare them in the real component.

**Avoid:** Do not solve one ratio by making every interface color identical.

## Worked example (authored, synthetic)

**Input:** Black text token #000000 on white #ffffff has a supplied threshold of 4.5.

**Method:** Compute luminance for both opaque sRGB tokens and compare the unrounded ratio.

**Result:** The ratio is 21 and the pair passes; the tool does not claim the rendered interface or full accessibility was inspected.

## Edge or recovery example 1 (authored, synthetic)

**Input:** Muted text #aaaaaa is paired with white at the same threshold.

**Method:** Calculate the actual token pair instead of judging its appearance from a palette label.

**Result:** The pair fails the requested ratio, and a designer must choose and inspect a suitable replacement in context.

## Failure diagnosis

### Text remains hard to read despite a passing palette sheet.
**Likely cause:** The inspected tokens were not the colors actually adjacent in the rendered state.

**Repair:** Trace the component styles and inspect real compositing and background variants.

**Recheck:** The measured pair matches the actual component and state.

### A borderline pair is incorrectly reported as passing.
**Likely cause:** The checker rounded the ratio before threshold comparison.

**Repair:** Compare the full-precision value and retain the exact threshold.

**Recheck:** A value below the threshold remains a failure even when its displayed ratio rounds upward.

### A palette check is presented as complete accessibility approval.
**Likely cause:** A narrow numeric result was promoted to a broad conformance claim.

**Repair:** Separate token results from keyboard, semantics, zoom, focus and screen-reader evidence.

**Recheck:** The report retains explicit untested dimensions and conformance_certified false.

## Preserve for the next turn

Preserve the exact supplied input and tool version, the returned report, any unresolved source assumptions and the next authorized check. Return every checked pair with token identities, calculated ratio, threshold and pass/fail result. Include an overall calculation result while keeping conformance_certified and rendered_ui_inspected false. The design handoff should also identify real component states and any missing browser, keyboard or visual inspection.

## Practice and mechanical checks

Three authored public exercises cover a standard input, an edge condition and changed evidence or recovery. Expected outputs are development examples, not hidden model evaluations.

Practice case IDs: `design-token-audit-r5-standard`, `design-token-audit-r5-edge`, `design-token-audit-r5-recovery`.
Packaged exercises live under `practice/`. The optional `practice/check_outputs.py` checks supplied JSON outputs; it does not call Muse or certify semantic/visual quality.

## Evidence boundary

Original first-party source and supplied-input calculations. No native Muse performance or superiority claim follows from the source examples.

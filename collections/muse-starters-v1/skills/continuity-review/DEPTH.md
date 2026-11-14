# Review Continuity Across a Creative Sequence — operational depth

Read only the branch needed for the current task. These are working methods, not a demand for additional approvals on ordinary reading or drafting.

## Choose the right action

### A brief defines persistent character or scene attributes.
Make a continuity card separating invariants from intentional transitions: handedness, prop ownership, costume, screen direction, scale, light and time.

**Avoid:** Do not treat every visual change as a defect.

### The actual frames or audio are available.
Inspect the start, midpoint, end and each cut; compare observations to the continuity card. Record timestamps or frame IDs.

**Avoid:** Do not accept filenames, shot notes or a render exit as proof of what appears on screen.

### Only a shot manifest or someone else's observation notes are supplied.
Perform a scoped manifest/record review and mark direct visual inspection not run. Still flag contradictions present in the records.

**Avoid:** Do not claim you watched a sequence you could not open.

### A violation is localized.
Ask for the smallest affected shot or transition to be repaired, preserving accepted frames and intended motion.

**Avoid:** Do not restart the entire production or change the approved character.

### The sequence passes continuity but export quality is unknown.
Keep continuity, timing, readability, audio and consumer-open checks separate.

**Avoid:** Do not equate continuity with finished-media acceptance.

## Worked example (authored, synthetic)

**Input:** The approved character carries a red satchel in the left hand throughout shots 1–3. Supplied frame observations say frame 001 is left-hand, frame 025 is right-hand, frame 049 is left-hand.

**Method:** Locate the discrepancy at frame 025 and ask for a repair to shot 2 only. A later shot intentionally switches lighting from day to night; that approved transition is not a defect.

**Result:** Finding: shot-2/frame-025 violates the left-hand invariant. Preserve shots 1 and 3. State that this review used supplied observation records, not newly viewed frames.

## Failure diagnosis

### The checklist passes but the rendered prop moves hands.
**Likely cause:** The review inspected plan metadata instead of frame observations.

**Repair:** Open the actual frames or label direct review unavailable; compare frame-level observations.

**Recheck:** The repaired cut has observed frame IDs, not only a checklist tick.

### Intentional changes are reported as continuity failures.
**Likely cause:** Invariants and transitions were mixed.

**Repair:** Re-read approved transition notes and narrow findings.

**Recheck:** Each finding violates a stated invariant rather than taste.

### A text storyboard is called a finished animation.
**Likely cause:** Artifact types were conflated.

**Repair:** Report exactly which files exist and which render/decode checks ran.

**Recheck:** A consumer can open the claimed output format.

## Preserve for the next turn

Preserve approved continuity rules, accepted frames, shot and frame IDs, actual observation provenance, unresolved regions, timing and the smallest repair scope. Resume the failed shot; do not regenerate accepted shots.

## Practice and mechanical checks

Public regression exercises. Worked answers are for learning; exclude them from comparison sessions.

Practice case IDs: `continuity-review-standard`, `continuity-review-intentional`, `continuity-review-missing-view`.
Packaged exercises live under `practice/`. The optional `practice/check_outputs.py` checks supplied JSON outputs; it does not call Muse or certify semantic/visual quality.

## Evidence boundary

More explicit procedures and checkable examples; comparative Muse performance has not been measured.

# Deliver Media in the Requested Usable Form — operational depth

Read only the branch needed for the current task. These are working methods, not a demand for additional approvals on ordinary reading or drafting.

## Domain method

Export quality has distinct technical, perceptual and delivery dimensions. Bind the final artifact to the requested dimensions, frame rate, duration tolerance, audio/caption requirements and usable format. Decode or probe the actual file, inspect representative visual states and listen where audio matters. A successful encoder exit does not establish that the requested content survived editing.

## Output contract

Deliver the actual requested file when the authorized tools can produce it, plus a compact verification record: identity, media properties, content checks, missing requirements and destination readback. Label planning-only, rendered-partial and complete distinctly.

## Choose the right action

### A requested music or narration track is missing.
Render the independent parts only if useful, state the missing requirement and keep completion partial.

**Avoid:** Do not invent licensed audio or call a silent file complete.

### The output aspect ratio differs from the assets.
Choose a deliberate crop, letterbox or reframe and inspect the subject at relevant moments.

**Avoid:** Do not stretch the image or assume the default crop preserves content.

### Captions are requested without a transcript.
Use an authorized transcription route or identify the missing caption source.

**Avoid:** Do not guess dialogue and describe it as accurate captions.

### The renderer is unavailable.
Provide the usable edit specification as supporting work and name the missing renderer.

**Avoid:** Do not claim a produced file or substitute a plan without stating the gap.

### An upload acknowledgment is missing.
Read the original destination and artifact identity before retrying.

**Avoid:** Do not duplicate an external upload or confuse a local path with delivered access.

## Worked example (authored, synthetic)

**Input:** The requested output is 1080 × 1920, 30 fps,20 seconds within 0.5 seconds, with audio. The file probes correctly but contains no audio stream.

**Method:** Compare each requirement with the actual probe and inspection record.

**Result:** Status is rendered-partial with audio missing. Correct dimensions and duration remain verified; a successful render does not satisfy the absent track.

## Edge or recovery example 1 (authored, synthetic)

**Input:** A repaired file has audio, correct properties and inspected frames, but the share upload times out.

**Method:** Keep local rendering complete and reconcile the original upload separately.

**Result:** The local artifact is complete; external delivery remains unknown until destination readback. Do not rerender or duplicate-upload solely to obtain a new acknowledgment.

## Failure diagnosis

### The file has the right extension but cannot be played.
**Likely cause:** Container naming was used as a proxy for decoded media.

**Repair:** Probe and decode the actual bytes, then re-export if the stream is invalid.

**Recheck:** A real decoder reads the intended streams and duration.

### The technical check passes but text is cut off.
**Likely cause:** Visual inspection was omitted.

**Repair:** Adjust layout or safe area and re-render the affected sequence.

**Recheck:** Reopened frames show the complete required text at usable size.

### The report says complete despite missing audio.
**Likely cause:** Completion was tied only to encoder success.

**Repair:** List the unmet requirement and downgrade to rendered-partial.

**Recheck:** Complete requires every mandatory technical and content condition.

## Preserve for the next turn

Keep source identities, edit decisions, export settings, output digest, probe/inspection records and original delivery operation. Resume the missing content or delivery check without overwriting originals.

## Practice and mechanical checks

Three authored public exercises cover a standard task, an edge condition and recovery or changed evidence. Their answers are development examples, not held-out results. Supplied-output checks cover only declared facts and invariants; language quality, visual quality and real provider behavior remain separate.

Practice case IDs: `edit-and-export-r3-standard`, `edit-and-export-r3-edge`, `edit-and-export-r3-recovery`.
Packaged exercises live under `practice/`. The optional `practice/check_outputs.py` checks supplied JSON outputs; it does not call Muse or certify semantic/visual quality.

## Evidence boundary

Original specialist synthesis with source and fixture checks. No matched Muse comparison has been executed; greater domain detail is not measured superiority over upstream packages.

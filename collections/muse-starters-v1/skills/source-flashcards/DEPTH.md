# Create Traceable Study Cards — operational depth

Read only the branch needed for the current task. These are working methods, not a demand for additional approvals on ordinary reading or drafting.

## Choose the right action

### The learner supplies a closed lecture or reference set.
Use that set as the answer source. Preserve its terminology, numbers, units and exceptions; put clarifications outside the cards if requested.

**Avoid:** Do not silently replace exam material with outside facts or put caveats into every answer.

### A fact contains a qualifier, threshold or contrast.
Create one answerable card that retains the qualifier. Split a multi-part fact only when each part remains independently meaningful.

**Avoid:** Do not turn sometimes into always, a range into a point estimate, or an example into a universal rule.

### An image or table carries the answer.
Inspect it using an available viewer, retain page/region identity and resolve ambiguous cells before using them. If unavailable, hold only that card.

**Avoid:** Do not infer unread visual content from nearby text.

### Two versions disagree.
Keep version and source locator attached. Mark the specific contested card for review while continuing unambiguous cards.

**Avoid:** Do not merge incompatible answers into a supposedly authoritative card.

### The learner answers incorrectly.
Show the answer and one source-grounded explanation, identify the missed distinction, then ask a transfer question without leaking its answer.

**Avoid:** Do not declare mastery from one correct attempt.

## Worked example (authored, synthetic)

**Input:** Synthetic equipment lesson: “Cool storage is 2–8 degrees C. Recheck the seal every 14 days. A broken seal is replaced immediately.”

**Method:** Create separate questions for storage range and routine inspection interval. Keep the immediate-replacement exception separate from the routine interval. Each answer retains an exact source location and supporting quotation.

**Result:** Card: “What is the cool-storage range?” Answer: “2–8 degrees C.” Evidence: lesson-v1:L1. A second card asks the routine inspection interval, and its answer is 14 days—not the interval for replacing a broken seal.

## Failure diagnosis

### A numeric answer lost its units.
**Likely cause:** A fragment was copied without its governing clause.

**Repair:** Restore the complete measured quantity from the source.

**Recheck:** Compare value, range endpoints, units and conditions.

### The question gives away the answer.
**Likely cause:** A cloze was made from nearly the whole sentence.

**Repair:** Ask a direct retrieval question with a distinct answer.

**Recheck:** Read the prompt without the answer and check that retrieval is required.

### All answers are exact quotes but some support the wrong question.
**Likely cause:** Quotation matching was mistaken for semantic entailment.

**Repair:** Check question-answer-evidence alignment manually.

**Recheck:** Treat the script as a locator/value check, not an educational-quality certificate.

## Preserve for the next turn

Preserve source version, page/line locators, card IDs, pending visual checks and learner corrections. Save actual attempts separately from cards; do not overwrite the learner's established source rules.

## Practice and mechanical checks

Public regression exercises. Worked answers are for learning; exclude them from comparison sessions.

Practice case IDs: `source-flashcards-standard`, `source-flashcards-qualifier`, `source-flashcards-conflict`.
Packaged exercises live under `practice/`. The optional `practice/check_outputs.py` checks supplied JSON outputs; it does not call Muse or certify semantic/visual quality.

## Evidence boundary

More explicit procedures and checkable examples; comparative Muse performance has not been measured.

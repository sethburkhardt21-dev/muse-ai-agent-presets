# Map a Lecture Before Deep Study — operational depth

Read only the branch needed for the current task. These are working methods, not a demand for additional approvals on ordinary reading or drafting.

## Domain method

Build a source-bounded concept graph before detailed notes. Distinguish prerequisites, mechanisms, consequences, contrasts and exceptions; keep the lecturer's terminology and numeric qualifiers. A heading map is not yet an explanation, and a plausible prerequisite is not automatically in the examinable source.

## Output contract

Deliver a small concept hierarchy, directional prerequisite edges, slide/page anchors, key contrasts, numeric facts with conditions, and a short reading route. Label inferred teaching links separately from explicit lecture claims. Preserve the original lecture file.

## Choose the right action

### Slides mostly contain labels and diagrams.
Inspect the figure and its legend before explaining relationships; mark edges unavailable if the diagram cannot be read.

**Avoid:** Do not infer a complete mechanism from labels alone.

### A prerequisite is useful but absent from the supplied material.
Label it an organizing prerequisite or optional background; keep it separate from exam-source facts.

**Avoid:** Do not present added knowledge as a quote from the lecture.

### Two slides use different meanings for one term.
Preserve both contexts and attach the local definitions.

**Avoid:** Do not merge homonyms into one misleading node.

### A threshold has a population or condition attached.
Carry the qualifier and units into the map and fact list.

**Avoid:** Do not strip the condition to produce a simpler but false flashcard.

### The learner wants only an initial skim.
Return the main questions, dependencies and contrasts; reserve detailed notes for a later pass.

**Avoid:** Do not transform a short orientation into a complete textbook chapter.

## Worked example (authored, synthetic)

**Input:** A fictional lecture has P1: flow depends on pressure difference and resistance; P2: resistance rises when a tube narrows; P3: compare two tubes at the same pressure difference.

**Method:** Map pressure difference and resistance before the comparison; keep same-pressure as a condition.

**Result:** Read P1, then P2, then P3. Contrast pressure difference with absolute pressure. Comparison conclusion remains conditional on the same pressure difference; no unsupported numeric law is added.

## Edge or recovery example 1 (authored, synthetic)

**Input:** P3 is an unreadable diagram and the caption only says two configurations.

**Method:** Retain P1/P2 and mark the P3 relationship unresolved.

**Result:** Map complete for P1/P2; P3 comparison held pending the diagram. Do not invent which configuration has greater flow.

## Failure diagnosis

### The map is a slide-title list.
**Likely cause:** Headings were copied without identifying relationships.

**Repair:** Add one causal or prerequisite link for each major sequence and cite the supporting locations.

**Recheck:** The learner can explain why the reading order helps.

### The map contains a cycle of prerequisites.
**Likely cause:** Related concepts were mislabeled as strict prerequisites.

**Repair:** Convert the unsupported edge to association or separate the levels of explanation.

**Recheck:** A claimed prerequisite order is acyclic.

### A numeric fact contradicts the slide.
**Likely cause:** A condition, sign or unit was lost in summarization.

**Repair:** Reopen the precise source and correct the entire fact tuple.

**Recheck:** Value, unit, direction and condition all match the source.

## Preserve for the next turn

Keep source revision, page anchors, concept IDs, explicit versus inferred edge labels and unreadable regions. Re-map only changed lecture sections and never silently merge different course versions.

## Practice and mechanical checks

Three authored public exercises cover a standard task, an edge condition and recovery or changed evidence. Their answers are development examples, not held-out results. Supplied-output checks cover only declared facts and invariants; language quality, visual quality and real provider behavior remain separate.

Practice case IDs: `lecture-map-r3-standard`, `lecture-map-r3-edge`, `lecture-map-r3-recovery`.
Packaged exercises live under `practice/`. The optional `practice/check_outputs.py` checks supplied JSON outputs; it does not call Muse or certify semantic/visual quality.

## Evidence boundary

Original specialist synthesis with source and fixture checks. No matched Muse comparison has been executed; greater domain detail is not measured superiority over upstream packages.

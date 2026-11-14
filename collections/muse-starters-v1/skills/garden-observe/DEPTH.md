# Turn Garden Observations Into a Useful Care Log — operational depth

Read only the branch needed for the current task. These are working methods, not a demand for additional approvals on ordinary reading or drafting.

## Domain method

Build a plant-specific observation record before proposing care changes. Keep location, light, watering history, substrate, weather context and the actual observed symptom separate. Similar visible symptoms can have multiple causes; a photograph or a single sensor value does not automatically establish a diagnosis.

Use stable plant IDs and dated observations to distinguish a new condition from an old note. Prefer low-risk information gathering when evidence is incomplete. Do not automate watering, pesticide use or other physical effects merely because a generic plant profile suggests a routine. For species-specific treatment or toxicity questions, verify appropriate current sources.

## Output contract

Deliver an observation log, competing explanations where useful, the missing discriminating measurements and a bounded next observation or care question. Mark diagnosis and treatment state honestly. Keep plants, pots and locations distinguishable across records.

## Choose the right action

### A clear dated observation is available.
Record the symptom and context without adding unobserved details.

**Avoid:** Do not convert a description into a confirmed disease diagnosis.

### Several records describe the same plant.
Use the current sequence or timestamp and preserve the history.

**Avoid:** Do not let input ordering override the latest actual observation.

### The plant identity or environment is uncertain.
Ask for the discriminating information needed for the next decision.

**Avoid:** Do not prescribe species-specific care from an assumed identity.

### A measurement conflicts with visible condition.
Check the measurement location, timing and reliability before choosing an explanation.

**Avoid:** Do not treat a sensor reading as infallible.

### A proposed action changes a physical system or uses a chemical.
Verify the relevant guidance and actual user authorization; keep uncertain treatment on hold.

**Avoid:** Do not trigger irrigation or recommend hazardous treatment from a generic template.

## Worked example (authored, synthetic)

**Input:** P1 has observations at sequences 1 and 2; P2 has one observation but no usable measurement.

**Method:** Choose the latest observation for each stable plant ID and preserve the measurement gap.

**Result:** Use P1’s sequence-2 record and P2’s existing record. Request the relevant missing P2 observation; no diagnosis or treatment is claimed.

## Edge or recovery example 1 (authored, synthetic)

**Input:** P2 receives a new observation and a usable measurement.

**Method:** Update only P2’s current record and compare it with its own history.

**Result:** The missing-measurement hold is resolved, but the evidence still does not by itself prove a diagnosis.

## Failure diagnosis

### A care suggestion is based on an old observation.
**Likely cause:** Plant history was flattened or sorted incorrectly.

**Repair:** Reconcile the latest dated record for the correct plant.

**Recheck:** The next step reflects current evidence.

### Repeated care changes make the condition harder to interpret.
**Likely cause:** Several variables were changed simultaneously.

**Repair:** Record prior changes and choose a bounded observation strategy.

**Recheck:** The next observation can distinguish relevant explanations.

### Two plants’ histories are mixed.
**Likely cause:** Names or pot locations were treated as stable identity.

**Repair:** Assign and preserve plant IDs with location history.

**Recheck:** Each observation maps to the correct plant.

## Preserve for the next turn

Preserve stable plant IDs, dates, environmental context, observed symptoms, measurements, actual care changes and uncertainty. Resume with the latest verified observation rather than automatically repeating an old care schedule.

## Practice and mechanical checks

Three authored public exercises cover a routine case, a constraint or ambiguity, and a changed-evidence recovery. Their answers are teaching and regression material, not hidden benchmarks. The checker tests supplied structured records only; a person must still assess usefulness, source fidelity and actual visual or interpersonal quality.

Practice case IDs: `garden-observe-r4-standard`, `garden-observe-r4-edge`, `garden-observe-r4-recovery`.
Packaged exercises live under `practice/`. The optional `practice/check_outputs.py` checks supplied JSON outputs; it does not call Muse or certify semantic/visual quality.

## Evidence boundary

Original task procedures and input-derived public exercise checks. No real Muse comparison, independent semantic superiority, clinical effectiveness or consumer adoption has been established.

# Turn Customer Assumptions Into Testable Questions — operational depth

Read only the branch needed for the current task. These are working methods, not a demand for additional approvals on ordinary reading or drafting.

## Domain method

Decompose a business idea into assumptions about a specific person, recurring task, current workaround, consequence and willingness to change. Interview evidence should describe actual behavior before soliciting reactions to a proposed solution. Distinguish what participants said, what they demonstrably did, and what they paid for.

Count people and independent observations rather than the number of quotes. A convenient sample can identify useful problems but does not establish population demand. Keep negative evidence, recruitment filters and leading questions visible. A useful outcome is a sharper hypothesis and next discriminating test, not automatic validation of the founder’s idea.

## Output contract

Deliver an assumption map, neutral interview questions, source-linked observations grouped by participant, contradictory evidence and a bounded next experiment. Separate direct behavior from opinion and observed willingness to pay from hypothetical enthusiasm. Do not contact participants or store personal details beyond the authorized scope.

## Choose the right action

### The user has only an idea and target audience.
Identify the riskiest behavior assumption and create questions about the last real occurrence of the problem.

**Avoid:** Do not lead with a sales pitch or ask whether people like the idea.

### Interview notes already exist.
Extract observations with participant IDs and preserve exact context before clustering.

**Avoid:** Do not paraphrase every favorable quote into proof of demand.

### Several quotes come from one participant.
Count that person once for participant-level patterns and retain the distinct events separately.

**Avoid:** Do not inflate support by counting repeated quotations as independent customers.

### Participants praise the concept but show no behavior.
Label the evidence as opinion and propose a low-cost test of an actual next step.

**Avoid:** Do not equate politeness, clicks or hypothetical payment with sales.

### Evidence contradicts the initial assumption.
Narrow, revise or stop the hypothesis and retain the disconfirming observations.

**Avoid:** Do not discard inconvenient interviews to rescue the original story.

## Worked example (authored, synthetic)

**Input:** Two quotes come from P1 expressing interest; P2 shows a recurring manual workaround.

**Method:** Use participant-level counting and separate opinion from behavior.

**Result:** Two participants, one with observed workaround behavior, zero observed paying customers. This is a useful problem signal, not proven market demand.

## Edge or recovery example 1 (authored, synthetic)

**Input:** P2 later pays for a small pilot.

**Method:** Add the observed payment event without turning one person into a new participant.

**Result:** Two participants, one paying participant. Keep the sample limitation and test whether the problem recurs elsewhere.

## Failure diagnosis

### Every interview appears positive.
**Likely cause:** Questions introduced the desired answer.

**Repair:** Rewrite prompts around recent real behavior and inspect negative or neutral cases.

**Recheck:** The next interview can falsify the assumption.

### A pattern is supported by many quotes but few people.
**Likely cause:** The unit of analysis drifted.

**Repair:** Deduplicate at the participant level and show the denominator.

**Recheck:** The report distinguishes quote count from independent participants.

### A pilot is declared successful before anyone commits.
**Likely cause:** Interest was promoted to purchase evidence.

**Repair:** Define a real behavioral success event before the next test.

**Recheck:** The outcome uses the original event and denominator.

## Preserve for the next turn

Preserve the hypothesis version, participant-safe IDs, recruitment criteria, interview questions, raw observations, contradictory evidence and frozen next-test criteria. Resume from actual new evidence rather than rewriting history as validation.

## Practice and mechanical checks

Three authored public exercises cover a routine case, a constraint or ambiguity, and a changed-evidence recovery. Their answers are teaching and regression material, not hidden benchmarks. The checker tests supplied structured records only; a person must still assess usefulness, source fidelity and actual visual or interpersonal quality.

Practice case IDs: `customer-discovery-r4-standard`, `customer-discovery-r4-edge`, `customer-discovery-r4-recovery`.
Packaged exercises live under `practice/`. The optional `practice/check_outputs.py` checks supplied JSON outputs; it does not call Muse or certify semantic/visual quality.

## Evidence boundary

Original task procedures and input-derived public exercise checks. No real Muse comparison, independent semantic superiority, clinical effectiveness or consumer adoption has been established.

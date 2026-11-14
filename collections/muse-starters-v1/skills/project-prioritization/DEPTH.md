# Prioritize Work Using Dependencies and Capacity — operational depth

Read only the branch needed for the current task. These are working methods, not a demand for additional approvals on ordinary reading or drafting.

## Domain method

Prioritization first establishes feasibility, then ranks value. Model dependency closure, owner/resource capacity, deadlines and uncertainty before applying scores. RICE, weighted value or cost-of-delay are heuristics whose inputs and units must be stated; they do not create capacity or establish causal impact. A high-scoring blocked task is not executable work, and a dependency cycle needs resolution rather than a reordered list.

## Output contract

Deliver an executable selection with dependency order, per-resource capacity accounting, explicit deferred and blocked items, scoring assumptions and one next action. Keep stakeholder preference separate from measured benefit and never turn an estimate into a delivery promise.

## Choose the right action

### The highest-value item depends on unfinished work.
Include its prerequisite closure and total cost, or mark it blocked if the dependency cannot be met.

**Avoid:** Do not schedule the dependent item as independently executable.

### Two tasks need the same scarce person at the same time.
Account for that person's capacity once and sequence or defer the conflict.

**Avoid:** Do not sum nominal team hours as interchangeable capacity.

### A dependency cycle appears.
Report the cycle and identify the decision or split that would break it.

**Avoid:** Do not manufacture a topological order for a cyclic graph.

### Scores are based on uncertain reach or effort.
Show a sensitivity range or alternative ordering rather than false precision.

**Avoid:** Do not present a decimal score as proof of business value.

### A stakeholder adds a mandatory task mid-cycle.
Recompute capacity and state exactly which commitment is displaced.

**Avoid:** Do not silently add work while preserving the old deadline promise.

## Worked example (authored, synthetic)

**Input:** A resource has 10 hours. Task A costs 3, B costs 5 and depends on A, C costs 4. The user ranks B above C and requires complete tasks.

**Method:** Treat B as an 8-hour dependency bundle A+B, then test whether C fits the 2-hour residual.

**Result:** Select A then B for 8 hours and defer C. Do not select B alone or squeeze C into the remaining 2 hours.

## Edge or recovery example 1 (authored, synthetic)

**Input:** A depends on B and B depends on A.

**Method:** Detect the cycle before scoring or scheduling.

**Result:** No executable order exists for that pair until a dependency is removed or work is split with authority. Independent task C may proceed if its own prerequisites and capacity permit.

## Failure diagnosis

### The plan fits total hours but overloads one owner.
**Likely cause:** Capacity was aggregated across noninterchangeable skills.

**Repair:** Recalculate by resource and move or defer conflicting tasks.

**Recheck:** Every resource stays within its own admitted budget.

### A selected item cannot start despite being ranked first.
**Likely cause:** Dependencies were ignored during selection.

**Repair:** Add the prerequisite closure or mark the item blocked.

**Recheck:** Every scheduled dependency precedes its consumer.

### A priority score changes without new evidence.
**Likely cause:** Weights were adjusted to justify a preferred outcome.

**Repair:** Preserve the original scoring rule and document a deliberate policy change separately.

**Recheck:** The ranking can be reproduced from stated inputs and weights.

## Preserve for the next turn

Preserve backlog and score versions, resource budgets, prerequisite closure, completed work and displacement decisions. Resume from the changed constraint rather than rescoring everything to fit a preferred answer.

## Practice and mechanical checks

Three authored public exercises cover a standard task, an edge condition and recovery or changed evidence. Their answers are development examples, not held-out results. Supplied-output checks cover only declared facts and invariants; language quality, visual quality and real provider behavior remain separate.

Practice case IDs: `project-prioritization-r3-standard`, `project-prioritization-r3-edge`, `project-prioritization-r3-recovery`.
Packaged exercises live under `practice/`. The optional `practice/check_outputs.py` checks supplied JSON outputs; it does not call Muse or certify semantic/visual quality.

## Evidence boundary

Original specialist synthesis with source and fixture checks. No matched Muse comparison has been executed; greater domain detail is not measured superiority over upstream packages.

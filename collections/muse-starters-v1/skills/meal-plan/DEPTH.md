# Plan Meals Around Real Preferences and Supplies — operational depth

Read only the branch needed for the current task. These are working methods, not a demand for additional approvals on ordinary reading or drafting.

## Domain method

Plan meals from the person’s stated preferences, schedule, equipment, available ingredients and budget. Treat allergies, dietary restrictions and ingredient uncertainty as explicit constraints rather than lifestyle guesses. Use the actual package or authoritative ingredient information when a real safety decision depends on it.

Scale recipes with portions and yield, subtract usable pantry quantities in compatible units, and distinguish shopping cost from ingredients already owned. Avoid prescribing medical diets, making weight-loss promises or certifying food safety from a text-only list. A useful plan has practical preparation order and alternatives when an ingredient or label is unknown.

## Output contract

Deliver a feasible menu, portions, preparation steps at an ordinary cooking-planning level, a unit-consistent shopping list and unresolved label questions. Respect the user’s food preferences and constraints. Keep medical nutrition questions and uncertain allergy safety outside unsupported claims.

## Choose the right action

### Preferences and ingredient constraints are clear.
Build the plan directly around acceptable foods and realistic preparation time.

**Avoid:** Do not add disliked foods or unnecessary diet goals.

### A recipe conflicts with a stated allergen restriction.
Exclude it or find a clearly verified compatible alternative.

**Avoid:** Do not assume that a small amount or an unverified substitution is safe.

### An ingredient label is unknown.
Hold the safety-sensitive choice and use a verified alternative where available.

**Avoid:** Do not certify safety from a recipe title or generic category.

### Portions differ from the recipe yield.
Compute whole batches or a practical scaled quantity and reconcile pantry units.

**Avoid:** Do not round down and leave required portions missing.

### The user has a clinical nutrition requirement.
Use their qualified clinician’s supplied instructions and clarify unresolved treatment questions appropriately.

**Avoid:** Do not invent a therapeutic diet or replace clinical advice.

## Worked example (authored, synthetic)

**Input:** Five portions are needed, each batch yields two, each batch uses three units, and four units are in the pantry.

**Method:** Round up to three batches, then subtract usable stock from nine required units.

**Result:** Buy five units. Exclude the recipe with a stated conflicting allergen; no medical safety certification is implied.

## Edge or recovery example 1 (authored, synthetic)

**Input:** The apparently compatible recipe’s ingredient label is unavailable.

**Method:** Retain the portion calculation but hold the uncertain recipe choice.

**Result:** Choose a verified alternative or obtain the actual label; do not treat missing information as safety.

## Failure diagnosis

### The shopping list is too small for the requested portions.
**Likely cause:** Yield was rounded down.

**Repair:** Recompute batches and ingredient quantities before subtracting pantry stock.

**Recheck:** The plan covers the requested portions.

### A restriction is violated by an overlooked ingredient.
**Likely cause:** Constraints were checked only against the recipe name.

**Repair:** Inspect the actual ingredient list and labels.

**Recheck:** Excluded or uncertain ingredients are not presented as cleared.

### The plan is nutritionally elaborate but impractical.
**Likely cause:** Schedule and equipment were ignored.

**Repair:** Reduce preparation burden while preserving stated constraints.

**Recheck:** The person can execute the plan with available time and tools.

## Preserve for the next turn

Preserve stated preferences and restrictions, recipe versions, observed labels, portions, compatible units, pantry quantities and unresolved clinical or ingredient questions. Resume from verified constraints without inventing dietary goals.

## Practice and mechanical checks

Three authored public exercises cover a routine case, a constraint or ambiguity, and a changed-evidence recovery. Their answers are teaching and regression material, not hidden benchmarks. The checker tests supplied structured records only; a person must still assess usefulness, source fidelity and actual visual or interpersonal quality.

Practice case IDs: `meal-plan-r4-standard`, `meal-plan-r4-edge`, `meal-plan-r4-recovery`.
Packaged exercises live under `practice/`. The optional `practice/check_outputs.py` checks supplied JSON outputs; it does not call Muse or certify semantic/visual quality.

## Evidence boundary

Original task procedures and input-derived public exercise checks. No real Muse comparison, independent semantic superiority, clinical effectiveness or consumer adoption has been established.

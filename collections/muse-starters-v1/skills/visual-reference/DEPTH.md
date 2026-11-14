# Translate References Into Reusable Visual Rules — operational depth

Read only the branch needed for the current task. These are working methods, not a demand for additional approvals on ordinary reading or drafting.

## Domain method

Translate observed visual references into explicit constraints: hierarchy, spacing, shape language, type roles, palette roles, material treatment and composition. Separate measured or visible properties from guesses about fonts, dimensions or hidden components. A reference you cannot actually inspect is an unverified source, not permission to invent its appearance.

Build a coherent design rule set rather than collaging incompatible styles. Identify what must stay invariant and what can vary across screens, frames or assets. Preserve usage and redistribution boundaries separately from the ability to view an image. Visual resemblance alone does not establish rights or accessibility.

## Output contract

Deliver a reference-to-rule table, prioritized visual invariants, permitted variation, conflicts between references and an artifact review checklist. When actual files are generated, inspect the render against these rules; a prompt or token list is not visual verification.

## Choose the right action

### The reference is available and clearly observed.
Extract a few high-value rules with the reference location that supports each.

**Avoid:** Do not invent exact font names or color values from an inaccessible source.

### Several references conflict.
Choose which reference governs each role and resolve the conflict explicitly.

**Avoid:** Do not combine every attractive detail into an incoherent result.

### The image is named but not provided.
Use known constraints and mark the missing reference-dependent decisions unverified.

**Avoid:** Do not claim to reproduce an image you have not seen.

### The design must adapt to another format.
Preserve identity and hierarchy while changing layout to fit the new aspect ratio or device.

**Avoid:** Do not distort the subject or shrink essential content solely to force a fit.

### The user wants to redistribute source assets.
Check the specific asset’s rights and consent separately from the design analysis.

**Avoid:** Do not treat public visibility or an inspiration link as a redistribution license.

## Worked example (authored, synthetic)

**Input:** Reference one is visible and supports generous spacing; reference two is unavailable but supposedly supplies a typeface.

**Method:** Separate observed rules from missing-source claims.

**Result:** Spacing rule supported; typeface choice unverified. Produce a provisional layout without claiming faithful typography.

## Edge or recovery example 1 (authored, synthetic)

**Input:** Reference two becomes available but its narrow type conflicts with the readability requirement.

**Method:** Keep the requirement authoritative and adapt the role rather than copying literally.

**Result:** Use the reference’s hierarchy and rhythm with a readable type treatment; document the deliberate deviation.

## Failure diagnosis

### The output looks like several unrelated brands.
**Likely cause:** Rules were copied without a hierarchy.

**Repair:** Assign a governing source to each visual role and remove incompatible choices.

**Recheck:** The rendered result has a consistent visual logic.

### The assistant claims an exact match without inspecting the render.
**Likely cause:** Prompt compliance was mistaken for visual evidence.

**Repair:** Open the actual output and compare concrete constraints.

**Recheck:** The verification names observed differences and remaining limits.

### A missing reference is filled with plausible details.
**Likely cause:** Availability was not checked.

**Repair:** Mark those properties unknown and ask only for the missing asset when essential.

**Recheck:** No invented source property is presented as observed.

## Preserve for the next turn

Preserve the exact reference files or links, observed properties, rights status, governing role assignments, visual invariants and last rendered evidence. Do not substitute a new reference silently or claim an unobserved image match.

## Practice and mechanical checks

Three authored public exercises cover a routine case, a constraint or ambiguity, and a changed-evidence recovery. Their answers are teaching and regression material, not hidden benchmarks. The checker tests supplied structured records only; a person must still assess usefulness, source fidelity and actual visual or interpersonal quality.

Practice case IDs: `visual-reference-r4-standard`, `visual-reference-r4-edge`, `visual-reference-r4-recovery`.
Packaged exercises live under `practice/`. The optional `practice/check_outputs.py` checks supplied JSON outputs; it does not call Muse or certify semantic/visual quality.

## Evidence boundary

Original task procedures and input-derived public exercise checks. No real Muse comparison, independent semantic superiority, clinical effectiveness or consumer adoption has been established.

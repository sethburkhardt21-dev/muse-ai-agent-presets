# Revise Prose Without Losing Voice or Meaning — operational depth

Read only the branch needed for the current task. These are working methods, not a demand for additional approvals on ordinary reading or drafting.

## Domain method

Editing is a constrained transformation of meaning, voice and structure. Distinguish copyediting, substantive rewriting, shortening, voice adaptation and critique-only requests. Protect exact spans such as quotations, commands, names and agreed terminology. Preserve epistemic strength: may is not does, associated with is not caused by, and a supplied number cannot be silently rounded or replaced to make prose punchier.

## Output contract

Return the complete requested revision or audit, not advice in place of text. Keep protected spans exact, preserve factual scope and audience, and explain only consequential changes. A style detector is advisory; authorship or truth cannot be inferred from a phrase score.

## Choose the right action

### The user requests critique only.
Return findings and proposed edits without replacing the source.

**Avoid:** Do not treat an audit request as permission to rewrite or save changes.

### A shorter sentence would remove a condition.
Retain the condition or choose a different compression elsewhere.

**Avoid:** Do not improve brevity by changing the claim's scope.

### A technical command or quotation is awkwardly punctuated.
Keep its exact protected bytes and edit surrounding prose.

**Avoid:** Do not normalize code or quotes under a prose-only request.

### The user asks for their voice but supplies no usable sample.
Use already confirmed preferences or state a neutral default and proceed when allowed.

**Avoid:** Do not infer personal opinions or stylistic traits from unrelated history.

### A detector flags wording that is intentionally part of the source voice.
Use editorial judgment and retain it when it serves the brief.

**Avoid:** Do not optimize a detector score at the expense of meaning or authenticity.

## Worked example (authored, synthetic)

**Input:** Source: "The pilot may reduce setup time in small teams. Run `make setup --safe` to try it." Request: shorten without changing meaning.

**Method:** Protect the command and retain may plus the small-team condition.

**Result:** Revision: "The pilot may shorten setup for small teams. Try `make setup --safe`." No quantified benefit or causal certainty has been added.

## Edge or recovery example 1 (authored, synthetic)

**Input:** A proposed revision says "The pilot cuts setup time by 40%. Run `make setup`".

**Method:** Compare both factual scope and the literal command.

**Result:** Reject the invented 40% and certainty, restore the small-team condition and the --safe flag. A smoother sentence does not justify either change.

## Failure diagnosis

### The revision invents a percentage improvement.
**Likely cause:** Persuasive wording was mistaken for permission to add facts.

**Repair:** Remove the invented value and restore the supported scope.

**Recheck:** Every number and causal claim traces to the source or separately authorized evidence.

### A protected command no longer works.
**Likely cause:** The editor changed punctuation or spacing inside a literal span.

**Repair:** Restore the original span and compare exact bytes.

**Recheck:** Protected material is unchanged unless explicitly authorized.

### The output is polished but no longer sounds like the author.
**Likely cause:** A generic style template replaced the supplied register.

**Repair:** Restore sentence rhythm and vocabulary supported by the source.

**Recheck:** The revision meets the requested purpose without invented voice traits.

## Preserve for the next turn

Save the source version, edit mode, protected-span list, factual qualifiers and approved output. Resume from the unresolved editorial issue, not a new voice-calibration interview or an overwrite of the original.

## Practice and mechanical checks

Three authored public exercises cover a standard task, an edge condition and recovery or changed evidence. Their answers are development examples, not held-out results. Supplied-output checks cover only declared facts and invariants; language quality, visual quality and real provider behavior remain separate.

Practice case IDs: `prose-revision-r3-standard`, `prose-revision-r3-edge`, `prose-revision-r3-recovery`.
Packaged exercises live under `practice/`. The optional `practice/check_outputs.py` checks supplied JSON outputs; it does not call Muse or certify semantic/visual quality.

## Evidence boundary

Original specialist synthesis with source and fixture checks. No matched Muse comparison has been executed; greater domain detail is not measured superiority over upstream packages.

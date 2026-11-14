# Organize Family Memories With Provenance and Consent — operational depth

Read only the branch needed for the current task. These are working methods, not a demand for additional approvals on ordinary reading or drafting.

## Domain method

Organize family material while preserving originals, provenance, identity uncertainty and consent. Distinguish byte-identical duplicates from different edits, scans or photographs of the same event. A matching hash can support duplicate-byte grouping but does not identify the people or establish ownership.

Record names and dates as supplied or evidenced, with uncertainty where needed. Do not infer sensitive relationships or identify people solely from resemblance. Public sharing requires attention to the item’s rights and the consent of relevant people; a private archive and a public album are different audiences. Keep access and redaction decisions reversible where possible.

## Output contract

Deliver an archive index, original-to-derivative links, duplicate groups, uncertain captions and an audience-specific sharing queue. Keep originals untouched by default. Preserve the source of each name, date or relationship claim and do not present guesses as settled family history.

## Choose the right action

### Two files have identical bytes.
Group them as byte duplicates while preserving original locations and metadata.

**Avoid:** Do not delete originals or assume the files have identical historical context.

### Two images look similar but differ in bytes.
Treat them as related candidates and inspect metadata or content as appropriate.

**Avoid:** Do not merge different crops, annotations or moments automatically.

### A person or date is uncertain.
Record the uncertainty and the source of any proposed identification.

**Avoid:** Do not identify a real person from facial resemblance alone.

### The user requests public sharing.
Check item-level rights and the intended consent scope for relevant people.

**Avoid:** Do not treat possession of a photo as permission for every audience.

### A caption or relationship is corrected.
Preserve the correction and its basis, updating affected derivatives.

**Avoid:** Do not erase the original attribution history or propagate an unsupported old caption.

## Worked example (authored, synthetic)

**Input:** Files A and B have the same digest, but only A has explicit public permission; C is separately authorized.

**Method:** Group identical bytes without transferring consent between records.

**Result:** A and B form a duplicate-byte group. Public eligibility is evaluated per item; B remains private or unresolved. No original is deleted.

## Edge or recovery example 1 (authored, synthetic)

**Input:** A newly documented person in C has not granted the required public-sharing consent.

**Method:** Update C’s consent evaluation without changing its private archival value.

**Result:** Hold C from public sharing until the intended scope is resolved; keep the original safely indexed.

## Failure diagnosis

### A cleanup loses the only original scan.
**Likely cause:** Visual similarity was treated as disposable duplication.

**Repair:** Restore from the preserved original and separate duplicate review from deletion.

**Recheck:** No original is removed without explicit informed authorization.

### A tentative identity becomes a permanent caption.
**Likely cause:** Uncertainty was dropped during formatting.

**Repair:** Restore the qualifier and source of the identification.

**Recheck:** The archive distinguishes confirmed and tentative metadata.

### A private image appears in a public album.
**Likely cause:** Audience and consent were not checked per item.

**Repair:** Stop further sharing and use the original provider to address the specific exposure.

**Recheck:** The sharing queue admits only the intended authorized items.

## Preserve for the next turn

Preserve original locations and hashes, derivatives, supplied identity and date evidence, uncertainty, rights and audience-specific consent. Resume from corrected metadata without deleting originals or broadening sharing silently.

## Practice and mechanical checks

Three authored public exercises cover a routine case, a constraint or ambiguity, and a changed-evidence recovery. Their answers are teaching and regression material, not hidden benchmarks. The checker tests supplied structured records only; a person must still assess usefulness, source fidelity and actual visual or interpersonal quality.

Practice case IDs: `family-archive-r4-standard`, `family-archive-r4-edge`, `family-archive-r4-recovery`.
Packaged exercises live under `practice/`. The optional `practice/check_outputs.py` checks supplied JSON outputs; it does not call Muse or certify semantic/visual quality.

## Evidence boundary

Original task procedures and input-derived public exercise checks. No real Muse comparison, independent semantic superiority, clinical effectiveness or consumer adoption has been established.

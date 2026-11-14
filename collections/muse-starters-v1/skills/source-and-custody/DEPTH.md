# Keep Sources and Changes Traceable — operational depth

Read only the branch needed for the current task. These are working methods, not a demand for additional approvals on ordinary reading or drafting.

## Domain method

Keep an evidence object distinct from claims about its origin. A cryptographic digest can establish equality with a pinned byte sequence; it does not establish authorship, truth, permission or independent review. Bind each observation to a source locator, retrieved revision, observation date and allowed reuse.

Preserve original inputs separately from normalized, redacted or transformed derivatives. Record the transformation and its input/output digests where byte-level custody matters. For ordinary personal notes, use proportionate records rather than unnecessary forensic overhead. Disagreement between two sources belongs in the evidence ledger; it must not disappear during tidying.

## Output contract

Deliver the usable source set with a compact provenance table, transformation links and a quarantine list for missing rights, hash mismatches or unresolved identity. Do not delete originals or replace source text with a paraphrase disguised as a quote. State whether authenticity was checked or only byte identity.

## Choose the right action

### The bytes match a known digest.
Record the exact match and continue within the permitted reuse scope.

**Avoid:** Do not label the author, claim or provider authenticated by the hash alone.

### The observed bytes differ from the pinned revision.
Preserve both versions, quarantine dependent conclusions, and identify the changed material.

**Avoid:** Do not overwrite the expected digest to make validation pass.

### A source can be read but redistribution rights are unclear.
Use bounded research notes and a source pointer; hold copied material from distributable packs.

**Avoid:** Do not treat a public URL as blanket redistribution permission.

### A cleaned derivative is requested.
Keep the original untouched and record which normalization or redaction produced the derivative.

**Avoid:** Do not mix a transformed file with the original provenance record.

### The same item has conflicting authoritative-looking versions.
Maintain both source identities and scope the conflict; seek the governing version for the actual task.

**Avoid:** Do not silently select the newest-looking filename.

## Worked example (authored, synthetic)

**Input:** One artifact matches its pinned digest; a second differs although both have readable content.

**Method:** Verify identity separately for each item and preserve both originals.

**Result:** Use the first within its allowed scope. Quarantine the second for revision reconciliation; do not claim either author was authenticated by the digest.

## Edge or recovery example 1 (authored, synthetic)

**Input:** The original provider later supplies the exact intended second revision and its permitted use.

**Method:** Compare the replacement to the independently recorded expected revision rather than relabeling the earlier mismatch.

**Result:** Admit the verified replacement; retain the mismatch record and update only dependent outputs.

## Failure diagnosis

### A citation points to a different version.
**Likely cause:** The source changed between extraction and delivery.

**Repair:** Reopen the pinned revision and recheck the supported passage.

**Recheck:** The citation and evidence bytes refer to the same version.

### A transformed file is mistaken for an original.
**Likely cause:** Derivative lineage was omitted.

**Repair:** Record the original locator and transformation chain.

**Recheck:** The reader can distinguish source from edited output.

### A checksum is presented as a trust certificate.
**Likely cause:** Integrity and authenticity were conflated.

**Repair:** Limit the claim to byte equality and identify any separate origin check.

**Recheck:** The report does not infer identity or truth from a hash.

## Preserve for the next turn

Preserve original source locators and revisions, raw and derivative hashes, rights decisions, unresolved conflicts and the next evidence check. Never place access tokens, private recipient data or copied confidential context into the reusable skill.

## Practice and mechanical checks

Three authored public exercises cover a routine case, a constraint or ambiguity, and a changed-evidence recovery. Their answers are teaching and regression material, not hidden benchmarks. The checker tests supplied structured records only; a person must still assess usefulness, source fidelity and actual visual or interpersonal quality.

Practice case IDs: `source-and-custody-r4-standard`, `source-and-custody-r4-edge`, `source-and-custody-r4-recovery`.
Packaged exercises live under `practice/`. The optional `practice/check_outputs.py` checks supplied JSON outputs; it does not call Muse or certify semantic/visual quality.

## Evidence boundary

Original task procedures and input-derived public exercise checks. No real Muse comparison, independent semantic superiority, clinical effectiveness or consumer adoption has been established.

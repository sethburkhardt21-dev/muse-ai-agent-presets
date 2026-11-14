# Reconcile Versioned Events Without Resurrection — operational depth

Read only the branch needed for the current task. These are working methods, not a demand for additional approvals on ordinary reading or drafting.

## Domain method

Treat source version as business order and deletion as a durable versioned fact. Group all state and batch records by key/version before changing the candidate state. Equal-version unequal payloads hold the entire batch; identical repeats contribute no extra row. A higher-version tombstone prevents a later-arriving lower version from resurrecting data. Report order-independent batch counts, and distinguish a pure in-memory reconciliation from transactional writes and checkpoint persistence.

## Output contract

Return a newly calculated state, applied keys, stale-event count, duplicate-event count and any conflicting keys. Conflict returns the original state without partial application. Preserve source and batch digests, version semantics and deletion retention requirements for a real pipeline owner. External writes remain false.

## Choose the right action

### A late update is older than a retained deletion marker.
Keep the higher-version tombstone and classify the update as stale.

**Avoid:** Do not resurrect the deleted row because the event arrived later.

### An identical source event appears again.
Count the repeat as duplicate and preserve the same output state.

**Avoid:** Do not treat the replay as a fresh business event.

### The same key and source version carry different payloads.
Return a conflict with the original state and preserve all contradictory evidence.

**Avoid:** Do not choose last-arrival-wins or silently increment the source version.

### A batch contains valid changes plus one conflict.
Hold the complete batch under the declared atomic policy.

**Avoid:** Do not partially commit unrelated keys while reporting a single successful batch.

### The pipeline proposes pruning deletion markers.
Require the original retention and replay horizon contract before removal.

**Avoid:** Do not use this local reconciliation as proof that original production retention is solved.

## Worked example (authored, synthetic)

**Input:** State contains A version 3 deleted; incoming A version 2 value 10 and a repeat of the tombstone.

**Method:** Group by key/version, preserve version 3 and count stale and duplicate input independently.

**Result:** A remains deleted at version 3; one stale event and one duplicate are reported, with no external writes.

## Edge or recovery example 1 (authored, synthetic)

**Input:** State has A version 1; a batch carries A version 2 with values 20 and 21 plus a valid B update.

**Method:** Detect the contradiction before selecting either value or applying B.

**Result:** The whole batch is held as conflict and the original state is returned unchanged.

## Failure diagnosis

### A deleted item reappears after an import.
**Likely cause:** Arrival order replaced source-version order or a tombstone was discarded.

**Repair:** Restore the last trusted versioned state and replay the bounded batch in a disposable copy.

**Recheck:** Permutations of the batch retain the same tombstone and final state.

### Duplicate deliveries increase record count.
**Likely cause:** The pipeline identified events by delivery attempt instead of source key/version/payload.

**Repair:** Apply source identity deduplication and compare exact repeats separately from conflicts.

**Recheck:** Replaying an identical batch does not introduce new keys or versions.

### A conflict is hidden by a successful aggregate count.
**Likely cause:** The implementation validated only totals after selecting arbitrary winners.

**Repair:** Compare payload identity at each equal key/version before producing output.

**Recheck:** A contradictory same-version pair returns conflict and unchanged prior state.

## Preserve for the next turn

Preserve the exact supplied input and tool version, the returned report, any unresolved source assumptions and the next authorized check. Return a newly calculated state, applied keys, stale-event count, duplicate-event count and any conflicting keys. Conflict returns the original state without partial application. Preserve source and batch digests, version semantics and deletion retention requirements for a real pipeline owner. External writes remain false.

## Practice and mechanical checks

Three authored public exercises cover a standard input, an edge condition and changed evidence or recovery. Expected outputs are development examples, not hidden model evaluations.

Practice case IDs: `incremental-pipeline-r5-standard`, `incremental-pipeline-r5-edge`, `incremental-pipeline-r5-recovery`.
Packaged exercises live under `practice/`. The optional `practice/check_outputs.py` checks supplied JSON outputs; it does not call Muse or certify semantic/visual quality.

## Evidence boundary

Original first-party source and supplied-input calculations. No native Muse performance or superiority claim follows from the source examples.

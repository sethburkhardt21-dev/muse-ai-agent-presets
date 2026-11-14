# Design an API Around Consumer Behavior — operational depth

Read only the branch needed for the current task. These are working methods, not a demand for additional approvals on ordinary reading or drafting.

## Domain method

An API contract includes observable request, response, error, authorization, pagination and retry behavior, not only a JSON schema. Evaluate compatibility from the actual consumer's perspective: optional response fields can still break a strict decoder, and enum expansion can break exhaustive clients. Treat idempotency as a scoped relationship among a principal, operation key and canonical request, with explicit retention and conflict semantics.

## Output contract

Deliver an endpoint or operation contract with examples, required and optional fields, errors, permission boundary, retry policy, versioning impact and consumer tests. Mark proposed semantics as proposed. Do not claim a deployed service, generated SDK or authenticated caller from a schema alone.

## Choose the right action

### A response adds an optional field.
Check whether known consumers ignore unknown fields; classify compatibility as conditional until tested.

**Avoid:** Do not assume additive always means nonbreaking.

### A retry repeats an idempotency key with different payload.
Return the specified conflict outcome without applying the second effect.

**Avoid:** Do not silently treat the key as permission to overwrite the first request.

### A timed-out write has an unknown outcome.
Reconcile the original operation key through the supported status or readback route.

**Avoid:** Do not issue a new key and risk duplicate creation.

### Pagination crosses changing data.
Specify cursor stability, ordering and duplicate/missing-record semantics.

**Avoid:** Do not promise a consistent snapshot from an offset-only live list.

### No service or client can be executed in this session.
Deliver the complete proposed contract and executable fixture examples where possible, marking runtime checks not run.

**Avoid:** Do not simulate a remote success and label it integration proof.

## Worked example (authored, synthetic)

**Input:** A create operation has key K1 and canonical payload P1. The first request created resource R1. A retry uses K1/P1; another uses K1/P2.

**Method:** Apply the stated idempotency contract within the same principal and operation scope.

**Result:** K1/P1 returns the original R1 with no new creation. K1/P2 returns a conflict and also creates nothing. Neither retry receives a new resource ID.

## Edge or recovery example 1 (authored, synthetic)

**Input:** An optional field is added to a response consumed by a strict decoder that rejects unknown properties.

**Method:** Treat the consumer behavior as part of the compatibility surface.

**Result:** The addition is breaking for this consumer until the decoder is updated or a compatible representation/version is provided; it is not automatically safe because the field is optional.

## Failure diagnosis

### The server and generated client disagree on a required field.
**Likely cause:** Schema and implementation evolved independently.

**Repair:** Compare the exact versions and restore a shared contract plus a consumer regression.

**Recheck:** Both sides accept and reject the same representative payloads.

### A retry creates two resources.
**Likely cause:** Operation identity was not retained across retries.

**Repair:** Bind the retry to the original scoped key and document retention behavior.

**Recheck:** Same key/same canonical request returns the original result without another effect.

### An enum addition breaks an existing client.
**Likely cause:** Exhaustive decoding was ignored in compatibility review.

**Repair:** Add an unknown-value handling path or a versioned migration.

**Recheck:** The old consumer contract is exercised, not just the new schema.

## Preserve for the next turn

Carry the schema version, consumer assumptions, examples, scoped idempotency identity, retention policy, compatibility findings and executed test commands. Resume unresolved consumer or runtime checks without inventing deployment.

## Practice and mechanical checks

Three authored public exercises cover a standard task, an edge condition and recovery or changed evidence. Their answers are development examples, not held-out results. Supplied-output checks cover only declared facts and invariants; language quality, visual quality and real provider behavior remain separate.

Practice case IDs: `api-contract-r3-standard`, `api-contract-r3-edge`, `api-contract-r3-recovery`.
Packaged exercises live under `practice/`. The optional `practice/check_outputs.py` checks supplied JSON outputs; it does not call Muse or certify semantic/visual quality.

## Evidence boundary

Original specialist synthesis with source and fixture checks. No matched Muse comparison has been executed; greater domain detail is not measured superiority over upstream packages.

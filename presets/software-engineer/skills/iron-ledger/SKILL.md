---
name: engineering-evidence-receipt-consumer
description: Read-only existing Evidence Finder receipts, TaskGuard recovery and local actor/recipient observations.
version: 0.3.0
scope: software-engineer
authority: local-source-only; native-muse-not-registered; no-external-effects
---

# Iron Ledger — read-only Evidence Finder consumer

This is a narrowly translated neutral consumer interface, not the
original full Iron Ledger receipt logger, TaskGuard, persistent registry,
provenance journal, operator controller or host native wiring.

## Preconditions

- Obtain an already-opened, owner-scoped Evidence Finder EvidenceLedger
  from the actual host. The source-only reference uses an injected authority
  callback for scope shape; it does not authenticate host-issued user IDs.
- Specify only the exact operation IDs to read (1–32). Do not enumerate
  another owner's records, inspect private source text or write sidecars.
- Confirm the existing ledger owner/workspace/role/actor at the actual host
  boundary. These Python source checks alone cannot verify the issuer.

## Operations

1. build_local_receipt_index(ledger, operation_ids) verifies the actual
   existing hash-linked chain, reopens each explicitly named operation,
   and rechecks the chain head. It emits only operation/sequence/digest
   metadata and FOUND/NOT_FOUND—not the source observation, source path,
   query, personal memory or raw finding text.
2. verify_local_receipt_index(ledger, index) reopens original operations
   and refuses if the head, scope, source digest, record bytes or index
   digest changed. There is NO allow_stale override.
3. Keep the resulting index in an owned ephemeral task context. It is
   a local self-hash, not a signed attestation or durable receipt ledger.
4. Pass independently verified local evidence to existing Claim Gate for
   a separately authorized claim or task. Iron Ledger never grants
   release, deployment, model execution or external provider effects.

## TaskGuard recovery — read-only (not original TaskGuard)

5. Use `task_run_claim_id(task_id,run_id)` for deterministic, bounded
   task/run identity in the **existing** Claim Gate namespace. This merely
   maps an identity; it never creates a claim.
6. Pass an already-opened `ClaimGate` instance to
   `review_local_task_run(gate,scope="software-engineer",
   task_id="task-A",run_id="run-1",expected_payload_sha256=digest)`.
   The adapter calls only `reconcile_unknown` and examines existing
   records. Missing history, corrupt marker, UNKNOWN, CLAIMED, unexpected
   state, mismatched run or payload are all HELD. A local EFFECT_DONE
   record is NOT recipient confirmation and does not authorize release.
7. For up to 32 explicit run identities use `review_local_task_runs`.
   Every result always sets safe_to_claim/resume/retry/release to false,
   and never writes a claim, starts a model, or deletes/rewrites a marker.
   A human/authorized host must reconcile the actual original outcome
   at its true recipient and enforce fencing separately.

## Actor and recipient observation — (source-only)

8. Bind one exact owner/actor/session, task/run, scope, recipient and
   payload SHA-256. Inject three independently scoped *readers*: an
   existing ClaimGate with `reconcile_unknown(scope, claim_id)`,
   an actor reader with `inspect_actor(scope, owner_id, actor_id, session_id)`
   and a recipient reader with `inspect_receipt(recipient_id, claim_id)`.
   Use `review_local_task_observations(...)` to compare their local
   assertions and re-open the claim after external reads.
9. The host assertion must have schema
   `software-engineer/local-actor-observation-v1`, status
   `CALLER_SUPPLIED_ASSERTION`, matching exact IDs, and false
   `host_authenticated`/`effect_authorized`. The recipient assertion
   must have schema `software-engineer/local-recipient-observation-v1`,
   matching recipient/claim/payload and a bounded reported outcome
   SUCCESS, FAILED, UNKNOWN or NOT_FOUND with false authentication
   flags. This contract **rejects forged claims of real authentication**
   rather than granting authority from booleans in local JSON.
10. If exact bindings and an unchanged local terminal claim agree with
    the reported outcome, the status is
    `LOCAL_CONSISTENT_UNAUTHENTICATED_HELD`. This does **not** verify
    the real target: both reader implementations may be synthetic or
    caller-controlled. UNKNOWN, mismatched effects, absent receipts,
    invalid session, stale/changed claims and unreadable readers are
    always held. All safe-to-claim/retry/resume/release fields stay false.
11. Real principal verification and recipient receipt integrity require
    actual host-issued credentials and separately authenticated native
    recipient APIs, which this portable source module does not possess.
    Never substitute a self-hash, mock response or another local JSON
    field for that external trust boundary. Do not execute any effect.

The private original Iron Ledger TaskGuard code has known unsafe
release/reclaim semantics on malformed claims. This is deliberately
**not a copy** of that writer; the one existing Claim Gate owns state.
These purely local observations do not prove independently authenticated
host/owner authority or successful external effects.

## Refusal and recovery

Missing original operation, wrong owner/actor scope, corrupt receipt chain,
ambiguous reader response, duplicate IDs, stale head and forged authority
must refuse. Unknown/partial external effects remain held for real recipient
reconciliation; do not create a fresh claim or blindly retry.

This opt-in skill has NO scheduler, subchat, Family Link or native Muse
registration. Its skill instructions and runtime module are SHA-pinned
with rights_verified=false. Do not transplant the original agent's private
receipt chain, identity or worker state.

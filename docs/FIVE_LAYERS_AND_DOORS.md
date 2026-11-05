# Five layers, five execution doors, and effect gates

These three sets of five are **not synonyms**. They answer different questions and must be graded separately for every role/capability.

## Capability maturity (the owner's five layers)

| Layer | Required evidence | Example result |
| --- | --- | --- |
| **EXISTS** | Source/manifest and exact content identity | A skill and runner have immutable source paths |
| **CORRECT** | Relevant unit, contract, adversarial and regression tests | Wrong owner, stale token and corrupted state refuse |
| **WIRED** | Actual supported host registration, callable path and source-version readback | Muse discovers the correct skill, hook or Space action |
| **USED** | Host-originated invocation, effect/receipt, consuming recipient | An original specialist performs the intended bounded action |
| **USEFUL** | Independent review of a real outcome and recovery after interruption | User receives a correct result and tests an adverse case |

Never upgrade one layer from a file path, copied receipt, simulation, mocked sender or historical milestone. Record `PASS`, `FAIL`, `UNKNOWN` or `NOT_APPLICABLE` per layer and host version.

## The S1–S5 execution doors: what is enforced and where

1. **S1 — Source/candidate identity:** pin exact source, task, inputs, paths, scope and version at intake. Before each consequential effect, refresh relevant identity.
2. **S2 — Admission/permission:** enforce actual owner identity, role, authorized tool, budget, current lease/fence and supported host grant. Default refuse on missing authority.
3. **S3 — Original capability invocation:** route through the real callable skill/connector/Space/host tool—not a synthetic stand-in. Record the host-issued invocation ID.
4. **S4 — Regression, recovery and anti-replay:** run affected tests and negative controls, preserve incomplete results, reconcile `UNKNOWN_EFFECT` under the same identity, and never blindly resend.
5. **S5 — Durable outcome/witness:** read back original recipient/consumer state, preserve evidence and obtain independent acceptance where required.

**Every effect-capable entrypoint needs action-time enforcement:** CLI, worker, browser, connector, filesystem, scheduling, remote desktop and release/publish. An advisory checker off to the side is not a universal door. Auditors must test bypass paths, not merely the intended happy path.

## The separate L1–L5 external/provider chain

- **L1:** authentic host-issued actor/task/lease/intent.
- **L2:** authenticated actual transport effect.
- **L3:** the correct original lane/executor performed it.
- **L4:** same-recipient durable GET/readback and correct correlation.
- **L5:** independent native witness and originating controller reconciliation.

No local or owner-supplied JSON label can supply L1 or L3. No local S5 can substitute for L5.

## Initial public-shell status

EXISTS and CORRECT can be measured **only for the renderer, catalog and proposal parser**. WIRED, USED, USEFUL and provider L1–L5 are **NOT_RUN**. `family-preview` emits `PROPOSAL_ONLY_NOT_SENT` without attempting transport. No native registration, approval, effect or recovery is claimed.

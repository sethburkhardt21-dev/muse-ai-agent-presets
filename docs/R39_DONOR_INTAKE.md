# R39 - Owner-authorized generic donor intake and integration map

**Source baseline:** `07ce1c90d704733ed6445875c14c5e32b1938e56`; the exact per-file SHA-256 records live in `control/r39/ROLE_DONOR_MATRIX.json`.

## Scope decision

The original Muse/Atlas implementations in scope are **first-party owner work**, and the owner explicitly authorizes reuse, neutralization and planned redistribution as generic drop-in agents. Record this as **OWNER_ATTESTED_FIRST_PARTY_AUTHORIZED**. Do not block engineering while seeking repetitive first-party licensing approvals. Do not misinterpret historical `public_release_approved=false` as a third-party copyright claim.

Keep personal identities, memories, contact data, machine/host IDs, auth/session tokens and unrelated private owner state outside the generic source distribution. Actual **third-party** software or media, if later introduced, must meet its own license terms. Preserve the private repository's prior history as evidence but publish selected neutral files through a separately audited clean public release; never wholesale-push historical private commits.

## Source-backed role inventory

| Role | Source maturity | Callable components already present | Native approval |
|---|---|---|---|
| `coordinator` | LOCAL_ENGINE_TESTED | coordinator_dropin, coordinator_review | D1-D4 provider proof NOT_RUN |
| `software-engineer` | LOCAL_ENGINE_TESTED | engineer_dropin, engineering_pack, provenance_vault, iron_ledger_consumer | D1-D4 provider proof NOT_RUN |
| `model-builder` | PLAYBOOK_ONLY | role manifest/playbook | D1-D4 provider proof NOT_RUN |
| `research-evaluator` | PLAYBOOK_ONLY | role manifest/playbook | D1-D4 provider proof NOT_RUN |
| `creative-studio` | PLAYBOOK_ONLY | role manifest/playbook | D1-D4 provider proof NOT_RUN |
| `adversarial-verifier` | PLAYBOOK_ONLY | role manifest/playbook | D1-D4 provider proof NOT_RUN |
| `personal-companion` | LOCAL_SLICE | family | D1-D4 provider proof NOT_RUN |
| `garden-companion` | LOCAL_ENGINE_TESTED | garden, garden_calendar | D1-D4 provider proof NOT_RUN |
| `learning-coach` | LOCAL_ENGINE_TESTED | learning, learning_session | D1-D4 provider proof NOT_RUN |
| `claims-adjudicator` | LOCAL_SLICE | claims | D1-D4 provider proof NOT_RUN |
| `reverse-engineering-researcher` | LOCAL_SLICE | reverse | D1-D4 provider proof NOT_RUN |

Evidence Finder is a **shared service, not a twelfth agent**. Its already available `finder` and `evidence_ledger` code provides local source search and SQLite custody; genuine recipient delivery remains separate.

## Execution ordering (no repeated broad discovery)

1. **Immediately reuse** existing source-tested Coordinator and Software Engineer packs with their documented neutral profile/skill/subchat drafts, local engines and disabled host registrations. For each exact source file, verify the corresponding SHA before adaptation; do not rewrite working first-party logic only to make it 'generic'.
2. **Reuse** local Garden Companion, Learning Coach, Claims and Reverse observation functions already pinned here. Add native adapters only as required by each role and its verified provider contract.
3. **Defer** deeper donor import until the exact role needs it. The initial list includes first-party Continuum, Omnium, Inquiry, Appwright/Swiftwright, Family Link, animation, training, security and optional Space/desktop bridges. This is a dependency queue rather than an instruction to scan all VMs or clone all repositories now.
4. **Personal Hatch interface:** inspect authenticated provider-supported skill discovery and host ownership. Do not equate `skills.yaml`, a source package, an agent template or a Space callback with a host-issued model-selected tool event. D1 discover, D2 bind, D3 invoke and D4 recipient/denial gates remain separate.
5. **Public release:** retain zero new spending, no automatic cron/model/connector activation, no forbidden private assets, independent A/B/C tests and honest maturity labels. First-party source ownership is already settled by the owner's instruction; only the content/privacy, external dependencies and applicable native-usefulness checks remain.

## Next concrete packets

**`coordinator`:** Pin/adapt original orchestration/recovery interface without inventing planner authority; verify model selection in disposable host. Acceptance: provider model-selected coordinator skill+host action+recipient readback; no dry-run promotion.

**`software-engineer`:** Reuse qualified original Claim Gate/Vault/Iron and source-pinned local Forge; qualify native skill registration and RED to GREEN on a disposable owner repo. Acceptance: native registered custom skill+source-bound disposable repository red-green command+recipient readback.

**`model-builder`:** Admit owner's train/model adapter through bounded cheap synthetic datasets and resource-controlled worker; prove actual results. Acceptance: owner model-run selection+bounded artifact+independent result.

**`research-evaluator`:** Use existing protected Inquiry via authorized interface; evidence/citation and independent receiver proof, do not modify Inquiry source. Acceptance: source-cited research command with provider-issued tool and recipient receipt.

**`creative-studio`:** Import/adapt original owner animation/media runtime only with source pins and tests; verify output continuity. Acceptance: native media task action, rendered artifact and actual inspection.

**`adversarial-verifier`:** Connect existing authorized defensive sandbox and evidence reports; deny outside-scope operations. Acceptance: authorized sandbox execution, finding artifact, independent fix verification.

**`personal-companion`:** Adapt consent-based user memory, opt-in reminders and private Space patterns; exclude original donor memory. Acceptance: owner consent+host registered reminder or Space/voice action+readback.

**`garden-companion`:** Integrate local garden transaction/owner-scoped SQLite into native callable skill with viewer/recipient proof. Acceptance: owner-scoped garden action with durable calendar result and wrong-owner refusal.

**`learning-coach`:** Integrate source-bound local cards/review/score/reopen through an authenticated receiving owner. Acceptance: owner-scoped quiz/score/reopen and source identity proof.

**`claims-adjudicator`:** Compose claims scope with shared evidence ledger, provenance and correction; separate evidence from verdict. Acceptance: provenance ledger+reviewer gate+preserved correction.

**`reverse-engineering-researcher`:** Compose owned toy UI/trace comparison with approved desktop capture and bounded sandbox. Acceptance: bounded authorized toy observation and evidence-backed report.

The exact private external donor repo/commit lookup is stored in an operator-controlled sidecar **outside this Git checkout**, not embedded in neutral distributable source. A changing upstream SHA triggers a new *technical* source-drift review, not a new first-party redistribution request.

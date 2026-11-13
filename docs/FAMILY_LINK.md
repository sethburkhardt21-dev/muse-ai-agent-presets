# Optional Family Link: bounded cross-specialist handoff

Every one of the 15 source presets declares `family_link` inside `preset.json`, with `enabled: false`, `transport: unbound` and a **suggested receiving-role allowlist**. Rendering the preset writes a local `FAMILY_LINK.json`. The shared Evidence Finder is an optional service, not a family member or native agent.

## The adapter implemented today

`muse_presets.family.propose_handoff` validates sender/receiver IDs, request IDs, capability labels and role-specific allowed recipients. It always returns `PROPOSAL_ONLY_NOT_SENT`, `effect_authorized: false`, `native_receipt: false` and `recipient_acknowledged: false`. It has **no network, filesystem send, signer, identity minting, secret lookup or native listener**.

`verify_finding` validates an immutable-shaped finder result with `source_uri`, 64-character SHA256, `observation` and `FOUND/NOT_FOUND`; it rejects extra verdict fields and fake found-without-observation. This is schema checking only, **not** authentication of a remote source or owner.

## Future authenticated bridge (not yet implemented)

A production integration must bind: source role and live native identity, recipient's authenticated host/account, owner-approved scope, exact task hash and immutable intent, lease/fence, host capacity, approved transport, one-effect identity, recipient readback, no unknown replay and an independent acceptance result. Create separate `family_link/native/` adapters per verified host; prohibit self-issued grants. The source of truth for native sender/receiver ownership remains the receiving host and actual original role.

## Suggested patterns

- Garden Companion → Evidence Finder → Claims Adjudicator for factual planting-source review; never silently edit a calendar.
- Learning Coach → Research Evaluator for question/answer quality and contamination review; no unapproved medical content.
- Model Builder → Research Evaluator for frozen held-out assessment and truthful failures.
- Reverse Engineering Researcher → Adversarial Verifier or Evidence Finder for scoped reproducibility and source provenance.
- Evidence Finder → Claims Adjudicator for exact findings; the finder cannot issue verdicts.

The current shell cannot and does not establish cross-account messaging or Family Link membership.

# Evidence Finder shared service

A neutral, shared service used by the eleven specialist presets. Evidence Finder locates literal source text, preserves whole original findings, and returns an honest null when a literal is absent. It never adjudicates claims, authorizes an external action or sends a message.

**Locally executable public source:** The bounded finder is in src/muse_presets/finder.py. The durable source/receipt reference is in src/muse_presets/evidence_ledger.py, with tests and a synthetic example. It persists exact positive findings and scoped no-hit receipts in SQLite, refuses conflicting operation replays and detects ordinary local tampering. See docs/EVIDENCE_LEDGER.md.

The Software Engineer's R32 candidate adds a read-only source-inventory/local-
seal consumer that accepts the existing EvidenceLedger.verify() chain head.
It does not write to this ledger, establish a separate controller, or turn a
local hash into authenticated externally anchored evidence.

The Software Engineer's R32.2 *local* Iron Ledger consumer accepts an
already-opened EvidenceLedger from the existing service. It derives a
bounded, non-persistent receipt index for explicitly named operations and
re-verifies the scoped chain head before reuse. It does not copy raw source
observations, append receipts, create a second ledger or perform TaskGuard
claims. An injected role resolver remains synthetic unless the actual
host authenticates it; publication of the original-source-guided adapter
is separately held pending rights review.

All roles can reuse the ledger under an explicit host-supplied EvidenceScope, but the public code does **not** authenticate that scope. Existing Family Link verify_finding validates record shape only. There is no real Muse native registration, external transport, signed receipt, independent truth proof, or verdict. Default denied.

# Evidence Finder: local durable evidence custody

Maturity: Source-tested reference implementation. NOT a native Muse skill, authenticated owner service, installed connector, source authenticity certificate, or multi-agent transport.

The public EvidenceLedger extends the existing bounded find_exact_text primitive with local SQLite storage and replay-safe, SHA-256-linked receipts. It uses only the Python standard library and does not import private agent code.

## Quick start

From the repository root:

    PYTHONPATH=src python examples/evidence_ledger_demo.py
    PYTHONPATH=src python -m unittest discover -s tests -p test_evidence_ledger.py -v

The example uses only fictional data and an ephemeral temporary directory. It records a complete exact-text finding and an explicit NOT_FOUND, deletes the source, and reopens the recorded evidence in a separate SQLite connection.

A different specialist role uses the same source API:

    from muse_presets.evidence_ledger import EvidenceLedger, EvidenceScope

    # Fictional callback, NOT a real Muse login or signed grant.
    scope = EvidenceScope('demo-owner', 'demo-workspace',
                          'research-evaluator', 'demo-operator')
    with EvidenceLedger('/absolute/path/to/local.sqlite3',
                        authority=lambda: scope) as evidence:
        saved = evidence.capture('/path/to/owned/source-root', 'note.txt',
                                 'literal phrase', operation_id='unique-op-id')
        restored = evidence.read('unique-op-id')
        proof = evidence.verify()

The host must provide a genuinely authenticated authority callback and source permissions on every call. EvidenceScope is a data shape, not an identity token. Source-only examples do not prove a Muse principal.

## Exact behavior

The existing bounded Finder searches one explicitly supplied UTF-8 file under an allowed root, refusing traversal and symlinks. The ledger stores its exact source digest, query and whole original text for FOUND records. A NOT_FOUND receipt stores the source digest and scope but no full absent-match source text. It preserves the original observed negative result without independently proving the absence after source deletion.

Records are partitioned by owner/workspace/role/actor labels, checked through the host-supplied callback. On each read, verify or capture the complete local chain is validated before returning a result. An identical operation ID and input preserves its first receipt, even if the source later disappears; a changed request under the same operation ID refuses. A changed source under a new operation ID creates a distinct record.

The SQLite chain keeps a separate local head. Truncated history, ordinary row deletion and byte modifications are detected. A local chain is NOT a cryptographic signature, immutable ledger or externally anchored anti-rollback system: someone who can rewrite both rows and head can forge another valid-looking history.

## Deliberate boundaries

- No external messages, signed receipts, court/adjudication, verdict, automatic approval, arbitrary execution or model training.
- No installed Muse skill, profile, hook, scheduler, Space, native session or permissions.
- No implicit file-system crawling or private-source access.
- No source-owner authentication, independent truth verification or live agent execution.
- No original personal records, owner-specific projects, clinical training material or proprietary creative assets.

SQLite retains actual matched document text. Integrators must keep it in the owning user's protected workspace, apply retention and deletion rules and avoid committing real databases to public repositories.

This is one cross-role capability in the [generic specialist showcase](GENERIC_SPECIALIST_SHOWCASE.md). Any native host adapter will require independently proven owner identity, effect admission and recipient readback.

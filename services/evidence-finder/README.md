# Evidence Finder

A shared local service for the eleven specialist kits. Find literal source text, preserve findings and record a scoped no-hit result when the requested text is absent.

The implementation lives in `src/muse_presets/finder.py`. The SQLite ledger in `src/muse_presets/evidence_ledger.py` preserves findings, rejects conflicting operation replays and supports recovery after an original source file is removed.

```bash
PYTHONPATH=src python3 -B examples/evidence_ledger_demo.py
```

Run this from the repository root. The example uses synthetic local inputs and temporary storage. It does not adjudicate claims, contact a provider or send messages.

Other local modules can consume the ledger's verified chain head to inspect source custody and derive a scoped receipt index. Those readers do not create another ledger or mutate the original task controller.

A local hash establishes consistency of bytes, not publisher identity, independent truth, authenticated owner consent or a trustworthy external timestamp.

[Evidence ledger reference](../../docs/EVIDENCE_LEDGER.md) · [Runnable workflows](../../docs/WORKFLOWS.md) · [Security](../../docs/SECURITY.md)

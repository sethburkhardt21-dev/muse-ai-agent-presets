# Evidence Finder — shared, local-first source custody

**One shared service used by all eleven neutral specialist presets.** Evidence
Finder searches a caller-supplied, bounded UTF-8 file, preserves the entire
unchanged text when a literal is found, or reports an explicit NOTHING_FOUND.
It never judges a claim, modifies the source, makes a decision, or
contacts another agent.

## Working source implementation

- src/muse_presets/finder.py: literal bounded search, source SHA-256,
  scoped file paths, symlink/traversal refusal.
- src/muse_presets/evidence_custody.py: explicit opt-in SQLite receipt
  recording with exact found-source text, reopen after the original source
  disappears, honest no-hit scope, idempotent operation IDs, role-labelled
  namespaces and a locally checked hash chain.
- tests/test_evidence_custody.py: recover/replay/tamper/concurrency and
  negative controls.
- examples/evidence_custody_demo.py: safe synthetic demonstration.

From the repository root:

    PYTHONPATH=src python examples/evidence_custody_demo.py
    PYTHONPATH=src python -m unittest discover -s tests -v

### Trust boundary

This is **not** a native Muse listener, signed provenance vault, network
crawler, independent fact-checker or authenticated owner service. Role IDs
are local labels and do not grant access. The supplied storage root must be a
user-controlled local directory. Local SHA-256 chains detect ordinary edits
but **do not prevent a writer with complete storage access from rewriting
an entire history**; no independent external anchor exists. The caller
is responsible for rights, retention and private data handling.

The shared service is separate from Claims Adjudicator, which may evaluate
evidence only under its own qualified authority. Family Link is disabled
and unbound by default. No private donor tree, personal record, host path,
model weights or credentials are packaged here.

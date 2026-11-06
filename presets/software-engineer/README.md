# Software Engineer — runnable generic specialist

A neutral, configurable Muse-oriented engineering specialist with real offline execution-safety modules, reproducible tests and a source-controlled role playbook.

## Implemented today

The runtime/claim-gate directory contains nine Python source files: the original-source-neutralized atomic Claim Gate and its retention, lease, fencing, approval, composite and restart dependencies, plus a source-bounded CLI. The skills/claim-gate directory contains neutral skill metadata and a runbook.

Stage a brand-new local pack:

    PYTHONPATH=src python -m muse_presets.engineering_pack --to ./my-software-engineer

Run the synthetic example on POSIX:

    PYTHONPATH=src python examples/software_engineer_claim_gate_demo.py

The original locking uses POSIX fcntl, so execution on native Windows is not supported. Staging is source-only; this does not register a native Muse skill, grant any host permission or execute an external effect.

## Still remaining for the full specialist

The original agent has additional engineering, source-provenance, evidence-ledger, collaboration, recovery and host-effect skills to qualify and neutralize. This release is the first functional vertical slice, not the entire original agent. Never install or merge this pack over an existing owner's memories or active services.

See INSTALL.md, playbook.json, and the shared Evidence Finder documentation in docs/EVIDENCE_LEDGER.md.

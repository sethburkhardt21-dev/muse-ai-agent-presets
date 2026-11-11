# Claims Adjudicator — runnable offline source kit

A self-contained source ZIP wraps the existing first-party Claims Adjudicator scope checker, preserving its conservative evidence grades and every limiting condition. It runs actual local Python logic, but **does not authenticate the supplied evidence**, deliver an external opinion, modify accounts, install native Muse skills, or judge factual truth.

The downloadable kit is separate from the smaller generic Claims Adjudicator starter. It includes two executable Python source files, a disabled role profile, editable playbook, a fictional input, installation directions, license and byte-integrity manifest.

## Build, verify and run

Requirements: Python 3.12+ and a trusted copy of this repository. No paid API, network or pip packages. From the repository root:

    PYTHONPATH=src python3 -B examples/export_claims_sourcekit.py --to /absolute/NEW/claims-adjudicator.zip
    PYTHONPATH=src python3 -B examples/export_claims_sourcekit.py --verify /absolute/NEW/claims-adjudicator.zip --sha256 EXTERNALLY_VERIFIED_SHA256

On Windows PowerShell, set $env:PYTHONPATH = "src" and use python.

The exporter refuses an occupied ZIP destination and mismatched original first-party source bytes. It creates a repeatable archive with a deterministic file list and ZIP metadata. An embedded SHA-256 receipt does **not** certify its publisher or independent reviewer.

After confirming the ZIP digest through a separately trusted release/source record, extract it into a new directory. Run:

    python -I -B claims-adjudicator/run.py --operation demo

Expected: LOCAL_CLAIMS_DEMO_PASSED with disposition OVERCLAIM, no native installation, and no authorized external effect. To assess an explicitly reviewed fictional or user-supplied JSON claim, pipe EXAMPLE_CLAIM.json into:

    python -I -B claims-adjudicator/run.py --operation assess --allow-reviewed-local

Missing opt-in, malformed/duplicate-key JSON, nonfinite values, invalid grades and altered source bytes are refused. The runner accepts at most 16 KiB of stdin and does not use an external provider. The imported code runs under the local account. Python isolation switches are **not an OS sandbox**.

## Operational boundary

The result distinguishes asserted evidence grades from caller-declared evidence grades. It does not search for evidence, prove truth, perform an independent examination, authenticate identities, issue grants, or publish conclusions. No native account, connected model, external effect, Family Link or scheduling is bundled. For these capabilities use their separately authorized original providers.

The verifier admits the complete member list, regular-file paths, exact expected sizes, compression method, header flags and total unpacked budget before opening any member body. Stored and DEFLATE members are supported; encryption and unsupported ZIP features are refused. Corrupt ZIP containers or compressed data produce a bounded `REFUSED` response and exit code 2, not a successful verification. The external archive digest and canonical source-byte comparisons remain required.

Run both the source-kit and archive-boundary regressions:

    PYTHONPATH=src python3 -B -m unittest discover -s tests -p "test_claims*.py" -v

The public release must not present this executable ZIP as an installed native agent. Preserve the original source-kit ZIPs and tags when releasing a newer version.

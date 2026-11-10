# Reverse Engineering & Security Researcher — executable offline source kit

This independent Python 3.12+ source package reuses the existing first-party
`muse_presets.reverse.compare_observed_flows` implementation **byte-for-byte**.
It compares two supplied, benign UI observation sequences. It performs no
live reverse engineering, packet capture, binary execution, malware detonation,
network probing, desktop control, sandbox administration or authorization grants.

## Create and verify

From this repository:

    PYTHONPATH=src python3 -B examples/export_reverse_sourcekit.py --to ../reverse-offline-kit.zip
    PYTHONPATH=src python3 -B examples/export_reverse_sourcekit.py --verify ../reverse-offline-kit.zip --sha256 <trusted-sha256>

On Windows PowerShell, set `$env:PYTHONPATH='src'` and use `python`. The exporter
requires an absent ZIP path, a safe existing destination parent and unmodified,
SHA-256-pinned source. The verifier requires a separately trusted digest and
compares exact bounded canonical ZIP bytes; it **never opens or extracts the
submitted ZIP**. A different ZIP with the caller's correct digest is rejected.

After checking the ZIP hash and extracting into a new directory:

    python -I -B run.py --operation demo
    python -I -B run.py --operation self-test

The first command compares a fictional form's saved/cancel/export outcomes:
a changed Save behavior and added/removed controls are reported without
asserting a security vulnerability. The second runs 10 bundled engine tests.
These are local exercises, not independently audited target observations.

## Use your own locally supplied fixture

Create a JSON file **outside** the immutable extracted kit:

    {
      "schema": "muse-presets/reverse-offline-fixture-input-v1",
      "analysis_boundary": "OFFLINE_SUPPLIED_OBSERVATIONS_ONLY",
      "authorization_declaration": "OWNER_OR_PERMISSION_DECLARED_UNVERIFIED",
      "before": [{"action": "click", "target": "save", "outcome": "silent"}],
      "after": [{"action": "click", "target": "save", "outcome": "toast"}]
    }

Then:

    python -I -B run.py --operation compare --fixture /absolute/path/fixture.json

The maximum input is 128 KiB. The engine accepts at most 256 observations per
side, and only the actions `view`, `click`, `scroll` and `hover` with short
symbolic target names. Duplicate action:target pairs and external URL targets
are rejected. Output includes changed/added/removed action:target keys and
the fixture SHA-256, **not raw observation outcomes**. Untrusted text remains
data, never instructions.

The permission declaration is a caller statement, **not independently
verified ownership or an execution grant**. Because this code does not access
targets at all, the declaration does not authorize later live inspection.
Compare results prove only differences in the supplied records, not causality,
a real security defect, binary equivalence or a successful remediation.

## Trust and lifecycle

The kit includes `reverse.py`, a 10-test engine suite, role preset/playbook,
license, and a runner with fixed file hashes, duplicate-key-safe JSON, resource
limits, unknown-file refusal, import-shadow refusal, and Windows junction /
POSIX symlink controls. Modified source, rehashed manifests and unsupported
optimized interpreter runs are refused before importing the engine. External
fixture files must be regular, non-hardlinked and outside the kit.

Hashes check bytes, not publisher identity. Python `-I` is not an OS sandbox;
supplied observations may still be incorrect. No source code or assets of
third-party target programs are bundled. No native Muse account, model,
provider-issued tool call, calendar, network connector or Family Link is
installed. Privacy-sensitive observations should not be placed in public Git.

Updates require a newly frozen, verified kit. There is no auto-update,
cleanup of owner data, scheduled job or destructive migration. The kit does not manage production task ownership or retention.

Repository regressions:

    PYTHONPATH=src python3 -B -m unittest discover -s tests -p test_reverse_fixture.py -v
    PYTHONPATH=src python3 -B -m unittest discover -s tests -p test_reverse_sourcekit.py -v
    PYTHONPATH=src python3 -B -m unittest discover -s tests -v

Private-source integration, independent A/B/C verification, public export
and native deployment are distinct stages; never equate one with another.

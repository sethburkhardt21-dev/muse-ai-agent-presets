# T32 — GitHub clean-clone source-role acceptance

**Release target:** eleven independently reusable, neutral GitHub source packages.
**Result grade:** CLEAN_CLONE_ROLE_MATRIX_SOURCE_ONLY, not native agent deployment.

This is executable source-only qualification, not a screenshot of a template
or a test that mistakes generated skill descriptors for executable tools.

## Run from the released repository root

Use Python 3.10+ and no paid account, plugin, native Hatch VM or external service.

macOS / Linux:

    PYTHONPATH=src python3 -B examples/verify_role_packages.py --all
    PYTHONPATH=src python3 -B examples/verify_role_packages.py --role coordinator

Windows PowerShell:

    $env:PYTHONPATH = "src"
    python -B examples/verify_role_packages.py --all
    python -B examples/verify_role_packages.py --role learning-coach

The verifier uses temporary local folders, creates a pristine T04/T05/T06
standalone package for each selected role, inspects exact source pins,
exports its role ZIP into a separate new path, reopens the ZIP and checks
the profile role/receipt, then executes a deterministic offline connector
fixture with the role's real capability allowlist. A failed package or
incorrect receipt refuses the run. Temporary test folders are deleted
after testing; actual receiving-owner memory is never read or modified.

A package's LOCAL_STANDALONE_MATCH status proves only source consistency.
All connector providers remain unbound, native_installed=false,
public_git_pushed=false, external effects disabled. No remote Desktop
Commander, SSH, CUA, calendar, Space, plugin, model or cron executes.

## Honest eleven-role capability matrix

| Role | Local demonstration grade | What was actually exercised |
| --- | --- | --- |
| coordinator | LOCAL_ENGINE_DEMO_PASSED | A real local workgraph/evidence review skill executed with synthetic tasks |
| software-engineer | LOCAL_ENGINE_DEMO_PASSED on POSIX; UNSUPPORTED_POSIX_ENGINE_ON_WINDOWS otherwise | Source-pinned local Claim Gate claim/reuse/UNKNOWN workflow; not a Windows-native executor |
| model-builder | LOCAL_ENGINE_DEMO_PASSED | Synthetic dev metrics and local checkpoint digest, not model training or inference |
| research-evaluator | SOURCE_TEMPLATE_ONLY | Method/playbook/skill and offline connector fixture only; no scholarly retrieval backend |
| creative-studio | SOURCE_TEMPLATE_ONLY | Method/playbook/skill and offline connector fixture only; no renderer bundled |
| adversarial-verifier | SOURCE_TEMPLATE_ONLY | Safe defensive playbook and fixture only; no live attack engine or OS tooling |
| personal-companion | SOURCE_TEMPLATE_ONLY | Scoped profile, memory and consent templates; no live reminders or owner account |
| garden-companion | LOCAL_ENGINE_DEMO_PASSED | Real local SQLite calendar proposal/approval/recovery example |
| learning-coach | LOCAL_ENGINE_DEMO_PASSED | Synthetic-source SQLite study, owner review and due-review demo |
| claims-adjudicator | LOCAL_SLICE_DEMO_PASSED | Small pure scope/overclaim check; no independent autonomous adjudicator |
| reverse-engineering-researcher | LOCAL_SLICE_DEMO_PASSED | Deterministic supplied trace comparison; no desktop capture or protocol probing |

The shared Evidence Finder is NOT a twelfth role. Its source-only SQLite
receipt/custody demo is run separately and must report a locally verified
receipt chain, without claiming independent source authority.

A grade is relative to the exact local source demonstration only.
An offline fixture, role template or self-generated source receipt cannot
grant permissions or verify an external recipient.

## Negative and cross-platform gates

Tests additionally refuse unknown roles, role/source mismatches, modified
skills catalogs, duplicate or unsafe ZIP members, corrupted receipt bytes,
and occupied destinations. Unsupported POSIX locking on Windows is
UNSUPPORTED_POSIX_ENGINE_ON_WINDOWS, not a green engine execution.

After the T31 clean public export, use an independent clean extraction on
Windows and macOS to run --all, role-specific positive tests and the
repository test suite. Record frozen artifact SHA, exact Python version,
pass/skip counts and report SHA for each host. Do not claim Linux tested
unless an actual Linux reviewer ran the frozen source.

Publishing source does not automatically install native agents in
personal Muse/Hatch; that remains optional and out of scope under the
owner's GitHub-only release criteria. T34 publishes from clean public
source only after independent package, CI, privacy and manifest
acceptance. The private repository history must never be wholesale
pushed to the public repository.

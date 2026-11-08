# GitHub quickstart — eleven generic agent source kits

This guide is for a **GitHub source-only** release. You can prepare, inspect,
and test all eleven neutral role packages without a Muse/Hatch account or
paid provider. Native agent installation, model-selected tool use, desktop
control, Family Link transport, scheduling and remote services are **not
connected**. They are optional integrations, not release requirements.

**Release timing:** the public GitHub repository currently holds an earlier
alpha until the guarded source publication gate (T34) passes. These commands
apply to the release containing examples/github_quickstart.py; do not
mistake an older public checkout for the pending release.

## Requirements and checkout

- Git and Python 3.10+ are intended; no pip dependencies are needed for
  the basic examples. The verified release run records exact interpreter
  versions separately (Python 3.12 on Windows and 3.14 on macOS).
- At publication, clone the public GitHub repository:

      git clone https://github.com/sethburkhardt21-dev/muse-ai-agent-presets.git
      cd muse-ai-agent-presets

- Before publication, an authorized maintainer can run the same commands
  inside the private working source checkout or an isolated frozen-source
  copy; an older public clone does **not** include the latest features.

### macOS / Linux terminal

    PYTHONPATH=src python3 -B -m muse_presets.cli doctor
    PYTHONPATH=src python3 -B examples/github_quickstart.py --all
    PYTHONPATH=src python3 -B examples/github_quickstart.py --role garden-companion --to ../my-new-garden-agent

### Windows PowerShell

    $env:PYTHONPATH = "src"
    python -B -m muse_presets.cli doctor
    python -B examples/github_quickstart.py --all
    python -B examples/github_quickstart.py --role garden-companion --to ../my-new-garden-agent

The --all command exercises all eleven role-source manifests, builds each
T04/T05/T06 package inside a disposable temporary folder, reopens it,
checks its source pins and disabled skill registry, then verifies one
synthetic connector observation per role. The folder is cleaned up after
the check. The --role command checks one role. --to additionally creates
one *new* source package at the specified absent path and refuses to
overwrite existing owner files; do not use --all with --to.

This is an executable **source-only** smoke test; synthetic observations
are not real connector access or proof of trained agent behavior. Its JSON
report includes source inspection, three scoped subchats, three disabled
skills, and an offline fixture result for every selected role.

## Choose a role and run its local example

| Role | Verified local source capability | Local demo or limit |
| --- | --- | --- |
| [coordinator](../presets/coordinator/INSTALL.md) | Bounded graph and evidence review | Independent local reviewer demo in existing INSTALL |
| [software-engineer](../presets/software-engineer/INSTALL.md) | Source-pinned claim/recovery components | POSIX Claim Gate demo; Windows stages but cannot run its POSIX fcntl engine |
| [model-builder](../presets/model-builder/INSTALL.md) | Synthetic dev metrics and checkpoint digest | Local model-metrics script; no real training, inference or GPU |
| [research-evaluator](../presets/research-evaluator/INSTALL.md) | Role procedures and offline connector scope | No standalone scholarly retrieval engine shipped |
| [creative-studio](../presets/creative-studio/INSTALL.md) | Source profile, methods and render scope | No rendering backend bundled |
| [adversarial-verifier](../presets/adversarial-verifier/INSTALL.md) | Defensive procedures and bounded fixture contract | No live attack engine bundled |
| [personal-companion](../presets/personal-companion/INSTALL.md) | Configurable profile and notebook scope | No live reminders or personal account integration |
| [garden-companion](../presets/garden-companion/INSTALL.md) | Transactional local calendar proposals | Run examples/garden_calendar_demo.py |
| [learning-coach](../presets/learning-coach/INSTALL.md) | Source-grounded local study transactions | Run examples/learning_session_demo.py |
| [claims-adjudicator](../presets/claims-adjudicator/INSTALL.md) | Claim scope and evidence references | Run examples/priority_slices.py; no autonomous verdict engine |
| [reverse-engineering-researcher](../presets/reverse-engineering-researcher/INSTALL.md) | Compare supplied observation fixtures | Run examples/priority_slices.py; no live desktop capture |

The Evidence Finder is one shared service, **not a twelfth agent**.
It has a source-tested local SQLite example:

    PYTHONPATH=src python3 -B examples/evidence_ledger_demo.py

On Windows, use python instead of python3 and set PYTHONPATH as shown.
These examples use synthetic content. Local source tests qualify only the
implemented capabilities, not an actual personal Muse runtime.

## Run the test suite and inspect a package

    PYTHONPATH=src python3 -B -m unittest discover -s tests -q
    PYTHONPATH=src python3 -B -m muse_presets.cli audit-neutrality
    PYTHONPATH=src python3 -B -m muse_presets.cli dropin-inspect --path ../my-new-garden-agent

On Windows, the POSIX engine has documented unsupported cases; a test
**skip** is not an engine PASS. The repository tests source safety and
expected denials. The source doctor is not a native plugin check.

To inspect/export or preview an upgrade without changing owner files:

    PYTHONPATH=src python3 -B -m muse_presets.cli dropin-export --path ../my-new-garden-agent --to ../new-garden-source.zip
    PYTHONPATH=src python3 -B -m muse_presets.cli dropin-upgrade-preview --candidate ../my-new-garden-agent --target ../existing-owner-agent
    PYTHONPATH=src python3 -B -m muse_presets.cli dropin-uninstall-plan --path ../my-new-garden-agent

Export requires a pristine package and a nonexistent output destination.
An upgrade preview never applies changes; the uninstall plan never deletes
files. Back up actual owner data separately before any later host install.

## Source-only role acceptance matrix

The quickstart proves that every role kit can be staged and inspected.
To test the actual available local demos separately from generic
templates, run:

    PYTHONPATH=src python3 -B examples/verify_role_packages.py --all

This checks all eleven role ZIP manifests, examples and disabled
connectors. It labels template-only roles and the unsupported
Windows POSIX Claim Gate honestly. See
[GitHub role acceptance](GITHUB_ROLE_ACCEPTANCE.md).

## Add a feature or resolve a failure

[Extension recipes](EXTENDING_GENERIC_AGENTS.md) cover additional role
methods, SKILL.md generation, local engines, connector contracts, testing,
source hashes, and fail-closed upgrades.

| Symptom | What to do |
| --- | --- |
| ModuleNotFoundError for muse_presets | Run from repo root with PYTHONPATH=src; verify Python 3.10+ |
| Source pin mismatch / SOURCE_DRIFT | Stop; verify actual repository commit and source bytes; create a new destination. Never bypass hashes |
| Destination occupied | Choose an absent folder; keep existing owner state intact |
| REVIEW_REQUIRED / incomplete stage | Preserve the failed output and diagnose it; never retry blindly or delete unrelated files |
| Desktop/CUA/SSH says not connected | Expected. Only local source contract is shipped; configure an authorized provider separately |
| Native Muse skill not found | Native skill installation is unsupported in the GitHub-only package; do not edit a live owner's registry |
| POSIX Claim Gate does not run on Windows | Use its documented source staging/inspection only, or a qualified POSIX host for the local demo |
| Public repository lacks these commands | It is still the earlier alpha; check the published release tag/commit after T34 |

No credentials or private memories should enter bug reports, public issues,
tests or exported ZIP files. A GitHub source release can be complete while
native host functionality is unsupported and clearly labeled.

# Get started

This source-only toolkit includes **eight runnable offline Python tools** and **eleven starter role profiles**. Download an executable ZIP without cloning, or customize a profile from source. The starter profiles are not installed assistants, and live connectors are **not connected** by default.

## Run a standalone tool without cloning

Choose an **executable** ZIP from the [current v0.4.1-alpha release](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/releases/tag/v0.4.1-alpha), not a smaller **starter** profile ZIP. **Python 3.12+; Git is not required** for an extracted executable kit.

[Download the Creative Studio executable](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/releases/download/v0.4.1-alpha/creative-studio-executable-v0.4.1-alpha.zip), verify its hash with [SHA256SUMS.txt](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/releases/download/v0.4.1-alpha/SHA256SUMS.txt), and extract into a new directory. Inside it, run:

```bash
python -I -B run.py --operation self-test
python -I -B run.py --operation demo --to ../creative-production-demo
```

These commands run a fictional production planner and textual storyboard. They do not connect a provider, render a movie, or install a native Muse agent. Other executable kits contain their own `START_HERE.md`. Starter role ZIPs are **not a model-backed autonomous assistant**.

## Prerequisites

- For cloning: Python 3.12+ and Git. For executable ZIPs: Python 3.12+ only.
- Windows with PowerShell, macOS or Linux. Some platform-specific engines are unsupported on Windows; see [capabilities](CAPABILITIES.md).
- A new output location. The tools refuse to overwrite an existing folder.

## Clone and verify

**macOS / Linux**

```bash
git clone https://github.com/sethburkhardt21-dev/muse-ai-agent-presets.git
cd muse-ai-agent-presets
PYTHONPATH=src python3 -B -m muse_presets.cli doctor
PYTHONPATH=src python3 -B examples/github_quickstart.py --all
```

**Windows PowerShell**

```powershell
git clone https://github.com/sethburkhardt21-dev/muse-ai-agent-presets.git
cd muse-ai-agent-presets
$env:PYTHONPATH = "src"
python -B -m muse_presets.cli doctor
python -B examples/github_quickstart.py --all
```

The `--all` smoke check creates temporary examples of all eleven role-source packages, inspects their configuration and verifies synthetic connector observations. It does **not** install native assistants or authenticate a remote account.

## Create a kit

```bash
PYTHONPATH=src python3 -B examples/github_quickstart.py --role garden-companion --to ../my-garden-agent
```

Use `python` on Windows after setting `$env:PYTHONPATH`. Each kit includes `INSTALL.md`, a role playbook and configuration templates. Change the name, instructions, capabilities and preferences to fit your work. Existing output directories are never overwritten.

Other choices include `software-engineer`, `coordinator` and `reverse-engineering-researcher`. [Browse all roles](CAPABILITIES.md).

## Run local demonstrations

```bash
PYTHONPATH=src python3 -B examples/garden_calendar_demo.py
PYTHONPATH=src python3 -B examples/learning_session_demo.py
PYTHONPATH=src python3 -B examples/evidence_ledger_demo.py
PYTHONPATH=src python3 -B examples/priority_slices.py
```

These programs use fictional inputs and local files. Garden and Learning exercises demonstrate SQLite recovery. A local receipt is not proof of an authenticated native owner or an external action.

## Validate or extend

```bash
PYTHONPATH=src python3 -B -m unittest discover -s tests -q
PYTHONPATH=src python3 -B -m muse_presets.cli audit-neutrality
PYTHONPATH=src python3 -B examples/verify_role_packages.py --all
```

Read [customization](CUSTOMIZE.md), [skills](SKILLS.md) and [extending the source](EXTENDING_GENERIC_AGENTS.md) before adding a provider or executing external tools.

## Common issues

| Problem | Resolution |
| --- | --- |
| `ModuleNotFoundError` | Run from the repository root with `PYTHONPATH=src`. |
| Output already exists | Choose a new destination; preserve existing owner files. |
| A source or receipt hash changed | Inspect the source and create a new verified package rather than bypassing the check. |
| Connector or native skill unavailable | This is expected until a separately authorized host integration exists. |
| A POSIX engine is unsupported on Windows | Use its documented source-only path or a compatible POSIX environment. Unsupported is **not** a passed test. |
| Need a ZIP instead of a clone | Use the eight **executable** ZIP downloads on the [current release page](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/releases/tag/v0.4.1-alpha). Starter ZIPs are for customization. |

The toolkit does not provide an OS security sandbox. Run reviewed local source only. Native host activation remains optional and separate from the GitHub distribution.

## Advanced local workflows

Current repository source also includes engineering repair, reviewed builder execution, portable model kits, research metrics and restart verification. See [Runnable workflows](WORKFLOWS.md). Archived ZIPs remain tied to their original release versions.

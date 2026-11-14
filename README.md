# Specialist AI Agent Kits

**Eight runnable offline Python tools. Fifteen customizable specialist profiles.**

[![Source checks](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/actions/workflows/checks.yml/badge.svg)](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/actions/workflows/checks.yml) · [MIT license](LICENSE)

Run useful offline tools or apply specialist methods to your existing assistant. No paid API is needed for the fictional examples.

[**Download tools and profiles**](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/releases/tag/v0.4.1-alpha) · [**Get started**](docs/GITHUB_QUICKSTART.md) · [**Compare capabilities**](docs/CAPABILITIES.md)

**Choose the right version:** the published **v0.4.1-alpha** has eight executable ZIPs and eleven starter-profile ZIPs. The profile source has **15 roles and 50 profile/shared procedures**; the separate curated collection below provides deeper task methods. Published archives have not been replaced.

Executable ZIPs contain local programs; profiles contain source-only instructions. They are **not installed native Muse agents**. A profile is not a model-backed autonomous assistant. Live tools require real host permissions.

## Run a standalone tool now

1. Download the [Creative Studio executable](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/releases/download/v0.4.1-alpha/creative-studio-executable-v0.4.1-alpha.zip) and verify it against [SHA256SUMS.txt](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/releases/download/v0.4.1-alpha/SHA256SUMS.txt).
2. Extract it into a new folder. You need Python 3.12+ for this example, but not Git or an API key.
3. Open a terminal in the extracted folder and run:

```bash
python -I -B run.py --operation self-test
python -I -B run.py --operation demo --to "$HOME/creative-production-demo"
```

This also works in PowerShell. Choose a new destination. The local outputs are JSON, CSV and a textual storyboard, not images or animation.

## For AI agents and automated readers

[AI-agent discovery index](llms.txt) · [Verified capability facts](docs/discovery/agent-capabilities.json) · [Questions and answers](docs/discovery/AI_AGENT_GUIDE.md).

## Choose your specialist

| Specialist | What it is for |
| --- | --- |
| [Coordinator](presets/coordinator/) | Review task plans, dependencies and completion evidence. |
| [Software Engineer](presets/software-engineer/) | Reproduce bugs, review patches and test in disposable Git repositories. |
| [Model Builder](presets/model-builder/) | Train small examples; compare development and held-out results. |
| [Research Evaluator](presets/research-evaluator/) | Check quotations against source text and score supplied held-out predictions. |
| [Creative Studio](presets/creative-studio/) | Plan shots, timelines and continuity, then export production files and a textual storyboard. |
| [Adversarial Verifier](presets/adversarial-verifier/) | Organize defensive checks, record failures and review evidence. |
| [Personal Companion](presets/personal-companion/) | Plan and organize with your own preferences. |
| [Garden Companion](presets/garden-companion/) | Keep plant observations and review local calendar changes in SQLite. |
| [Learning Coach](presets/learning-coach/) | Study from supplied sources and keep scored review history. |
| [Claims Adjudicator](presets/claims-adjudicator/) | Compare claims with supplied evidence and record qualifications or corrections. |
| [Reverse Engineering & Security Researcher](presets/reverse-engineering-researcher/) | Compare recorded application behavior and review observations. |
| [Data Engineering & Database Architect](presets/data-engineering-architect/) | Detect duplicate keys and plan reversible schema changes |
| [Infrastructure & Reliability Engineer](presets/infrastructure-reliability-engineer/) | Calculate fictional error budgets and review incident evidence |
| [Automation Engineer](presets/automation-engineer/) | Order dependency graphs, reject cycles and plan safe retries |
| [Product & Interface Designer](presets/product-interface-designer/) | Find unlabeled controls in supplied screen descriptions |

The [capability guide](docs/CAPABILITIES.md) distinguishes executable tools from profiles. The shared [Evidence Finder](services/evidence-finder/) serves these roles; it is not another assistant.

## Create your own profile from source

Use Python 3.12+ and Git. Clone the repository, then create a new kit:

```bash
git clone https://github.com/sethburkhardt21-dev/muse-ai-agent-presets.git
cd muse-ai-agent-presets
python -B quickstart.py --role personal-companion --to "$HOME/my-assistant-kit"
python -B quickstart.py --all
```

Use `python3` where appropriate; PowerShell is supported. No `PYTHONPATH` or pip setup is needed. Choose a new absolute destination: existing files are preserved. `--all` checks 15 temporary source kits, not installed assistants.

The kit has editable identity, memory, voice and prompt drafts in `system-profile/profile/`, three `subchat-scopes/`, and eight **disabled** descriptors in `role-skills/`. [Installation and saved data](docs/INSTALL_AND_PERSISTENCE.md) explains owner control and the separate host boundary.

## Use the portable instruction library

The original exporter keeps **45 role methods plus five shared procedures = 50 procedures**. Repeating shared methods across 15 kits creates 120 descriptor instances, not 120 different capabilities.

```bash
python -B examples/export_portable_skills.py --plan
python -B examples/export_portable_skills.py --to "$HOME/my-portable-skills"
python -B examples/export_portable_skills.py --inspect "$HOME/my-portable-skills"
```

This creates 50 portable `SKILL.md` folders without renaming native-style IDs or granting tools. See [Skills](docs/SKILLS.md) for the two formats and [Capabilities](docs/CAPABILITIES.md) for runnable scope.

## Enhance your existing assistant

**15 specialists, 75 skills, 25 workflows and 100 starters** are now available in the [task collection](docs/collection/MUSE_CURATED_COLLECTION.md), without replacing identity or memory.

```sh
python -B tools/muse_collection.py show daily-planner
python -B tools/muse_collection.py demo data-engineer
python -B tools/collection_compatibility.py
```

The 75 skills overlap with the original 50 procedures: **not 125 unique capabilities**. [Collection setup](docs/collection/SPECIALIST_QUICKSTART.md) ? [Specialist catalog](docs/collection/SPECIALIST_CATALOG.md) ? [Operating handbook](docs/handbook/README.md). Starters are not new agents; release ZIPs remain unchanged.

**Daily Desk:** [Open the local task-and-note workbench](docs/spaces/DAILY_DESK.md). Run `python -B examples/daily_desk.py` for the disposable edit/reopen/backup/restore demo; no account is needed.

## Documentation

| Use the toolkit | Adapt it |
| --- | --- |
| [Installation and first run](docs/GITHUB_QUICKSTART.md) | [Customize a profile](docs/CUSTOMIZE.md) |
| [Capabilities](docs/CAPABILITIES.md) | [Architecture](docs/ARCHITECTURE.md) |
| [Runnable workflows](docs/WORKFLOWS.md) | [Skills](docs/SKILLS.md) |
| [Downloads and earlier versions](docs/RELEASES.md) | [Development](docs/DEVELOPMENT.md) |
| [Security](docs/SECURITY.md) | [Host compatibility](docs/HOST_COMPATIBILITY.md) |

## Before running code

Local programs run under your operating-system account: this is **not a sandbox**. Review downloaded code and keep personal data outside the repository. Optional connectors are disabled by default. Hashes help detect changed files; they do not establish identity, permission or successful delivery to another service.

Model examples use small synthetic models, not large-language-model training. Native Muse installation and live provider access require separate setup and verification.

MIT licensed. Unofficial; not affiliated with or endorsed by Meta. [Contributing](CONTRIBUTING.md) · [Changelog](CHANGELOG.md).

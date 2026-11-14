# Muse Specialist Toolkit

### Your Muse. Your Specialists. Your Possibilities.

**15 AI Specialists · 100+ Configurations · 150+ Custom Connectors**

Extend your **Muse personal assistant** with specialist tools for work, learning, creativity and daily life. Choose a specialist, run useful tools, explore connectors and save your work.

**Free · Open source (MIT) · Customizable · Built for Muse**

[![Source checks](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/actions/workflows/checks.yml/badge.svg)](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/actions/workflows/checks.yml)

[AI-agent discovery index](llms.txt) | [Verified capability facts](docs/discovery/agent-capabilities.json)
[**Start here**](docs/v1/START_HERE.md) · [**Explore 151 connectors**](docs/connectors/CATALOG.md) · [**Find your specialist**](docs/collection/SPECIALIST_CATALOG.md) · [**Release downloads**](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/releases)

**100+ configurations:** 100 task starters and 15 customizable role profiles, not 115 independently installed agents. **151 custom connectors:** searchable, source-linked setup guides. The original 50 role/shared procedures overlap the developed 75 task skills.

## Find your starting point

| I want to… | Start here | First result |
| --- | --- | --- |
| **Customize Muse** | [Specialist and task configuration guide](docs/v1/START_HERE.md#1-use-with-muse) | A task-ready kit that preserves your assistant's existing identity and permissions |
| **Run specialist tools** | [Executable tools guide](docs/v1/START_HERE.md#2-run-specialist-tools) | Inspectable results from an actual Python program |
| **Organize my day** | [Personal Companion's Daily Desk](docs/v1/START_HERE.md#3-open-personal-companion) | Tasks and notes you can edit, reopen, export and restore |
| **Connect a service** | [Browse 151 custom connectors](docs/connectors/CATALOG.md) | A setup message and original source instructions for your chosen service |

## Choose your specialist

Each role offers distinct methods and editable configurations.

| Specialist | What you can work on |
| --- | --- |
| [Coordinator](presets/coordinator/) | Plans, dependencies and verifiable handoffs |
| [Software Engineer](presets/software-engineer/) | Bugs, patches, source changes and test evidence |
| [Model Builder](presets/model-builder/) | Data preparation, local experiments and evaluation |
| [Research Evaluator](presets/research-evaluator/) | Source verification, research claims and evaluation |
| [Creative Studio](presets/creative-studio/) | Production briefs, timelines, continuity and exports |
| [Adversarial Verifier](presets/adversarial-verifier/) | Defensive testing and remediation evidence |
| [Personal Companion](presets/personal-companion/) | Personal planning, tasks, notes and preferences |
| [Garden Companion](presets/garden-companion/) | Plant records, observations and care planning |
| [Learning Coach](presets/learning-coach/) | Study workflows, practice and scored review |
| [Claims Adjudicator](presets/claims-adjudicator/) | Evidence matrices and disputed claims |
| [Reverse Engineering & Security Researcher](presets/reverse-engineering-researcher/) | Artifact and recorded-behavior analysis |
| [Data Engineering & Database Architect](presets/data-engineering-architect/) | Data quality, schema comparisons and migrations |
| [Infrastructure & Reliability Engineer](presets/infrastructure-reliability-engineer/) | Incident analysis, error budgets and reliability |
| [Automation Engineer](presets/automation-engineer/) | Dependencies, triggers, safe execution plans |
| [Product & Interface Designer](presets/product-interface-designer/) | Interface states, contrast and design validation |

[Capability matrix](docs/CAPABILITIES.md) ? [Task starters](collections/muse-starters-v1/CATALOG.md) ? [Handbook](docs/handbook/README.md)

## Go beyond instructions: run an actual tool

Local demonstrations run with Python 3.12+ and no paid API.

```bash
python -B tools/muse_collection.py specialists
python -B tools/muse_collection.py demo data-engineer
python -B tools/muse_collection.py workflow-demo pipeline-validation
```

For a portable runnable collection:

```bash
python -B tools/muse_collection.py check
python -B examples/export_specialist_collection.py --to "$HOME/Muse_Specialist_Collection.zip"
```

Exports preserve existing destinations; outputs identify executed stages.

**Without cloning:** the historical [Creative Studio executable ZIP](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/releases/download/v0.4.1-alpha/creative-studio-executable-v0.4.1-alpha.zip) contains a runnable program. Verify its hash using [SHA256SUMS.txt](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/releases/download/v0.4.1-alpha/SHA256SUMS.txt), extract and run:

```bash
python -I -B run.py --operation self-test
python -I -B run.py --operation demo --to "$HOME/creative-production-demo"
```

These produce text/JSON/CSV, not video. Historical `v0.4.1-alpha` contains **eight runnable tools and eleven starter profiles**; see [versions](docs/RELEASES.md).

## Make Muse your own

```bash
git clone https://github.com/sethburkhardt21-dev/muse-ai-agent-presets.git
cd muse-ai-agent-presets
python -B quickstart.py --role personal-companion --to "$HOME/my-assistant-kit"
python -B quickstart.py --all
python -B examples/export_portable_skills.py --plan
```

Exports are source-only drafts, **not installed native Muse agents**; a profile is **not a model-backed autonomous assistant**. Your host controls live credentials and permissions.

## Personal Companion: meet Daily Desk

A local tasks-and-notes workbench: edit, reopen, refuse stale writes, export and restore using `PersonalCompanion` and `SpaceCompanion` infrastructure.

```bash
python -B examples/daily_desk.py
```

The demo creates three tasks and two notes, edits, reopens and restores. [Open Daily Desk](docs/spaces/DAILY_DESK.md).

## Custom connectors for the work you do

[**Browse all 151 custom connectors**](docs/connectors/CATALOG.md), searchable by service, category and specialist, with setup prompts and pinned original instructions. The [directory guide](docs/connectors/README.md) explains how to choose and connect a service. Connector support extends your assistant through the platform's supported setup rather than changing its underlying identity.

## Built for verifiable work

The repository includes source-integrity checks, portability tests, strict validation, versioned persistence and guarded local operation receipts. Run `python -B scripts/check_public.py` to inspect the source distribution. Actual host operations and permissions remain separate from examples.

[**Get started**](docs/GITHUB_QUICKSTART.md) · [**AI-agent discovery index**](llms.txt) · [**Verified capability facts**](docs/discovery/agent-capabilities.json) · [**Security**](docs/SECURITY.md) · [**Source-only integration**](docs/EXTENDING_GENERIC_AGENTS.md) · [**MIT license**](LICENSE)

Support: [Issues](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/issues) · [Contributing](CONTRIBUTING.md) · [Current and historical downloads](docs/RELEASES.md)

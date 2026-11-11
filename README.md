# Specialist AI Agent Kits

**Eleven customizable assistant starter kits. One open-source toolkit.**

[![Source checks](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/actions/workflows/checks.yml/badge.svg)](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/actions/workflows/checks.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Source kits](https://img.shields.io/badge/assistant_kits-11-555.svg)](presets/catalog.json)

Build a focused AI assistant from reusable role profiles, editable methods, skill descriptions, local examples and optional connector contracts. Download a ready-to-customize source kit or use the repository to generate one yourself.

[**Download v0.4.1 alpha**](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/releases/tag/v0.4.1-alpha) · [**Get started**](docs/GITHUB_QUICKSTART.md) · [**Compare capabilities**](docs/CAPABILITIES.md)

> **What ships:** source-only packages and offline tooling—not eleven preinstalled, autonomous Muse agents. Native host connections, accounts and external actions require separate setup and authorization. The project is unofficial and is not affiliated with or endorsed by Meta.

## Choose your specialist

| Kit | Designed for |
| --- | --- |
| [Coordinator](presets/coordinator/) | Organizing tasks, reviewing plans and documenting handoffs |
| [Software Engineer](presets/software-engineer/) | Debugging, source review and controlled engineering workflows |
| [Model Builder](presets/model-builder/) | Model evaluation methods, data checks and development workflows |
| [Research Evaluator](presets/research-evaluator/) | Evidence tracking, evaluation design and held-out comparisons |
| [Creative Studio](presets/creative-studio/) | Offline production briefs, timelines, continuity checks, and textual storyboards |
| [Adversarial Verifier](presets/adversarial-verifier/) | Defensive testing, failure analysis and independent review |
| [Personal Companion](presets/personal-companion/) | Everyday organization and adaptable assistant experiences |
| [Garden Companion](presets/garden-companion/) | Plant notes, planning and local calendar examples |
| [Learning Coach](presets/learning-coach/) | Source-based study, questions and review planning |
| [Claims Adjudicator](presets/claims-adjudicator/) | Evidence boundaries, claim qualification and correction |
| [Reverse Engineering & Security Researcher](presets/reverse-engineering-researcher/) | Authorized observation and behavioral comparison |

The shared **[Evidence Finder](services/evidence-finder/)** is available to multiple roles; it is not a twelfth agent. Individual kits include a role profile, methods, configuration templates, local documentation and disabled optional connector declarations.

## Try the toolkit

Requires **Python 3.12+ and Git**. The core examples use the Python standard library and do not require a paid API.

```bash
git clone https://github.com/sethburkhardt21-dev/muse-ai-agent-presets.git
cd muse-ai-agent-presets

PYTHONPATH=src python3 -B -m muse_presets.cli doctor
PYTHONPATH=src python3 -B examples/github_quickstart.py --all
PYTHONPATH=src python3 -B examples/github_quickstart.py --role garden-companion --to ../my-garden-agent
```

On Windows PowerShell, set `$env:PYTHONPATH = "src"` and use `python` instead of `python3`. The last command creates a **new** folder and refuses to overwrite existing user files.

For a shorter route, download an individual ZIP from the [current release](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/releases/tag/v0.4.1-alpha), extract it and follow its included `INSTALL.md`.

## More than role templates

The current source includes **runnable engineering, model-building and research tools**, alongside the editable starter profiles.

| Goal | Start here |
| --- | --- |
| Reproduce and repair a bug | Disposable Git workflow with failing tests, passing tests and independent review |
| Build and test safely | Source-pinned worktree staging, reviewed Python execution and optional Mac Swift typechecking |
| Explore model training | Small deterministic training examples, held-out evaluation and transactional local installation |
| Check research evidence | Exact quotation/source checks and grouped numerical evaluation |
| Preserve progress | Local restart verification, evidence storage and handoff review |

**[Run a workflow](docs/WORKFLOWS.md)** · **[See exactly what ships](docs/CAPABILITIES.md)**

```bash
PYTHONPATH=src python3 -B examples/research_evaluator_demo.py
PYTHONPATH=src python3 -B examples/numeric_evaluation_demo.py
PYTHONPATH=src python3 -B examples/continuum_checkpoint_demo.py
```

Engineering examples execute reviewed code under your OS account, not inside a security sandbox. Model examples train small synthetic models—not large language models. Connectors remain disabled until separately configured.

For archived downloads, see the [eleven starter ZIPs](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/releases/tag/v0.2.0-alpha) and [extended engineering kit](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/releases/tag/software-engineer-sourcekit-r56-alpha). **Those versioned ZIPs do not automatically include newer code on main.** Clone this repository for the latest source.

## Standalone offline specialists

Build self-contained **Creative Studio, Claims, Garden, Learning and observation-comparison kits**, each with local verification and usage instructions. These complement the existing Coordinator, engineering and model-building packages. [Compare the packages](docs/CAPABILITIES.md#standalone-offline-packages).

These executable kits are also distributed as versioned ZIPs. Earlier release files are preserved byte-for-byte.

## Documentation

| Start here | Build on it |
| --- | --- |
| [Installation and first run](docs/GITHUB_QUICKSTART.md) | [Customize profiles and methods](docs/CUSTOMIZE.md) |
| [Which capabilities are executable?](docs/CAPABILITIES.md) | [Skills and local verification](docs/SKILLS.md) |
| [Optional connectors and Family Link](docs/CONNECTORS.md) | [Development and quality checks](docs/DEVELOPMENT.md) |
| [Security and privacy](docs/SECURITY.md) | [Downloads and versions](docs/RELEASES.md) |

## Repository layout

- `presets/` — eleven role-specific source packages and setup guides
- `src/muse_presets/` — standard-library local tooling and supported engines
- `examples/` — reproducible offline demonstrations
- `services/evidence-finder/` — shared evidence service source
- `tests/` — regression and refusal tests
- `docs/` — product and developer documentation

**Safety by default:** new files are created without overwriting existing assistant memory; optional connectors are disabled; receipt hashes verify local consistency, not identity or permission. Only run Python code from sources you trust. See [security guidance](docs/SECURITY.md).

MIT licensed. [Contributing](CONTRIBUTING.md) · [Releases](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/releases) · [Changelog](CHANGELOG.md).

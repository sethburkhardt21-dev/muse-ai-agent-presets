# Specialist AI Agent Kits

**Eight runnable offline Python tools. Fifteen customizable specialist profiles.**

[![Source checks](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/actions/workflows/checks.yml/badge.svg)](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/actions/workflows/checks.yml) · [MIT license](LICENSE)

Run tools for software repair, model experiments, evidence review, study, planning and creative production. Or customize a role profile with your own instructions and working methods. The included offline examples need no paid API.

[**Download tools and profiles**](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/releases/tag/v0.4.1-alpha) · [**Get started**](docs/GITHUB_QUICKSTART.md) · [**Compare capabilities**](docs/CAPABILITIES.md)

**Choose the right version:** the published **v0.4.1-alpha** has eight executable ZIPs and eleven starter-profile ZIPs. The current source has **15 profiles and 50 unique instruction procedures**, including four newer source-only roles. Published archives have not been replaced.

Executable ZIPs contain programs you can run; starter profiles contain instructions you can edit. They are **not installed native Muse agents**. A starter profile is not a model-backed autonomous assistant. Live accounts, native installation and model-selected tool use require separate integration and verification.

## Run a standalone tool now

1. Download the [Creative Studio executable](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/releases/download/v0.4.1-alpha/creative-studio-executable-v0.4.1-alpha.zip) and verify it against [SHA256SUMS.txt](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/releases/download/v0.4.1-alpha/SHA256SUMS.txt).
2. Extract it into a new folder. You need Python 3.12+ for this example, but not Git or an API key.
3. Open a terminal in the extracted folder and run:

```bash
python -I -B run.py --operation self-test
python -I -B run.py --operation demo --to "$HOME/creative-production-demo"
```

The same commands work in Windows PowerShell. Choose a new absolute destination if that folder already exists. The demo creates JSON production files, a CSV shot list and a textual HTML storyboard. It does not render images or animation.

## For AI agents and automated readers

[AI-agent discovery index](llms.txt) · [Verified capability facts](docs/discovery/agent-capabilities.json) · [Questions and answers](docs/discovery/AI_AGENT_GUIDE.md).

## Choose your specialist

| Specialist | What it is for |
| --- | --- |
| [Coordinator](presets/coordinator/) | Review task plans, dependencies and completion evidence. |
| [Software Engineer](presets/software-engineer/) | Reproduce bugs, apply reviewed patches and check the results in disposable Git repositories. |
| [Model Builder](presets/model-builder/) | Run small-model training examples and compare development and held-out results. |
| [Research Evaluator](presets/research-evaluator/) | Check quotations against source text and score supplied held-out predictions. |
| [Creative Studio](presets/creative-studio/) | Plan shots, timelines and continuity, then export production files and a textual storyboard. |
| [Adversarial Verifier](presets/adversarial-verifier/) | Organize defensive checks, record failures and review evidence. |
| [Personal Companion](presets/personal-companion/) | Customize an assistant for planning, preferences and everyday organization. |
| [Garden Companion](presets/garden-companion/) | Keep plant observations and review local calendar changes in SQLite. |
| [Learning Coach](presets/learning-coach/) | Build study sessions from supplied sources, score practice and keep review history. |
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

Use `python3` instead of `python` on macOS/Linux where appropriate. These commands also work in Windows PowerShell. The wrapper needs no `PYTHONPATH` setting or pip installation. Choose a new absolute destination: existing files are never overwritten. The `--all` command checks all 15 source kits in temporary folders; it does not install assistants.

Your kit contains an editable identity, soul, user preferences, memory, opinion, voice and system-prompt draft under `system-profile/profile/`. Its three `subchat-scopes/` keep separate context and blank owner memory. `role-skills/` contains eight **disabled** descriptors: three role-specific methods plus five shared procedures. See [Installation and saved data](docs/INSTALL_AND_PERSISTENCE.md) before customizing or connecting a host.

## Use the portable instruction library

The source has **45 role methods plus five shared procedures = 50 unique procedures**. The five shared methods cover evidence, recovery, research, consent and handoff; repeating them across 15 kits creates 120 descriptor instances, not 120 different capabilities.

```bash
python -B examples/export_portable_skills.py --plan
python -B examples/export_portable_skills.py --to "$HOME/my-portable-skills"
python -B examples/export_portable_skills.py --inspect "$HOME/my-portable-skills"
```

The exporter creates 50 portable `SKILL.md` folders. It preserves native-style registry identifiers separately and does not register skills or grant tools. [Skills](docs/SKILLS.md) explains the two formats; [Capabilities](docs/CAPABILITIES.md) distinguishes runnable programs from instructions and offline fixtures.

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

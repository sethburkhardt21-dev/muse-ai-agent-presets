# Specialist AI Agent Kits

**Eight runnable offline Python tools. Eleven customizable specialist profiles.**

[![Source checks](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/actions/workflows/checks.yml/badge.svg)](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/actions/workflows/checks.yml) · [MIT license](LICENSE)

Run tools for software repair, model experiments, evidence review, study, planning and creative production. Or customize a role profile with your own instructions and working methods. The included offline examples need no paid API.

[**Download tools and profiles**](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/releases/tag/v0.4.1-alpha) · [**Get started**](docs/GITHUB_QUICKSTART.md) · [**Compare capabilities**](docs/CAPABILITIES.md)

Executable ZIPs contain programs you can run; starter ZIPs contain instructions you can edit. They are **not installed native Muse agents**. A starter profile is not a model-backed autonomous assistant. The source-only downloads contain readable code rather than a hosted service, and live accounts require separate integration.

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

The [capability guide](docs/CAPABILITIES.md) distinguishes executable tools from profiles. The shared [Evidence Finder](services/evidence-finder/) serves these roles; it is not a twelfth assistant.

## Work from source

Use Python 3.12+ and Git. From a terminal on macOS or Linux:

```bash
git clone https://github.com/sethburkhardt21-dev/muse-ai-agent-presets.git
cd muse-ai-agent-presets
PYTHONPATH=src python3 -B -m muse_presets.cli doctor
PYTHONPATH=src python3 -B examples/github_quickstart.py --all
```

On Windows PowerShell, set `$env:PYTHONPATH = "src"` and use `python` instead of `python3`. The doctor and examples inspect local packages; they do not install assistants or connect external services.

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

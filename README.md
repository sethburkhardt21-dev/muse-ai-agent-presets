# Specialist AI Agent Kits

**Eight runnable offline Python tools. Fifteen customizable specialist AI role profiles. Fifty distinct source procedures.**

[![Source checks](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/actions/workflows/checks.yml/badge.svg)](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/actions/workflows/checks.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Source roles: 15](https://img.shields.io/badge/source_roles-15-555.svg)](presets/catalog.json)

**Start with a useful result:** run an offline executable, or create a personal assistant source kit with editable identity, memory, voice, methods, subchats and disabled skills. No paid API is needed for the included fictional demos.

[**Download v0.4.1 alpha**](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/releases/tag/v0.4.1-alpha) · [**Get started**](docs/GITHUB_QUICKSTART.md) · [**Compare capabilities**](docs/CAPABILITIES.md)

> **Released vs source:** v0.4.1-alpha contains **eight runnable offline Python executable ZIPs and eleven starter-profile ZIPs**. This source tree adds four editable specialist roles and local examples—not four new released ZIPs. Starter profiles are **not installed native Muse agents**, model-backed autonomous services or authenticated accounts. Real Muse permissions and tools require separate supported host setup. Unofficial; not affiliated with or endorsed by Meta.

## Run a released offline executable

1. [Download Creative Studio executable](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/releases/download/v0.4.1-alpha/creative-studio-executable-v0.4.1-alpha.zip) and verify its SHA-256 against [SHA256SUMS.txt](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/releases/download/v0.4.1-alpha/SHA256SUMS.txt).
2. Extract to a new directory. Use Python 3.12+; this demo needs no Git, API key or Muse installation.
3. Inside the extracted folder:

```bash
python -I -B run.py --operation self-test
python -I -B run.py --operation demo --to "$HOME/creative-production-demo"
```

This creates JSON/CSV and a **textual HTML storyboard**. It does not render animation; it is not a model-backed autonomous assistant. [Other executable ZIPs](docs/RELEASES.md) offer offline engineering, planning, study and evidence workflows.

## Create a source-only agent kit

Clone and use the source wrapper—**no PYTHONPATH or pip install needed**:

```bash
git clone https://github.com/sethburkhardt21-dev/muse-ai-agent-presets.git
cd muse-ai-agent-presets
python -B quickstart.py --role personal-companion --to "$HOME/my-assistant-kit"
```

Use `python3` on macOS/Linux as appropriate. It refuses an existing destination. The created `system-profile/` contains AGENTS, IDENTITY, SOUL, USER, MEMORY, OPINION, VOICE, SYSTEM_PROMPT, TOOLS, HEARTBEAT, DOORS and ENGINE_MATRIX. Three separate `subchat-scopes/` have their own context and blank memory. `role-skills/` has eight **disabled** skill descriptors per role. No native host registration occurs.

Run `python -B quickstart.py --all` to smoke all 15 roles in temporary directories. Four new specialist engines have separate **fictional offline examples**: set `PYTHONPATH=src`, then run `python -B examples/specialist_engine_demo.py --role automation-engineer` (PowerShell: `$env:PYTHONPATH = "src"`). This reports a graph; it does not dispatch jobs.

## For AI agents and automated readers

[AI-agent discovery index](llms.txt) ? [Verified capability facts](docs/discovery/agent-capabilities.json) ? [Agent FAQ](docs/discovery/AI_AGENT_GUIDE.md).

## Choose your specialist

| Role | Useful source-based task |
| --- | --- |
| [Coordinator](presets/coordinator/) | Scope tasks, reconcile interruptions and review handoffs |
| [Software Engineer](presets/software-engineer/) | Reproduce defects, test repairs and review Git source |
| [Model Builder](presets/model-builder/) | Small synthetic model-training and evaluation examples |
| [Research Evaluator](presets/research-evaluator/) | Check quotations, held-out scores and evaluation limits |
| [Creative Studio](presets/creative-studio/) | Offline briefs, timelines and textual storyboards |
| [Adversarial Verifier](presets/adversarial-verifier/) | Defensive review methods; starter template |
| [Personal Companion](presets/personal-companion/) | Editable organization, preference and assistance methods |
| [Garden Companion](presets/garden-companion/) | Local SQLite plant records and calendar review |
| [Learning Coach](presets/learning-coach/) | Source-based study, scores and review sessions |
| [Claims Adjudicator](presets/claims-adjudicator/) | Evidence boundaries and conservative claim review |
| [Reverse Engineering & Security Researcher](presets/reverse-engineering-researcher/) | Compare supplied observations, not live targets |
| [Data Engineering & Database Architect](presets/data-engineering-architect/) | Detect duplicate keys and plan reversible schema changes |
| [Infrastructure & Reliability Engineer](presets/infrastructure-reliability-engineer/) | Calculate fictional error budgets and review incident evidence |
| [Automation Engineer](presets/automation-engineer/) | Order dependency graphs, reject cycles and plan safe retries |
| [Product & Interface Designer](presets/product-interface-designer/) | Find unlabeled controls in supplied screen descriptions |

## Fifty unique source procedures

There are **45 role-specific methods plus five shared methods**: [evidence audit](skills/shared/evidence-audit/SKILL.md), [safe resume](skills/shared/safe-resume/SKILL.md), [research verification](skills/shared/research-verification/SKILL.md), [consent/effects](skills/shared/consent-and-effects/SKILL.md), and [quality handoff](skills/shared/quality-handoff/SKILL.md). The five shared methods repeat in each export: 15×8 = 120 descriptor instances, **not 120 different skills**. They are all disabled until a real owner and native host separately configure them.

Engines differ by role: released offline executables run local programs; four new roles provide bounded source-only Python demos; others remain instruction templates. The [capability matrix](docs/CAPABILITIES.md) differentiates them. [Evidence Finder](services/evidence-finder/) is a shared service, **not another agent**.

For a portable 50-folder instruction library, run `python -B examples/export_portable_skills.py --to "$HOME/my-portable-skills"`. This uses standard hyphenated names without changing native IDs. [Details](docs/SKILLS.md#portable-instruction-library).

## Evidence, permissions and discovery

External [donor research](docs/donors/DONOR_RESEARCH.json) records pinned source references and licensing observations. No donor executable code, identity, memory or credentials are imported. Local Python execution uses your OS account, **not a security sandbox**. Family Link, connectors, hooks, schedules and external effects start disabled.

AI-facing resources: [llms.txt](llms.txt), [machine-readable capabilities](docs/discovery/agent-capabilities.json), [AI agent FAQ](docs/discovery/AI_AGENT_GUIDE.md). These aid truthful discovery but do not guarantee search results or superiority over other repositories.

[First use](docs/GITHUB_QUICKSTART.md) · [Skills](docs/SKILLS.md) · [Connectors](docs/CONNECTORS.md) · [Customization](docs/CUSTOMIZE.md) · [Releases](docs/RELEASES.md) · [Contribute](CONTRIBUTING.md). Historical [v0.2.0-alpha source ZIPs](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/releases/tag/v0.2.0-alpha) remain available.

MIT licensed.

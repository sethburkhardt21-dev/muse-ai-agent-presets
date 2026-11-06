# Muse AI Agent Presets — Specialist Assistants, Skills, Memory & Workflows

[![Source checks](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/actions/workflows/checks.yml/badge.svg)](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/actions/workflows/checks.yml)  [License: MIT](LICENSE)  [Release checklist](docs/RELEASE_CHECKLIST.md)

**An unofficial, free, open-source starter collection of configurable specialist AI assistants for Muse.** Eleven neutral role presets, a shared Evidence Finder service, safe profile templates, offline validation, and an optional Family Link proposal interface. Designed to help people build more useful Muse assistants without copying someone else's private identity or data.

> **Alpha / source-first.** These are **local drafts**, not installed Muse assistants, native skill registrations, active schedulers, live connectors, or multi-agent communications. This project is **not affiliated with or endorsed by Meta**. The name Muse is used descriptively for compatibility.

## Choose an assistant

| Preset | Focus |
| --- | --- |
| [Coordinator](presets/coordinator/) | Planning, bounded delegation, durable work and recovery |
| [Software Engineer](presets/software-engineer/) | Debugging, implementation, tests and source verification |
| [Model Builder](presets/model-builder/) | Model training, fine-tuning, LoRA/QLoRA and distillation |
| [Research & Evaluation Scientist](presets/research-evaluator/) | Independent experiments, held-out evaluations and research |
| [Creative Studio](presets/creative-studio/) | Media, animation, design and production QA |
| [Adversarial Verifier](presets/adversarial-verifier/) | Fault finding, red teaming and independent technical review |
| [Personal Companion](presets/personal-companion/) | Planning, accessible experiences and everyday assistance |
| [Garden Companion](presets/garden-companion/) | Planting, observations, calendars and seasonal planning |
| [Learning Coach](presets/learning-coach/) | Source-grounded study, assessment and adaptive practice |
| [Claims Adjudicator](presets/claims-adjudicator/) | Evidence-aware claims, qualifications and correction records |
| [Reverse Engineering & Security Researcher](presets/reverse-engineering-researcher/) | Authorized app behavior research, protocol analysis, defensive sandboxing |

**Shared service:** [Evidence Finder](services/evidence-finder/) discovers and preserves exact findings; it never makes verdicts. Each specialist includes a **Family Link adapter declaration, disabled by default**. No real cross-account service is shipped or invoked.

## Start locally in Python 3.10+

```bash
git clone https://github.com/sethburkhardt21-dev/muse-ai-agent-presets.git
cd muse-ai-agent-presets
PYTHONPATH=src python -m muse_presets.cli list
PYTHONPATH=src python -m muse_presets.cli doctor
PYTHONPATH=src python -m muse_presets.cli audit-neutrality
PYTHONPATH=src python -m muse_presets.cli render --preset garden-companion --name 'My Garden Guide' --to ./my-new-guide
PYTHONPATH=src python -m muse_presets.cli inspect --path ./my-new-guide
PYTHONPATH=src python -m muse_presets.cli family-preview --from-role garden-companion --to-role evidence-finder --request-id demo-001 --capability find
PYTHONPATH=src python -m unittest discover -s tests -v
```

### Run the shared Evidence Finder custody engine

    PYTHONPATH=src python examples/evidence_custody_demo.py

This executable, standard-library SQLite reference preserves an entire exact
UTF-8 finding with a local SHA-256 receipt chain, survives source-file
removal, distinguishes a no-hit from a fabricated finding, and refuses
tampered receipts or conflicting operation-ID reuse. It is available to all
eleven role labels plus Evidence Finder. **Role labels are not authenticated
Muse principals**, and local hashes are not signed external provenance.
See [Evidence Finder](services/evidence-finder/) and the
[public engine adoption matrix](docs/SHOWCASE_ENGINE_MATRIX.md).

### Run the durable local Garden Companion calendar example

```bash
PYTHONPATH=src python examples/garden_calendar_demo.py
```

This source-tested, standard-library SQLite workflow supports owner-scoped planting events, specialist proposals, read-only before/after review, atomic 1–21-event approval, revision fencing, durable operation IDs and readback after reopening. **The owner/Space verifier is simulated in the demo, not a native Muse authority.** See [Garden transaction contract](docs/GARDEN_LOCAL_CALENDAR.md).

### Run the nonclinical Learning Coach study workflow

```bash
PYTHONPATH=src python examples/learning_session_demo.py
```

This separately authored local SQLite engine adds owner-admitted sources, literal source-backed held cards, owner review, learner-session-bound questions, one-time scoring and durable due-review projection. The demo uses fictional content and mock host roles; **no native Muse tutor, classroom account, medical approval or scheduled reminder is implied**. See [local Learning Coach contract](docs/LEARNING_LOCAL_STUDY.md).

### Run five offline specialist examples

```bash
PYTHONPATH=src python examples/priority_slices.py
```

This runs five newly authored, bounded source-only primitives: exact evidence search, claim-scope checks, a revision-fenced garden date preview, a source-quoted learning-card draft, and deterministic comparison of **supplied** UI-observation fixtures. The examples use disposable fictional data. They do not install Muse components, contact targets, connect Family Link, run training, or claim independent review.

See [priority transfer decisions](docs/PRIORITY_TRANSFERS.md) for their relationship to the more mature separately maintained projects and what remains to integrate.

Every rendered draft now includes a role-specific `ROLE_PLAYBOOK.md` with **three methods**, evidence/stop rules, a suggested handoff, and a bounded test exercise. The instructions are carefully separated from installed skills; no new tools, hooks, subchats, models or authorizations are created. Details: [specialist capability fit audit](docs/CAPABILITY_FIT_AUDIT.md) and [genericity/provenance policy](docs/NEUTRALITY_AND_PROVENANCE.md).

The `inspect` command is read-only: it compares a draft against its self-reported versioned render receipt, distinguishes owner-customized files from source/policy drift (including `ROLE_PLAYBOOK.md`), and never repairs or installs anything. Old v1 receipts are explicitly unverified. These local hashes are **not signatures** or proof that Muse loaded the files.

The `render` command only creates new local files. It **refuses to overwrite** existing directories, including existing user memory. Nothing is installed into Muse, registered in a host, or sent to another assistant by these commands. On Windows PowerShell, use `$env:PYTHONPATH='src'` followed by the commands above without the `PYTHONPATH=src` prefix.

## What the complete project will provide

The target is an owner-configurable specialist package containing `AGENTS.md`, `SOUL.md`, `IDENTITY.md`, `USER.md`, `TOOLS.md`, `MEMORY.md`, `HEARTBEAT.md`, `PROACTIVE_PREFERENCES.md`, user-editable custom instructions, skills, subchat role contracts, hooks, scripts, Space assets, connector recipes, state persistence, recovery procedures and verification evidence. These capabilities are **planned and graded individually**; a file present does not mean Muse loads or executes it.

The project uses two separate host profiles:

- **Personal Muse/Hatch:** primary target; native file loading, skill discovery, Spaces, callbacks, scheduling and permissions must be proved on the receiving account.
- **Muse Code:** optional developer-host target; its plugin and MCP formats are different and still require separate review and native testing. See [host compatibility](docs/HOST_COMPATIBILITY.md).

Start with the [architecture](docs/ARCHITECTURE.md), [five-layer proof and execution doors](docs/FIVE_LAYERS_AND_DOORS.md), [presets and capability transfer decisions](docs/PRIORITY_TRANSFERS.md), [Family Link](docs/FAMILY_LINK.md), and [roadmap](docs/ROADMAP.md).

## Security, rights and scope

The public repository contains **only newly authored generic starter code and documentation**. The specialist engines from separate development projects are **mapped for later review, not copied here**. No proprietary SDK snapshot, account credentials, malware sample, private chat, personal memory, private image/ROM, model weights or external connector tokens are included. External repos are linked in a [review queue](docs/COMMUNITY_RESEARCH.md) and [per-role connector intake map](docs/COMMUNITY_ROLE_INTEGRATIONS.md), with licensing and host-compatibility obligations before reuse.

- [Install, personalize and preserve state](docs/INSTALL_AND_PERSISTENCE.md)
- [Source status](docs/STATUS.md)
- [Security policy](SECURITY.md)
- [Contributing](CONTRIBUTING.md)

**Keywords:** Muse AI assistant presets · Muse agent skills · specialist AI agents · Muse Code skills · AI agent workflows · agent memory · multi-agent handoffs · optional connectors · Family Link · model training · security research · study coach · garden assistant.

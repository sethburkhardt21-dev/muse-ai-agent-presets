# Muse AI Agent Presets — Specialist Assistants, Skills, Memory & Workflows

[![Source checks](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/actions/workflows/checks.yml/badge.svg)](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/actions/workflows/checks.yml)  [License: MIT](LICENSE)  [Release checklist](docs/RELEASE_CHECKLIST.md)

**An unofficial, free, open-source starter collection of configurable specialist AI assistants for Muse.** Eleven neutral role presets, a shared Evidence Finder service, safe profile templates, offline validation, and an optional Family Link proposal interface. Designed to help people build more useful Muse assistants without copying someone else's private identity or data.

> **Alpha / source-first with tested local engines.** Generic profiles are local drafts; selected roles now include independently tested source-only engines. Nothing is an installed Muse assistant, native skill registration, active scheduler, live connector, or cross-account communication. This project is **not affiliated with or endorsed by Meta**. The name Muse is used descriptively for compatibility.

**GitHub delivery target:** [scope and acceptance gates](docs/GITHUB_RELEASE_SCOPE.md).
Source-only release does not require an authenticated native Muse/Hatch host.
The [portable connector contract](docs/R44_PORTABLE_CONNECTORS.md) is
tested locally; desktop/SSH/browser providers are declared but not connected.

For a source-only capability audit that distinguishes actual local engine
execution from template-only roles and POSIX-only features, run
PYTHONPATH=src python3 -B examples/verify_role_packages.py --all.
See [eleven-role clean-clone acceptance](docs/GITHUB_ROLE_ACCEPTANCE.md)
for the current scope and platform limitations.

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

## GitHub zero-to-one quickstart (R45)

The eleven source kits now have a tested, offline GitHub quickstart and
individual setup guides. No Muse account, native host registration or
paid connector is required to create and inspect them. An optional
real-host integration remains **not connected** unless configured later.

From a checkout containing R45 (the public repository is still at an
older alpha until its verified release), run:

    PYTHONPATH=src python3 -B examples/github_quickstart.py --all
    PYTHONPATH=src python3 -B examples/github_quickstart.py --role garden-companion --to ../new-garden-companion

Windows PowerShell: set $env:PYTHONPATH='src' and use python instead
of python3. See [tested GitHub quickstart](docs/GITHUB_QUICKSTART.md),
[extension and recovery guide](docs/EXTENDING_GENERIC_AGENTS.md), and
[release gates](docs/GITHUB_RELEASE_SCOPE.md). --all is a disposable
smoke check; --to creates a new source folder and never overwrites one.

## Other starter commands in Python 3.10+

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

### Optional native-host fixture packets (not required for GitHub source release)

The generic project can now create **disposable source-only acceptance packets**
for each role and for the two separate receiving host profiles. This is a
working, create-only packaging and validation path; it does **not** install a
skill or authenticate to any existing personal agent.

```bash
PYTHONPATH=src python -B -m muse_presets.cli generic-native-canary --preset software-engineer --host personal-hatch --to ./new-generic-host-packet
PYTHONPATH=src python -B -m muse_presets.cli generic-native-inspect --path ./new-generic-host-packet
```

The packet contains exact role source SHA-256 pins, a proposed skill identifier,
a disposable challenge, a host-boundary runbook and a fail-closed receipt.
Fixture evidence checks can reject replayed or mismatched events, but never
claim native WIRED/USED/USEFUL.

To assemble the **entire neutral fleet** (11 standalone profile drafts and
22 disposable host acceptance packets) in one new folder:

```bash
PYTHONPATH=src python -B -m muse_presets.cli generic-native-fleet --to ./new-generic-fleet
PYTHONPATH=src python -B -m muse_presets.cli generic-native-fleet-inspect --path ./new-generic-fleet
```

See [generic native acceptance](docs/GENERIC_NATIVE_ACCEPTANCE.md) for the
exact source and native-host proof boundaries.

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

### Run the shared Evidence Finder custody workflow

The Evidence Finder is a shared source service for all eleven neutral specialists, not a twelfth autonomous assistant. Its new, **local durable evidence ledger** preserves exact findings across restarts and records honest no-hit receipts with replay fencing and tamper-detecting local SHA-256 links.

    PYTHONPATH=src python examples/evidence_ledger_demo.py

This uses only synthetic files and a temporary SQLite database. It has no source-owner authentication, external chain anchor, verdict, native Muse tool registration or cross-account delivery. See [Evidence Finder custody](docs/EVIDENCE_LEDGER.md) and the [general-purpose specialist capability map](docs/GENERIC_SPECIALIST_SHOWCASE.md).

### Stage the executable Software Engineer claim and recovery pack

On any machine, this creates a new source-only pack without overwriting owner memory:

    PYTHONPATH=src python -m muse_presets.engineering_pack --to ./my-software-engineer

On POSIX/Python 3.12+, the synthetic demo exercises the original-source-neutralized Claim Gate with atomic claims, fencing, approval primitives and held-UNKNOWN recovery:

    PYTHONPATH=src python examples/software_engineer_claim_gate_demo.py

The engine uses POSIX fcntl locking; **native Windows execution is not supported**. Staging does not call Muse, run external effects, grant permissions or activate schedulers. See [Software Engineer engine pack](presets/software-engineer/INSTALL.md).

### R33: stage the generic Model Builder development verifier

Model Builder now includes two executable, standard-library local skills:
bounded development accuracy scoring and synthetic checkpoint-byte SHA-256
verification. The verifier refuses train/dev/final source-family leakage,
exposed protected-final labels, forged optimizer steps, fake weights and
unapproved data rights. **No GPU, training or real model inference runs.**

    PYTHONPATH=src python -B -m muse_presets.cli model-builder-dropin --to ./new-model-builder
    PYTHONPATH=src python -B -m muse_presets.cli model-builder-dropin-inspect --path ./new-model-builder
    python -I -B ./new-model-builder/custom-skills/model_development_metrics/run.py --operation demo

See [R33 Model Builder source-only package](docs/R33_MODEL_BUILDER_DROPIN.md)
for metrics, protected holdout, checkpoint and native-host boundaries.

### R33: stage the generic Coordinator with a real offline reviewer

Coordinator now has its own independent create-only native-format source
bundle, two locally executable skill scripts, three meaningful subchat role
contracts, disabled native skill registrations and a source-pinned
workgraph/verification engine. It validates task budgets, cycles, distinct
reviewers, source hashes and UNKNOWN-effect holds without dispatching a
mission, impersonating an original agent or claiming provider authority.

    PYTHONPATH=src python -B -m muse_presets.cli coordinator-dropin --to ./new-coordinator
    PYTHONPATH=src python -B -m muse_presets.cli coordinator-dropin-inspect --path ./new-coordinator
    python -I -B ./new-coordinator/custom-skills/coordinator_workgraph/run.py --operation demo

Details: [R33 Coordinator source-only drop-in](docs/R33_COORDINATOR_DROPIN.md).

### R33: stage the richer generic Software Engineer drop-in

The first role-specific native-format package can now stage real source-pinned
Claim Gate/Vault/Iron code, a standalone local canary and offline doctor, neutral
system-file drafts, three bounded custom skills, three scoped subchat
role/context/memory contracts, a **disabled** skill registry and hooks OFF.
This is an independent generic package; it does not modify any original agent.

    PYTHONPATH=src python -B -m muse_presets.cli engineer-dropin --to ./new-engineer-dropin
    PYTHONPATH=src python -B -m muse_presets.cli engineer-dropin-inspect --path ./new-engineer-dropin

See [R33 Software Engineer source-only drop-in](docs/R33_SOFTWARE_ENGINEER_DROPIN.md)
for the real POSIX local canary, Windows limitations, installation boundaries,
source-release privacy gates; optional native-host acceptance is not required for GitHub source.

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

The public repository contains neutral generic starter code and an explicitly source-derived, neutralized Software Engineer Claim Gate implementation. Its original developer identity, owner paths, private profiles and runtime records are excluded. This is the first tested transferable engine slice; other original specialist engines remain mapped for later qualification. Source authorship and third-party provenance must remain auditable before further redistribution. No proprietary SDK snapshot, account credentials, malware sample, private chat, personal memory, private image/ROM, model weights or external connector tokens are included. External repos are linked in a [review queue](docs/COMMUNITY_RESEARCH.md) and [per-role connector intake map](docs/COMMUNITY_ROLE_INTEGRATIONS.md), with licensing and host-compatibility obligations before reuse.

- [Install, personalize and preserve state](docs/INSTALL_AND_PERSISTENCE.md)
- [Source status](docs/STATUS.md)
- [Security policy](SECURITY.md)
- [Whole-distribution privacy gate and release-review policy](docs/PRIVACY_RELEASE_ASSURANCE.md)
- [Contributing](CONTRIBUTING.md)

**Keywords:** Muse AI assistant presets · Muse agent skills · specialist AI agents · Muse Code skills · AI agent workflows · agent memory · multi-agent handoffs · optional connectors · Family Link · model training · security research · study coach · garden assistant.

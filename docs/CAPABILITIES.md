# Capabilities

This page describes the code on the public main branch. A downloaded ZIP contains the code from its release, so use the instructions included with that package. [Downloads](RELEASES.md) explains the choices.

## Choose a tool or profile

| Specialist | Available here | Limits |
| --- | --- | --- |
| `coordinator` | Review task plans, dependencies and supplied completion evidence; export a standalone tool. | Does not dispatch workers or run a scheduler. |
| `software-engineer` | Stage code with hash checks; run reviewed repairs and tests in disposable Git repositories; export the runtime. | Not an OS sandbox or unattended deployment service. |
| `model-builder` | Train small synthetic models, calculate held-out metrics and inspect local model artifacts. | No GPU service or large-model fine-tuning. |
| `research-evaluator` | Match quotations to supplied text; score predictions and check group leakage. | Does not authenticate publishers or establish scientific truth. |
| `creative-studio` | Build production briefs, shot timelines, continuity records and textual storyboards. | Does not render images or video or clear third-party rights. |
| `adversarial-verifier` | Defensive review instructions and refusal-test patterns. **Template only** as a standalone public package. | No autonomous testing or third-party access. |
| `personal-companion` | Editable preferences, identity and everyday-assistance methods. **Template only** in the public package. | No live reminders, connected accounts or hosted assistant. |
| `garden-companion` | Record observations and review local calendar changes in SQLite. | No external calendar writes or biological diagnosis. |
| `learning-coach` | Build source-based study sessions, score practice and store review history. | No clinical approval or independent mastery assessment. |
| `claims-adjudicator` | Review claims against supplied evidence and record qualifications. | Not an independently authenticated verdict. |
| `reverse-engineering-researcher` | Compare supplied application-observation records. | No live capture, network probing or attack engine. |

The [Evidence Finder](../services/evidence-finder/) preserves local findings for these tools. It is a shared service, not another assistant.

## Run an example

[Workflows](WORKFLOWS.md) provides the commands and expected results. Start with `examples/research_evaluator_demo.py` for quotation checks, `examples/numeric_evaluation_demo.py` for scoring, or `examples/software_engineer_workflow_demo.py` for a disposable repair exercise.

The `research-numeric` result `LOCAL_NUMERIC_HELDOUT_EVALUATED` means the supplied data passed the numerical checks. It does not prove the truth of a scientific hypothesis. The [capability catalog](../presets/capabilities.json) connects declared features to their modules and examples.

## Requirements and permissions

Use Python 3.12+. Git is required for repository workflows; individual packages document other prerequisites. Core tools support Windows, macOS and Linux, with platform-specific limitations. Swift typechecking needs an installed Swift toolchain on macOS.

Reviewed code executes under your OS account and can access its files and network. Explicit execution consent is **not a sandbox**. Local handoff, plan and restart utilities do not authenticate another account or authorize an external action.

These are source-only distributions: runnable code and editable profiles, not a hosted service or installed native assistants. [Host compatibility](HOST_COMPATIBILITY.md) explains the separate integration checks.

## Standalone offline packages

| Package | Guide |
| --- | --- |
| Creative Studio | [Build, verify and run](kits/CREATIVE_SOURCEKIT.md) |
| Claims Adjudicator | [Build, verify and run](kits/CLAIMS_SOURCEKIT.md) |
| Garden Companion | [Build, verify and run](kits/GARDEN_SOURCEKIT.md) |
| Learning Coach | [Build, verify and run](kits/LEARNING_SOURCEKIT.md) |
| Reverse Engineering & Security Researcher | [Build, verify and run](kits/REVERSE_SOURCEKIT.md) |
| Coordinator, Software Engineer and Model Builder | [Runnable workflows](WORKFLOWS.md) |

[Get started](GITHUB_QUICKSTART.md) · [Downloads](RELEASES.md) · [Security](SECURITY.md)

# Capabilities

This page describes the code on the public main branch. A downloaded ZIP contains the code from its release, so use the instructions included with that package. [Downloads](RELEASES.md) explains the choices.

The source provides **15 profiles and 50 unique instruction procedures**. The unchanged **v0.4.1-alpha** download contains **eight executable ZIPs and eleven starter profiles**. The four newer roles have source-tree offline examples, not new tagged executable packages or native agents.

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
| `data-engineering-architect` | Check supplied rows and keys; report duplicates and null observations. | No live database access, migration or lineage certification. |
| `infrastructure-reliability-engineer` | Calculate failure fractions and error-budget use from supplied synthetic events. | No live monitoring or production reliability certification. |
| `automation-engineer` | Produce stable dependency order; reject cycles, duplicate IDs and unknown prerequisites. | Does not schedule jobs, run adapters or prove external idempotency. |
| `product-interface-designer` | Flag missing control labels in supplied screen descriptions. | Not a rendered-browser, screen-reader or human usability audit. |

The [Evidence Finder](../services/evidence-finder/) preserves local findings for these tools. It is a shared service, not another assistant.

## Run an example

[Workflows](WORKFLOWS.md) provides the commands and expected results. Start with `examples/research_evaluator_demo.py` for quotation checks, `examples/numeric_evaluation_demo.py` for scoring, or `examples/software_engineer_workflow_demo.py` for a disposable repair exercise.

The `research-numeric` result `LOCAL_NUMERIC_HELDOUT_EVALUATED` means the supplied data passed the numerical checks. It does not prove the truth of a scientific hypothesis. The [capability catalog](../presets/capabilities.json) connects declared features to their modules and examples.

For the four newer roles, run `PYTHONPATH=src python3 -B examples/specialist_engine_demo.py --role automation-engineer` from the source checkout, substituting one of the four role IDs above. On PowerShell, set `$env:PYTHONPATH = "src"` and use `python`. The demo processes a fictional fixture and returns explicit offline-only evidence. Skill text alone does not execute these engines.

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

## Richer task collection, without replacing the original fixtures

The [75-skill collection](collection/MUSE_CURATED_COLLECTION.md) reuses eleven bounded local implementations across four standalone toolkits. `python -B tools/muse_collection.py demo data-engineer` runs logical schema comparison, versioned-event reconciliation and supplied-query-plan classification. The other toolkit IDs are `reliability-engineer`, `automation-engineer` and `product-interface-designer`; their actual operations and limits are in the [specialist quickstart](collection/SPECIALIST_QUICKSTART.md).

These tools complement the simpler source fixtures above; they do not rename existing public role IDs or establish native integration. Five workflow demos run only their local registered stages and explicitly report the remaining host/human handoffs. A 100-starter bundle selects instructions rather than creating agents. Existing tagged release assets remain unchanged.

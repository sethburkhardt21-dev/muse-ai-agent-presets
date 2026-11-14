# Select and use a skill without installation theater

A skill is a reusable method. Some skills link runnable code; some are instruction-only. A descriptor tells a system about a method, while an authenticated host decides whether and how it is available. None of these automatically grants a connector or permission to send, buy, deploy or delete.

## First useful result

From this repository, with Python 3.12 or newer, inspect a useful task starter:

```sh
python -B tools/muse_collection.py check
python -B tools/muse_collection.py show daily-planner
python -B tools/muse_collection.py build daily-planner --to "$HOME/daily-planner.zip"
```

Use `python3` where that is the interpreter name. Choose a new destination. Read the resulting PROFILE.md and selected skill instructions, or attach the ZIP through your assistant's supported attachment flow. Ask it to apply the relevant method to your current task while preserving your existing preferences and memory. The starter's sample task is an example, not an instruction to replace your real request.

A fictional first task: **I have two fixed appointments, one report and ninety minutes of flexible time. Use the daily-planning method to propose a realistic plan. Do not edit my calendar or create reminders.** The output is a proposal, not an existing calendar event.

## Understand the two source formats

The task collection contains 75 authored skills, 25 optional workflows and 100 starter selections. Separately, the existing profile exporter has 50 role/shared procedures. Their overlap is documented; these are not 125 distinct capabilities. The old identifiers and exporters remain usable.

`SKILL.md` contains the method. The public profile generator's `skill.yaml` describes a native-style source entry, and its `skills.yaml` is a proposed registry that starts disabled. A native registry entry, model selection and an observed tool invocation are separate stages. The portable exporter instead emits standard-format folders for compatible instruction readers. Use the format your receiving host actually supports; never rename a live registry behind its back.

## Verify

For source-package inspection run:

```sh
python -B tools/collection_compatibility.py
python -B examples/export_portable_skills.py --plan
```

The first checks the 75-skill collection's source relationship to the preserved public profiles. The second still previews the original 50-procedure portable library. Neither is a native install. For a runnable example, `python -B tools/muse_collection.py demo data-engineer` produces real local calculations on authored inputs, with no model or external effect.

When using instructions with an assistant, inspect the actual task result against the method's output contract. If available, preserve the provider's actual skill-discovery or tool event. Do not infer native use merely because the assistant repeats the skill title.

## Failure and recovery

An existing output file is preserved and the exporter refuses replacement. Create a new version, inspect it, then reconcile customizations. If a method asks for an unavailable connector, use supplied material where useful and disclose the missing evidence. Do not paste passwords or run an unreviewed remote installer. A changed manifest indicates a changed package; do not reseal it merely to hide unexplained drift.

## Scope and evidence

The source checks and offline examples are reproducible repository behavior. Real native discovery, persistence and permission controls must be observed through the receiving host. [Skills](../SKILLS.md), [the collection guide](../collection/MUSE_CURATED_COLLECTION.md) and [capability boundaries](source-and-host-capabilities.md) describe the distinction.

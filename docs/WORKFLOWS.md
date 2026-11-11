# Runnable workflows

Run from the repository root with Python 3.12+ and Git. No paid API or native Muse account is needed for these examples. All data fixtures are synthetic.

**macOS/Linux:** prefix commands with `PYTHONPATH=src python3 -B`.

**Windows PowerShell:** set `$env:PYTHONPATH = "src"`, then use `python -B`.

## Research quotations and held-out scores

```bash
PYTHONPATH=src python3 -B examples/research_evaluator_demo.py
PYTHONPATH=src python3 -B examples/numeric_evaluation_demo.py
```

The first verifies exact quotation bytes and locations, checks disjoint source families, and refuses modified source. The second calculates local metrics and checks group leakage and prediction commitments.

To evaluate your own reviewed input file:

```bash
PYTHONPATH=src python3 -B -m muse_presets.cli research-trace --file /absolute/case.json
PYTHONPATH=src python3 -B -m muse_presets.cli research-numeric --file /absolute/predictions.json
```

These are numerical and source-integrity checks, not scientific verification. A local prediction digest establishes consistency, **not historical timing** or independent reviewer identity. Read the example files for the accepted schema.

## Engineering: reproduce, repair, review

```bash
PYTHONPATH=src python3 -B examples/software_engineer_workflow_demo.py
```

The fixture creates a disposable repository, reproduces an assertion failure, applies a source-bounded repair, runs the passing tests and independently reviews the result. It uses the existing Claim Gate rather than creating another task controller.

**Only execute code you have reviewed.** A disposable Git directory is not OS isolation. The process retains the permissions of your local account.

## Builder delivery

```bash
PYTHONPATH=src python3 -B examples/builder_delivery_demo.py
PYTHONPATH=src python3 -B -m muse_presets.cli builder-plan --help
PYTHONPATH=src python3 -B -m muse_presets.cli builder-stage --help
PYTHONPATH=src python3 -B -m muse_presets.cli builder-run --help
```

Staging requires `--allow-disposable-stage`; execution separately requires `--allow-reviewed-execution`. Existing output folders and ambiguous interrupted effects are held for inspection. The example runs a real local Python test. On a supported Mac, it also typechecks Swift source with `swiftc`; it does not build, sign or deploy an Apple application.

## Portable executable kits

Choose a new absolute ZIP destination. These exports refuse to overwrite an existing file.

```bash
PYTHONPATH=src python3 -B examples/export_coordinator_sourcekit.py --to /absolute/coordinator.zip
PYTHONPATH=src python3 -B examples/export_software_engineer_sourcekit.py --to /absolute/software-engineer.zip
PYTHONPATH=src python3 -B examples/export_model_builder_sourcekit.py --to /absolute/model-builder.zip
```

Each kit includes a start guide, a bounded local example and file-integrity metadata. The Model Builder kit contains small deterministic training, model packaging and opt-in install/recovery tools. Its generated guide explains the supported training commands. This is not large-model training or a remote inference service.

## Restart and handoff review

```bash
PYTHONPATH=src python3 -B examples/continuum_checkpoint_demo.py
PYTHONPATH=src python3 -B examples/family_offline_handoff_demo.py
PYTHONPATH=src python3 -B examples/omnium_plan_only_demo.py
```

The restart example saves JSON and reloads it in a separate process. Handoff review preserves receiver context and supplied replay/revocation declarations. The plan preview holds absent worker adapters. These are local consistency checks—not authenticated consent, durable cross-account replay protection or worker dispatch.

## Garden, study and evidence

```bash
PYTHONPATH=src python3 -B examples/garden_calendar_demo.py
PYTHONPATH=src python3 -B examples/learning_session_demo.py
PYTHONPATH=src python3 -B examples/evidence_ledger_demo.py
```

These examples exercise local SQLite persistence and recovery. They do not send calendar events, enroll a native tutor or authenticate a remote source owner.

[Capabilities](CAPABILITIES.md) · [Customize](CUSTOMIZE.md) · [Development](DEVELOPMENT.md)

## Package an offline specialist

The five [standalone kit guides](CAPABILITIES.md#standalone-offline-packages) cover Creative Studio, Claims, Garden, Learning and observation comparison.
For example, from a source checkout:

```bash
PYTHONPATH=src python3 -B examples/export_garden_sourcekit.py --to ../garden-kit.zip
```

Verify the archive digest before extraction into a new directory. Follow the kit guide for its exact runner command.

## Creative Studio: compile a textual production board

Use `PYTHONPATH=src python3 -B examples/export_creative_sourcekit.py --to ../creative-studio.zip` to create a new ZIP. Verify its SHA-256 and extract into a fresh directory, then run `python -I -B run.py --operation self-test` and `python -I -B run.py --operation demo --to /absolute/new/production`. The output includes a JSON production plan, CSV shot list and textual HTML storyboard—not an image or animation render. See [the source-kit guide](kits/CREATIVE_SOURCEKIT.md).

## Inspect optional local adapters

```bash
PYTHONPATH=src python3 -B -m muse_presets.cli donor-list
PYTHONPATH=src python3 -B -m muse_presets.cli donor-inspect --capability garden
```

Five adapters reuse reviewed local engines. Synthetic execution requires an explicit opt-in; animation remains source-link-only with no bundled renderer.

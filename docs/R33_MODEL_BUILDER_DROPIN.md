# R33 Model Builder — standalone generic source-only evaluation package

This is the third generic specialist with locally executable role-specific
logic, distinct from Coordinator and Software Engineer. It is not an
original personal Muse agent, a real trainer or a signed publisher release.

## Stage and inspect from source

    PYTHONPATH=src python -B -m muse_presets.cli model-builder-dropin --to ./new-model-builder
    PYTHONPATH=src python -B -m muse_presets.cli model-builder-dropin-inspect --path ./new-model-builder

Use a new, absent directory whose parent already exists. No existing
owner memory, registry, model state or files are overwritten. A failure
leaves STAGING_INCOMPLETE for inspection rather than silently retrying.

## Actual executable functions

The package includes two local Python source skills that use **only the
standard library** and do not connect to a model provider:

- **model_development_metrics** computes measured local accuracy for
  candidate and baseline binary predictions on a bounded development
  partition (up to 64 records). It rejects duplicate examples, train/dev/
  protected-final source-family contamination and malformed records.
  Protected final labels and predictions MUST NOT appear; the final set
  remains HELD_UNEVALUATED.
- **model_checkpoint_verifier** computes SHA-256 of actual supplied
  synthetic checkpoint bytes (1–4096 bytes) and matches a strict
  source/lineage manifest. Optimizer steps must be zero and weights_trained
  false. This is **not** evidence of an actual training run, valid weights,
  source rights, signer, model quality or an independent evaluator.

Run the zero-spend synthetic development/checkpoint demonstration:

    python -I -B ./new-model-builder/custom-skills/model_development_metrics/run.py --operation demo

Expected status: LOCAL_MODEL_BUILDER_DEMO_PASSED, two development records
scored, synthetic byte SHA-256 matched and no native/tool/external effects.
For real permitted offline input, send a strictly bounded JSON document
via standard input and --operation evaluate or --operation checkpoint,
using the schemas in src/muse_presets/model_eval.py. The checkpoint input
contains exactly manifest and bytes_base64 fields. Any forged training,
rights clearance or source receipt is rejected. This package does not
evaluate protected final records.

## Native-format package contents

- profile/: neutral owner-editable profile and first canary.
- system-files/: AGENTS, SOUL, IDENTITY, USER, TOOLS, MEMORY,
  HEARTBEAT, SYSTEM_INSTRUCTIONS and CONNECTORS/BROWSER/VOICE policies.
- subchats/: data-custody, development-evaluation and artifact-verification,
  each with independent ROLE/CONTEXT/TOOLS/MEMORY/SUBCHAT.json. Native chat
  IDs and per-host registration remain null/unbound.
- custom-skills/: the two actual local run.py scripts with their SKILL.md
  and skill.yaml. They are disabled in config/skills.yaml.
- runtime/model_eval.py: local scorer and SHA-256 verifier source.
- scripts/doctor.py: closed-tree read-only **self-hash** checker.
  It is not a publisher-issued signature.
- config/host-binding.json and hooks/HOOKS.json: no owner identity,
  no native tool grant, no training, no cron and no external effects.
- receipts/MODEL_BUILDER_RECEIPT.json: exact local source hashes and
  fail-closed, uninstalled status.

## Qualification boundaries

No LoRA/QLoRA, optimizer process, GPU training, paid model, model download,
real weights, real inference or external dataset is used. Development
accuracy on caller-provided predictions cannot establish model gains.
Final protected examination must be performed once by an independently
authorized evaluator with genuine source identity and a trusted result
receipt. Source-only digest consistency never establishes licensing.

A genuine receiving Muse/Hatch owner account must separately establish
native profile loading, registered skill discovery, actual model-selected
tool execution, real subchat IDs, wrong-owner denial, recipient readback,
restart/rollback and source rights. Muse Code is a separate host target.
Do not install this pack into or repair original donor agents.

## Operating recovery

The stager is create-only; refuse an occupied destination. On partial
staging, reconcile before retry. An actual receiver upgrade, migration,
uninstall, training job or model placement is not implemented here and
requires supported host APIs plus explicit owner approval. Keep all source
rights and native-use gates open until independently verified.

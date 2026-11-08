# Model Builder — source-only native-format package

This independent neutral specialist includes local metric measurement and
checkpoint bytes verification. It does **not** perform optimizer steps,
train LoRA/QLoRA adapters, execute real model inference, use CUDA, fetch
datasets, approve data rights, evaluate the protected final set or install
anything in Muse.

From the generic repository root:

    PYTHONPATH=src python -B -m muse_presets.cli model-builder-dropin --to ./new-model-builder
    PYTHONPATH=src python -B -m muse_presets.cli model-builder-dropin-inspect --path ./new-model-builder

Run a real local standard-library synthetic canary:

    python -I -B ./new-model-builder/custom-skills/model_development_metrics/run.py --operation demo

The other skill verifies a 1–4096-byte synthetic artifact against SHA-256
with optimizer_steps=0. It does not treat bytes or self hashes as licensed,
trained model weights.

All three subchat contracts are unbound. Both custom skills are disabled
in the package-local skills.yaml, hooks/cron are off and host identity
is absent. The installer is create-only and protects existing owner files.

See [full procedures](../../docs/R33_MODEL_BUILDER_DROPIN.md).

## GitHub source-only quickstart (R45)

From the repository root with PYTHONPATH=src, run:

    python -B examples/github_quickstart.py --role model-builder --to ../new-model-builder

The destination must not exist. This stages and inspects the neutral
source profile/subchats/disabled skills and runs a local synthetic
connector fixture. It does not install a native Muse agent or enable
a provider. See [GitHub quickstart](../../docs/GITHUB_QUICKSTART.md)
and [extension methods](../../docs/EXTENDING_GENERIC_AGENTS.md).

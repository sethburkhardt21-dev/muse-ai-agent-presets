# Coordinator — independent generic native-format source package

This Coordinator has two REAL offline skill procedures: workgraph review and
evidence assertion review. It is a different role from Software Engineer
and does not require original donor engines or accounts.

Stage a fresh folder from repository root:

    PYTHONPATH=src python -B -m muse_presets.cli coordinator-dropin --to ./new-coordinator
    PYTHONPATH=src python -B -m muse_presets.cli coordinator-dropin-inspect --path ./new-coordinator

Run a synthetic, local graph canary:

    python -I -B ./new-coordinator/custom-skills/coordinator_workgraph/run.py --operation demo

No native Muse session or tool call is implied. The receiving owner must
separately approve actual installation, host-loaded system instructions,
skill discovery, subchat identity, granted tools and original recipient
readback. The role-local config/skills.yaml explicitly disables both skills.

See [detailed usage, security and limits](../../docs/R33_COORDINATOR_DROPIN.md).

## GitHub source-only quickstart (R45)

From the repository root with PYTHONPATH=src, run:

    python -B examples/github_quickstart.py --role coordinator --to ../new-coordinator

The destination must not exist. This stages and inspects the neutral
source profile/subchats/disabled skills and runs a local synthetic
connector fixture. It does not install a native Muse agent or enable
a provider. See [GitHub quickstart](../../docs/GITHUB_QUICKSTART.md)
and [extension methods](../../docs/EXTENDING_GENERIC_AGENTS.md).

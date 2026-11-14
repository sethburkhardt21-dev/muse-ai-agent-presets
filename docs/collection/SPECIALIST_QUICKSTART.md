# Start with a useful result

## Run a specialist locally

Use a current source checkout and Python 3.12 or newer. These commands work from the repository root in PowerShell, macOS Terminal or a Linux shell; no `PYTHONPATH` setup is required for the collection commands.

```sh
python -B tools/muse_collection.py specialists
python -B tools/muse_collection.py demo data-engineer
python -B tools/muse_collection.py demo reliability-engineer
python -B tools/muse_collection.py demo automation-engineer
python -B tools/muse_collection.py demo product-interface-designer
```

Use `python3` in place of `python` where that is the installed interpreter name.

| Demonstration | What actually runs |
| --- | --- |
| Data engineering | Logical schema comparison, atomic versioned-event reconciliation and supplied SQLite plan classification. |
| Reliability | Event-ratio error budget, decimal capacity sizing and offset-aware incident timing. |
| Automation | Dependency/approval declaration review, locator observation selection and supplied effect-evidence consistency checks. |
| Interface design | Opaque sRGB contrast calculations and deterministic declared-state graph coverage. |

Each demonstration prints JSON containing the exact skill ID, input digest, actual calculated output and scope. The inputs are authored examples, not live account data. No model, API, database mutation, browser action or infrastructure change is performed.

## Take an executable kit with you

```sh
python tools/muse_collection.py kit data-engineer --to ./data-engineer.zip
```

Extract the ZIP into a new directory, then run:

```sh
python run.py --demo
```

The extracted kit needs only Python 3.10 or newer; it does not import the source repository. It includes a role contract, playbook, relevant skill guides, worked input records and the actual executable module closure. `MANIFEST.json` verifies package self-consistency before imports; it is not a publisher signature.

For your own schema input, save this as `schema.json` in the extracted kit:

```json
{
  "current": [{"name": "id", "type": "integer", "nullable": false}],
  "proposed": [
    {"name": "id", "type": "integer", "nullable": false},
    {"name": "note", "type": "text", "nullable": true}
  ],
  "row_count": 40
}
```

Then run:

```sh
python run.py --tool schema-evolution --input schema.json
```

The result identifies `note` as added and requires no backfill under this logical contract. Database locks, defaults, indexes, consumer compatibility and an actual migration remain separate questions.

## Use a starter with your existing assistant

Choose from the [starter catalog](../../collections/muse-starters-v1/CATALOG.md), inspect the selection, and export it:

```sh
python tools/muse_collection.py show data-cleaner
python tools/muse_collection.py build data-cleaner --to ./data-cleaner-starter.zip
```

A starter ZIP contains the relevant instructions and public practice materials. It is not a new assistant identity or automatic native installation. Give your assistant the selected playbook and relevant skills, then ask it to apply them to your current task with its actual supported tools. Its existing preferences, memory and permissions stay intact.

Four starters now select the new toolkits: `data-cleaner`, `operations-analyst`, `customer-support-designer` and `frontend-partner`. Their original base-role IDs remain compatible.

## Try a cross-specialist workflow

```sh
python tools/muse_collection.py workflow-demo pipeline-validation
python tools/muse_collection.py workflow-demo incident-recovery
python tools/muse_collection.py workflow-demo interface-quality
python tools/muse_collection.py workflow-demo automation-readiness
python tools/muse_collection.py workflow-demo product-to-implementation
```

These commands execute the registered local calculation/review stages. The JSON explicitly lists `unexecuted_skills` for existing host or human handoffs and keeps `full_workflow_executed` false. To complete a real task, use those outputs with the original qualified executor, actual target permissions and observed result readback.

## Save a report without overwriting work

```sh
python tools/muse_collection.py demo reliability-engineer --to ./capacity-and-incident-report.json
```

The parent directory must already exist and the destination must be new. A collision is a refusal, not permission to replace a user's file.

## Build the complete downloadable collection

```sh
python -B examples/export_specialist_collection.py --to ./Muse_Specialist_Collection.zip
```

This builds and reopens all 100 starter archives and the four new executable kits, then includes nine actual local demonstration reports. The original eleven engine sourcekits keep their existing export routes; the bundle does not claim to rebuild them or install 15 native assistants.

The earlier development CI retained collection artifacts; this promotion does not change the public CI workflow or promise a retained download. Build the exact bundle locally with the command above. Older public release assets do not change automatically. The command above reproduces a fresh bundle locally without a hosted service.

## Common problems

**The command cannot find the tool:** run from the repository root or use the absolute path to `tools/muse_collection.py`. Older release assets may not include the new extension commands.

**The JSON input is rejected:** use one input object for the selected tool, not the whole `EXAMPLE.json` wrapper. Keep integer fields as integers and decimal measurement fields as strings. Duplicate keys, nonfinite numbers and unknown fields are refused.

**The kit says a member changed:** compare it with the original export and preserve your edits separately. Do not rewrite the manifest merely to make an unknown package pass.

**You need a live operation:** the local reports do not grant access or execute that operation. Use the existing supported host and its actual approval, target and effect controls.

Continue with the [15-specialist catalog](SPECIALIST_CATALOG.md), [original role quickstart](../GITHUB_QUICKSTART.md) or [source-versus-host guide](../handbook/source-and-host-capabilities.md).

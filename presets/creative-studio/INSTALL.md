# Set up Creative Studio

Use Python 3.12+ and Git. These are portable source files, not a native Muse installation.

## From the repository

```bash
PYTHONPATH=src python3 -B examples/github_quickstart.py --role creative-studio --to "$HOME/my-creative-studio"
```

On Windows PowerShell, set `$env:PYTHONPATH = "src"` and use `python`. Choose a new output directory; existing files are never overwritten. The source kit and its local inspection result do not authenticate a native host or grant tool access.

## From a download

Extract the ZIP into a new directory and follow its included guide. Keep existing user memory separate. For the latest runnable features, use current repository source and [the workflow guide](../../docs/WORKFLOWS.md).

Use this neutral source profile with the optional offline Creative Studio planner. No image/animation renderer or creative provider is bundled.

The local receipt is an integrity check, not a native installation or authenticated publisher signature. Optional connectors remain disconnected. See [security guidance](../../docs/SECURITY.md).

[Complete installation guide](../../docs/GITHUB_QUICKSTART.md)

## Executable offline production planner

From this repository, run `PYTHONPATH=src python3 -B examples/export_creative_sourcekit.py --to "$HOME/creative-studio.zip"`. Verify the archive hash and extract into a new directory. Then run `python -I -B run.py --operation self-test` and `python -I -B run.py --operation demo --to /absolute/new/production`. See [supported briefs and safety boundaries](../../docs/kits/CREATIVE_SOURCEKIT.md). No native account is connected, and user briefs stay outside the immutable kit.

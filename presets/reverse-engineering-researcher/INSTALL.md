# Set up Reverse Engineering Researcher

Use Python 3.12+ and Git. These are portable source files, not a native Muse installation.

## From the repository

```bash
PYTHONPATH=src python3 -B examples/github_quickstart.py --role reverse-engineering-researcher --to ../my-reverse-engineering-researcher
```

On Windows PowerShell, set `$env:PYTHONPATH = "src"` and use `python`. Choose a new output directory; existing files are never overwritten. The source kit and its local inspection result do not authenticate a native host or grant tool access.

## From a download

Extract the ZIP into a new directory and follow its included guide. Keep existing user memory separate. For the latest runnable features, use current repository source and [the workflow guide](../../docs/WORKFLOWS.md).

Compare supplied observation records and document authorized behavioral analysis. No live capture or network probing is performed.

The local receipt is an integrity check, not a native installation or authenticated publisher signature. Optional connectors remain disconnected. See [security guidance](../../docs/SECURITY.md).

[Complete installation guide](../../docs/GITHUB_QUICKSTART.md)

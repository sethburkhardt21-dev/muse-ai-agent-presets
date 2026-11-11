# Set up Learning Coach

Use Python 3.12+ and Git. These are portable source files, not a native Muse installation.

## From the repository

```bash
PYTHONPATH=src python3 -B examples/github_quickstart.py --role learning-coach --to ../my-learning-coach
```

On Windows PowerShell, set `$env:PYTHONPATH = "src"` and use `python`. Choose a new output directory; existing files are never overwritten. The source kit and its local inspection result do not authenticate a native host or grant tool access.

## From a download

Extract the ZIP into a new directory and follow its included guide. Keep existing user memory separate. For the latest runnable features, use current repository source and [the workflow guide](../../docs/WORKFLOWS.md).

Build source-based study sessions, score local practice and preserve review history in SQLite.

The local receipt is an integrity check, not a native installation or authenticated publisher signature. Optional connectors remain disconnected. See [security guidance](../../docs/SECURITY.md).

[Complete installation guide](../../docs/GITHUB_QUICKSTART.md)

## Standalone executable kit

Build an independently runnable offline package using `examples/export_learning_sourcekit.py`.
Follow the [kit guide](../../docs/kits/LEARNING_SOURCEKIT.md) for verified extraction,
self-tests and usage. It does not install a native assistant or activate external connectors.

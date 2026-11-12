# Set up Coordinator

## Run the executable

[Download the executable ZIP](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/releases/download/v0.4.1-alpha/coordinator-executable-v0.4.1-alpha.zip) and compare its SHA-256 with [the release checksum list](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/releases/download/v0.4.1-alpha/SHA256SUMS.txt). Extract into a new directory and read its `START_HERE.md` or `INSTALL.md`. Python 3.12+ is required; follow the guide for additional dependencies such as Git.

## Create a profile copy

From the repository root:

```bash
PYTHONPATH=src python3 -B examples/github_quickstart.py --role coordinator --to ./my-coordinator
```

On Windows PowerShell, set `$env:PYTHONPATH = "src"` and use `python`. The destination must not exist. Read the generated guide before editing your copy, and keep personal memory and credentials outside the repository.

## Check before connecting

Run the package's supported local checks and review the files it creates. A hash receipt detects changed bytes; it does not establish a host identity or grant tool access. No external account, skill registration or scheduled job is activated by these steps.

[Role guide](README.md) · [Installation and saved data](../../docs/INSTALL_AND_PERSISTENCE.md)

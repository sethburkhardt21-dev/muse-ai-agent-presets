# Software Engineer

Reproduce bugs, apply reviewed patches and check the results in disposable Git repositories.

## Run the tool

[Download the executable kit](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/releases/download/v0.4.1-alpha/software-engineer-executable-v0.4.1-alpha.zip) and its [checksum list](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/releases/download/v0.4.1-alpha/SHA256SUMS.txt). Extract into a new folder and follow the included start guide.

From the repository root:

```bash
PYTHONPATH=src python3 -B examples/software_engineer_workflow_demo.py
```

## Customize the profile

Use [the setup guide](INSTALL.md) to create a separate working copy, then edit its instructions and preferences. Generated skills and connectors remain disabled until you configure an integration.

## Limits

Reviewed code runs under your operating-system account, not in a sandbox. Production TaskGuard and retention guarantees require separate acceptance. No native Muse installation is performed.

[Installation and saved data](../../docs/INSTALL_AND_PERSISTENCE.md)

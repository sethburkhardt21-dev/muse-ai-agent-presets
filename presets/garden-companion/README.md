# Garden Companion

Keep plant observations and review local calendar changes in SQLite.

## Run the tool

[Download the executable kit](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/releases/download/v0.4.1-alpha/garden-companion-executable-v0.4.1-alpha.zip) and its [checksum list](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/releases/download/v0.4.1-alpha/SHA256SUMS.txt). Extract into a new folder and follow the included start guide.

From the repository root:

```bash
PYTHONPATH=src python3 -B examples/garden_calendar_demo.py
```

## Customize the profile

Use [the setup guide](INSTALL.md) to create a separate working copy, then edit its instructions and preferences. Generated skills and connectors remain disabled until you configure an integration.

## Limits

The example does not write to an external calendar or provide biological diagnosis. No native Muse installation is performed.

[Package guide](../../docs/kits/GARDEN_SOURCEKIT.md) · [Installation and saved data](../../docs/INSTALL_AND_PERSISTENCE.md)

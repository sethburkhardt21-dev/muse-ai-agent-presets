# Learning Coach

Build study sessions from supplied sources, score practice and keep review history.

## Run the tool

[Download the executable kit](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/releases/download/v0.4.1-alpha/learning-coach-executable-v0.4.1-alpha.zip) and its [checksum list](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/releases/download/v0.4.1-alpha/SHA256SUMS.txt). Extract into a new folder and follow the included start guide.

From the repository root:

```bash
PYTHONPATH=src python3 -B examples/learning_session_demo.py
```

## Customize the profile

Use [the setup guide](INSTALL.md) to create a separate working copy, then edit its instructions and preferences. Generated skills and connectors remain disabled until you configure an integration.

## Limits

Scoring is literal and review timing is heuristic; neither is a clinical or mastery assessment. No native Muse installation is performed.

[Package guide](../../docs/kits/LEARNING_SOURCEKIT.md) · [Installation and saved data](../../docs/INSTALL_AND_PERSISTENCE.md)

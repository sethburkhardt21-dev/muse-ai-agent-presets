# Claims Adjudicator

Compare claims with supplied evidence and record qualifications or corrections.

## Run the tool

[Download the executable kit](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/releases/download/v0.4.1-alpha/claims-adjudicator-executable-v0.4.1-alpha.zip) and its [checksum list](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/releases/download/v0.4.1-alpha/SHA256SUMS.txt). Extract into a new folder and follow the included start guide.

From the repository root:

```bash
PYTHONPATH=src python3 -B examples/priority_slices.py
```

## Customize the profile

Use [the setup guide](INSTALL.md) to create a separate working copy, then edit its instructions and preferences. Generated skills and connectors remain disabled until you configure an integration.

## Limits

The output is a review of supplied evidence, not an independently authenticated verdict. No native Muse installation is performed.

[Package guide](../../docs/kits/CLAIMS_SOURCEKIT.md) · [Installation and saved data](../../docs/INSTALL_AND_PERSISTENCE.md)

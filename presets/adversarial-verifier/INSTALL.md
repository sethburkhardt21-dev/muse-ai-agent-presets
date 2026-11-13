# Set up Adversarial Verifier

This public starter contains instructions and configuration, not an installed assistant. Use the complete toolkit for any local examples linked from the [role guide](README.md).

## Create a profile copy

From the repository root:

```bash
python -B quickstart.py --role adversarial-verifier --to "$HOME/my-adversarial-verifier"
```

Use `python3` on macOS/Linux where appropriate; the wrapper also works in Windows PowerShell without setting `PYTHONPATH`. The destination must not exist. Read the generated guide before editing your copy, and keep personal memory and credentials outside the repository.

## Check before connecting

Run the package's supported local checks and review the files it creates. A hash receipt detects changed bytes; it does not establish a host identity or grant tool access. No external account, skill registration or scheduled job is activated by these steps.

[Role guide](README.md) · [Installation and saved data](../../docs/INSTALL_AND_PERSISTENCE.md)

For the complete source setup, expected outputs and troubleshooting, see [Get started](../../docs/GITHUB_QUICKSTART.md).

The source wrapper delegates to [examples/github_quickstart.py](../../examples/github_quickstart.py); use the wrapper above for the no-environment-variable route.

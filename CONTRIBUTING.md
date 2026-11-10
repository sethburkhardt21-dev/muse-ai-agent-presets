# Contributing

Contributions are welcome when they improve the public source kits, documentation, tests or accessibility.

## Before opening a pull request

1. Use a separate branch based on the current public `main`.
2. Keep private assistant memory, credentials, machine-specific records and internal work logs out of public files.
3. Make one bounded change with an executable example or a test where appropriate.
4. Run the source tests and privacy check.
5. Describe the user-visible improvement and any unsupported platforms or untested integrations.

```bash
PYTHONPATH=src python3 -B -m unittest discover -s tests -q
PYTHONPATH=src python3 -B -m muse_presets.cli audit-neutrality
PYTHONPATH=src python3 -B -m muse_presets.cli doctor
```

On Windows PowerShell, set `$env:PYTHONPATH = "src"` and use `python`.

The public repository is a **product source distribution**, not an engineering scratchpad. Do not add milestone-numbered progress documents, internal task trackers, temporary checkpoints or machine-local receipts to its default branch.

Source-only, independently tested, native-ready and deployed are distinct states. Do not claim a live agent or external tool was invoked unless an actual supported host operation was verified.

For coding conventions and role APIs, see [Extend the toolkit](docs/EXTENDING_GENERIC_AGENTS.md). For sensitive reports, follow [Security](SECURITY.md). Code and documentation contributions must be compatible with the [MIT license](LICENSE).

# Development and distribution

The public repository is the product source tree. Keep personal data, host-specific state and operational logs outside it. Product documentation should describe current behavior, supported platforms and how to use the software.

## Make a change

1. Create a branch from current public `main`.
2. Add a regression test and update the appropriate user guide.
3. Add new advertised functionality to `presets/capabilities.json` with real module and example paths.
4. Review the diff for private content and unsupported claims.
5. Refresh the integrity manifest, then run the checks below.
6. Submit a pull request. Both source tests and public-quality checks must pass before integration.

```bash
python -B scripts/check_public.py --refresh-manifest
python -B scripts/check_public.py
PYTHONPATH=src python3 -B -m unittest discover -s tests -v
PYTHONPATH=src python3 -B -m muse_presets.cli audit-neutrality
PYTHONPATH=src python3 -B -m muse_presets.cli doctor
```

On Windows, set `$env:PYTHONPATH = "src"` and use `python` for all commands.

## What the public-quality check covers

- Recursive product documentation, including individual role guides.
- Broken local links and internal-only operational documents.
- Symlinks, sensitive file formats and privacy/neutrality findings.
- Advertised modules and examples that are missing from the distribution.
- Exact file-set and SHA-256 manifest consistency.

Refreshing the manifest does **not** bypass these rules and does not publish anything. Private development history must never be merged into a public repository merely to synchronize source. Bring over reviewed product files with their regression tests; rewrite their user-facing documentation and verify the complete distribution.

## Packaging and versions

Use versioned downloads, checksum them and test extraction on supported platforms. Never silently replace an existing release ZIP to make it appear newer. A new source release needs a new tag and clear user-facing release notes. Existing downloads and their checksums remain valid historical artifacts.

Local, tested, native-connected and deployed are different capability states. The catalog and documentation must state the state actually supported by the software. Technical schema versions may remain stable across documentation improvements.

[Extend a specialist](EXTENDING_GENERIC_AGENTS.md) · [Security](SECURITY.md) · [Downloads](RELEASES.md)

# Host compatibility

The Python tools can run without a Muse account. Connecting a profile or tool to a model host is a separate integration: the host must identify the user, grant permissions and confirm that it actually loaded and invoked the tool.

Personal Muse/Hatch and Muse Code use different integration surfaces. Do not assume that a Muse Code plugin manifest or SDK method works in a personal Muse account. Check the receiving host's current documentation and supported interfaces. The toolkit does not include a certified native installation for either host.

## Inspect the local environment

From the repository root:

```bash
PYTHONPATH=src python3 -B -m muse_presets.cli host-doctor --host personal-hatch
```

Use `--host muse-code` to inspect that target instead. On Windows PowerShell, set `$env:PYTHONPATH = "src"` and use `python`.

The command reads a bounded inventory of candidate executables, process names, skill directories and optional SDK package metadata. It does not launch the discovered executable, log in, install software, call a model or change host state. Runtime versions can remain unknown when there is no trusted metadata source.

An exit code of 2 and `HOST_UNVERIFIED` are deliberate: a local process observation is not an authenticated host connection. Even `HOST_RUNTIME_PRESENT_UNATTESTED` means only that a candidate runtime was observed. It does not grant permission to use it.

## Inspect a skill catalog

Use paths approved for your own installation:

```bash
PYTHONPATH=src python3 -B -m muse_presets.cli skill-binding-doctor \
  --host personal-hatch \
  --custom-root /owner-approved/custom-skills \
  --registry /owner-approved/config/skills.yaml \
  --skill local_claim_gate \
  --skill local_provenance_vault \
  --skill local_iron_ledger
```

The inspector checks the named descriptors, Markdown, entrypoints and supported catalog fields. A `LOCAL_CATALOG_GAP` result means a local descriptor is missing from the inspected catalog. Any proposed YAML is a preview; the command does not register a skill or modify the catalog.

A file being present, a catalog saying `connected`, and a model being able to invoke a tool are different observations. Verify each separately.

## Portable instructions are a separate format

The source exporter can create 50 hyphen-named `SKILL.md` folders. The native-style role drafts retain their existing underscore-based identifiers and disabled `skills.yaml`. Format compatibility alone proves neither native registration nor model-selected invocation. Use only the format and supported import route accepted by your receiving host; do not copy a portable directory over a live registry.

## Verify a real integration

1. Confirm the receiving account, host version and supported API.
2. Stage the package in a new, approved location without replacing personal files.
3. Read back the host's registered tool or loaded instructions.
4. Invoke a bounded test through the actual host and retain its call identifier.
5. Check the result at the receiving system, including permission denial and restart behavior.

Do not substitute a shell execution, a manifest flag or a caller-supplied user ID for host authentication. Unsupported interfaces remain unverified; do not install another runtime to bypass the missing integration.

## Filesystem limits

Inspection rejects traversal and owner-controlled symlink or junction ancestors. Exact root-owned macOS `/var`, `/tmp` and `/etc` aliases into `/private` are allowed by the shared path checker. These checks reduce accidental path misuse but are not an atomic filesystem sandbox or a native identity guarantee.

[Architecture](ARCHITECTURE.md) · [Installation and saved data](INSTALL_AND_PERSISTENCE.md)

# Muse personal host vs Muse Code: compatibility contract

**Primary:** personal Muse/Hatch agents and fullstack Muse Spaces. **Secondary:** Muse Code developer host. These are different installation targets; a Muse Code `.muse-plugin` manifest does not establish personal Hatch support.

Personal Muse/Hatch must independently prove home-file injection, effective instruction precedence, skill catalog resolution, state and memory persistence, authenticated artifact/Space callback, scheduled wake, original subchat ID, connector scopes and owner grants. Record the current host SDK/version/schema rather than trusting historical research. Never copy first-party private runtime source.

Muse Code developer documentation currently describes skills, hooks, MCP and plugin manifests, and warns the plugin surface is Developer Preview. Qualified installations require local review and approval. See [official extension overview](https://meta-models.github.io/muse-code-sdk/next/guides/extend/) and [plugin guidance](https://meta-models.github.io/muse-code-sdk/next/guides/plugins/).

The portable R32 implementation now includes [generic native acceptance](GENERIC_NATIVE_ACCEPTANCE.md) for all eleven specialist roles. It creates independent source-only packets and correlated fixture checks. These do not implement or imply a receiving account's authenticated native skill-search or model invocation.\n\n## Host doctor phases

- `D0` offline catalog and renderer checks (this repository can execute now).
- `D1` real host capability discovery (no inferred tool names).
- `D2` install into a fresh owner-approved test account/workspace, read back exact bytes and manifest.
- `D3` fresh model turn chooses one skill and produces provider-issued invocation/receipt.
- `D4` verify actual outcome, update/restart, permission-denied negative and rollback.

If a feature is missing, log `HOST_UNSUPPORTED`, never create a second controller to bypass it. Integrations never read or publish owner secrets. No unsupported filesystem write is assumed to update a managed Space.


## R32.S2 read-only host inventory (source-only)

`PYTHONPATH=src python -m muse_presets.cli host-doctor --host personal-hatch` reads only candidate executable presence, short process names, installed skill directory names and optional `@hatch/space-sdk` package metadata. It never launches a candidate executable, including with `--version`: a caller-supplied executable may mutate state. Without a supported trusted host metadata source, its runtime version is `null` and its status is `HOST_UNVERIFIED`. For the independent developer product use `--host muse-code`; it looks for the Muse Code binary and **does not infer Hatch agent support**. No login, installation, model call, network request, state mutation or external recipient action occurs. The probe cannot attest the local machine and prints `provenance: UNATTESTED_LOCAL_PROCESS_OBSERVATION`.

The optional Space SDK metadata reader permits the three canonical, root-owned macOS `/var`, `/tmp` and `/etc` aliases into `/private`, using the shared trusted-root predicate; arbitrary symlinked ancestors and symlinked SDK files remain denied. This changes only an unauthenticated version hint and never grants native authority. The macOS alias and malicious-user-symlink regression cases are mandatory in cross-host acceptance.

Every host invocation, owner grant, skill-search capability, authenticated Space callback, schedule, subchat and external receipt stays `UNVERIFIED`; authority flags are always `false`. Its CLI intentionally exits 2 even when it discovers a running binary: a local observation is not a passed native integration gate. A service binary's `--version` is **not** a host-issued actor/session credential. Never use `HOST_RUNTIME_PRESENT_UNATTESTED` as a reason to install, merge owner files, run tools or elevate privileges. D2–D4 require separate authorized host/recipient evidence.

Muse Code's independently documented `muse serve` protocol and `@muse-code/sdk` do not imply those surfaces exist in personal Hatch. Do not install or authenticate Muse Code as part of the personal Hatch gate.


## R32.S2 native custom-skill catalog reconciliation (read-only)

One reference-host configuration suggests checking (1) a custom
`SKILL.md` trigger, (2) `skill.yaml` metadata, (3) a local catalog,
(4) the declared local entrypoint, (5) an actual provider-supported
model-selected skill-discovery and invocation tool, and (6) the
provider-issued call ID plus independent recipient readback. These are
separate gates, not a portable API guarantee. Host tool names MUST be
discovered in the authenticated receiving session; never assume a tool
name from another owner's runtime. No private reference data is shipped.

Source-only audit command, run in an owner-authorized local shell:

```sh
PYTHONPATH=src python3 -B -m muse_presets.cli skill-binding-doctor \
  --host personal-hatch \
  --custom-root /owner-approved/custom-skills \
  --registry /owner-approved/config/skills.yaml \
  --skill local_claim_gate \
  --skill local_provenance_vault \
  --skill local_iron_ledger
```

This checks only the three explicitly named custom skills. It validates their
descriptor metadata, local Markdown and optional entrypoint presence, and a
strict, duplicate-rejecting read of the observed host-local `skills.yaml`
version-1 status subset. It accepts optional, bounded `SKILL.md` front matter.
A `connected` catalog value is not the same as `available` for a skill.
The resulting `proposal.snippet` is inert suggested YAML with a SHA-256
base hash: no native registration, memory rewrite or catalog mutation occurs.

Source-root and registry admission rejects literal `..` traversal and all
owner-controlled symlink or junction ancestors before reading descriptor or
catalog bytes. Only exact, root-owned macOS `/var`, `/tmp` and `/etc` aliases
into `/private` are permitted. These local checks are not atomic `openat`
attestations; a future owner-approved catalog writer must recheck its base
hash and authority before any effect.

In a separately held reference-host observation, three present skill
descriptors were missing from a host-local catalog. That demonstrates why
source presence and catalog advertisement must be tested independently;
it does **not** prove what the receiving model can discover or invoke.
The generic inspector reports `LOCAL_CATALOG_GAP` without writing the
catalog. Exact reference account names, fingerprints and receipts stay
outside the distributable package.

Even after an explicitly authorized catalog admission, a fresh personal
Hatch owner session must prove the exact skill is discoverable by the host,
a fresh model turn selects and invokes it using the supported native tool,
the host issues a tool-call ID bound to the current actor/session and
approved scope, and the original recipient independently reopens the result.
The tool cannot manufacture this proof by shell execution or by setting
`host_authenticated=true`. Unavailable host APIs yield `UNVERIFIED`, not
simulated acceptance. Keep D2-D4 and any live effect or public release on
HOLD until the receiving owner and provider establish those observations.

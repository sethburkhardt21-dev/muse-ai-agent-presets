# Muse personal host vs Muse Code: compatibility contract

**Primary:** personal Muse/Hatch agents and fullstack Muse Spaces. **Secondary:** Muse Code developer host. These are different installation targets; a Muse Code `.muse-plugin` manifest does not establish personal Hatch support.

Personal Muse/Hatch must independently prove home-file injection, effective instruction precedence, skill catalog resolution, state and memory persistence, authenticated artifact/Space callback, scheduled wake, original subchat ID, connector scopes and owner grants. Record the current host SDK/version/schema rather than trusting historical research. Never copy first-party private runtime source.

Muse Code developer documentation currently describes skills, hooks, MCP and plugin manifests, and warns the plugin surface is Developer Preview. Qualified installations require local review and approval. See [official extension overview](https://meta-models.github.io/muse-code-sdk/next/guides/extend/) and [plugin guidance](https://meta-models.github.io/muse-code-sdk/next/guides/plugins/).

## Host doctor phases

- `D0` offline catalog and renderer checks (this repository can execute now).
- `D1` real host capability discovery (no inferred tool names).
- `D2` install into a fresh owner-approved test account/workspace, read back exact bytes and manifest.
- `D3` fresh model turn chooses one skill and produces provider-issued invocation/receipt.
- `D4` verify actual outcome, update/restart, permission-denied negative and rollback.

If a feature is missing, log `HOST_UNSUPPORTED`, never create a second controller to bypass it. Integrations never read or publish owner secrets. No unsupported filesystem write is assumed to update a managed Space.

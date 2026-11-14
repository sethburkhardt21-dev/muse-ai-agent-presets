# 150+ Custom Connectors for Muse

Find the services you use, choose the connector that fits your task, and copy its setup prompt.

**[Open the searchable directory](index.html)** · [Browse all 151 on GitHub](CATALOG.md)

The directory includes every connector in the pinned source catalog, organized by category and relevant specialist. Each entry gives the service's capabilities, authentication prerequisites, allowed hosts, versioned setup guide and a ready-to-copy message. Search works in the downloaded HTML file; no account or server is required to browse.

## Connect a service

1. Search for the service or choose a category/specialist.
2. Read the entry's access and setup information.
3. Copy **Set up with Muse**, paste it into your Muse conversation and choose the actual task.
4. Complete sign-in through the supported secure flow. Keep raw keys and passwords out of chat.
5. Start with the connector's status or read operation, then approve the actions you need.

Use the exact provider instructions for account plans, regions, scopes and fees. The source guide is linked at a fixed version so you can inspect changes before updating. Consult [Meta's connector documentation](https://platform.muse.ai/docs) for current permission behavior. Custom-connector support does not imply endorsement of every external implementation.

## Source, updates and attribution

Descriptions and authentication summaries are adapted from **bluman1/muse-connectors**, MIT licensed; its complete copyright and license are in [UPSTREAM_LICENSE.txt](UPSTREAM_LICENSE.txt). We preserve all 151 metadata entries and the source hashes. Connector programs are not bundled or executed by this directory.

Run `python -B scripts/connector_catalog.py check` from the toolkit root. To report upstream changes without applying them, obtain the newer upstream `docs/connectors.json`, then run `python -B scripts/connector_catalog.py compare --candidate /absolute/new-connectors.json`. The report lists additions, removals and changed source metadata. Review rights, authentication changes and source files before accepting any update.

## Common setup problems

A missing secure credential flow, unsupported provider authentication type, insufficient account scope or unavailable service plan needs its specific remedy. Preserve the prior connector and inspect the exact failed operation rather than blindly retrying a write. A failed status check is not permission to disable approval controls. Disconnect through the receiving host/service and revoke unused access where appropriate.

[Start here](../v1/START_HERE.md) · [Source provenance](PROVENANCE.json) · [Machine-readable catalog](catalog.json)

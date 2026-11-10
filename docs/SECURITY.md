# Security, privacy and responsible use

This repository is a collection of **source files and local examples**. It is not a hosted agent or an OS sandbox, and it does not grant access to any account or computer.

## Safe defaults

- Generated packages refuse to overwrite existing user or assistant data.
- Optional connectors, native skills, Family Link transport and scheduling are disabled or unconfigured.
- Local SHA-256 hashes detect changes to supplied bytes; they are not publisher signatures or authenticated user consent.
- Source descriptions and synthetic fixtures are not proof that a model executed a tool or that a recipient received a message.

## Protect your data

Do not publish API keys, access tokens, host identifiers, private memory, private chat transcripts, full user profiles, personal contacts or local operation receipts. Keep actual owner credentials and machine-specific settings in separately protected storage.

Only run Python programs from sources you trust. Some examples execute repository tests under the invoking OS account: they can access that account's filesystem and network. **This toolkit does not provide an isolation sandbox.**

## Source and distribution

The original public files are offered under the [MIT license](../LICENSE). The project's first-party generic code is published for reuse; third-party packages, media and SDKs have their own applicable terms. Private development repositories and histories are not bundled in this public distribution.

A source release should contain only its intended files, accurate instructions and validated examples. Changing public documentation does not modify the bytes of previously published release ZIPs. Refer to [Releases](RELEASES.md) for distribution details.

## Report a vulnerability

Follow the [security policy](../SECURITY.md) rather than placing exploitable details or credentials in a public issue. Avoid using this project to test systems without authorization.

[Get started](GITHUB_QUICKSTART.md) · [Connectors](CONNECTORS.md) · [Capabilities](CAPABILITIES.md)
